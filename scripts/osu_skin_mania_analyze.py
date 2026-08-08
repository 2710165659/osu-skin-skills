"""TODO module for analyzing osu!mania sections and resource dependencies."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "analyze a Mania keycount section, paths, geometry, and dependencies"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="skin directory or skin.ini")
    parser.add_argument("--keys", type=int, required=True, help="target Keys:N section")
    parser.add_argument("--client", choices=("stable", "lazer"), required=True)
    parser.add_argument("--dependencies", action="store_true", help="resolve files, HD, and frames")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement mania-analyze")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
