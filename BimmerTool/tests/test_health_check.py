import unittest
from unittest.mock import Mock
from pathlib import Path

from bimmertool import ev
from bimmertool.health_check import public_health, run_health_check
from bimmertool.hsfz import NoResponse
from bimmertool.uds import NegativeResponse

HERE = Path(__file__).resolve().parents[1]
VIN = b"WBY21CF000S123456"


def demo_profile():
    return ev.load_profile(HERE / "sim_ix_olcumler.json")


class HealthCheckTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.present = {0x10, 0x40, 0x07}
        self.client.is_present.side_effect = lambda ecu, timeout=1.0: ecu in self.present
        self.client.read_did.side_effect = lambda ecu, did, timeout=None: (
            VIN if ecu in (0x10, 0x40) else (_ for _ in ()).throw(NegativeResponse(0x22, 0x31)))
        self.client.read_dtcs.side_effect = lambda ecu: ([(0x21F0A1, 0x08)] if ecu == 0x07 else [])

    def test_health_check_uses_only_read_services(self):
        report = run_health_check(self.client, [0x10, 0x40, 0x07, 0x63], simulator=True,
                                  profile=demo_profile(), vin=VIN.decode())
        methods = {call[0] for call in self.client.mock_calls}
        self.assertLessEqual(methods, {"is_present", "read_did", "read_dtcs"})
        self.assertNotIn("write_did", methods)
        self.assertNotIn("clear_dtcs", methods)
        self.assertNotIn("session", methods)
        self.assertEqual(report["scan"]["found"], [0x10, 0x40, 0x07])
        self.assertTrue(report["vin"]["vin_consistent"])
        self.assertEqual(report["dtcs"]["total_codes"], 1)
        self.assertEqual(report["dtcs"]["active_codes"], 0)
        self.assertEqual(len(report["measurements"]["results"]), 6)

    def test_scan_and_dtc_errors_are_isolated(self):
        self.client.is_present.side_effect = lambda ecu, timeout=1.0: (_ for _ in ()).throw(NoResponse("yok"))
        self.client.read_did.side_effect = OSError("transport")
        report = run_health_check(self.client, [0x10, 0x40], simulator=False)
        self.assertEqual(report["scan"]["found"], [])
        self.assertEqual(len(report["scan"]["errors"]), 2)
        self.assertEqual(report["dtcs"]["modules_tried"], 0)
        self.assertTrue(any("tester-present" in warning for warning in report["warnings"]))

    def test_invalid_candidates_send_nothing(self):
        for candidates in [[], [-1], [0x10000], [True], list(range(65))]:
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                run_health_check(self.client, candidates)
        self.assertFalse(self.client.mock_calls)

    def test_public_health_redacts_vin_unless_opted_in(self):
        report = run_health_check(self.client, [0x10], simulator=True)
        self.assertIsNone(public_health(report)["vin"]["results"][0]["vin"])
        self.assertEqual(public_health(report, True)["vin"]["results"][0]["vin"], VIN.decode())


if __name__ == "__main__":
    unittest.main()
