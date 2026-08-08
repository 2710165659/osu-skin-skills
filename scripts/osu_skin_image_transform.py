"""TODO module for generic osu! skin image transformations."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "scale, crop, recolor, or create HD/SD image variants"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="source image or image directory")
    parser.add_argument(
        "--operation",
        required=True,
        choices=("scale", "crop", "recolor", "hd-to-sd", "sd-to-hd"),
    )
    parser.add_argument("--output", required=True, help="output file or directory")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--filter", choices=("nearest", "lanczos", "bicubic"))
    parser.add_argument("--dry-run", action="store_true")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement image-transform")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
