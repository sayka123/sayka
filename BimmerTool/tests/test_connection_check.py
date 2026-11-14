import unittest
from unittest.mock import Mock
from bimmertool.connection_check import check_connection, decode_vin, public_result
from bimmertool.uds import NegativeResponse, ProtocolError
from bimmertool.hsfz import NoResponse

VIN = b'WBY21CF000S123456'


class ConnectionCheck(unittest.TestCase):
    def test_valid_vin_and_no_write_requests(self):
        client = Mock()
        client.read_did.return_value = VIN
        result = check_connection(client, [16, 16, 64], simulator=True)
        self.assertEqual(len(result['results']), 2)
        self.assertTrue(result['vin_consistent'])
        self.assertEqual(result['source'], 'simulator')
        self.assertTrue(all(call[0] == 'read_did' for call in client.mock_calls))
        self.assertEqual(result['results'][0]['state'], 'vin_read')
        self.assertIsNone(public_result(result)['results'][0]['vin'])
        self.assertEqual(public_result(result, True)['results'][0]['vin'], VIN.decode())
        self.assertEqual(result['results'][0]['vin'], VIN.decode())

    def test_failures_are_distinguished(self):
        client = Mock()
        client.read_did.side_effect = [NegativeResponse(0x22, 0x31), NoResponse('timeout'),
                                      ProtocolError('bad'), b'invalid', OSError('closed')]
        result = check_connection(client, [1, 2, 3, 4, 5, 6])
        self.assertEqual([row['state'] for row in result['results']],
                         ['refused', 'no_response', 'invalid_response', 'invalid_response', 'transport_error'])
        self.assertIsNone(result['vin_consistent'])
        self.assertEqual(client.read_did.call_count, 5)

    def test_inconsistent_vins_flagged(self):
        client = Mock()
        client.read_did.side_effect = [VIN, b'WBY21CF000S123457']
        self.assertFalse(check_connection(client, [1, 2])['vin_consistent'])

    def test_bad_addresses_never_send(self):
        client = Mock()
        for addresses in [[], [-1], [65536], [True], list(range(65))]:
            with self.subTest(addresses=addresses), self.assertRaises(ValueError):
                check_connection(client, addresses)
        self.assertFalse(client.mock_calls)

    def test_vin_rejects_invalid_characters_and_lengths(self):
        for value in [b'', b'I' * 17, b'W' * 16, b'\xff' * 17]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_vin(value)
        self.assertEqual(decode_vin(VIN + b'\0 '), VIN.decode())
