"""Query the bundled osu! skin database."""

import argparse
import json
import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from ._paths import default_db_path


DESCRIPTION = "query element, field, lazer JSON, client, or tag facts from osu_skin.db"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "query",
        nargs="?",
        help="element id, filename, skin.ini command, lazer JSON field/type, tag, or read-only SQL",
    )
    sql_group = parser.add_mutually_exclusive_group()
    sql_group.add_argument(
        "--sql",
        dest="sql_query",
        help="execute this read-only SQL directly (SELECT/WITH/EXPLAIN/PRAGMA)",
    )
    sql_group.add_argument(
        "--sql-file",
        type=Path,
        help="read and execute read-only SQL from a UTF-8 file",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db_path(),
        help="path to osu_skin.db (default: bundled database)",
    )
    parser.add_argument("--client", choices=("stable", "lazer", "both"))
    parser.add_argument("--type", choices=("image", "audio", "skin_ini", "lazer_json"))
    parser.add_argument("--tag", action="append", default=[], help="required element tag; repeatable")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")


def _connect_read_only(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"database file does not exist: {resolved}")
    connection = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _json_value(value: object) -> object:
    return value.hex() if isinstance(value, bytes) else value


def _rows(rows: Sequence[sqlite3.Row]) -> list[dict[str, object]]:
    return [{key: _json_value(row[key]) for key in row.keys()} for row in rows]


def _is_sql(query: str) -> bool:
    # Permit the comments commonly used at the top of a saved SQL recipe.
    without_comments = re.sub(r"\A(?:\s*(?:--[^\r\n]*(?:\r?\n|$)|/\*.*?\*/))*", "", query, flags=re.DOTALL)
    return bool(re.match(r"\s*(SELECT|WITH|EXPLAIN|PRAGMA)\b", without_comments, re.IGNORECASE))


def execute_read_only_sql(connection: sqlite3.Connection, query: str) -> list[dict[str, object]]:
    if not _is_sql(query):
        raise ValueError("only SELECT, WITH, EXPLAIN, or PRAGMA queries are allowed")
    cursor = connection.execute(query)
    return _rows(cursor.fetchall())


def _search_terms_in_definitions(
    connection: sqlite3.Connection, query: str
) -> list[dict[str, object]]:
    terms = _search_terms(query)
    clauses: list[str] = []
    parameters: dict[str, object] = {}
    for index, term in enumerate(terms):
        name = f"term_{index}"
        parameters[name] = f"%{term.lower()}%"
        clauses.append(
            f"(LOWER(term) LIKE :{name} OR LOWER(description) LIKE :{name})"
        )
    if not clauses:
        return []
    rows = connection.execute(
        "SELECT term, description FROM term_definitions "
        f"WHERE {' OR '.join(clauses)} ORDER BY term",
        parameters,
    ).fetchall()
    return _rows(rows)


def _search_terms(query: str) -> list[str]:
    raw = Path(query).name
    stem = Path(raw).stem if Path(raw).suffix else raw
    normalized = re.sub(r"@2x$", "", stem, flags=re.IGNORECASE)
    normalized = re.sub(r"-\d+$", "", normalized)
    return list(dict.fromkeys(term for term in (query, raw, stem, normalized) if term))


def search_elements(
    connection: sqlite3.Connection,
    query: str,
    client: str | None = None,
    element_type: str | None = None,
    tags: Sequence[str] = (),
) -> list[dict[str, object]]:
    terms = _search_terms(query)
    match_parts: list[str] = []
    parameters: dict[str, object] = {}
    for index, term in enumerate(terms):
        name = f"term_{index}"
        parameters[name] = f"%{term.lower()}%"
        match_parts.append(
            "(" + " OR ".join(
                f"LOWER(COALESCE({column}, '')) LIKE :{name}"
                for column in (
                    "e.id", "e.filename", "e.command", "e.category",
                    "e.subcategory", "e.description", "e.notes", "et.tag",
                )
            ) + ")"
        )
    where = ["(" + " OR ".join(match_parts) + ")"]
    if client == "stable":
        where.append("e.client IN ('both', 'stable')")
    elif client == "lazer":
        where.append("e.client IN ('both', 'lazer')")
    elif client == "both":
        where.append("e.client = 'both'")
    if element_type:
        where.append("e.type = :element_type")
        parameters["element_type"] = element_type
    for index, tag in enumerate(tags):
        parameter = f"tag_{index}"
        parameters[parameter] = tag
        where.append(
            f"EXISTS (SELECT 1 FROM element_tags required_{index} "
            f"WHERE required_{index}.element_id = e.id AND required_{index}.tag = :{parameter})"
        )

    sql = f"""
        SELECT e.id, e.filename, e.command, e.section, e.type,
               e.category, e.subcategory, e.description, e.notes, e.client,
               d.blend_mode, d.origin, d.suggested_size, d.hd_supported,
               d.beatmap_skinnable AS image_beatmap_skinnable,
               a.pattern AS animation_pattern, a.frame_range, a.fps,
               a.loops AS animation_loops, a.rule AS animation_rule,
               ad.looped AS audio_looped, ad.formats AS audio_formats,
               ad.beatmap_skinnable AS audio_beatmap_skinnable,
               ad.requires_supporter,
               sd.value_type, sd.default_value, sd.valid_values, sd.game_mode,
               GROUP_CONCAT(DISTINCT et.tag) AS tags
        FROM elements e
        LEFT JOIN image_details d ON d.element_id = e.id
        LEFT JOIN animation a ON a.element_id = e.id
        LEFT JOIN audio_details ad ON ad.element_id = e.id
        LEFT JOIN skin_ini_details sd ON sd.element_id = e.id
        LEFT JOIN element_tags et ON et.element_id = e.id
        WHERE {' AND '.join(where)}
        GROUP BY e.id
        ORDER BY CASE
                   WHEN LOWER(e.id) = LOWER(:exact) THEN 0
                   WHEN LOWER(COALESCE(e.command, '')) = LOWER(:exact) THEN 1
                   WHEN LOWER(COALESCE(e.filename, '')) = LOWER(:exact) THEN 2
                   ELSE 3
                 END,
                 e.type, e.id
    """
    parameters["exact"] = query
    results = _rows(connection.execute(sql, parameters).fetchall())
    element_ids = [result["id"] for result in results]
    tag_details: dict[str, list[dict[str, object]]] = {element_id: [] for element_id in element_ids}
    if element_ids:
        placeholders = ",".join("?" for _ in element_ids)
        tag_rows = connection.execute(
            f"""
            SELECT et.element_id, et.tag, td.description
            FROM element_tags et
            JOIN tag_definitions td ON td.tag = et.tag
            WHERE et.element_id IN ({placeholders})
            ORDER BY et.element_id, et.tag
            """,
            element_ids,
        ).fetchall()
        for row in tag_rows:
            tag_details[row["element_id"]].append(
                {"tag": row["tag"], "description": row["description"]}
            )
    for result in results:
        result["tags"] = result["tags"].split(",") if result["tags"] else []
        result["tag_details"] = tag_details[result["id"]]
        result["consumer_scope"] = {
            "client": result["client"],
            "game_modes": (
                [mode for mode in (result["game_mode"] or "").split(",") if mode]
                if result["game_mode"]
                else []
            ),
            "tags": result["tags"],
        }
        result["details"] = {
            "image": {
                "blend_mode": result["blend_mode"],
                "origin": result["origin"],
                "suggested_size": result["suggested_size"],
                "hd_supported": result["hd_supported"],
                "beatmap_skinnable": result["image_beatmap_skinnable"],
            },
            "animation": {
                "pattern": result["animation_pattern"],
                "frame_range": result["frame_range"],
                "fps": result["fps"],
                "loops": result["animation_loops"],
                "rule": result["animation_rule"],
            },
            "audio": {
                "looped": result["audio_looped"],
                "formats": result["audio_formats"],
                "beatmap_skinnable": result["audio_beatmap_skinnable"],
                "requires_supporter": result["requires_supporter"],
            },
            "skin_ini": {
                "value_type": result["value_type"],
                "default_value": result["default_value"],
                "valid_values": result["valid_values"],
                "game_mode": result["game_mode"],
            },
        }
    return results


def search_lazer_json(
    connection: sqlite3.Connection,
    query: str,
) -> list[dict[str, object]]:
    terms = _search_terms(query)
    match_parts: list[str] = []
    parameters: dict[str, object] = {}
    columns = (
        "id",
        "entry_kind",
        "file_name",
        "json_path",
        "ruleset_scope",
        "component_type",
        "assembly_qualified_type",
        "field_name",
        "value_type",
        "default_value",
        "valid_values",
        "description",
        "notes",
        "search_terms",
    )
    for index, term in enumerate(terms):
        name = f"json_term_{index}"
        parameters[name] = f"%{term.lower()}%"
        match_parts.append(
            "(" + " OR ".join(
                f"LOWER(COALESCE({column}, '')) LIKE :{name}"
                for column in columns
            ) + ")"
        )

    rows = connection.execute(
        f"""
        SELECT id, entry_kind, file_name, json_path, ruleset_scope,
               component_type, assembly_qualified_type, field_name,
               value_type, default_value, valid_values, description, notes,
               verified_lazer_version, search_terms
        FROM lazer_json_entries
        WHERE {' OR '.join(match_parts)}
        ORDER BY CASE
                   WHEN LOWER(id) = LOWER(:exact) THEN 0
                   WHEN LOWER(COALESCE(field_name, '')) = LOWER(:exact) THEN 1
                   WHEN LOWER(COALESCE(component_type, '')) = LOWER(:exact) THEN 2
                   WHEN LOWER(file_name) = LOWER(:exact) THEN 3
                   ELSE 4
                 END,
                 file_name, entry_kind, json_path, id
        """,
        {**parameters, "exact": query},
    ).fetchall()
    return _rows(rows)


def query_database(args: argparse.Namespace) -> dict[str, object]:
    database = args.db.expanduser().resolve()
    positional_query = getattr(args, "query", None)
    sql_query = getattr(args, "sql_query", None)
    sql_file = getattr(args, "sql_file", None)
    if sql_query and sql_file:
        raise ValueError("--sql and --sql-file cannot be combined")
    if sql_file:
        try:
            sql_query = sql_file.expanduser().read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(f"cannot read SQL file {sql_file}: {error}") from error
    if sql_query and positional_query:
        raise ValueError("a positional query cannot be combined with --sql or --sql-file")
    effective_query = sql_query or positional_query
    if not effective_query:
        raise ValueError("provide a query, --sql, or --sql-file")
    with _connect_read_only(database) as connection:
        if _is_sql(effective_query):
            if args.client or args.type or args.tag:
                raise ValueError("--client, --type, and --tag cannot be combined with raw SQL")
            mode = "sql"
            results = execute_read_only_sql(connection, effective_query)
            term_matches: list[dict[str, object]] = []
        else:
            mode = "search"
            search_element_records = args.type != "lazer_json"
            search_json_records = (
                args.type in (None, "lazer_json")
                and args.client in (None, "lazer")
                and not args.tag
            )
            results = (
                search_elements(connection, effective_query, args.client, args.type, args.tag)
                if search_element_records
                else []
            )
            lazer_json_results = (
                search_lazer_json(connection, effective_query)
                if search_json_records
                else []
            )
            term_matches = _search_terms_in_definitions(connection, effective_query)
        if mode == "sql":
            lazer_json_results = []
    return {
        "ok": True,
        "database": str(database),
        "mode": mode,
        "query": effective_query,
        "count": len(results),
        "results": results,
        "lazer_json_count": len(lazer_json_results),
        "lazer_json_results": lazer_json_results,
        "total_count": len(results) + len(lazer_json_results),
        "term_count": len(term_matches),
        "term_matches": term_matches,
    }


def run(args: argparse.Namespace) -> int:
    try:
        result = query_database(args)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Database: {result['database']}")
            print(f"Results: {result['count']}")
            for item in result["results"]:
                identity = item.get("id") or item.get("command") or item.get("filename") or "row"
                detail = item.get("description") or ""
                print(f"- {identity}: {detail}")
            if result["lazer_json_count"]:
                print(f"Lazer JSON results: {result['lazer_json_count']}")
                for item in result["lazer_json_results"]:
                    print(f"- {item['id']}: {item['description']}")
        return 0
    except (FileNotFoundError, sqlite3.Error, ValueError) as error:
        payload = {"ok": False, "error": str(error)}
        print(json.dumps(payload, ensure_ascii=False) if args.json else f"Error: {error}")
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure_parser(parser)
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
