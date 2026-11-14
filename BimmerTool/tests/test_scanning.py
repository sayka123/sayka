import unittest
from unittest.mock import Mock
from bimmertool.scanning import scan
from bimmertool.uds import ProtocolError, UdsClient
from bimmertool.hsfz import HsfzError
from bimmertool.simulator import Simulator
from bimmertool.doip import DoipConnection


class AddressScanning(unittest.TestCase):
    def test_256_addresses_only_presence_requests(self):
        client=Mock()
        client.is_present.side_effect=lambda address, timeout: address in (7,16,64,99)
        result=scan(client, range(256), tester=244)
        self.assertTrue(result['complete'])
        self.assertFalse(result['exhaustive'])
        self.assertEqual(result['found'], [7,16,64,99])
        self.assertEqual(len(result['results']),256)
        self.assertEqual(client.is_present.call_count,255)
        self.assertEqual(set(c[0] for c in client.mock_calls),{'is_present'})

    def test_cancel_preserves_partial_result(self):
        client=Mock()
        client.is_present.return_value=True
        result=scan(client, range(256), stop=lambda:client.is_present.call_count==3)
        self.assertTrue(result['cancelled'])
        self.assertFalse(result['complete'])
        self.assertEqual(result['found'],[0,1,2])

    def test_bad_response_is_not_presence_and_transport_failure_stops(self):
        client=Mock()
        client.is_present.side_effect=[True,ProtocolError('bad'),HsfzError('closed')]
        result=scan(client,[7,16,64,99])
        self.assertEqual([r['state'] for r in result['results']],['responded','invalid_response','transport_error'])
        self.assertEqual(result['found'],[7])
        self.assertFalse(result['complete'])

    def test_invalid_input_never_calls_vehicle(self):
        for addresses in [[],[True],[-1],[65536],list(range(257))]:
            client=Mock()
            with self.subTest(addresses=addresses),self.assertRaises(ValueError):
                scan(client,addresses)
            self.assertFalse(client.mock_calls)

    def test_malformed_positive_tester_present_is_rejected(self):
        conn=Mock();conn.request.return_value=b'\x7E'
        with self.assertRaises(ProtocolError):
            UdsClient(conn).is_present(7)

    def test_doip_valid_absent_and_cancel(self):
        sim=Simulator(model='ix',port=0,discovery_port=0).start()
        conn=DoipConnection('127.0.0.1',port=sim.port)
        try:
            conn.connect()
            result=scan(UdsClient(conn),[7,16,0x55,99],timeout=.1)
            self.assertEqual(result['found'],[7,16,99])
            self.assertEqual(result['results'][2]['state'],'no_response')
            self.assertTrue(result['complete'])
        finally:
            conn.close();sim.stop()
