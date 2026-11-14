import os
import unittest
from unittest.mock import patch

from bimmertool import ev
from bimmertool.doip import DoipConnection
from bimmertool.simulator import Simulator
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


if __name__ == "__main__":
    unittest.main()
