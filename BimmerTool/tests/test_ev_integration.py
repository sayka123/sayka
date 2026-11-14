import os
import unittest
from unittest.mock import patch

from bimmertool import ev
from bimmertool.connection_check import check_connection
from bimmertool.health_check import run_health_check
from bimmertool.doip import DoipConnection
from bimmertool.simulator import Simulator
from bimmertool.simulator import SIM_IX_VIN
from bimmertool.uds import UdsClient

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EvIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator(model="ix", port=0, discovery_port=0).start()

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def setUp(self):
        self.conn = DoipConnection("127.0.0.1", port=self.sim.port)
        self.conn.connect()
        self.uds = UdsClient(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_simulator_profile_reads_values_and_raw_hex(self):
        profile = ev.load_profile(os.path.join(HERE, "sim_ix_olcumler.json"))

        results = ev.read_profile(self.uds, profile, is_simulator=True)

        expected_values = {
            "soc": 78.4,
            "voltage": 382.5,
            "current": -12.5,
            "temperature": 26.3,
            "charge_power": 11.0,
            "soh": 96.3,
        }
        expected_raw = {
            "soc": "03 10",
            "voltage": "0E F1",
            "current": "FF 83",
            "temperature": "01 07",
            "charge_power": "00 6E",
            "soh": "03 C3",
        }
        self.assertEqual(len(results), 6)
        for result in results:
            with self.subTest(signal=result["key"]):
                self.assertIsNone(result["error"])
                self.assertAlmostEqual(result["value"], expected_values[result["key"]])
                self.assertEqual(result["raw"], expected_raw[result["key"]])

    def test_simulator_only_profile_is_rejected_before_any_read(self):
        profile = ev.load_profile(os.path.join(HERE, "sim_ix_olcumler.json"))

        with patch.object(self.uds, "read_did", wraps=self.uds.read_did) as read_did:
            with self.assertRaisesRegex(ValueError, "simulator-only"):
                ev.read_profile(self.uds, profile, is_simulator=False)

        read_did.assert_not_called()

    def test_connection_check_distinguishes_vin_and_refused_reads(self):
        result = check_connection(self.uds, [0x10, 0x40, 0x07, 0x63], simulator=True)
        self.assertEqual([row["state"] for row in result["results"]],
                         ["vin_read", "vin_read", "refused", "refused"])
        self.assertTrue(result["vin_consistent"])
        self.assertTrue(all(row["latency_ms"] >= 0 for row in result["results"]))

    def test_read_only_health_check_on_ix_simulator(self):
        profile = ev.load_profile(os.path.join(HERE, "sim_ix_olcumler.json"))
        report = run_health_check(self.uds, [0x10, 0x40, 0x07, 0x63, 0x72, 0x55],
                                  simulator=True, profile=profile, vin=SIM_IX_VIN)
        self.assertEqual(report["scan"]["found"], [0x10, 0x40, 0x07, 0x63, 0x72])
        self.assertEqual(report["dtcs"]["total_codes"], 1)
        self.assertEqual([r["key"] for r in report["measurements"]["results"]],
                         ["soc", "voltage", "current", "temperature", "charge_power", "soh"])


if __name__ == "__main__":
    unittest.main()
