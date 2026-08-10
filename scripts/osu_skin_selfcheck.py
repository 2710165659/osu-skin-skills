"""Validate the bundled osu! skin database."""

import argparse
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from ._paths import default_db_path


DESCRIPTION = "check database integrity, foreign keys, and required tables"

REQUIRED_TABLES = frozenset(
    {
        "animation",
        "audio_details",
        "element_tags",
        "elements",
        "image_details",
        "lazer_json_entries",
        "skin_ini_details",
        "tag_definitions",
        "term_definitions",
    }
)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db_path(),
        help="path to osu_skin.db (default: bundled database)",
    )
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def inspect_database(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    result: dict[str, object] = {
        "database": str(resolved),
        "exists": resolved.is_file(),
        "integrity": None,
        "foreign_keys": None,
        "required_tables": None,
        "missing_tables": [],
        "errors": [],
        "ok": False,
    }
    if not resolved.is_file():
        result["errors"] = ["database file does not exist"]
        return result

    try:
        connection = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
        integrity_rows = [row[0] for row in connection.execute("PRAGMA quick_check")]
        foreign_key_rows = [list(row) for row in connection.execute("PRAGMA foreign_key_check")]
        actual_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    except sqlite3.Error as error:
        result["errors"] = [str(error)]
        return result
    finally:
        if "connection" in locals():
            connection.close()

    missing_tables = sorted(REQUIRED_TABLES - actual_tables)
    integrity_ok = integrity_rows == ["ok"]
    foreign_keys_ok = not foreign_key_rows
    tables_ok = not missing_tables
    result.update(
        {
            "integrity": {"ok": integrity_ok, "messages": integrity_rows},
            "foreign_keys": {"ok": foreign_keys_ok, "violations": foreign_key_rows},
            "required_tables": {"ok": tables_ok},
            "missing_tables": missing_tables,
            "ok": integrity_ok and foreign_keys_ok and tables_ok,
        }
    )
    return result


def run(args: argparse.Namespace) -> int:
    result = inspect_database(args.db)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        integrity = result["integrity"] or {}
        foreign_keys = result["foreign_keys"] or {}
        required_tables = result["required_tables"] or {}
        print(f"Database: {result['database']}")
        print(f"Integrity: {'ok' if integrity.get('ok') else 'failed'}")
        print(f"Foreign keys: {'ok' if foreign_keys.get('ok') else 'failed'}")
        print(f"Required tables: {'ok' if required_tables.get('ok') else 'failed'}")
        for error in result["errors"]:
            print(f"Error: {error}")
        if result["missing_tables"]:
            print(f"Missing tables: {', '.join(result['missing_tables'])}")
        print(f"Self-check: {'ok' if result['ok'] else 'failed'}")
    return 0 if result["ok"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
