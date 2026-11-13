import os
import socket
import tempfile
import time
import unittest

from bimmertool import coding, livedata
from bimmertool.hsfz import HsfzConnection, discover
from bimmertool.simulator import SIM_VIN, Simulator
from bimmertool.uds import NegativeResponse, UdsClient

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator(port=0, discovery_port=0).start()

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def setUp(self):
        self.conn = HsfzConnection("127.0.0.1", port=self.sim.port, timeout=1.0)
        self.conn.connect()
        self.uds = UdsClient(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_discovery_finds_vin(self):
        cars = discover("127.0.0.1", port=self.sim.discovery_port, timeout=0.5)
        self.assertEqual([c["vin"] for c in cars], [SIM_VIN])

    def test_read_vin(self):
        self.assertEqual(self.uds.read_did(0x10, 0xF190).decode(), SIM_VIN)

    def test_scan_distinguishes_present_and_missing(self):
        self.assertTrue(self.uds.is_present(0x12))
        start = time.monotonic()
        self.assertFalse(self.uds.is_present(0x55, timeout=0.3))
        self.assertLess(time.monotonic() - start, 1.0)
        # A timed-out request must not poison the next one.
        self.assertTrue(self.uds.is_present(0x29))

    def test_dtc_read_and_clear(self):
        dtcs = self.uds.read_dtcs(0x29)
        self.assertEqual(dtcs, [(0x480A01, 0x08)])
        self.uds.clear_dtcs(0x29)
        self.assertEqual(self.uds.read_dtcs(0x29), [])

    def test_live_data(self):
        values = {name: (v, err) for name, v, _unit, err in livedata.read_all(self.uds)}
        rpm, err = values["Motor devri"]
        self.assertIsNone(err)
        self.assertTrue(800 <= rpm <= 2000)
        self.assertEqual(values["Akü / modül voltajı"][0], 14.2)

    def test_coding_apply_backup_restore(self):
        defs = coding.load_definitions(os.path.join(HERE, "sim_kodlama_ornek.json"))
        welcome, horn, secured = defs
        self.assertEqual(coding.read_current(self.uds, welcome), "Açık")
        with tempfile.TemporaryDirectory() as d:
            backup = coding.apply(self.uds, welcome, "Kapalı", d, vin=SIM_VIN)
            self.assertEqual(coding.read_current(self.uds, welcome), "Kapalı")
            # Other bits of the same byte block stay untouched.
            self.assertEqual(self.uds.read_did(0x72, 0x3000), bytes([0x10, 0x00, 0x00, 0x00]))
            coding.apply(self.uds, horn, "Uzun", d)
            self.assertEqual(coding.read_current(self.uds, horn), "Uzun")
            coding.restore(self.uds, backup, d)
            self.assertEqual(self.uds.read_did(0x72, 0x3000), bytes([0x10, 0x00, 0x01, 0x00]))
            with self.assertRaises(NegativeResponse) as ctx:
                coding.apply(self.uds, secured, "Açık", d)
            self.assertEqual(ctx.exception.nrc, 0x33)

    def test_unknown_did_is_negative_response(self):
        with self.assertRaises(NegativeResponse) as ctx:
            self.uds.read_did(0x12, 0x1234)
        self.assertEqual(ctx.exception.nrc, 0x31)


if __name__ == "__main__":
    unittest.main()
