import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from osu_skin_skills.osu_skin_mania_lazer_hold_body_fix import (
    TARGET_HEIGHT,
    main as hold_body_main,
    repair_hold_body,
)
from osu_skin_skills.osu_skin_mania_lazer_key_fix import (
    main as key_main,
    repair_key,
)


class LazerHoldBodyFixTests(unittest.TestCase):
    def test_scales_proportionally_then_repeats_scaled_bottom_rows(self) -> None:
        image = Image.new("RGBA", (2, 1500), (0, 0, 0, 255))
        for y in range(1500):
            color = y % 256
            for x in range(2):
                image.putpixel((x, y), (color, 0, 0, 255))

        output, result = repair_hold_body(image, 1.25)

        self.assertEqual(output.size, (2, TARGET_HEIGHT))
        self.assertEqual(result["scaled_size"], [2, 1500])
        self.assertEqual(result["operation"], "repeat_bottom")
        self.assertEqual(result["bottom_source_rows"], 1000)
        self.assertEqual(output.getpixel((0, 1500)), image.getpixel((0, 500)))
        self.assertEqual(output.getpixel((0, 2500)), image.getpixel((0, 500)))

    def test_repeat_pattern_comes_from_original_bottom_1000_before_scaling(self) -> None:
        image = Image.new("RGBA", (4, 3000), (0, 0, 0, 255))
        for y in range(3000):
            color = y % 256
            for x in range(4):
                image.putpixel((x, y), (color, 0, 0, 255))

        output, result = repair_hold_body(image, 1.25)

        self.assertEqual(result["scaled_size"], [2, 1500])
        self.assertEqual(result["bottom_source_rows"], 1000)
        self.assertEqual(result["bottom_pattern_rows"], 500)
        expected_pattern = image.crop((0, 2000, 4, 3000)).resize(
            (2, 500), Image.Resampling.LANCZOS
        )
        self.assertEqual(output.getpixel((0, 1500)), expected_pattern.getpixel((0, 0)))
        self.assertEqual(output.getpixel((0, 2000)), output.getpixel((0, 1500)))

    def test_scales_proportionally_and_crops_only_the_bottom(self) -> None:
        image = Image.new("RGBA", (2, 40000), (10, 20, 30, 255))
        image.putpixel((0, 0), (200, 10, 20, 255))

        output, result = repair_hold_body(image, 1.25)

        self.assertEqual(output.size, (2, TARGET_HEIGHT))
        self.assertEqual(result["operation"], "crop_bottom")
        self.assertEqual(result["bottom_cropped_rows"], 7200)
        self.assertEqual(output.getpixel((0, 0)), (200, 10, 20, 255))

    def test_cli_dry_run_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "mania-note1L.png"
            dry_output = root / "dry.png"
            output = root / "fixed.png"
            Image.new("RGBA", (4, 12), (10, 20, 30, 255)).save(source)

            with redirect_stdout(io.StringIO()):
                dry_result = hold_body_main(
                    [
                        str(source),
                        "--column-width",
                        "5",
                        "--output",
                        str(dry_output),
                        "--dry-run",
                    ]
                )
                write_result = hold_body_main(
                    [
                        str(source),
                        "--column-width",
                        "5",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(dry_result, 0)
            self.assertFalse(dry_output.exists())
            self.assertEqual(write_result, 0)
            with Image.open(output) as written:
                self.assertEqual(written.size, (8, TARGET_HEIGHT))


class LazerKeyFixTests(unittest.TestCase):
    @staticmethod
    def _key_image() -> Image.Image:
        image = Image.new("RGBA", (10, 12), (255, 255, 255, 0))
        for y in range(3, 10):
            for x in range(2, 8):
                image.putpixel((x, y), (20, 40, 60, 255))
        return image

    def test_crops_subject_removes_top_and_preserves_left_and_bottom_counts(self) -> None:
        output, result = repair_key(self._key_image(), 5, False)

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(result["alpha_bbox"], [2, 3, 8, 10])
        self.assertEqual(result["left_padding"], 2)
        self.assertEqual(result["removed_top_padding"], 3)
        self.assertEqual(result["bottom_padding"], 2)
        self.assertEqual(result["scaled_subject_size"], [6, 7])
        self.assertEqual(output.size, (8, 9))
        self.assertEqual(output.getchannel("A").getbbox(), (2, 0, 8, 7))

    def test_hd_doubles_the_already_rounded_target_width(self) -> None:
        output, result = repair_key(self._key_image(), 5, True)

        self.assertIsNotNone(output)
        assert output is not None
        self.assertEqual(result["base_target_width"], 8)
        self.assertEqual(result["target_width"], 16)
        self.assertEqual(result["scaled_subject_size"], [14, 16])
        self.assertEqual(output.size, (16, 18))

    def test_fully_transparent_image_is_skipped(self) -> None:
        output, result = repair_key(Image.new("RGBA", (10, 12), (1, 2, 3, 0)), 5)

        self.assertIsNone(output)
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "source image is fully transparent")

    def test_cli_detects_hd_name_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "mania-key1@2x.png"
            output = root / "fixed@2x.png"
            self._key_image().save(source)

            with redirect_stdout(io.StringIO()):
                result = key_main(
                    [
                        str(source),
                        "--column-width",
                        "5",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            with Image.open(output) as written:
                self.assertEqual(written.size, (16, 18))

    def test_cli_skips_fully_transparent_image_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "mania-key1.png"
            output = root / "fixed.png"
            Image.new("RGBA", (10, 12), (0, 0, 0, 0)).save(source)

            with redirect_stdout(io.StringIO()):
                result = key_main(
                    [
                        str(source),
                        "--column-width",
                        "5",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
