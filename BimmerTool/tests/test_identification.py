import unittest
from unittest.mock import Mock

from bimmertool.identification import read_identification, FIELDS
from bimmertool.uds import NegativeResponse, ProtocolError, UdsClient
from bimmertool.hsfz import NoResponse, HsfzError
from bimmertool.doip import DoipConnection
from bimmertool.simulator import Simulator


class IdentityReads(unittest.TestCase):
    def test_only_reads_and_preserves_binary(self):
        client = Mock()
        client.read_did.side_effect = [b'DEMO-123\0', b'\x01\xFF', b'V1', b'HW1', b'SW1', b'V2']
        report = read_identification(client, 0x63, simulator=True)
        self.assertEqual(report['results'][0]['ascii'], 'DEMO-123')
        self.assertEqual(report['results'][1]['raw'], '01 FF')
        self.assertIsNone(report['results'][1]['ascii'])
        self.assertFalse(report['cafd_verified'])
        self.assertFalse(report['module_type_verified'])
        self.assertEqual(report['source'], 'simulator')
        self.assertEqual([call[0] for call in client.mock_calls], ['read_did'] * 6)
        self.assertEqual([call.args[1] for call in client.read_did.call_args_list], [did for did, _ in FIELDS])
        self.assertTrue(all(call.kwargs['timeout'] == 1 for call in client.read_did.call_args_list))

    def test_errors_separated_and_transport_stops(self):
        client = Mock()
        client.read_did.side_effect = [NegativeResponse(0x22, 0x31), NoResponse('timeout'),
                                      ProtocolError('bad'), b'', HsfzError('closed')]
        result = read_identification(client, 0x63)
        self.assertEqual([row['state'] for row in result['results']],
                         ['refused', 'no_response', 'invalid_response', 'invalid_response', 'transport_error'])
        self.assertEqual(result['results'][0]['nrc'], 0x31)
        self.assertEqual(client.read_did.call_count, 5)

    def test_invalid_address_and_source_send_nothing(self):
        client = Mock()
        for address in [True, -1, 65536, '0x63']:
            with self.subTest(address=address), self.assertRaises(ValueError):
                read_identification(client, address)
        with self.assertRaises(ValueError):
            read_identification(client, 0x63, simulator='yes')
        self.assertEqual(client.mock_calls, [])

    def test_actual_doip_protocol_with_synthetic_identity_and_unsupported_dids(self):
        sim = Simulator(model='ix', port=0, discovery_port=0).start()
        conn = DoipConnection('127.0.0.1', port=sim.port)
        try:
            sim.car[0x63].dids[0xF187] = b'DEMO-ONLY'
            conn.connect()
            result = read_identification(UdsClient(conn), 0x63, simulator=True)
            self.assertEqual(result['results'][0]['ascii'], 'DEMO-ONLY')
            self.assertEqual([row['state'] for row in result['results'][1:]], ['refused'] * 5)
        finally:
            conn.close()
            sim.stop()
