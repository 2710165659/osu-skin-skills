"""TODO module for inspecting osu! skin audio."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "inspect codec, duration, channels, sample families, and loop risks"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="audio file or skin directory")
    parser.add_argument("--family", action="store_true", help="group related hitsound samples")
    parser.add_argument("--loop", action="store_true", help="inspect loop boundary and DC offset")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement audio-inspect")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
