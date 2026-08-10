"""Inspect osu! skin audio metadata, sample families, and WAV loop boundaries."""

import argparse
import json
import math
import struct
import wave
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import mutagen


DESCRIPTION = "inspect codec, duration, channels, sample families, and loop risks"
AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".ogg"})
HIT_PARTS = frozenset({"hitnormal", "hitclap", "hitfinish", "hitwhistle"})
SAMPLE_SETS = frozenset({"normal", "soft", "drum"})
SILENCE_THRESHOLD = 10 ** (-60 / 20)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="audio file or skin directory")
    parser.add_argument("--family", action="store_true", help="group related hitsound samples")
    parser.add_argument("--loop", action="store_true", help="inspect WAV loop boundary and DC offset")
    parser.add_argument("--recursive", action="store_true", help="inspect nested directories")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def discover_audio(path: Path, recursive: bool = False) -> list[Path]:
    resolved = path.expanduser().resolve()
    if resolved.is_file():
        return [resolved]
    if not resolved.is_dir():
        raise FileNotFoundError(f"audio path does not exist: {resolved}")
    iterator = resolved.rglob("*") if recursive else resolved.iterdir()
    return sorted(item for item in iterator if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS)


def _codec_name(audio: object) -> str:
    name = type(audio).__name__.lower()
    if "wave" in name:
        return "wav"
    if "mp3" in name:
        return "mp3"
    if "ogg" in name or "vorbis" in name:
        return "ogg"
    return name


def _decode_pcm_frame(data: bytes, sample_width: int, channels: int) -> list[float]:
    values = []
    for channel in range(channels):
        sample = data[channel * sample_width : (channel + 1) * sample_width]
        if sample_width == 1:
            integer = sample[0] - 128
            maximum = 128
        elif sample_width == 2:
            integer = struct.unpack("<h", sample)[0]
            maximum = 32768
        elif sample_width == 3:
            integer = int.from_bytes(sample, "little", signed=True)
            maximum = 8388608
        elif sample_width == 4:
            integer = struct.unpack("<i", sample)[0]
            maximum = 2147483648
        else:
            raise ValueError(f"unsupported PCM sample width: {sample_width}")
        values.append(integer / maximum)
    return values


def analyze_pcm_wav(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        frames = audio.getnframes()
        sample_rate = audio.getframerate()
        if frames == 0:
            raise ValueError("WAV contains no frames")

        first: list[float] | None = None
        last: list[float] | None = None
        peaks = [0.0] * channels
        sums = [0.0] * channels
        sums_squared = [0.0] * channels
        leading_silent_frames = 0
        trailing_silent_frames = 0
        found_signal = False
        processed_frames = 0
        frame_width = sample_width * channels

        while data := audio.readframes(4096):
            if len(data) % frame_width:
                raise ValueError("WAV PCM data ends inside a sample frame")
            for offset in range(0, len(data), frame_width):
                values = _decode_pcm_frame(
                    data[offset : offset + frame_width], sample_width, channels
                )
                if first is None:
                    first = values
                last = values
                processed_frames += 1
                silent = max(abs(value) for value in values) <= SILENCE_THRESHOLD
                if silent:
                    trailing_silent_frames += 1
                    if not found_signal:
                        leading_silent_frames += 1
                else:
                    found_signal = True
                    trailing_silent_frames = 0
                for channel, value in enumerate(values):
                    peaks[channel] = max(peaks[channel], abs(value))
                    sums[channel] += value
                    sums_squared[channel] += value * value

    if first is None or last is None or processed_frames != frames:
        raise ValueError("WAV frame count does not match decoded PCM data")
    differences = [abs(a - b) for a, b in zip(first, last)]
    return {
        "supported": True,
        "silence_threshold_dbfs": -60,
        "peak_amplitude": peaks,
        "peak_dbfs": [20 * math.log10(value) if value else None for value in peaks],
        "rms_amplitude": [math.sqrt(value / frames) for value in sums_squared],
        "dc_offset": [value / frames for value in sums],
        "leading_silent_frames": leading_silent_frames,
        "leading_silence_seconds": leading_silent_frames / sample_rate,
        "trailing_silent_frames": trailing_silent_frames,
        "trailing_silence_seconds": trailing_silent_frames / sample_rate,
        "first_sample": first,
        "last_sample": last,
        "boundary_delta": differences,
        "max_boundary_delta": max(differences),
        "click_risk": max(differences) > 0.05,
    }


def inspect_wav_loop(path: Path) -> dict[str, object]:
    """Return PCM signal and loop-boundary metrics for compatibility with callers."""
    return analyze_pcm_wav(path)


def inspect_audio(path: Path, loop: bool = False) -> dict[str, object]:
    parsed = mutagen.File(path)
    if parsed is None or not hasattr(parsed, "info"):
        raise ValueError("unsupported or invalid audio file")
    info = parsed.info
    codec = _codec_name(parsed)
    result: dict[str, object] = {
        "path": str(path),
        "extension": path.suffix.lower().lstrip("."),
        "codec": codec,
        "extension_matches_codec": path.suffix.lower().lstrip(".") == codec,
        "file_size": path.stat().st_size,
        "duration_seconds": getattr(info, "length", None),
        "sample_rate": getattr(info, "sample_rate", None),
        "channels": getattr(info, "channels", None),
        "bitrate": getattr(info, "bitrate", None),
    }
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as audio:
            result["sample_width_bits"] = audio.getsampwidth() * 8
            result["pcm_frames"] = audio.getnframes()
            result["compression"] = audio.getcomptype()
        signal_analysis = analyze_pcm_wav(path)
        result["signal_analysis"] = signal_analysis
        if loop:
            result["loop_boundary"] = {
                key: signal_analysis[key]
                for key in (
                    "first_sample",
                    "last_sample",
                    "boundary_delta",
                    "max_boundary_delta",
                    "click_risk",
                    "dc_offset",
                )
            }
    elif loop:
        result["loop_boundary"] = {"supported": False, "reason": "sample-level loop analysis requires PCM WAV"}
    return result


def analyze_families(paths: Sequence[Path]) -> list[dict[str, object]]:
    families: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in paths:
        stem = path.stem.lower()
        if "-" not in stem:
            continue
        sample_set, part = stem.split("-", 1)
        part = part.rstrip("0123456789")
        if sample_set in SAMPLE_SETS and part in HIT_PARTS:
            families[sample_set][part].append(str(path))
    return [
        {
            "sample_set": sample_set,
            "present": sorted(parts),
            "missing": sorted(HIT_PARTS - set(parts)),
            "files": dict(parts),
            "complete": HIT_PARTS <= set(parts),
        }
        for sample_set, parts in sorted(families.items())
    ]


def inspect_path(args: argparse.Namespace) -> dict[str, object]:
    paths = discover_audio(args.path, args.recursive)
    files = []
    errors = []
    for path in paths:
        try:
            files.append(inspect_audio(path, args.loop))
        except (OSError, ValueError, wave.Error) as error:
            errors.append({"path": str(path), "error": str(error)})
    return {
        "ok": not errors,
        "root": str(args.path.expanduser().resolve()),
        "count": len(files),
        "files": files,
        "families": analyze_families(paths) if args.family else [],
        "errors": errors,
    }


def run(args: argparse.Namespace) -> int:
    try:
        result = inspect_path(args)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Audio files: {result['count']}")
            for item in result["files"]:
                duration = item["duration_seconds"]
                duration_text = f"{duration:.3f}s" if isinstance(duration, (int, float)) else "unknown duration"
                print(
                    f"- {item['path']}: {item['codec']}, {duration_text}, "
                    f"{item['sample_rate']}Hz, {item['channels']}ch"
                )
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
