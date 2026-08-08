"""TODO module for inspecting osu! skin images and animation groups."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "inspect dimensions, alpha, HD/SD pairs, and animation frames"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="image file or skin directory")
    parser.add_argument("--recursive", action="store_true", help="inspect nested directories")
    parser.add_argument("--animation", action="store_true", help="group animation frames")
    parser.add_argument("--transparent-rows", action="store_true", help="measure fully transparent rows")
    parser.add_argument("--transparent-rgb", action="store_true", help="inspect RGB beneath alpha=0")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement image-inspect")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
