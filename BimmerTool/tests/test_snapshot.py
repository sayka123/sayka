import os
import tempfile
import unittest

from bimmertool import coding, snapshot, transport
from bimmertool.coding import CodingRejected
from bimmertool.simulator import SIM_IX_VIN, Simulator
from bimmertool.uds import UdsClient


class SnapshotDiscovery(unittest.TestCase):
    def setUp(self):
        self.sim = Simulator(port=0, discovery_port=0, model="ix").start()
        self.conn = transport.open_connection("127.0.0.1", hsfz_port=1, doip_port=self.sim.port)
        self.uds = UdsClient(self.conn)

    def tearDown(self):
        self.conn.close()
        self.sim.stop()

    def snap(self):
        # 0x55 is absent: it must be dropped after a few timeouts, not scanned to the end.
        return snapshot.take_snapshot(self.uds, [0x72, 0x55], (0x2FF0, 0x3010), timeout=0.2)

    def test_snapshot_diff_and_definition(self):
        with tempfile.TemporaryDirectory() as d:
            before_path = os.path.join(d, "a.json")
            snapshot.save(before_path, self.snap(), SIM_IX_VIN)
            # Stands in for the owner changing a setting from iDrive.
            self.sim.car[0x72].dids[0x3000] = bytes([0x10, 0x00, 0x03, 0x00])
            before, vin = snapshot.load(before_path)
            self.assertEqual(vin, SIM_IX_VIN)
            after = self.snap()
            self.assertNotIn(0x55, after)

            changes = snapshot.diff(before, after)
            self.assertEqual([(c.ecu, c.did, c.byte, c.old, c.new, c.mask) for c in changes],
                             [(0x72, 0x3000, 2, 0x01, 0x03, 0x02)])

            listing = os.path.join(d, "liste.json")
            snapshot.append_definition(listing, changes[0].to_definition("Test ayarı"))
            (definition,) = coding.load_definitions(listing)
            self.assertEqual(coding.read_current(self.uds, definition), "Sonra")
            # The iX simulator refuses unsigned writes, like the real car's secured modules.
            with self.assertRaises(CodingRejected):
                coding.apply(self.uds, definition, "Önce", d)
            self.assertEqual(self.uds.read_did(0x72, 0x3000), bytes([0x10, 0x00, 0x03, 0x00]))


if __name__ == "__main__":
    unittest.main()
