"""Inspect osu! skin images, alpha data, HD pairs, and animation frames."""

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ._paths import default_db_path


DESCRIPTION = "inspect dimensions, alpha, HD/SD pairs, and animation frames"
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"})


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="image file or skin directory")
    parser.add_argument("--recursive", action="store_true", help="inspect nested directories")
    parser.add_argument(
        "--animation", action="store_true", help="group database-declared animation frames"
    )
    parser.add_argument("--transparent-rows", action="store_true", help="measure transparent edges")
    parser.add_argument("--transparent-rgb", action="store_true", help="inspect RGB beneath alpha=0")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def discover_images(path: Path, recursive: bool = False) -> list[Path]:
    resolved = path.expanduser().resolve()
    if resolved.is_file():
        return [resolved]
    if not resolved.is_dir():
        raise FileNotFoundError(f"image path does not exist: {resolved}")
    iterator = resolved.rglob("*") if recursive else resolved.iterdir()
    return sorted(item for item in iterator if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS)


def _transparent_edges(alpha: Image.Image) -> dict[str, int]:
    width, height = alpha.size
    data = memoryview(alpha.tobytes())
    top = 0
    while top < height and not any(data[top * width : (top + 1) * width]):
        top += 1
    bottom = 0
    while bottom < height and not any(data[(height - bottom - 1) * width : (height - bottom) * width]):
        bottom += 1
    left = 0
    while left < width and not any(data[row * width + left] for row in range(height)):
        left += 1
    right = 0
    while right < width and not any(data[row * width + width - right - 1] for row in range(height)):
        right += 1
    return {"top": top, "bottom": bottom, "left": left, "right": right}


def inspect_image(path: Path, transparent_rows: bool, transparent_rgb: bool) -> dict[str, object]:
    with Image.open(path) as opened:
        opened.load()
        result: dict[str, object] = {
            "path": str(path),
            "format": opened.format,
            "mode": opened.mode,
            "width": opened.width,
            "height": opened.height,
            "file_size": path.stat().st_size,
            "frames": getattr(opened, "n_frames", 1),
            "bands": list(opened.getbands()),
            "has_alpha": "A" in opened.getbands() or "transparency" in opened.info,
        }
        rgba = opened.convert("RGBA")
    alpha = rgba.getchannel("A")
    histogram = alpha.histogram()
    transparent = histogram[0]
    opaque = histogram[255]
    total = rgba.width * rgba.height
    result["alpha"] = {
        "min": alpha.getextrema()[0],
        "max": alpha.getextrema()[1],
        "transparent": transparent,
        "translucent": total - transparent - opaque,
        "opaque": opaque,
    }
    if transparent_rows:
        result["transparent_edges"] = _transparent_edges(alpha)
    if transparent_rgb:
        raw = memoryview(rgba.tobytes())
        colors = Counter(
            (raw[index], raw[index + 1], raw[index + 2])
            for index in range(0, len(raw), 4)
            if raw[index + 3] == 0
        )
        result["transparent_rgb"] = {
            "pixel_count": transparent,
            "top_colors": [
                {"rgb": list(color), "count": count}
                for color, count in colors.most_common(10)
            ],
            "white_pixels": colors[(255, 255, 255)],
            "black_pixels": colors[(0, 0, 0)],
        }
    return result


def _compact_animation_bases() -> frozenset[str]:
    """Read element names whose database animation pattern omits the hyphen."""
    database = default_db_path()
    if not database.is_file():
        return frozenset()
    try:
        with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as connection:
            rows = connection.execute(
                """
                SELECT e.filename, a.pattern
                FROM elements e
                JOIN animation a ON a.element_id = e.id
                WHERE e.filename IS NOT NULL AND a.pattern IS NOT NULL
                """
            )
            bases = {
                Path(filename).stem.lower()
                for filename, pattern in rows
                if "{n}" in pattern and "-{n}" not in pattern
            }
    except sqlite3.Error:
        return frozenset()
    return frozenset(bases)


def _animation_frame(
    path: Path, compact_bases: frozenset[str]
) -> tuple[str, int, bool, str] | None:
    match = re.fullmatch(r"(?P<base>.+)-(?P<frame>\d+)(?P<hd>@2x)?", path.stem, re.IGNORECASE)
    if match:
        return match.group("base"), int(match.group("frame")), bool(match.group("hd")), "hyphen"

    stem = path.stem
    hd = stem.lower().endswith("@2x")
    without_hd = stem[:-3] if hd else stem
    lowered = without_hd.lower()
    for base in sorted(compact_bases, key=len, reverse=True):
        suffix = lowered[len(base) :] if lowered.startswith(base) else ""
        if suffix.isdigit():
            return without_hd[: len(base)], int(suffix), hd, "compact"
    return None


def _animation_groups(
    paths: Sequence[Path],
    dimensions: dict[Path, tuple[int, int]],
    compact_bases: frozenset[str] | None = None,
) -> list[dict[str, object]]:
    groups: dict[tuple[Path, str, str, bool, str], list[tuple[int, Path]]] = defaultdict(list)
    compact_bases = _compact_animation_bases() if compact_bases is None else compact_bases
    for path in paths:
        frame = _animation_frame(path, compact_bases)
        if frame:
            base, number, hd, pattern = frame
            groups[(path.parent, base, path.suffix.lower(), hd, pattern)].append((number, path))
    output = []
    for (parent, base, extension, hd, pattern), frames in sorted(
        groups.items(), key=lambda item: str(item[0])
    ):
        frames.sort()
        numbers = [number for number, _ in frames]
        expected = set(range(0, numbers[-1] + 1))
        sizes = {dimensions[path] for _, path in frames}
        counts = Counter(numbers)
        base_file = parent / f"{base}{'@2x' if hd else ''}{extension}"
        output.append(
            {
                "base": str(parent / base),
                "base_file": str(base_file),
                "base_exists": base_file.is_file(),
                "hd": hd,
                "pattern": pattern,
                "frames": [{"number": number, "path": str(path)} for number, path in frames],
                "starts_at_zero": numbers[0] == 0,
                "missing_frames": sorted(expected - set(numbers)),
                "duplicate_frames": sorted(number for number, count in counts.items() if count > 1),
                "consistent_size": len(sizes) == 1,
                "sizes": [list(size) for size in sorted(sizes)],
            }
        )
    return output


def inspect_path(args: argparse.Namespace) -> dict[str, object]:
    paths = discover_images(args.path, args.recursive)
    images = []
    errors = []
    dimensions: dict[Path, tuple[int, int]] = {}
    for path in paths:
        try:
            item = inspect_image(path, args.transparent_rows, args.transparent_rgb)
            images.append(item)
            dimensions[path] = (int(item["width"]), int(item["height"]))
        except (OSError, UnidentifiedImageError) as error:
            errors.append({"path": str(path), "error": str(error)})
    for item in images:
        path = Path(str(item["path"]))
        is_hd = path.stem.lower().endswith("@2x")
        pair = path.with_name((path.stem[:-3] if is_hd else f"{path.stem}@2x") + path.suffix)
        item["hd_sd"] = {"role": "hd" if is_hd else "sd", "pair": str(pair), "exists": pair in dimensions}
        if pair in dimensions:
            own = dimensions[path]
            other = dimensions[pair]
            sd, hd = (other, own) if is_hd else (own, other)
            item["hd_sd"]["scale_2x"] = hd == (sd[0] * 2, sd[1] * 2)
    return {
        "ok": not errors,
        "root": str(args.path.expanduser().resolve()),
        "count": len(images),
        "images": images,
        "animation_groups": _animation_groups(paths, dimensions) if args.animation else [],
        "errors": errors,
    }


def run(args: argparse.Namespace) -> int:
    try:
        result = inspect_path(args)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Images: {result['count']}")
            for item in result["images"]:
                alpha = item["alpha"]
                print(f"- {item['path']}: {item['width']}x{item['height']} {item['mode']}, alpha<255={alpha['transparent'] + alpha['translucent']}")
            for error in result["errors"]:
                print(f"Error: {error['path']}: {error['error']}")
        return 0 if result["ok"] else 1
    except (FileNotFoundError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
