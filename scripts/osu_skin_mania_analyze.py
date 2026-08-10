"""Analyze repeated osu!mania skin.ini sections and resource dependencies."""

import argparse
import json
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, UnidentifiedImageError


DESCRIPTION = "analyze a Mania keycount section, paths, geometry, and dependencies"
PATH_FIELD = re.compile(
    r"^(?:KeyImage\d+D?|NoteImage\d+(?:H|L|T)?|Lighting[NL]|"
    r"Stage(?:Bottom|Hint|Left|Right|Light)|WarningArrow|Hit(?:0|50|100|200|300|300g))$"
)
INDEXED_FIELD = re.compile(r"^(?P<base>KeyImage|NoteImage|Colour|ColourLight)(?P<index>\d+)(?P<suffix>[DHLT]?)$")
DEFAULT_SHARED_PATHS = {
    "LightingN": "lightingN",
    "LightingL": "lightingL",
    "StageBottom": "mania-stage-bottom",
    "StageHint": "mania-stage-hint",
    "StageLeft": "mania-stage-left",
    "StageRight": "mania-stage-right",
    "StageLight": "mania-stage-light",
    "WarningArrow": "mania-warningarrow",
    "Hit0": "mania-hit0",
    "Hit50": "mania-hit50",
    "Hit100": "mania-hit100",
    "Hit200": "mania-hit200",
    "Hit300": "mania-hit300",
    "Hit300g": "mania-hit300g",
}


@dataclass
class IniSection:
    name: str
    line: int
    fields: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def last(self, key: str) -> str | None:
        values = self.fields.get(key, [])
        return values[-1] if values else None


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="skin directory or skin.ini")
    parser.add_argument("--keys", type=int, required=True, help="target Keys:N section")
    parser.add_argument("--client", choices=("stable", "lazer"), required=True)
    parser.add_argument("--dependencies", action="store_true", help="resolve files, HD, and frames")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def _read_ini(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("skin.ini encoding could not be decoded")


def parse_sections(text: str) -> list[IniSection]:
    sections: list[IniSection] = []
    current: IniSection | None = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(("//", ";")):
            continue
        match = re.fullmatch(r"\[([^]]+)\]", stripped)
        if match:
            current = IniSection(match.group(1), line_number)
            sections.append(current)
            continue
        if current is not None and ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            if key:
                current.fields[key].append(value.strip())
    return sections


def _numbers(value: str | None, default: float) -> list[float]:
    if value is None or not value.strip():
        return [default]
    try:
        return [float(part.strip()) for part in value.split(",")]
    except ValueError as error:
        raise ValueError(f"invalid numeric list: {value}") from error


def _expand(values: list[float], expected_count: int, keys: int, field_name: str, warnings: list[str]) -> list[float]:
    if len(values) == 1:
        return values * expected_count
    if len(values) != expected_count:
        warnings.append(
            f"{field_name} has {len(values)} values for Keys:{keys}; expected {expected_count}"
        )
    return values


def _version_value(general: IniSection | None) -> float:
    if general is None:
        return 1.0
    value = general.last("Version")
    if value is None:
        return 1.0
    if value.lower() == "latest":
        return 999.0
    try:
        return float(value)
    except ValueError:
        return 1.0


def _alpha_summary(path: Path) -> dict[str, object]:
    """Summarize alpha without treating a transparent placeholder as missing."""
    try:
        with Image.open(path) as opened:
            opened.load()
            rgba = opened.convert("RGBA")
        alpha = rgba.getchannel("A")
        histogram = alpha.histogram()
        total = rgba.width * rgba.height
        transparent = histogram[0]
        opaque = histogram[255]
        translucent = total - transparent - opaque
        if transparent == total:
            status = "fully_transparent"
        elif opaque == total:
            status = "opaque"
        else:
            status = "mixed"
        return {
            "status": status,
            "min": alpha.getextrema()[0],
            "max": alpha.getextrema()[1],
            "transparent": transparent,
            "translucent": translucent,
            "opaque": opaque,
        }
    except (OSError, UnidentifiedImageError) as error:
        return {"status": "unreadable", "error": str(error)}


def _resource_files(root: Path, value: str) -> dict[str, object]:
    relative = value.strip().strip('"').replace("\\", "/")
    if relative in {"", "."}:
        return {"value": value, "error": "resource path is empty", "files": []}
    root = root.resolve()
    requested = (root / relative).resolve()
    if not requested.is_relative_to(root):
        return {
            "value": value,
            "error": "resource path escapes the skin directory",
            "files": [],
        }
    base = requested if requested.suffix else requested.with_suffix(".png")
    hd = base.with_name(f"{base.stem}@2x{base.suffix}")
    frames: list[tuple[int, Path]] = []
    hd_frames: list[tuple[int, Path]] = []
    if base.parent.is_dir():
        children = {path.name.casefold(): path for path in base.parent.iterdir() if path.is_file()}
        base = children.get(base.name.casefold(), base)
        hd = children.get(hd.name.casefold(), hd)
        frame_pattern = re.compile(
            rf"^{re.escape(base.stem)}-(?P<number>\d+)(?P<hd>@2x)?{re.escape(base.suffix)}$",
            re.IGNORECASE,
        )
        for path in children.values():
            match = frame_pattern.fullmatch(path.name)
            if not match:
                continue
            target = hd_frames if match.group("hd") else frames
            target.append((int(match.group("number")), path))
        frames.sort(key=lambda item: (item[0], item[1].name.casefold()))
        hd_frames.sort(key=lambda item: (item[0], item[1].name.casefold()))
    normal_paths = [path for _, path in frames]
    hd_paths = [path for _, path in hd_frames]
    files = [path for path in (base, hd, *normal_paths, *hd_paths) if path.is_file()]
    relative = requested.relative_to(root).as_posix()
    resolved_base = base if base.is_file() else requested
    location = "root" if resolved_base.parent == root else "subdirectory"
    return {
        "value": value,
        "relative_path": relative,
        "location": location,
        "resolved_base": str(resolved_base),
        "base": str(base),
        "base_exists": base.is_file(),
        "base_alpha": _alpha_summary(base) if base.is_file() else None,
        "hd": str(hd),
        "hd_exists": hd.is_file(),
        "hd_alpha": _alpha_summary(hd) if hd.is_file() else None,
        "frames": [str(path) for path in normal_paths],
        "hd_frames": [str(path) for path in hd_paths],
        "files": [str(path) for path in dict.fromkeys(files)],
    }


def _analyze_section(section: IniSection, root: Path, keys: int, client: str, version: float, dependencies: bool) -> dict[str, object]:
    warnings: list[str] = []
    widths = _expand(_numbers(section.last("ColumnWidth"), 30), keys, keys, "ColumnWidth", warnings)
    spacing = _expand(_numbers(section.last("ColumnSpacing"), 0), max(keys - 1, 0), keys, "ColumnSpacing", warnings)
    configured_line_width = section.last("ColumnLineWidth")
    configured_lines = _numbers(configured_line_width, 2)
    lines = _expand(configured_lines, keys + 1, keys, "ColumnLineWidth", warnings)
    if client == "lazer" and keys > 10 and keys % 2 == 0 and configured_line_width is not None:
        columns_per_stage = keys // 2
        first_unused_index = columns_per_stage + 1
        nonzero_unused_indices = [
            index
            for index, value in enumerate(
                configured_lines[first_unused_index : keys + 1],
                start=first_unused_index,
            )
            if value != 0
        ]
        if nonzero_unused_indices:
            indices = ", ".join(str(index) for index in nonzero_unused_indices)
            warnings.append(
                f"ColumnLineWidth has non-zero values at lazer-unused indices {indices} for Keys:{keys}; "
                f"forced {columns_per_stage}K+{columns_per_stage}K stages only render indices 0..{columns_per_stage}"
            )
    indexed_out_of_range = []
    for name in section.fields:
        match = INDEXED_FIELD.match(name)
        if match and int(match.group("index")) > keys:
            indexed_out_of_range.append(name)
    if indexed_out_of_range:
        warnings.append("indexed fields exceed keycount: " + ", ".join(sorted(indexed_out_of_range)))

    body_style = section.last("NoteBodyStyle")
    effective_body_style: int | None = None
    if body_style is not None:
        try:
            effective_body_style = int(body_style)
        except ValueError:
            warnings.append(f"invalid NoteBodyStyle: {body_style}")
    elif client == "lazer":
        effective_body_style = 0 if version < 2.5 else 3

    paths = {name: values[-1] for name, values in section.fields.items() if PATH_FIELD.match(name)}
    path_sources = {name: "configured" for name in paths}
    for name, default_path in DEFAULT_SHARED_PATHS.items():
        if name not in paths:
            paths[name] = default_path
            path_sources[name] = "default"

    fallback_candidates: dict[str, list[str]] = {}
    for index in range(1, keys + 1):
        for prefix, suffix in (
            ("KeyImage", ""),
            ("KeyImage", "D"),
            ("NoteImage", ""),
            ("NoteImage", "H"),
            ("NoteImage", "L"),
            ("NoteImage", "T"),
        ):
            name = f"{prefix}{index}{suffix}"
            if name in paths:
                continue
            family = "key" if prefix == "KeyImage" else "note"
            fallback_candidates[name] = [
                f"mania-{family}1{suffix}",
                f"mania-{family}2{suffix}",
                f"mania-{family}S{suffix}",
            ]
    resources = {name: _resource_files(root, value) for name, value in sorted(paths.items())} if dependencies else {}
    fallback_resources = {}
    if dependencies:
        for value in dict.fromkeys(
            candidate
            for candidates in fallback_candidates.values()
            for candidate in candidates
        ):
            resource = _resource_files(root, value)
            if resource.get("files"):
                fallback_resources[value] = resource
    duplicates = {name: values for name, values in section.fields.items() if len(values) > 1}
    long_notes = []
    for index in range(1, keys + 1):
        long_notes.append(
            {
                "column": index,
                "head": paths.get(f"NoteImage{index}H"),
                "body": paths.get(f"NoteImage{index}L"),
                "tail": paths.get(f"NoteImage{index}T"),
                "head_candidates": fallback_candidates.get(f"NoteImage{index}H", []),
                "body_candidates": fallback_candidates.get(f"NoteImage{index}L", []),
                "tail_candidates": fallback_candidates.get(f"NoteImage{index}T", []),
            }
        )

    scale = 1.6 if client == "lazer" else 1.0
    return {
        "line": section.line,
        "keys": keys,
        "fields": {name: values[-1] for name, values in section.fields.items()},
        "duplicates": duplicates,
        "geometry": {
            "column_width": widths,
            "rendered_column_width": [value * scale for value in widths],
            "column_spacing": spacing,
            "column_line_width": lines,
            "column_start": section.last("ColumnStart"),
            "hit_position": section.last("HitPosition"),
            "width_for_note_height_scale": section.last("WidthForNoteHeightScale"),
        },
        "note_body_style": {
            "configured": body_style,
            "effective": effective_body_style,
            "source": "configured" if body_style is not None else ("version default" if client == "lazer" else "not resolved"),
        },
        "paths": paths,
        "path_sources": path_sources,
        "fallback_candidates": fallback_candidates,
        "long_notes": long_notes,
        "resources": resources,
        "fallback_resources": fallback_resources,
        "warnings": warnings,
    }


def analyze_skin(path: Path, keys: int, client: str, dependencies: bool) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    ini = resolved / "skin.ini" if resolved.is_dir() else resolved
    if not ini.is_file():
        raise FileNotFoundError(f"skin.ini does not exist: {ini}")
    skininfo = ini.parent / "skininfo.json"
    if client == "stable" and skininfo.is_file():
        raise ValueError(
            "skininfo.json identifies this skin as lazer; confirm the target client before continuing"
        )
    text, encoding = _read_ini(ini)
    sections = parse_sections(text)
    general = next((section for section in sections if section.name == "General"), None)
    version = _version_value(general)
    mania_sections = [section for section in sections if section.name == "Mania"]
    matches = []
    for section in mania_sections:
        value = section.last("Keys")
        try:
            section_keys = int(value) if value is not None else None
        except ValueError:
            section_keys = None
        if section_keys == keys:
            matches.append(_analyze_section(section, ini.parent, keys, client, version, dependencies))
    if not matches:
        available = [section.last("Keys") for section in mania_sections if section.last("Keys") is not None]
        raise ValueError(f"no [Mania] section with Keys:{keys}; available: {', '.join(available) or 'none'}")
    return {
        "ok": True,
        "skin_ini": str(ini),
        "encoding": encoding,
        "client": client,
        "skininfo_json": str(skininfo) if skininfo.is_file() else None,
        "requested_keys": keys,
        "skin_version": general.last("Version") if general else None,
        "matching_sections": len(matches),
        "sections": matches,
        "warnings": ["multiple matching [Mania] sections require user confirmation"] if len(matches) > 1 else [],
    }


def run(args: argparse.Namespace) -> int:
    try:
        result = analyze_skin(args.path, args.keys, args.client, args.dependencies)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"skin.ini: {result['skin_ini']}")
            print(f"Keys:{result['requested_keys']}; matching sections: {result['matching_sections']}")
            for section in result["sections"]:
                print(f"- line {section['line']}: paths={len(section['paths'])}, warnings={len(section['warnings'])}")
        return 0
    except (FileNotFoundError, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
