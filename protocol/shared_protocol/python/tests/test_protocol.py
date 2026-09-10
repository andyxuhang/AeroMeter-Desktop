import json
from pathlib import Path
import sys
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
sys.path.insert(0, str(PACKAGE))

from galeon_protocol.measurement import (  # noqa: E402
    ProtocolError,
    decode_live_packet,
    decode_statistics_packet,
    encode_live_packet,
    encode_statistics_packet,
    encode_unsigned_hundredths,
    rate_command,
)

VECTORS = json.loads((ROOT / "vectors" / "measurement_v1.json").read_text(encoding="utf-8"))


class ProtocolTests(unittest.TestCase):
    def test_live_vector_round_trip(self):
        expected = bytes.fromhex(VECTORS["live"]["hex"])
        value = decode_live_packet(expected)
        self.assertEqual(value.sequence, VECTORS["live"]["sequence"])
        self.assertEqual(value.flow_l_min, VECTORS["live"]["flow"])
        actual = encode_live_packet(value.sequence, value.timestamp_ms, value.pressure_kpa,
                                    value.flow_l_min, value.stability_state,
                                    value.session_active, value.pressure_overrange,
                                    value.flow_overrange)
        self.assertEqual(actual, expected)

    def test_statistics_vector_round_trip(self):
        expected = bytes.fromhex(VECTORS["statistics"]["hex"])
        value = decode_statistics_packet(expected)
        actual = encode_statistics_packet(value.sequence, value.timestamp_ms,
                                          value.pressure_mean_kpa, value.pressure_sigma_kpa,
                                          value.pressure_peak_to_peak_kpa, value.flow_mean_l_min,
                                          value.flow_sigma_l_min, value.flow_peak_to_peak_l_min)
        self.assertEqual(actual, expected)

    def test_validation_and_rounding_contract(self):
        self.assertEqual(encode_unsigned_hundredths(1.125), 113)
        self.assertEqual(encode_unsigned_hundredths(-1), 0)
        self.assertEqual(encode_unsigned_hundredths(float("inf")), 0)
        self.assertEqual(rate_command(20), b"\x02\x14")
        with self.assertRaises(ProtocolError):
            decode_live_packet(b"\x01\x01")


if __name__ == "__main__":
    unittest.main()
