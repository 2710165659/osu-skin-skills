import argparse
import tempfile
import unittest
from pathlib import Path

from osu_skin_skills._paths import default_db_path
from osu_skin_skills.osu_skin_db_query import (
    _connect_read_only,
    execute_read_only_sql,
    query_database,
    search_elements,
    search_lazer_json,
)


EXPECTED_LAZER_COMPONENT_TYPES = {
    "osu.Game.Rulesets.Mania.Skinning.Argon.ArgonManiaComboCounter",
    "osu.Game.Rulesets.Mania.Skinning.Legacy.LegacyManiaComboCounter",
    "osu.Game.Rulesets.Osu.HUD.AimErrorMeter",
    "osu.Game.Screens.Play.ArgonKeyCounterDisplay",
    "osu.Game.Screens.Play.HUD.ArgonAccuracyCounter",
    "osu.Game.Screens.Play.HUD.ArgonComboCounter",
    "osu.Game.Screens.Play.HUD.ArgonHealthDisplay",
    "osu.Game.Screens.Play.HUD.ArgonPerformancePointsCounter",
    "osu.Game.Screens.Play.HUD.ArgonScoreCounter",
    "osu.Game.Screens.Play.HUD.ArgonSongProgress",
    "osu.Game.Screens.Play.HUD.ArgonUnstableRateCounter",
    "osu.Game.Screens.Play.HUD.ArgonWedgePiece",
    "osu.Game.Screens.Play.HUD.BPMCounter",
    "osu.Game.Screens.Play.HUD.ClicksPerSecond.ClicksPerSecondCounter",
    "osu.Game.Screens.Play.HUD.DefaultAccuracyCounter",
    "osu.Game.Screens.Play.HUD.DefaultComboCounter",
    "osu.Game.Screens.Play.HUD.DefaultHealthDisplay",
    "osu.Game.Screens.Play.HUD.DefaultKeyCounterDisplay",
    "osu.Game.Screens.Play.HUD.DefaultRankDisplay",
    "osu.Game.Screens.Play.HUD.DefaultScoreCounter",
    "osu.Game.Screens.Play.HUD.DefaultSongProgress",
    "osu.Game.Screens.Play.HUD.DrawableGameplayLeaderboard",
    "osu.Game.Screens.Play.HUD.HitErrorMeters.BarHitErrorMeter",
    "osu.Game.Screens.Play.HUD.HitErrorMeters.ColourHitErrorMeter",
    "osu.Game.Screens.Play.HUD.HitErrorMeters.LegacyBarHitErrorMeter",
    "osu.Game.Screens.Play.HUD.JudgementCounter.JudgementCounterDisplay",
    "osu.Game.Screens.Play.HUD.LongestComboCounter",
    "osu.Game.Screens.Play.HUD.PlayerAvatar",
    "osu.Game.Screens.Play.HUD.PlayerFlag",
    "osu.Game.Screens.Play.HUD.PlayerTeamFlag",
    "osu.Game.Screens.Play.HUD.SkinnableModDisplay",
    "osu.Game.Screens.Play.HUD.SpectatorList",
    "osu.Game.Skinning.Components.ArgonJudgementCounterDisplay",
    "osu.Game.Skinning.Components.BeatmapAttributeText",
    "osu.Game.Skinning.Components.BigBlackBox",
    "osu.Game.Skinning.Components.BoxElement",
    "osu.Game.Skinning.Components.PlayerName",
    "osu.Game.Skinning.Components.TextElement",
    "osu.Game.Skinning.LegacyAccuracyCounter",
    "osu.Game.Skinning.LegacyDefaultComboCounter",
    "osu.Game.Skinning.LegacyHealthDisplay",
    "osu.Game.Skinning.LegacyKeyCounterDisplay",
    "osu.Game.Skinning.LegacyPerformancePointsCounter",
    "osu.Game.Skinning.LegacyRankDisplay",
    "osu.Game.Skinning.LegacyScoreCounter",
    "osu.Game.Skinning.LegacySongProgress",
    "osu.Game.Skinning.SkinnableSprite",
    "osu.Game.Skinning.Triangles.TrianglesPerformancePointsCounter",
    "osu.Game.Skinning.Triangles.TrianglesUnstableRateCounter",
}

EXPECTED_LAZER_SETTINGS = {
    "osu.Game.Rulesets.Mania.Skinning.Argon.ArgonManiaComboCounter": {"wireframe_opacity", "show_label"},
    "osu.Game.Rulesets.Osu.HUD.AimErrorMeter": {
        "hit_marker_size", "hit_marker_style", "average_marker_size", "average_marker_style", "position_display_style"
    },
    "osu.Game.Screens.Play.HUD.ArgonAccuracyCounter": {"wireframe_opacity", "show_label", "accuracy_display"},
    "osu.Game.Screens.Play.HUD.ArgonComboCounter": {"wireframe_opacity", "show_label"},
    "osu.Game.Screens.Play.HUD.ArgonHealthDisplay": {"bar_height", "use_relative_size"},
    "osu.Game.Screens.Play.HUD.ArgonPerformancePointsCounter": {"wireframe_opacity", "show_label"},
    "osu.Game.Screens.Play.HUD.ArgonScoreCounter": {"wireframe_opacity", "show_label"},
    "osu.Game.Screens.Play.HUD.ArgonSongProgress": {"show_graph", "show_time", "use_relative_size", "accent_colour"},
    "osu.Game.Screens.Play.HUD.ArgonUnstableRateCounter": {"wireframe_opacity", "show_label"},
    "osu.Game.Screens.Play.HUD.ArgonWedgePiece": {"invert_shear", "accent_colour"},
    "osu.Game.Screens.Play.HUD.DefaultAccuracyCounter": {"accuracy_display"},
    "osu.Game.Screens.Play.HUD.DefaultRankDisplay": {"play_samples"},
    "osu.Game.Screens.Play.HUD.DefaultSongProgress": {"show_graph", "show_time", "use_relative_size", "accent_colour"},
    "osu.Game.Screens.Play.HUD.DrawableGameplayLeaderboard": {"collapse_during_gameplay"},
    "osu.Game.Screens.Play.HUD.HitErrorMeters.BarHitErrorMeter": {
        "judgement_line_thickness", "colour_bar_visibility", "show_moving_average", "centre_marker_style", "label_style"
    },
    "osu.Game.Screens.Play.HUD.HitErrorMeters.ColourHitErrorMeter": {"judgement_count", "judgement_spacing", "judgement_shape"},
    "osu.Game.Screens.Play.HUD.JudgementCounter.JudgementCounterDisplay": {
        "mode", "flow_direction", "show_judgement_names", "show_max_judgement"
    },
    "osu.Game.Screens.Play.HUD.PlayerAvatar": {"corner_radius"},
    "osu.Game.Screens.Play.HUD.SkinnableModDisplay": {"show_extended_information", "expansion_mode_setting", "direction"},
    "osu.Game.Skinning.Components.ArgonJudgementCounterDisplay": {
        "wireframe_opacity", "show_label", "show_max_judgement", "mode", "flow_direction"
    },
    "osu.Game.Skinning.Components.BeatmapAttributeText": {"attribute", "template", "font", "text_weight", "text_colour"},
    "osu.Game.Skinning.Components.BigBlackBox": {"text_spin", "box_alpha"},
    "osu.Game.Skinning.Components.BoxElement": {"corner_radius", "accent_colour"},
    "osu.Game.Skinning.Components.PlayerName": {"font", "text_weight", "text_colour"},
    "osu.Game.Skinning.Components.TextElement": {"text", "font", "text_weight", "text_colour"},
    "osu.Game.Skinning.LegacyAccuracyCounter": {"accuracy_display"},
    "osu.Game.Skinning.LegacyRankDisplay": {"play_samples"},
    "osu.Game.Skinning.SkinnableSprite": {"sprite_name"},
}


class DatabaseQueryTests(unittest.TestCase):
    def test_search_returns_joined_skin_ini_details(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            results = search_elements(connection, "NoteBodyStyle", "lazer", "skin_ini")
        self.assertTrue(results)
        self.assertEqual(results[0]["command"], "NoteBodyStyle")
        self.assertEqual(results[0]["value_type"], "integer")
        self.assertEqual(
            results[0]["valid_values"],
            "stable：0,1,2；lazer：任意整数（0=拉伸，非0=独立叠加效果）",
        )
        self.assertEqual(
            results[0]["default_value"],
            "stable：1；lazer 版本 <2.5：0，版本 >=2.5：非0",
        )
        self.assertIn("非 0 整数", results[0]["notes"])
        self.assertIn("类似从顶部叠加", results[0]["notes"])
        self.assertNotIn("RepeatTop", results[0]["notes"])
        self.assertNotIn("RepeatBottom", results[0]["notes"])
        self.assertIsInstance(results[0]["tags"], list)
        self.assertIn("details", results[0])
        self.assertIn("skin_ini", results[0]["details"])

    def test_note_body_style_does_not_expose_unimplemented_lazer_enum_terms(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            terms = connection.execute(
                """
                SELECT term
                FROM term_definitions
                WHERE term IN ('RepeatTop', 'RepeatBottom', 'RepeatTopAndBottom')
                """
            ).fetchall()

        self.assertEqual(terms, [])

    def test_search_returns_tag_definitions_and_term_matches(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            results = search_elements(connection, "cursor")
        cursor = next(item for item in results if item["id"] == "cursor")
        self.assertTrue(cursor["tag_details"])
        self.assertTrue(all("description" in item for item in cursor["tag_details"]))

        args = argparse.Namespace(
            query="Hold Body",
            db=default_db_path(),
            client=None,
            type=None,
            tag=[],
            json=True,
        )
        result = query_database(args)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["term_count"], 1)
        self.assertEqual(result["term_matches"][0]["term"], "Hold Body")

    def test_filename_normalization_finds_hd_animation_name(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            results = search_elements(connection, "followpoint-0@2x.png")
        self.assertTrue(any(item["id"] == "osu-followpoint" for item in results))

    def test_raw_select_is_allowed_and_write_is_rejected(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = execute_read_only_sql(connection, "SELECT id FROM elements LIMIT 1")
            self.assertEqual(len(rows), 1)
            with self.assertRaises(ValueError):
                execute_read_only_sql(connection, "DELETE FROM elements")

    def test_explicit_sql_and_sql_file_are_supported(self) -> None:
        sql_args = argparse.Namespace(
            query=None,
            sql_query="-- recipe\nSELECT COUNT(*) AS total FROM elements",
            sql_file=None,
            db=default_db_path(),
            client=None,
            type=None,
            tag=[],
            json=True,
        )
        result = query_database(sql_args)
        self.assertEqual(result["mode"], "sql")
        self.assertEqual(result["results"][0]["total"], 467)

        with tempfile.TemporaryDirectory() as directory:
            sql_file = Path(directory) / "query.sql"
            sql_file.write_text("SELECT 'ok' AS status", encoding="utf-8")
            file_args = argparse.Namespace(
                query=None,
                sql_query=None,
                sql_file=sql_file,
                db=default_db_path(),
                client=None,
                type=None,
                tag=[],
                json=True,
            )
            file_result = query_database(file_args)
        self.assertEqual(file_result["results"], [{"status": "ok"}])

    def test_query_result_has_stable_envelope(self) -> None:
        args = argparse.Namespace(
            query="NoteImage#L",
            db=default_db_path(),
            client=None,
            type="skin_ini",
            tag=[],
            json=True,
        )
        result = query_database(args)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["count"], 1)
        self.assertIn("lazer_json_results", result)
        self.assertEqual(result["total_count"], result["count"] + result["lazer_json_count"])

    def test_lazer_json_search_returns_exact_schema_and_component_facts(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            file_results = search_lazer_json(connection, "MainHUDComponents.json")
            combo_results = search_lazer_json(connection, "LegacyManiaComboCounter")
            position_results = search_lazer_json(connection, "UsesFixedAnchor")

        self.assertTrue(any(row["entry_kind"] == "file" for row in file_results))
        combo = next(row for row in combo_results if row["entry_kind"] == "component_type")
        self.assertEqual(combo["ruleset_scope"], "mania")
        self.assertIn("Version=2026.804.2.0", combo["assembly_qualified_type"])
        self.assertTrue(any(row["entry_kind"] == "component_field" for row in position_results))

    def test_lazer_json_type_filter_excludes_element_results(self) -> None:
        args = argparse.Namespace(
            query="LegacyManiaComboCounter",
            sql_query=None,
            sql_file=None,
            db=default_db_path(),
            client="lazer",
            type="lazer_json",
            tag=[],
            json=True,
        )
        result = query_database(args)
        self.assertEqual(result["results"], [])
        self.assertGreater(result["lazer_json_count"], 0)
        self.assertEqual(result["total_count"], result["lazer_json_count"])

    def test_lazer_json_facts_are_not_skin_specific(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = connection.execute(
                """
                SELECT id, description, notes
                FROM lazer_json_entries
                WHERE description LIKE '%皮肤%' OR notes LIKE '%皮肤%'
                """
            ).fetchall()

        self.assertFalse(
            [row for row in rows if "当前皮肤" in (row["description"] or "")]
            or [row for row in rows if "本皮肤" in (row["description"] or "")]
            or [row for row in rows if "当前皮肤" in (row["notes"] or "")]
            or [row for row in rows if "本皮肤" in (row["notes"] or "")]
        )

    def test_lazer_json_component_catalog_is_complete_and_unique(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = connection.execute(
                """
                SELECT component_type, assembly_qualified_type
                FROM lazer_json_entries
                WHERE entry_kind = 'component_type'
                """
            ).fetchall()

        self.assertEqual({row["component_type"] for row in rows}, EXPECTED_LAZER_COMPONENT_TYPES)
        self.assertEqual(len(rows), len(EXPECTED_LAZER_COMPONENT_TYPES))
        self.assertEqual(len({row["assembly_qualified_type"] for row in rows}), len(rows))
        legacy = next(
            row
            for row in rows
            if row["component_type"]
            == "osu.Game.Screens.Play.HUD.HitErrorMeters.LegacyBarHitErrorMeter"
        )
        self.assertIn("Version=2026.807.0.0", legacy["assembly_qualified_type"])
        self.assertTrue(
            all(
                "Version=2026.804.2.0" in row["assembly_qualified_type"]
                for row in rows
                if row["component_type"]
                != "osu.Game.Screens.Play.HUD.HitErrorMeters.LegacyBarHitErrorMeter"
            )
        )

    def test_lazer_json_catalog_has_database_uniqueness_guards(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            indexes = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'lazer_json_entries'"
                ).fetchall()
            }

        self.assertIn("lazer_json_component_type_unique_idx", indexes)
        self.assertIn("lazer_json_setting_unique_idx", indexes)

    def test_lazer_json_setting_catalog_matches_serialisable_properties(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = connection.execute(
                """
                SELECT component_type, assembly_qualified_type, field_name
                FROM lazer_json_entries
                WHERE entry_kind = 'setting'
                """
            ).fetchall()

        actual: dict[str, set[str]] = {}
        for row in rows:
            actual.setdefault(row["component_type"], set()).add(row["field_name"])
            self.assertIn("Version=2026.804.2.0", row["assembly_qualified_type"])

        self.assertEqual(actual, EXPECTED_LAZER_SETTINGS)
        self.assertEqual(len(rows), 73)
        self.assertEqual(len({(row["component_type"], row["field_name"]) for row in rows}), len(rows))
        self.assertNotIn(
            "osu.Game.Screens.Play.HUD.HitErrorMeters.LegacyBarHitErrorMeter",
            actual,
        )

    def test_representative_lazer_json_settings_are_exact(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                (row["component_type"], row["field_name"]): row
                for row in connection.execute(
                    """
                    SELECT component_type, field_name, value_type, default_value, valid_values
                    FROM lazer_json_entries
                    WHERE entry_kind = 'setting'
                    """
                ).fetchall()
            }

        box_radius = rows[("osu.Game.Skinning.Components.BoxElement", "corner_radius")]
        self.assertEqual(box_radius["default_value"], "0.25")
        self.assertEqual(box_radius["valid_values"], "0..0.5, step 0.01")
        self.assertIn(("osu.Game.Skinning.SkinnableSprite", "sprite_name"), rows)
        self.assertNotIn(("osu.Game.Skinning.SkinnableSprite", "sprite"), rows)
        judgement_mode = rows[("osu.Game.Screens.Play.HUD.JudgementCounter.JudgementCounterDisplay", "mode")]
        self.assertEqual(judgement_mode["default_value"], "0")
        self.assertEqual(judgement_mode["valid_values"], "0=Simple;1=Normal;2=All;3=MissesOnly")

        with _connect_read_only(default_db_path()) as connection:
            anchor = connection.execute(
                "SELECT valid_values FROM lazer_json_entries WHERE id = 'field:layout.Anchor'"
            ).fetchone()
        self.assertIn("17=TopCentre", anchor["valid_values"])
        self.assertIn("18=Centre", anchor["valid_values"])

    def test_combo_fields_are_scoped_to_osu_and_catch(self) -> None:
        combo_ids = [f"Combo{index}" for index in range(1, 9)] + [
            "ComboPrefix",
            "ComboOverlap",
        ]
        placeholders = ",".join("?" for _ in combo_ids)
        with _connect_read_only(default_db_path()) as connection:
            rows = connection.execute(
                f"""
                SELECT element_id, game_mode
                FROM skin_ini_details
                WHERE element_id IN ({placeholders})
                """,
                combo_ids,
            ).fetchall()
        self.assertEqual(len(rows), len(combo_ids))
        self.assertTrue(all(row["game_mode"] == "osu,catch" for row in rows))

    def test_cursor_records_explain_lazer_consumers(self) -> None:
        cursor_ids = [
            "cursor",
            "cursormiddle",
            "cursortrail",
            "cursor-ripple",
            "cursor-smoke",
            "CursorCentre",
            "CursorExpand",
            "CursorRotate",
            "CursorTrailRotate",
        ]
        placeholders = ",".join("?" for _ in cursor_ids)
        with _connect_read_only(default_db_path()) as connection:
            rows = connection.execute(
                f"SELECT id, notes FROM elements WHERE id IN ({placeholders})",
                cursor_ids,
            ).fetchall()
        self.assertEqual(len(rows), len(cursor_ids))
        self.assertTrue(all("lazer" in row["notes"] for row in rows))
        self.assertTrue(all("osu! 标准模式" in row["notes"] for row in rows))

    def test_legacy_audio_client_scope_matches_lazer_consumers(self) -> None:
        stable_only_ids = {
            "check-off",
            "check-on",
            "heartbeat",
            "key-confirm",
            "key-delete",
            "key-movement",
            "key-press",
            "metronomelow",
            "sectionfail",
            "sectionpass",
            "select-difficulty",
            "select-expand",
            "shutter",
        }
        placeholders = ",".join("?" for _ in stable_only_ids)
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                row["id"]: row
                for row in connection.execute(
                    f"""
                    SELECT e.id, e.client, e.notes,
                           GROUP_CONCAT(et.tag, '|') AS tags
                    FROM elements e
                    LEFT JOIN element_tags et ON et.element_id = e.id
                    WHERE e.id IN ({placeholders})
                    GROUP BY e.id
                    """,
                    tuple(sorted(stable_only_ids)),
                ).fetchall()
            }
            retry = connection.execute(
                """
                SELECT e.client, e.notes,
                       EXISTS (
                           SELECT 1 FROM element_tags et
                           WHERE et.element_id = e.id AND et.tag = '稳定独有'
                       ) AS has_stable_only_tag
                FROM elements e
                WHERE e.id = 'pause-retry-click'
                """
            ).fetchone()

        self.assertEqual(set(rows), stable_only_ids)
        self.assertTrue(all(row["client"] == "stable" for row in rows.values()))
        self.assertTrue(all("稳定独有" in row["tags"].split("|") for row in rows.values()))
        self.assertTrue(all("不从 legacy 皮肤加载" in row["notes"] for row in rows.values()))
        self.assertTrue(all("b45c1a26e5" not in row["notes"] for row in rows.values()))
        self.assertIsNotNone(retry)
        self.assertEqual(retry["client"], "both")
        self.assertEqual(retry["has_stable_only_tag"], 0)
        self.assertIn("从 legacy 皮肤加载", retry["notes"])

    def test_hit_result_base_images_are_not_animation_exceptions(self) -> None:
        hit_result_ids = {
            "hit0",
            "hit50",
            "hit100",
            "hit100k",
            "hit300",
            "hit300g",
            "hit300k",
            "mania-hit0",
            "mania-hit50",
            "mania-hit100",
            "mania-hit200",
            "mania-hit300",
            "mania-hit300g",
            "taiko-hit0",
            "taiko-hit100",
            "taiko-hit100k",
            "taiko-hit300",
            "taiko-hit300k",
        }
        placeholders = ",".join("?" for _ in hit_result_ids)
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                row["id"]: row
                for row in connection.execute(
                    f"""
                    SELECT e.id, e.client, e.notes, a.rule,
                           GROUP_CONCAT(et.tag, '|') AS tags
                    FROM elements e
                    JOIN animation a ON a.element_id = e.id
                    LEFT JOIN element_tags et ON et.element_id = e.id
                    WHERE e.id IN ({placeholders})
                    GROUP BY e.id
                    """,
                    tuple(sorted(hit_result_ids)),
                ).fetchall()
            }
            legacy_rule_count = connection.execute(
                "SELECT COUNT(*) FROM animation WHERE rule = 'always_load_base'"
            ).fetchone()[0]
            tag_definitions = {
                row["tag"]: row["description"]
                for row in connection.execute(
                    """
                    SELECT tag, description
                    FROM tag_definitions
                    WHERE tag IN ('始终加载基图', '结算统计基图')
                    """
                ).fetchall()
            }

        self.assertEqual(set(rows), hit_result_ids)
        self.assertEqual(legacy_rule_count, 0)
        self.assertTrue(all(row["rule"] == "has_0_hides_base" for row in rows.values()))
        self.assertTrue(all("有-0隐藏基图" in row["tags"].split("|") for row in rows.values()))
        self.assertTrue(all("始终加载基图" not in row["tags"].split("|") for row in rows.values()))
        self.assertNotIn("始终加载基图", tag_definitions)
        self.assertIn("结算统计基图", tag_definitions)
        self.assertIn("独立读取", tag_definitions["结算统计基图"])

        stable_only_generic_ids = {"hit100k", "hit300g", "hit300k"}
        for element_id in stable_only_generic_ids:
            self.assertEqual(rows[element_id]["client"], "stable")
            self.assertIn("稳定独有", rows[element_id]["tags"].split("|"))
            self.assertIn("lazer 不读取此通用判定资源", rows[element_id]["notes"])
        for element_id in hit_result_ids - stable_only_generic_ids:
            self.assertEqual(rows[element_id]["client"], "both")
            self.assertNotIn("稳定独有", rows[element_id]["tags"].split("|"))

        result_screen_ids = hit_result_ids - {"hit300k"}
        for element_id in result_screen_ids:
            tags = rows[element_id]["tags"].split("|")
            self.assertIn("结算统计基图", tags)
            self.assertIn("结算界面", tags)
            self.assertIn("动画不加载无后缀基图", rows[element_id]["notes"])
            self.assertIn("stable 结算", rows[element_id]["notes"])

        hit300k_tags = rows["hit300k"]["tags"].split("|")
        self.assertNotIn("结算统计基图", hit300k_tags)
        self.assertNotIn("结算界面", hit300k_tags)
        self.assertIn("动画不加载无后缀基图", rows["hit300k"]["notes"])
        self.assertIn("结算屏幕不显示", rows["hit300k"]["notes"])

    def test_audio_client_scope_matches_exclusive_tags(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            mismatches = connection.execute(
                """
                SELECT e.id, e.client, GROUP_CONCAT(et.tag, '|') AS tags
                FROM elements e
                LEFT JOIN element_tags et ON et.element_id = e.id
                WHERE e.type = 'audio'
                GROUP BY e.id
                HAVING (e.client = 'stable' AND instr(COALESCE(tags, ''), '稳定独有') = 0)
                    OR (e.client = 'lazer' AND instr(COALESCE(tags, ''), 'lazer独有') = 0)
                    OR (e.client = 'both' AND (
                        instr(COALESCE(tags, ''), '稳定独有') > 0
                        OR instr(COALESCE(tags, ''), 'lazer独有') > 0
                    ))
                """
            ).fetchall()

        self.assertEqual(mismatches, [])

    def test_mania_records_explain_lazer_forced_dual_stages(self) -> None:
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                row["id"]: row
                for row in connection.execute(
                    """
                    SELECT id, client, notes
                    FROM elements
                    WHERE id IN ('Keys', 'ColumnLineWidth', 'SplitStages')
                    """
                ).fetchall()
            }

        self.assertEqual(rows["Keys"]["client"], "both")
        self.assertIn("仅 lazer：10K 以上", rows["Keys"]["notes"])
        self.assertIn("强制使用双舞台并等分", rows["Keys"]["notes"])
        self.assertIn("18K 显示为 9K+9K", rows["Keys"]["notes"])
        self.assertEqual(rows["ColumnLineWidth"]["client"], "both")
        self.assertIn("每个舞台使用 ColumnLineWidth[0..N/2]", rows["ColumnLineWidth"]["notes"])
        self.assertIn("[10..18] 不参与列分隔线渲染", rows["ColumnLineWidth"]["notes"])
        self.assertEqual(rows["SplitStages"]["client"], "stable")
        self.assertIn("与本字段值无关", rows["SplitStages"]["notes"])

    def test_mania_vertical_positions_explain_legacy_coordinate_system(self) -> None:
        position_ids = ("HitPosition", "LightPosition", "ScorePosition", "ComboPosition")
        placeholders = ",".join("?" for _ in position_ids)
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                row["id"]: row
                for row in connection.execute(
                    f"""
                    SELECT e.id, e.description, e.notes, d.default_value
                    FROM elements e
                    JOIN skin_ini_details d ON d.element_id = e.id
                    WHERE e.id IN ({placeholders})
                    """,
                    position_ids,
                ).fetchall()
            }

        self.assertEqual(set(rows), set(position_ids))
        for row in rows.values():
            self.assertIn("480 高 legacy 坐标系", row["description"])
            self.assertIn("0=顶部", row["description"])
            self.assertIn("480=底部", row["description"])
            self.assertIn("240=中央", row["description"])
        self.assertIn("按 240..480 范围生效", rows["HitPosition"]["notes"])
        self.assertIn("不随滚动方向镜像", rows["ComboPosition"]["notes"])
        self.assertEqual(rows["ComboPosition"]["default_value"], "111")

    def test_mania_stage_records_match_lazer_layout_and_fallbacks(self) -> None:
        fallback_paths = {
            "StageBottom": "mania-stage-bottom",
            "StageHint": "mania-stage-hint",
            "StageLeft": "mania-stage-left",
            "StageRight": "mania-stage-right",
            "StageLight": "mania-stage-light",
        }
        with _connect_read_only(default_db_path()) as connection:
            path_rows = {
                row["element_id"]: row["default_value"]
                for row in connection.execute(
                    """
                    SELECT element_id, default_value
                    FROM skin_ini_details
                    WHERE element_id IN ('StageBottom', 'StageHint', 'StageLeft', 'StageRight', 'StageLight')
                    """
                ).fetchall()
            }
            image_rows = {
                row["id"]: row
                for row in connection.execute(
                    """
                    SELECT e.id, e.description, e.notes, d.origin, a.loops
                    FROM elements e
                    JOIN image_details d ON d.element_id = e.id
                    LEFT JOIN animation a ON a.element_id = e.id
                    WHERE e.id IN ('mania-stage-bottom', 'mania-stage-left', 'mania-stage-right', 'mania-stage-light')
                    """
                ).fetchall()
            }

        self.assertEqual(path_rows, fallback_paths)
        self.assertIn("统一缩放 1.6 倍", image_rows["mania-stage-bottom"]["description"])
        self.assertNotIn("0.625", image_rows["mania-stage-bottom"]["description"])
        self.assertEqual(image_rows["mania-stage-bottom"]["loops"], 1)
        self.assertEqual(image_rows["mania-stage-light"]["loops"], 1)
        self.assertEqual(image_rows["mania-stage-left"]["origin"], "TopRight")
        self.assertEqual(image_rows["mania-stage-right"]["origin"], "TopLeft")
        self.assertIn("图片右边贴住轨道左边", image_rows["mania-stage-left"]["notes"])
        self.assertIn("图片左边贴住轨道右边", image_rows["mania-stage-right"]["notes"])

    def test_mania_default_column_mapping_is_shared_and_zero_based(self) -> None:
        ids = (
            "mania-key1", "mania-key1D", "mania-key2", "mania-key2D", "mania-keyS", "mania-keySD",
            "mania-note1", "mania-note1H", "mania-note1L", "mania-note1T",
            "mania-note2", "mania-note2H", "mania-note2L", "mania-note2T",
            "mania-noteS", "mania-noteSH", "mania-noteSL", "mania-noteST",
        )
        fields = ("KeyImage#", "KeyImage#D", "NoteImage#", "NoteImage#H", "NoteImage#L", "NoteImage#T")
        placeholders = ",".join("?" for _ in ids)
        field_placeholders = ",".join("?" for _ in fields)
        with _connect_read_only(default_db_path()) as connection:
            rows = {
                row["id"]: row
                for row in connection.execute(
                    f"SELECT id, client, notes FROM elements WHERE id IN ({placeholders})", ids
                ).fetchall()
            }
            tags = {
                row["element_id"]: row["tag"]
                for row in connection.execute(
                    f"SELECT element_id, tag FROM element_tags WHERE element_id IN ({placeholders}) AND tag = '稳定独有'",
                    ids,
                ).fetchall()
            }
            details = {
                row["element_id"]: row
                for row in connection.execute(
                    f"""SELECT e.id AS element_id, e.description, e.notes, d.default_value
                        FROM elements e JOIN skin_ini_details d ON d.element_id = e.id
                        WHERE e.id IN ({field_placeholders})""",
                    fields,
                ).fetchall()
            }
            term = connection.execute(
                "SELECT term, description FROM term_definitions WHERE term = 'Mania 默认列映射'"
            ).fetchone()
            old_term = connection.execute(
                "SELECT 1 FROM term_definitions WHERE term = 'lazer Mania 默认列映射'"
            ).fetchone()
            animation = {
                row["element_id"]: row["rule"]
                for row in connection.execute(
                    f"SELECT element_id, rule FROM animation WHERE element_id IN ({placeholders})", ids
                ).fetchall()
            }

        self.assertEqual(set(rows), set(ids))
        self.assertTrue(all(row["client"] == "both" for row in rows.values()))
        self.assertEqual(tags, {})
        self.assertTrue(all("stable 与 lazer 均未配置时" in row["notes"] for row in rows.values()))
        self.assertIn("stable", rows["mania-note1"]["notes"])
        self.assertIn("lazer", rows["mania-noteS"]["notes"])
        self.assertEqual(animation["mania-noteS"], "has_0_hides_base")
        for field in fields:
            self.assertIn("0-based", details[field]["description"])
            self.assertNotIn("从1开始", details[field]["notes"] or "")
            self.assertIn("stable/lazer", details[field]["default_value"])
        self.assertEqual(details["NoteImage#"]["default_value"], "stable/lazer：按列映射为 mania-note1、mania-note2 或 mania-noteS")
        self.assertIsNotNone(term)
        self.assertIn("stable 与 lazer 均", term["description"])
        self.assertIsNone(old_term)


if __name__ == "__main__":
    unittest.main()
