"""Apply deterministic transformations to osu! skin PNG files."""

import argparse
import json
import os
import uuid
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, UnidentifiedImageError


DESCRIPTION = "scale, crop, recolor, or create HD/SD image variants"
FILTERS = {
    "nearest": Image.Resampling.NEAREST,
    "lanczos": Image.Resampling.LANCZOS,
    "bicubic": Image.Resampling.BICUBIC,
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="source PNG or directory")
    parser.add_argument("--operation", required=True, choices=("scale", "crop", "recolor", "hd-to-sd", "sd-to-hd"))
    parser.add_argument("--output", type=Path, required=True, help="output PNG or directory")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--left", type=int, help="crop left coordinate; defaults to centered")
    parser.add_argument("--top", type=int, help="crop top coordinate; defaults to centered")
    parser.add_argument("--color", help="recolor target as R,G,B or R,G,B,A")
    parser.add_argument("--filter", choices=tuple(FILTERS), default="lanczos")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")


def _parse_color(value: str | None) -> tuple[int, int, int, int]:
    if not value:
        raise ValueError("--color is required for recolor")
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) == 3:
        parts.append(255)
    if len(parts) != 4 or any(part < 0 or part > 255 for part in parts):
        raise ValueError("--color must be R,G,B or R,G,B,A with values from 0 to 255")
    return tuple(parts)  # type: ignore[return-value]


def transform_image(image: Image.Image, args: argparse.Namespace) -> Image.Image:
    operation = args.operation
    if operation == "scale":
        if args.width is None and args.height is None:
            raise ValueError("scale requires --width or --height")
        width = (
            args.width
            if args.width is not None
            else round(image.width * args.height / image.height)
        )
        height = (
            args.height
            if args.height is not None
            else round(image.height * args.width / image.width)
        )
        if width <= 0 or height <= 0:
            raise ValueError("target dimensions must be positive")
        return image.resize((width, height), FILTERS[args.filter])
    if operation == "crop":
        if args.width is None or args.height is None:
            raise ValueError("crop requires --width and --height")
        left = args.left if args.left is not None else (image.width - args.width) // 2
        top = args.top if args.top is not None else (image.height - args.height) // 2
        if args.width <= 0 or args.height <= 0 or left < 0 or top < 0 or left + args.width > image.width or top + args.height > image.height:
            raise ValueError("crop rectangle must remain inside the source image")
        return image.crop((left, top, left + args.width, top + args.height))
    if operation == "recolor":
        red, green, blue, opacity = _parse_color(args.color)
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A").point(lambda value: value * opacity // 255)
        output = Image.new("RGBA", rgba.size, (red, green, blue, 0))
        output.putalpha(alpha)
        return output
    if operation == "hd-to-sd" and (image.width % 2 or image.height % 2):
        raise ValueError("hd-to-sd requires even source dimensions for an exact 2:1 pair")
    factor = 0.5 if operation == "hd-to-sd" else 2
    width = int(image.width * factor)
    height = int(image.height * factor)
    if width <= 0 or height <= 0:
        raise ValueError("scaled dimensions must be positive")
    return image.resize((width, height), FILTERS[args.filter])


def _sources(path: Path, recursive: bool) -> tuple[Path, list[Path]]:
    resolved = path.expanduser().resolve()
    if resolved.is_file():
        if resolved.suffix.lower() != ".png":
            raise ValueError("source file must be PNG")
        return resolved.parent, [resolved]
    if not resolved.is_dir():
        raise FileNotFoundError(f"source path does not exist: {resolved}")
    iterator = resolved.rglob("*") if recursive else resolved.iterdir()
    return resolved, sorted(item for item in iterator if item.is_file() and item.suffix.lower() == ".png")


def _output_path(source: Path, root: Path, output: Path, operation: str, batch: bool) -> Path:
    if batch:
        relative = source.relative_to(root)
        stem = relative.stem
        if operation == "hd-to-sd":
            stem = stem[:-3] if stem.lower().endswith("@2x") else stem
        elif operation == "sd-to-hd" and not stem.lower().endswith("@2x"):
            stem += "@2x"
        return output.expanduser().resolve() / relative.parent / f"{stem}.png"
    resolved = output.expanduser().resolve()
    return resolved / source.name if resolved.exists() and resolved.is_dir() else resolved


def _save_atomic(image: Image.Image, output: Path, source_info: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{uuid.uuid4().hex}.tmp.png")
    options = {key: source_info[key] for key in ("icc_profile", "dpi") if key in source_info}
    try:
        image.save(temporary, "PNG", **options)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def execute_transform(args: argparse.Namespace) -> dict[str, object]:
    root, sources = _sources(args.path, args.recursive)
    batch = args.path.expanduser().resolve().is_dir()
    if batch and args.output.suffix.lower() == ".png":
        raise ValueError("directory input requires an output directory")
    if args.operation == "hd-to-sd":
        sources = [path for path in sources if path.stem.lower().endswith("@2x")]
    elif args.operation == "sd-to-hd":
        sources = [path for path in sources if not path.stem.lower().endswith("@2x")]
    if not sources:
        raise ValueError(f"no PNG files match the {args.operation} operation")
    plans = []
    outputs: set[Path] = set()
    for source in sources:
        output = _output_path(source, root, args.output, args.operation, batch)
        if output in outputs:
            raise ValueError(f"multiple inputs map to the same output: {output}")
        outputs.add(output)
        if source == output and not args.overwrite:
            raise ValueError("refusing to overwrite source without --overwrite")
        if output.exists() and source != output and not args.overwrite:
            raise FileExistsError(f"output exists; pass --overwrite: {output}")
        with Image.open(source) as opened:
            if opened.format != "PNG":
                raise ValueError(f"source is not PNG: {source}")
            opened.load()
            source_info = dict(opened.info)
            transformed = transform_image(opened, args)
        plan = {"source": str(source), "output": str(output), "source_size": list(opened.size), "output_size": list(transformed.size), "written": not args.dry_run}
        plans.append(plan)
        if not args.dry_run:
            _save_atomic(transformed, output, source_info)
    return {"ok": True, "operation": args.operation, "count": len(plans), "dry_run": args.dry_run, "files": plans}


def run(args: argparse.Namespace) -> int:
    try:
        result = execute_transform(args)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Operation: {result['operation']}; files: {result['count']}")
            for item in result["files"]:
                print(f"- {item['source']} -> {item['output']} ({item['source_size']} -> {item['output_size']})")
        return 0
    except (FileNotFoundError, FileExistsError, UnidentifiedImageError, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
