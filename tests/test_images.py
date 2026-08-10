import argparse
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from osu_skin_skills.osu_skin_image_inspect import inspect_image, inspect_path
from osu_skin_skills.osu_skin_image_transform import execute_transform


class ImageToolsTests(unittest.TestCase):
    def test_inspect_reports_alpha_edges_and_transparent_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            image = Image.new("RGBA", (4, 6), (255, 255, 255, 0))
            for y in range(2, 6):
                image.putpixel((1, y), (10, 20, 30, 255))
            image.save(path)
            result = inspect_image(path, True, True)
        self.assertEqual(result["transparent_edges"]["top"], 2)
        self.assertEqual(result["transparent_rgb"]["white_pixels"], 20)
        self.assertTrue(result["has_alpha"])

    def test_inspect_groups_animation_and_hd_pair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, size in (("x.png", (4, 4)), ("x@2x.png", (8, 8)), ("spark-0.png", (2, 2)), ("spark-2.png", (2, 2))):
                Image.new("RGBA", size, (1, 2, 3, 255)).save(root / name)
            args = argparse.Namespace(path=root, recursive=False, animation=True, transparent_rows=False, transparent_rgb=False, json=True)
            result = inspect_path(args)
        pair = next(item for item in result["images"] if item["path"].endswith("x.png"))
        self.assertTrue(pair["hd_sd"]["scale_2x"])
        self.assertEqual(result["animation_groups"][0]["missing_frames"], [1])
        self.assertTrue(result["animation_groups"][0]["starts_at_zero"])

    def test_inspect_uses_database_compact_animation_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("sliderb0.png", "sliderb2.png"):
                Image.new("RGBA", (2, 2), (1, 2, 3, 255)).save(root / name)
            args = argparse.Namespace(
                path=root,
                recursive=False,
                animation=True,
                transparent_rows=False,
                transparent_rgb=False,
                json=True,
            )
            result = inspect_path(args)
        group = result["animation_groups"][0]
        self.assertEqual(group["pattern"], "compact")
        self.assertEqual(group["missing_frames"], [1])

    def test_scale_and_recolor_write_expected_png(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            scaled = root / "scaled.png"
            recolored = root / "recolored.png"
            Image.new("RGBA", (10, 20), (1, 2, 3, 128)).save(source)
            scale_args = argparse.Namespace(path=source, operation="scale", output=scaled, width=20, height=None, left=None, top=None, color=None, filter="nearest", recursive=False, overwrite=False, dry_run=False, json=True)
            execute_transform(scale_args)
            with Image.open(scaled) as scaled_image:
                self.assertEqual(scaled_image.size, (20, 40))
            color_args = argparse.Namespace(path=source, operation="recolor", output=recolored, width=None, height=None, left=None, top=None, color="255,0,0,128", filter="nearest", recursive=False, overwrite=False, dry_run=False, json=True)
            execute_transform(color_args)
            with Image.open(recolored) as recolored_image:
                self.assertEqual(recolored_image.getpixel((0, 0)), (255, 0, 0, 64))

    def test_directory_hd_to_sd_renames_and_halves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            output = root / "output"
            source.mkdir()
            Image.new("RGBA", (8, 12), (1, 2, 3, 255)).save(source / "cursor@2x.png")
            args = argparse.Namespace(path=source, operation="hd-to-sd", output=output, width=None, height=None, left=None, top=None, color=None, filter="nearest", recursive=False, overwrite=False, dry_run=False, json=True)
            execute_transform(args)
            with Image.open(output / "cursor.png") as converted:
                self.assertEqual(converted.size, (4, 6))

    def test_hd_to_sd_rejects_odd_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "cursor@2x.png"
            Image.new("RGBA", (7, 8), (1, 2, 3, 255)).save(source)
            args = argparse.Namespace(
                path=source,
                operation="hd-to-sd",
                output=root / "cursor.png",
                width=None,
                height=None,
                left=None,
                top=None,
                color=None,
                filter="nearest",
                recursive=False,
                overwrite=False,
                dry_run=True,
                json=True,
            )
            with self.assertRaises(ValueError):
                execute_transform(args)


if __name__ == "__main__":
    unittest.main()
