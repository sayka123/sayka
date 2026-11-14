import os
import tempfile
import unittest

from bimmertool import coding, livedata, transport
from bimmertool.coding import CodingRejected
from bimmertool.doip import DoipConnection
from bimmertool.hsfz import HsfzError
from bimmertool.simulator import SIM_IX_VIN, Simulator
from bimmertool.uds import UdsClient

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class IxOverDoip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Accept only a non-default tester address so the fallback logic is exercised.
        cls.sim = Simulator(port=0, discovery_port=0, model="ix", accepted_testers={0x0E00}).start()

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def setUp(self):
        self.conn = transport.open_connection("127.0.0.1", hsfz_port=1, doip_port=self.sim.port)
        self.uds = UdsClient(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_auto_connect_falls_back_to_doip(self):
        self.assertEqual(self.conn.protocol, "doip")
        self.assertEqual(self.conn.tester, 0x0E00)
        self.assertEqual(self.uds.read_did(0x10, 0xF190).decode(), SIM_IX_VIN)

    def test_discovery(self):
        cars = transport.discover_all("127.0.0.1", timeout=1.0, hsfz_port=1,
                                      doip_port=self.sim.discovery_port)
        self.assertEqual([(c["vin"], c["protocol"]) for c in cars], [(SIM_IX_VIN, "doip")])

    def test_scan_and_dtcs(self):
        self.assertTrue(self.uds.is_present(0x07))
        self.assertFalse(self.uds.is_present(0x12, timeout=0.3))  # no combustion engine
        self.assertEqual(self.uds.read_dtcs(0x07), [(0x21F0A1, 0x08)])

    def test_live_data_on_ev(self):
        values = livedata.read_all(self.uds)
        self.assertTrue(all(v is None for _n, v, _u, _e in values))
        self.assertEqual(livedata.read_custom(self.uds, 0x07, 0x1234), "4E  (= 78)")

    def test_secure_coding_rejection_is_explained(self):
        defs = coding.load_definitions(os.path.join(HERE, "sim_kodlama_ornek.json"))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(CodingRejected) as ctx:
                coding.apply(self.uds, defs[0], "Kapalı", d)
            self.assertIn("Secure Coding", str(ctx.exception))
        self.assertEqual(self.uds.read_did(0x72, 0x3000), bytes([0x10, 0x00, 0x01, 0x00]))

    def test_refused_tester_reports_reason(self):
        conn = DoipConnection("127.0.0.1", port=self.sim.port, testers=(0x0EF4,))
        with self.assertRaises(HsfzError) as ctx:
            conn.connect()
        self.assertIn("tanınmadı", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
