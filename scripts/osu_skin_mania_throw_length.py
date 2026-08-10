"""Change the transparent top-row count of an osu!mania Hold Body PNG."""

import argparse
import json
import os
import uuid
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, UnidentifiedImageError


DESCRIPTION = "change the transparent top-row count of a Mania Hold Body image"
TAIL_SOURCE_ROWS = 1000


class ThrowLengthError(ValueError):
    """Raised when a Hold Body image cannot be transformed safely."""


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="source Hold Body PNG")
    parser.add_argument(
        "--throw-length",
        type=int,
        required=True,
        help="target number of fully transparent rows at the top",
    )
    parser.add_argument("--output", type=Path, required=True, help="output PNG")
    parser.add_argument("--dry-run", action="store_true", help="report a plan without writing")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def count_top_transparent_rows(image: Image.Image) -> int:
    """Count consecutive rows whose alpha values are all zero."""
    alpha = image.getchannel("A")
    width, height = alpha.size
    pixels = memoryview(alpha.tobytes())
    for row in range(height):
        start = row * width
        if any(pixels[start : start + width]):
            return row
    return height


def _repeat_tail(image: Image.Image, rows: int) -> Image.Image:
    """Fill rows by cycling through the original image's bottom 1000 rows."""
    width, height = image.size
    source_height = min(TAIL_SOURCE_ROWS, height)
    source = image.crop((0, height - source_height, width, height))
    repeated = Image.new("RGBA", (width, rows), (0, 0, 0, 0))
    offset = 0
    while offset < rows:
        chunk_height = min(source_height, rows - offset)
        repeated.paste(source.crop((0, 0, width, chunk_height)), (0, offset))
        offset += chunk_height
    return repeated


def change_throw_length(image: Image.Image, target: int) -> tuple[Image.Image, dict[str, object]]:
    """Shift pixels vertically while preserving the original canvas size."""
    rgba = image.convert("RGBA")
    width, height = rgba.size
    current = count_top_transparent_rows(rgba)
    if current == height:
        raise ThrowLengthError("source image is fully transparent")
    if target < 0 or target >= height:
        raise ThrowLengthError(f"throw length must be between 0 and {height - 1}")

    output = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    bottom_fill_rows = 0
    bottom_cropped_rows = 0
    if target > current:
        shift = target - current
        output.paste(rgba.crop((0, 0, width, height - shift)), (0, shift))
        direction = "down"
        bottom_cropped_rows = shift
    elif target < current:
        shift = current - target
        output.paste(rgba.crop((0, shift, width, height)), (0, 0))
        bottom_fill_rows = shift
        output.paste(_repeat_tail(rgba, shift), (0, height - shift))
        direction = "up"
    else:
        shift = 0
        output = rgba.copy()
        direction = "unchanged"

    detected = count_top_transparent_rows(output)
    if detected != target:
        raise ThrowLengthError(
            f"output validation failed: expected {target} transparent rows, detected {detected}"
        )

    result = {
        "ok": True,
        "width": width,
        "height": height,
        "current_throw_length": current,
        "target_throw_length": target,
        "direction": direction,
        "shift_rows": shift,
        "bottom_fill_rows": bottom_fill_rows,
        "bottom_cropped_rows": bottom_cropped_rows,
        "tail_source_rows": min(TAIL_SOURCE_ROWS, height) if bottom_fill_rows else 0,
    }
    return output, result


def _save_png_atomic(image: Image.Image, output: Path, source_info: dict[str, object]) -> None:
    output = output.expanduser().resolve()
    if output.suffix.lower() != ".png":
        raise ThrowLengthError("output path must use the .png extension")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{uuid.uuid4().hex}.tmp.png")
    save_options = {
        key: source_info[key]
        for key in ("icc_profile", "dpi")
        if key in source_info
    }
    try:
        image.save(temporary, format="PNG", **save_options)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def run(args: argparse.Namespace) -> int:
    source = args.path.expanduser().resolve()
    try:
        if not source.is_file():
            raise ThrowLengthError(f"source PNG does not exist: {source}")
        if source.suffix.lower() != ".png":
            raise ThrowLengthError("source path must use the .png extension")
        with Image.open(source) as opened:
            if opened.format != "PNG":
                raise ThrowLengthError("source file is not a valid PNG")
            source_info = dict(opened.info)
            output_image, result = change_throw_length(opened, args.throw_length)
        output = args.output.expanduser().resolve()
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
                if written.size != output_image.size:
                    raise ThrowLengthError("written image dimensions changed unexpectedly")
                written_throw_length = count_top_transparent_rows(written.convert("RGBA"))
                if written_throw_length != args.throw_length:
                    raise ThrowLengthError(
                        "written image does not contain the requested transparent top rows"
                    )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Source: {result['source']}")
            print(f"Output: {result['output']}")
            print(f"Size: {result['width']}x{result['height']} (unchanged)")
            print(
                f"Throw length: {result['current_throw_length']} -> "
                f"{result['target_throw_length']}"
            )
            print(f"Direction: {result['direction']} ({result['shift_rows']} rows)")
            print(f"Bottom fill: {result['bottom_fill_rows']} rows")
            print(f"Bottom crop: {result['bottom_cropped_rows']} rows")
            print(f"Written: {'no (dry run)' if args.dry_run else 'yes'}")
        return 0
    except (ThrowLengthError, UnidentifiedImageError, OSError) as error:
        if args.json:
            print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        else:
            print(f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
