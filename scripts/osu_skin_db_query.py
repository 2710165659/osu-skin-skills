"""TODO module for querying the bundled osu! skin database."""

import argparse
from collections.abc import Sequence


DESCRIPTION = "query element, field, client, or tag facts from osu_skin.db"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("query", help="element id, filename, skin.ini command, tag, or SQL")
    parser.add_argument("--db", default="assets/osu_skin.db", help="path to osu_skin.db")
    parser.add_argument("--client", choices=("stable", "lazer", "both"))
    parser.add_argument("--type", choices=("image", "audio", "skin_ini"))
    parser.add_argument("--tag", action="append", help="required element tag; repeatable")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def run(args: argparse.Namespace) -> int:
    del args
    print("TODO: implement db-query")
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
