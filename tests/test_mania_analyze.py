import tempfile
import unittest
from pathlib import Path

from PIL import Image

from osu_skin_skills.osu_skin_mania_analyze import analyze_skin, parse_sections


SKIN_INI = """[General]
Version: 2.7

[Mania]
Keys: 4
ColumnWidth: 30

[Mania]
Keys: 7
ColumnWidth: 30,31,32,33,34,35,36
ColumnSpacing: 1
NoteImage0L: custom/body
NoteImage0H: custom/head
NoteBodyStyle: 2
"""


class ManiaAnalyzeTests(unittest.TestCase):
    def test_parser_preserves_repeated_mania_sections(self) -> None:
        sections = parse_sections(SKIN_INI)
        self.assertEqual([section.name for section in sections].count("Mania"), 2)

    def test_parser_accepts_section_and_value_line_comments(self) -> None:
        sections = parse_sections(
            """[Mania] // source keycount
            Keys: 6 // keep this section
            NoteImage0: custom/note // custom path
            """
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].name, "Mania")
        self.assertEqual(sections[0].last("Keys"), "6")
        self.assertEqual(sections[0].last("NoteImage0"), "custom/note")

    def test_default_fallback_resources_report_definition(self) -> None:
        text = """[Mania]
        Keys: 6
        StageBottom: custom/stage-bottom
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            custom = root / "custom"
            custom.mkdir()
            (root / "skin.ini").write_text(text, encoding="utf-8")
            Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(root / "mania-stage-bottom.png")
            Image.new("RGBA", (8, 8), (4, 5, 6, 255)).save(custom / "stage-bottom.png")
            section = analyze_skin(root, 6, "lazer", True)["sections"][0]

        self.assertEqual(section["path_sources"]["StageBottom"], "configured")
        self.assertTrue(section["fallback_resources"]["mania-stage-bottom"]["defined"])
        self.assertTrue(section["fallback_resources"]["mania-stage-bottom"]["base_exists"])
        self.assertEqual(section["fallback_defined"]["StageBottom"][0]["path"], "mania-stage-bottom")
        self.assertTrue(section["fallback_defined"]["StageBottom"][0]["defined"])

    def test_missing_default_fallback_resources_are_reported_as_undefined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text("[Mania]\nKeys: 6\n", encoding="utf-8")
            section = analyze_skin(path, 6, "lazer", True)["sections"][0]

        fallback = section["fallback_resources"]["mania-stage-bottom"]
        self.assertFalse(fallback["defined"])
        self.assertFalse(fallback["base_exists"])
        self.assertFalse(section["fallback_defined"]["StageBottom"][0]["defined"])

    def test_selects_keycount_and_resolves_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "custom").mkdir()
            (root / "skin.ini").write_text(SKIN_INI, encoding="utf-8")
            Image.new("RGBA", (40, 1200), (1, 2, 3, 255)).save(root / "custom" / "body.png")
            Image.new("RGBA", (40, 40), (1, 2, 3, 255)).save(root / "custom" / "body-0.png")
            Image.new("RGBA", (40, 40), (1, 2, 3, 255)).save(root / "custom" / "body-0@2x.png")
            Image.new("RGBA", (40, 40), (1, 2, 3, 255)).save(root / "custom" / "body@2x.png")
            result = analyze_skin(root, 7, "lazer", True)
        section = result["sections"][0]
        self.assertEqual(result["matching_sections"], 1)
        self.assertEqual(section["long_notes"][0]["body"], "custom/body")
        self.assertEqual(section["geometry"]["rendered_column_width"][0], 48.0)
        self.assertTrue(section["resources"]["NoteImage0L"]["base_exists"])
        self.assertTrue(section["resources"]["NoteImage0L"]["hd_exists"])
        self.assertEqual(len(section["resources"]["NoteImage0L"]["frames"]), 1)
        self.assertEqual(section["path_sources"]["StageBottom"], "default")
        self.assertIn("NoteImage2L", section["fallback_candidates"])
        self.assertEqual(section["note_body_style"]["effective"], 2)

    def test_default_note_mapping_is_shared_by_stable_and_lazer(self) -> None:
        text = "[Mania]\nKeys: 4\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            for client in ("stable", "lazer"):
                with self.subTest(client=client):
                    section = analyze_skin(path, 4, client, False)["sections"][0]
                    self.assertEqual(section["default_column_types"], ["1", "2", "2", "1"])
                    first_index = 0 if client == "lazer" else 1
                    last_index = 3 if client == "lazer" else 4
                    self.assertEqual(section["paths"][f"NoteImage{first_index}"], "mania-note1")
                    self.assertEqual(section["paths"][f"NoteImage{last_index}"], "mania-note1")
                    self.assertNotIn("NoteImage4" if client == "lazer" else "NoteImage0", section["paths"])
                    self.assertEqual(section["long_notes"][0]["field_index"], 0 if client == "lazer" else None)
                    self.assertEqual(section["long_notes"][0]["column"], 1)

    def test_default_seven_key_mapping_uses_s_for_the_centre(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text("[Mania]\nKeys: 7\n", encoding="utf-8")
            section = analyze_skin(path, 7, "lazer", False)["sections"][0]

        self.assertEqual(section["default_column_types"], ["1", "2", "1", "S", "1", "2", "1"])
        self.assertEqual(section["paths"]["NoteImage3"], "mania-noteS")
        self.assertEqual(section["paths"]["NoteImage3H"], "mania-noteSH")
        self.assertEqual(section["paths"]["NoteImage3L"], "mania-noteSL")
        self.assertEqual(section["paths"]["NoteImage3T"], "mania-noteST")

    def test_hold_note_fallbacks_use_configured_short_note_and_head(self) -> None:
        text = "[Mania]\nKeys: 4\nNoteImage0: custom/note\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            section = analyze_skin(path, 4, "lazer", False)["sections"][0]

        self.assertEqual(section["fallback_candidates"]["NoteImage0H"], ["mania-note1H", "custom/note"])
        self.assertEqual(section["fallback_candidates"]["NoteImage0T"], ["mania-note1T", "mania-note1H", "custom/note"])

    def test_lazer_default_mapping_restarts_for_each_forced_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text("[Mania]\nKeys: 18\n", encoding="utf-8")
            section = analyze_skin(path, 18, "lazer", False)["sections"][0]

        self.assertEqual(section["stage_columns"], 9)
        self.assertEqual(section["default_column_types"], ["1", "2", "1", "2", "S", "2", "1", "2", "1"] * 2)
        self.assertEqual(section["paths"]["NoteImage9"], "mania-note1")

    def test_note_image_indexes_are_zero_based(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text("[Mania]\nKeys: 4\nNoteImage4: invalid\n", encoding="utf-8")
            warnings = analyze_skin(path, 4, "lazer", False)["sections"][0]["warnings"]

        self.assertEqual(warnings, ["indexed fields exceed keycount: NoteImage4"])

    def test_lazer_default_body_style_uses_skin_version(self) -> None:
        text = "[General]\nVersion: 2.7\n[Mania]\nKeys: 4\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            result = analyze_skin(path, 4, "lazer", False)
        self.assertEqual(result["sections"][0]["note_body_style"]["effective"], 3)

    def test_lazer_accepts_integer_body_styles_as_zero_or_nonzero_modes(self) -> None:
        for value in (0, 1, 2, 3, 4, -1, 99):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "skin.ini"
                path.write_text(
                    f"[General]\nVersion: 2.7\n[Mania]\nKeys: 4\nNoteBodyStyle: {value}\n",
                    encoding="utf-8",
                )
                section = analyze_skin(path, 4, "lazer", False)["sections"][0]

            self.assertEqual(section["note_body_style"]["effective"], value)
            self.assertFalse(any("not parseable by lazer" in warning for warning in section["warnings"]))

    def test_geometry_uses_boundary_and_gap_counts(self) -> None:
        line_widths = ",".join(str(value) for value in [*range(10), *([0] * 9)])
        column_spacing = ",".join(str(value) for value in range(17))
        text = f"""[Mania]
Keys: 18
ColumnLineWidth: {line_widths}
ColumnSpacing: {column_spacing}
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            section = analyze_skin(path, 18, "lazer", False)["sections"][0]

        self.assertEqual(len(section["geometry"]["column_line_width"]), 19)
        self.assertEqual(len(section["geometry"]["column_spacing"]), 17)
        self.assertEqual(section["warnings"], [])

    def test_lazer_warns_for_nonzero_unused_dual_stage_line_widths(self) -> None:
        line_widths = [0] * 19
        line_widths[10] = 2
        line_widths[18] = -1
        text = f"[Mania]\nKeys: 18\nColumnLineWidth: {','.join(str(value) for value in line_widths)}\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            lazer_warnings = analyze_skin(path, 18, "lazer", False)["sections"][0]["warnings"]
            stable_warnings = analyze_skin(path, 18, "stable", False)["sections"][0]["warnings"]

        self.assertEqual(
            lazer_warnings,
            [
                "ColumnLineWidth has non-zero values at lazer-unused indices 10, 18 for Keys:18; "
                "forced 9K+9K stages only render indices 0..9"
            ],
        )
        self.assertEqual(stable_warnings, [])

    def test_lazer_does_not_warn_for_unconfigured_dual_stage_line_widths(self) -> None:
        text = "[Mania]\nKeys: 18\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            warnings = analyze_skin(path, 18, "lazer", False)["sections"][0]["warnings"]

        self.assertEqual(warnings, [])

    def test_geometry_warns_with_field_specific_expected_count(self) -> None:
        text = "[Mania]\nKeys: 4\nColumnLineWidth: 1,1,1,1\nColumnSpacing: 1,1,1,1\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skin.ini"
            path.write_text(text, encoding="utf-8")
            warnings = analyze_skin(path, 4, "lazer", False)["sections"][0]["warnings"]

        self.assertIn("ColumnLineWidth has 4 values for Keys:4; expected 5", warnings)
        self.assertIn("ColumnSpacing has 4 values for Keys:4; expected 3", warnings)

    def test_keycount_paths_keep_root_subdirectory_and_transparency_separate(self) -> None:
        text = """[Mania]
Keys: 4
LightingN: mania-lightingN
Hit300: mania-hit300

[Mania]
Keys: 7
LightingN: custom/mania-lightingN
Hit300: custom/mania-hit300
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            custom = root / "custom"
            custom.mkdir()
            (root / "skin.ini").write_text(text, encoding="utf-8")
            Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(root / "mania-lightingN.png")
            Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(root / "mania-hit300.png")
            Image.new("RGBA", (8, 8), (0, 255, 0, 255)).save(custom / "mania-lightingN.png")
            Image.new("RGBA", (8, 8), (0, 0, 255, 255)).save(custom / "mania-hit300.png")
            four = analyze_skin(root, 4, "lazer", True)["sections"][0]
            seven = analyze_skin(root, 7, "lazer", True)["sections"][0]

        self.assertEqual(four["paths"]["LightingN"], "mania-lightingN")
        self.assertEqual(seven["paths"]["LightingN"], "custom/mania-lightingN")
        self.assertEqual(four["resources"]["LightingN"]["location"], "root")
        self.assertEqual(seven["resources"]["LightingN"]["location"], "subdirectory")
        self.assertEqual(four["resources"]["LightingN"]["base_alpha"]["status"], "fully_transparent")
        self.assertEqual(seven["resources"]["LightingN"]["base_alpha"]["status"], "opaque")
        self.assertNotEqual(four["resources"]["LightingN"]["relative_path"], seven["resources"]["LightingN"]["relative_path"])

    def test_skininfo_rejects_stable_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skin.ini").write_text("[Mania]\nKeys: 4\n", encoding="utf-8")
            (root / "skininfo.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "skininfo.json"):
                analyze_skin(root, 4, "stable", False)


if __name__ == "__main__":
    unittest.main()
