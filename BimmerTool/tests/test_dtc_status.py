import unittest
from bimmertool.dtc_status import explain, summary
from bimmertool.doip import DoipConnection
from bimmertool.simulator import Simulator
from bimmertool.uds import UdsClient


class StatusBits(unittest.TestCase):
    def test_each_bit_decodes_independently(self):
        for bit in range(8):
            mask = 1 << bit
            rows = explain(mask)
            self.assertEqual([row['mask'] for row in rows if row['set']], [mask])
            self.assertIn(f'0x{mask:02X}', summary(mask))
        self.assertTrue(all(row['set'] for row in explain(255)))
        self.assertIn('kanıtlanmaz', summary(0))

    def test_invalid_status(self):
        for value in [None, True, -1, 256, '8']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                explain(value)

    def test_live_uds_path_requests_all_status_bits_without_clear(self):
        sim = Simulator(model='ix', port=0, discovery_port=0).start()
        sim.car[7].dtcs = [(0x110001, 1), (0x110002, 2), (0x110004, 4), (0x110008, 8),
                           (0x110010, 16), (0x110020, 32), (0x110040, 64), (0x110080, 128)]
        conn = DoipConnection('127.0.0.1', port=sim.port)
        try:
            conn.connect()
            client = UdsClient(conn)
            result = client.read_dtcs(7)
            self.assertEqual(len(result), 8)
            self.assertEqual(len(sim.car[7].dtcs), 8)
            self.assertEqual(client.read_dtcs(7, 8), [(0x110008, 8)])
        finally:
            conn.close()
            sim.stop()
