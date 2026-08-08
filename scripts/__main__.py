"""Unified TODO CLI for the osu! skin skill."""

import argparse
from collections.abc import Sequence

from . import (
    osu_skin_audio_inspect,
    osu_skin_db_query,
    osu_skin_image_inspect,
    osu_skin_image_transform,
    osu_skin_mania_analyze,
    osu_skin_mania_throw_length,
)


COMMANDS = {
    "db-query": osu_skin_db_query,
    "image-inspect": osu_skin_image_inspect,
    "image-transform": osu_skin_image_transform,
    "audio-inspect": osu_skin_audio_inspect,
    "mania-analyze": osu_skin_mania_analyze,
    "mania-throw-length": osu_skin_mania_throw_length,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osu-skin", description="osu! skin domain CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, module in COMMANDS.items():
        command_parser = subparsers.add_parser(name, help=module.DESCRIPTION)
        module.configure_parser(command_parser)
        command_parser.set_defaults(handler=module.run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
