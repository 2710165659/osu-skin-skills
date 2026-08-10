import argparse
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from osu_skin_skills.osu_skin_audio_inspect import inspect_audio, inspect_path


def write_wav(path: Path, first: int = 0, last: int = 0) -> None:
    samples = [first] + [int(1000 * math.sin(index / 10)) for index in range(98)] + [last]
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(44100)
        audio.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))


class AudioInspectTests(unittest.TestCase):
    def test_wav_metadata_and_loop_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "normal-hitnormal.wav"
            write_wav(path, 0, 20000)
            result = inspect_audio(path, loop=True)
        self.assertEqual(result["codec"], "wav")
        self.assertEqual(result["sample_rate"], 44100)
        self.assertTrue(result["loop_boundary"]["click_risk"])
        self.assertGreater(result["signal_analysis"]["peak_amplitude"][0], 0.5)
        self.assertGreaterEqual(result["signal_analysis"]["leading_silent_frames"], 1)
        self.assertIn("dc_offset", result["loop_boundary"])

    def test_family_reports_missing_members(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_wav(root / "normal-hitnormal.wav")
            write_wav(root / "normal-hitclap.wav")
            args = argparse.Namespace(path=root, family=True, loop=False, recursive=False, json=True)
            result = inspect_path(args)
        self.assertEqual(result["families"][0]["sample_set"], "normal")
        self.assertIn("hitfinish", result["families"][0]["missing"])


if __name__ == "__main__":
    unittest.main()
