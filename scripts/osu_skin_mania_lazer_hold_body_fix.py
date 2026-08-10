"""Repair lazer stretching of an osu!mania Hold Body PNG."""

import argparse
import json
import os
import uuid
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, UnidentifiedImageError


DESCRIPTION = "repair lazer stretching of a Mania Hold Body image"
TARGET_HEIGHT = 32800
BOTTOM_SOURCE_ROWS = 1000
LIMITATION = (
    "repairs stretching introduced by lazer for an undeformed source image; "
    "it cannot reconstruct or adapt an appearance that already depended on stable client stretching"
)


class LazerHoldBodyFixError(ValueError):
    """Raised when a Hold Body image cannot be transformed safely."""


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="source NoteImage#L PNG")
    parser.add_argument(
        "--column-width",
        type=float,
        required=True,
        help="ColumnWidth value from the target Keys:N section",
    )
    parser.add_argument("--output", type=Path, required=True, help="output PNG")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing an existing output")
    parser.add_argument("--dry-run", action="store_true", help="report a plan without writing")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def rendered_column_width(column_width: float) -> int:
    if column_width <= 0:
        raise LazerHoldBodyFixError("column width must be positive")
    target = int(round(column_width * 1.6))
    if target <= 0:
        raise LazerHoldBodyFixError("rendered column width rounded to zero")
    return target


def _repeat_bottom(
    source_image: Image.Image, target_width: int, rows: int
) -> tuple[Image.Image, int, int]:
    source_width, source_height = source_image.size
    source_rows = min(BOTTOM_SOURCE_ROWS, source_height)
    source = source_image.crop(
        (0, source_height - source_rows, source_width, source_height)
    )
    pattern_height = max(1, int(round(source_rows * target_width / source_width)))
    pattern = source.resize((target_width, pattern_height), Image.Resampling.LANCZOS)
    repeated = Image.new("RGBA", (target_width, rows), (0, 0, 0, 0))
    offset = 0
    while offset < rows:
        chunk_height = min(pattern_height, rows - offset)
        repeated.paste(pattern.crop((0, 0, target_width, chunk_height)), (0, offset))
        offset += chunk_height
    return repeated, source_rows, pattern_height


def repair_hold_body(
    image: Image.Image, column_width: float
) -> tuple[Image.Image, dict[str, object]]:
    rgba = image.convert("RGBA")
    if rgba.width <= 0 or rgba.height <= 0:
        raise LazerHoldBodyFixError("source image dimensions must be positive")

    target_width = rendered_column_width(column_width)
    scaled_height = max(1, int(round(rgba.height * target_width / rgba.width)))
    scaled = rgba.resize((target_width, scaled_height), Image.Resampling.LANCZOS)

    cropped_rows = 0
    filled_rows = 0
    bottom_source_rows = 0
    bottom_pattern_rows = 0
    if scaled_height > TARGET_HEIGHT:
        output = scaled.crop((0, 0, target_width, TARGET_HEIGHT))
        operation = "crop_bottom"
        cropped_rows = scaled_height - TARGET_HEIGHT
    elif scaled_height < TARGET_HEIGHT:
        filled_rows = TARGET_HEIGHT - scaled_height
        repeated, bottom_source_rows, bottom_pattern_rows = _repeat_bottom(
            rgba, target_width, filled_rows
        )
        output = Image.new("RGBA", (target_width, TARGET_HEIGHT), (0, 0, 0, 0))
        output.paste(scaled, (0, 0))
        output.paste(repeated, (0, scaled_height))
        operation = "repeat_bottom"
    else:
        output = scaled
        operation = "scale_only"

    return output, {
        "ok": True,
        "column_width": column_width,
        "target_width": target_width,
        "target_height": TARGET_HEIGHT,
        "source_size": [rgba.width, rgba.height],
        "scaled_size": [target_width, scaled_height],
        "output_size": [output.width, output.height],
        "operation": operation,
        "bottom_cropped_rows": cropped_rows,
        "bottom_fill_rows": filled_rows,
        "bottom_source_rows": bottom_source_rows,
        "bottom_pattern_rows": bottom_pattern_rows,
        "resampling": "Lanczos3",
        "limitation": LIMITATION,
    }


def _save_png_atomic(image: Image.Image, output: Path, source_info: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{uuid.uuid4().hex}.tmp.png")
    options = {key: source_info[key] for key in ("icc_profile", "dpi") if key in source_info}
    try:
        image.save(temporary, "PNG", **options)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def run(args: argparse.Namespace) -> int:
    source = args.path.expanduser().resolve()
    output = args.output.expanduser().resolve()
    try:
        if not source.is_file() or source.suffix.lower() != ".png":
            raise LazerHoldBodyFixError(f"source PNG does not exist: {source}")
        if output.suffix.lower() != ".png":
            raise LazerHoldBodyFixError("output path must use the .png extension")
        if output.exists() and not args.overwrite:
            raise FileExistsError(f"output exists; pass --overwrite: {output}")
        if source == output and not args.overwrite:
            raise LazerHoldBodyFixError("refusing to overwrite source without --overwrite")

        with Image.open(source) as opened:
            if opened.format != "PNG":
                raise LazerHoldBodyFixError("source file is not a valid PNG")
            opened.load()
            source_info = dict(opened.info)
            output_image, result = repair_hold_body(opened, args.column_width)

        result.update(
            {
                "source": str(source),
                "output": str(output),
                "dry_run": args.dry_run,
                "written": not args.dry_run,
            }
        )
        if not args.dry_run:
            _save_png_atomic(output_image, output, source_info)
            with Image.open(output) as written:
                if written.size != (result["target_width"], TARGET_HEIGHT):
                    raise LazerHoldBodyFixError("written image dimensions failed validation")

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Source: {source}")
            print(f"Output: {output}")
            print(f"Size: {result['source_size']} -> {result['output_size']}")
            print(f"Operation: {result['operation']}")
            print(f"Written: {'no (dry run)' if args.dry_run else 'yes'}")
            print(f"Limitation: {LIMITATION}")
        return 0
    except (FileNotFoundError, FileExistsError, LazerHoldBodyFixError, UnidentifiedImageError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
