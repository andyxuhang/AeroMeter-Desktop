"""Shared vectors consumed by the Windows/macOS desktop implementation."""
import csv
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measurement_policy import VolumeIntegrator, coefficient
from app_version import APP_VERSION, FRAMEWORK_VERSION
from usb_transport import FrameDecoder

VECTORS = Path(__file__).resolve().parents[2] / "test_vectors"


class PolicyTests(unittest.TestCase):
    def test_shared_cv_vectors(self):
        with (VECTORS / "cv.csv").open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                result = coefficient(float(row["sigma"]), float(row["mean"]), float(row["minimum"]))
                if row["expected"] == "null": self.assertIsNone(result, row)
                else: self.assertAlmostEqual(result, float(row["expected"]), msg=str(row))

    def test_shared_volume_vectors(self):
        case = None
        with (VECTORS / "volume.csv").open(encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if case != row["case"]: integrator, case = VolumeIntegrator(), row["case"]
                result = integrator.add(float(row["flow"]), float(row["seconds"]), row["invalid"] == "true")
                self.assertAlmostEqual(result, float(row["increment"]), places=10, msg=str(row))

    def test_usb_decoder_is_standalone_and_bounded(self):
        decoder = FrameDecoder()
        self.assertEqual(decoder.feed(b'noise\n@AM1 {"ok":tr'), [])
        self.assertEqual(decoder.feed(b'ue}\n'), [{"ok": True}])
        self.assertEqual(decoder.feed(b'x' * 5000 + b'\n@AM1 {"id":1}\n'), [{"id": 1}])

    def test_separate_versions(self):
        self.assertEqual(APP_VERSION, "1.2.0-beta.8")
        self.assertEqual(FRAMEWORK_VERSION, "1.1.0")
