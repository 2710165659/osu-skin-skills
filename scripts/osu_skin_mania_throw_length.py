"""TODO module for changing osu!mania Hold Body throw length."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "change the transparent top-row count of a Mania Hold Body image"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="source Hold Body PNG or skin root")
    parser.add_argument(
        "--throw-length",
        type=int,
        required=True,
        help="target number of fully transparent rows at the top",
    )
    parser.add_argument("--output", required=True, help="output PNG or output skin directory")
    parser.add_argument("--height", type=int, help="final image height, often 32800")
    parser.add_argument("--width", type=int, help="final image width, often 40")
    parser.add_argument("--margin", type=int, help="symmetric left/right transparent margin")
    parser.add_argument("--cap-height", type=int, help="cap height when its boundary is ambiguous")
    parser.add_argument("--keys", type=int, help="select Keys:N when path is a skin")
    parser.add_argument("--client", choices=("stable", "lazer"), help="confirmed client")
    parser.add_argument(
        "--note-body-style",
        type=int,
        choices=(0, 2, 3, 4),
        help="confirmed NoteBodyStyle; omit when unknown",
    )
    parser.add_argument("--dry-run", action="store_true", help="report a plan without writing")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement mania-throw-length")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
