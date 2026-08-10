"""Repair lazer stretching of osu!mania KeyImage and KeyImageD PNG files."""

import argparse
import json
import os
import uuid
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .osu_skin_mania_lazer_hold_body_fix import rendered_column_width


DESCRIPTION = "repair lazer stretching of a Mania KeyImage or KeyImageD image"
LIMITATION = (
    "repairs stretching introduced by lazer for an undeformed source image; "
    "it cannot reconstruct or adapt an appearance that already depended on stable client stretching"
)


class LazerKeyFixError(ValueError):
    """Raised when a Key image cannot be transformed safely."""


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="source KeyImage# or KeyImage#D PNG")
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


def is_hd_filename(path: Path) -> bool:
    return path.stem.lower().endswith("@2x")


def repair_key(
    image: Image.Image, column_width: float, hd: bool = False
) -> tuple[Image.Image | None, dict[str, object]]:
    rgba = image.convert("RGBA")
    alpha_bbox = rgba.getchannel("A").getbbox()
    try:
        base_target_width = rendered_column_width(column_width)
    except ValueError as error:
        raise LazerKeyFixError(str(error)) from error
    target_width = base_target_width * (2 if hd else 1)
    common: dict[str, object] = {
        "ok": True,
        "column_width": column_width,
        "hd": hd,
        "base_target_width": base_target_width,
        "target_width": target_width,
        "source_size": [rgba.width, rgba.height],
        "resampling": "Lanczos3",
        "limitation": LIMITATION,
    }
    if alpha_bbox is None:
        common.update(
            {
                "skipped": True,
                "reason": "source image is fully transparent",
                "alpha_bbox": None,
                "output_size": None,
            }
        )
        return None, common

    left, top, right, bottom = alpha_bbox
    left_padding = left
    bottom_padding = rgba.height - bottom
    subject = rgba.crop(alpha_bbox)
    subject_target_width = target_width - left_padding
    if subject_target_width <= 0:
        raise LazerKeyFixError(
            f"target width {target_width} is not greater than left padding {left_padding}"
        )
    subject_target_height = max(
        1, int(round(subject.height * subject_target_width / subject.width))
    )
    scaled = subject.resize(
        (subject_target_width, subject_target_height), Image.Resampling.LANCZOS
    )
    output_height = subject_target_height + bottom_padding
    output = Image.new("RGBA", (target_width, output_height), (0, 0, 0, 0))
    output.paste(scaled, (left_padding, 0))

    common.update(
        {
            "skipped": False,
            "alpha_bbox": [left, top, right, bottom],
            "left_padding": left_padding,
            "removed_top_padding": top,
            "bottom_padding": bottom_padding,
            "subject_size": [subject.width, subject.height],
            "scaled_subject_size": [scaled.width, scaled.height],
            "output_size": [output.width, output.height],
        }
    )
    return output, common


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
            raise LazerKeyFixError(f"source PNG does not exist: {source}")
        if output.suffix.lower() != ".png":
            raise LazerKeyFixError("output path must use the .png extension")

        with Image.open(source) as opened:
            if opened.format != "PNG":
                raise LazerKeyFixError("source file is not a valid PNG")
            opened.load()
            source_info = dict(opened.info)
            output_image, result = repair_key(
                opened, args.column_width, is_hd_filename(source)
            )

        result.update(
            {
                "source": str(source),
                "output": str(output),
                "dry_run": args.dry_run,
                "written": output_image is not None and not args.dry_run,
            }
        )
        if output_image is not None:
            if output.exists() and not args.overwrite:
                raise FileExistsError(f"output exists; pass --overwrite: {output}")
            if source == output and not args.overwrite:
                raise LazerKeyFixError("refusing to overwrite source without --overwrite")
            if not args.dry_run:
                _save_png_atomic(output_image, output, source_info)
                with Image.open(output) as written:
                    if list(written.size) != result["output_size"]:
                        raise LazerKeyFixError("written image dimensions failed validation")

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["skipped"]:
            print(f"Skipped: {source} is fully transparent")
            print(f"Limitation: {LIMITATION}")
        else:
            print(f"Source: {source}")
            print(f"Output: {output}")
            print(f"Size: {result['source_size']} -> {result['output_size']}")
            print(f"Alpha bbox: {result['alpha_bbox']}")
            print(f"Written: {'no (dry run)' if args.dry_run else 'yes'}")
            print(f"Limitation: {LIMITATION}")
        return 0
    except (FileNotFoundError, FileExistsError, LazerKeyFixError, UnidentifiedImageError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
