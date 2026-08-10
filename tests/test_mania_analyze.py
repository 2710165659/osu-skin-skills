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
NoteImage1L: custom/body
NoteImage1H: custom/head
NoteBodyStyle: 2
"""


class ManiaAnalyzeTests(unittest.TestCase):
    def test_parser_preserves_repeated_mania_sections(self) -> None:
        sections = parse_sections(SKIN_INI)
        self.assertEqual([section.name for section in sections].count("Mania"), 2)

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
        self.assertTrue(section["resources"]["NoteImage1L"]["base_exists"])
        self.assertTrue(section["resources"]["NoteImage1L"]["hd_exists"])
        self.assertEqual(len(section["resources"]["NoteImage1L"]["frames"]), 1)
        self.assertEqual(section["path_sources"]["StageBottom"], "default")
        self.assertIn("NoteImage2L", section["fallback_candidates"])
        self.assertEqual(section["note_body_style"]["effective"], 2)

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
