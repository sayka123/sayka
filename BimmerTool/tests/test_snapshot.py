import os
import tempfile
import unittest
from unittest.mock import Mock

from bimmertool import snapshot, transport
from bimmertool.simulator import SIM_IX_VIN, Simulator
from bimmertool.uds import ProtocolError, UdsClient


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

    def test_snapshot_and_diff(self):
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

            self.assertEqual(self.uds.read_did(0x72, 0x3000), bytes([0x10, 0x00, 0x03, 0x00]))


class SnapshotValidation(unittest.TestCase):
    def test_invalid_targets_send_no_requests(self):
        client = Mock()
        for ecus, bounds in [([0x72], (2, 1)), ([-1], (0, 1)),
                             ([0x10000], (0, 1)), ([0x72], (0, 0x10000))]:
            with self.subTest(ecus=ecus, bounds=bounds), self.assertRaises(ValueError):
                snapshot.take_snapshot(client, ecus, bounds)
        self.assertEqual(client.mock_calls, [])

    def test_only_reads_and_deduplicates_targets(self):
        client = Mock()
        client.read_did.return_value = b"VIN"
        self.assertEqual(snapshot.take_snapshot(client, [0x10, 0x10]),
                         {0x10: {0xF190: b"VIN"}})
        self.assertEqual([call[0] for call in client.mock_calls], ["read_did"])

    def test_malformed_response_is_not_silently_ignored(self):
        client = Mock()
        client.read_did.side_effect = ProtocolError("bad response")
        with self.assertRaises(ProtocolError):
            snapshot.take_snapshot(client, [0x10])

    def test_stop_preserves_already_read_blocks(self):
        client = Mock()
        client.read_did.return_value = b"data"
        self.assertEqual(snapshot.take_snapshot(client, [0x10], (1, 3),
                                               stop=lambda: client.read_did.called),
                         {0x10: {1: b"data"}})

    def test_diff_length_change_and_missing_blocks(self):
        changes = snapshot.diff({1: {2: b"\x00", 3: b"\x04"}},
                                {1: {2: b"\x00\x01", 4: b"\x05"}})
        self.assertEqual([(c.byte, c.old, c.new) for c in changes], [(1, None, 1)])


if __name__ == "__main__":
    unittest.main()
