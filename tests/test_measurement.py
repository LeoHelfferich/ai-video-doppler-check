"""Checks that do not need ESC-50 or the generated clips."""
import unittest
import numpy as np
from doppler.common import config
from doppler.detect import fft_length, qualifies
from doppler.physics import speed_at_bound, speed_from_ratio
from doppler.verify import diff_checksums

class MeasurementTests(unittest.TestCase):
    def test_fft_length_is_finer_than_the_target(self):
        n = fft_length(44100, 2.5)
        self.assertEqual(n, 32768)
        # 44100/32768. The README quotes this as 1.35 Hz.
        self.assertAlmostEqual(44100 / n, 1.3458251953125, places=6)

    def test_esc50_download_is_pinned_to_the_measurement_commit(self):
        url = config()["data"]["esc50_url"]
        self.assertNotIn("master.zip", url)
        self.assertIn("33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6", url)

    def test_speed_from_ratio_inverts_the_approach_recede_formula(self):
        c, v = 343.0, 80.0
        self.assertAlmostEqual(speed_from_ratio((c + v) / (c - v), c), v, places=9)

    def test_a_fit_on_the_ceiling_is_not_a_speed(self):
        self.assertTrue(speed_at_bound(299.99999990848323))
        self.assertTrue(speed_at_bound(0.5))
        self.assertFalse(speed_at_bound(66.5))
        self.assertFalse(speed_at_bound(None))

    def test_published_thresholds_keep_a_smooth_descent(self):
        cfg = config()
        t = np.linspace(0, 3, 80)
        ok, info = qualifies({"t": t, "f": np.linspace(120, 80, 80)}, cfg)
        self.assertTrue(ok)
        self.assertGreater(info["ratio"], 1.3)

    def test_published_thresholds_drop_a_flat_tone_and_a_short_one(self):
        cfg = config()
        t = np.linspace(0, 3, 80)
        self.assertFalse(qualifies({"t": t, "f": np.full(80, 100.0)}, cfg)[0])
        short = np.linspace(0, 0.4, 20)
        self.assertFalse(qualifies({"t": short, "f": np.linspace(120, 80, 20)}, cfg)[0])

    def test_checksum_diff_lists_missing_and_mismatched_files(self):
        rows = [{"file": "a.mp4", "sha256": "abc"}, {"file": "b.mp4", "sha256": "def"}]
        missing, bad = diff_checksums(rows, {"a.mp4": "abc"})
        self.assertEqual(missing, ["b.mp4"])
        self.assertEqual(bad, [])
        missing, bad = diff_checksums(rows, {"a.mp4": "nope", "b.mp4": "def"})
        self.assertEqual(missing, [])
        self.assertEqual(bad, [("a.mp4", "nope")])

if __name__ == "__main__":
    unittest.main()
