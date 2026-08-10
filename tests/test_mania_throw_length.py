import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from osu_skin_skills.osu_skin_mania_throw_length import (
    ThrowLengthError,
    change_throw_length,
    count_top_transparent_rows,
    main,
)


def make_hold_body(height: int, current: int, width: int = 4) -> Image.Image:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(current, height):
        color = (y % 256, (y // 256) % 256, 17, 255)
        for x in range(width):
            pixels[x, y] = color
    return image


class ThrowLengthTests(unittest.TestCase):
    def test_increase_moves_content_down_and_preserves_size(self) -> None:
        source = make_hold_body(1200, 100)
        output, result = change_throw_length(source, 150)

        self.assertEqual(output.size, source.size)
        self.assertEqual(count_top_transparent_rows(output), 150)
        self.assertEqual(output.getpixel((0, 150)), source.getpixel((0, 100)))
        self.assertEqual(result["direction"], "down")
        self.assertEqual(result["bottom_fill_rows"], 0)
        self.assertEqual(result["bottom_cropped_rows"], 50)

    def test_decrease_moves_content_up_and_fills_from_original_tail(self) -> None:
        source = make_hold_body(1200, 100)
        output, result = change_throw_length(source, 50)

        self.assertEqual(output.size, source.size)
        self.assertEqual(count_top_transparent_rows(output), 50)
        self.assertEqual(output.getpixel((0, 50)), source.getpixel((0, 100)))
        self.assertEqual(output.getpixel((0, 1150)), source.getpixel((0, 200)))
        self.assertEqual(result["direction"], "up")
        self.assertEqual(result["bottom_fill_rows"], 50)
        self.assertEqual(result["bottom_cropped_rows"], 0)

    def test_bottom_fill_cycles_the_original_last_1000_rows(self) -> None:
        source = make_hold_body(3000, 1500)
        output, result = change_throw_length(source, 0)

        self.assertEqual(output.getpixel((0, 1500)), source.getpixel((0, 2000)))
        self.assertEqual(output.getpixel((0, 2500)), source.getpixel((0, 2000)))
        self.assertEqual(result["tail_source_rows"], 1000)
        self.assertEqual(result["bottom_fill_rows"], 1500)

    def test_unchanged_target_returns_identical_pixels(self) -> None:
        source = make_hold_body(1200, 100)
        output, result = change_throw_length(source, 100)

        self.assertEqual(output.tobytes(), source.tobytes())
        self.assertEqual(result["direction"], "unchanged")

    def test_rejects_fully_transparent_image(self) -> None:
        with self.assertRaises(ThrowLengthError):
            change_throw_length(Image.new("RGBA", (4, 1200), (0, 0, 0, 0)), 50)

    def test_cli_writes_png_and_dry_run_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.png"
            dry_output = root / "dry.png"
            make_hold_body(1200, 100).save(source)

            with redirect_stdout(io.StringIO()):
                result = main(
                    [str(source), "--throw-length", "50", "--output", str(output), "--json"]
                )
            self.assertEqual(result, 0)
            self.assertTrue(output.is_file())
            with Image.open(output) as written:
                self.assertEqual(written.size, (4, 1200))
                self.assertEqual(count_top_transparent_rows(written.convert("RGBA")), 50)

            with redirect_stdout(io.StringIO()):
                result = main(
                    [
                        str(source),
                        "--throw-length",
                        "50",
                        "--output",
                        str(dry_output),
                        "--dry-run",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertFalse(dry_output.exists())


if __name__ == "__main__":
    unittest.main()
