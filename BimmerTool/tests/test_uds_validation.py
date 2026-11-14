import unittest
from unittest.mock import Mock

from bimmertool.uds import NegativeResponse, ProtocolError, UdsClient


class UdsValidationTests(unittest.TestCase):
    def setUp(self):
        self.connection = Mock()
        self.client = UdsClient(self.connection)

    def reply(self, response):
        self.connection.request.return_value = response

    def test_empty_and_truncated_negative_responses_are_protocol_errors(self):
        for response in (b"", b"\x7f", b"\x7f\x22"):
            with self.subTest(response=response):
                self.reply(response)
                with self.assertRaises(ProtocolError):
                    self.client.read_did(0x12, 0xF190)

    def test_negative_response_must_match_requested_sid(self):
        self.reply(b"\x7f\x2e\x31")
        with self.assertRaises(ProtocolError):
            self.client.read_did(0x12, 0xF190)

    def test_well_formed_negative_response_remains_negative_response(self):
        self.reply(b"\x7f\x22\x31")
        with self.assertRaises(NegativeResponse) as caught:
            self.client.read_did(0x12, 0xF190)
        self.assertEqual((caught.exception.sid, caught.exception.nrc), (0x22, 0x31))

    def test_session_echo_is_validated(self):
        self.reply(b"\x50\x01")
        with self.assertRaises(ProtocolError):
            self.client.session(0x12, 0x03)

        self.reply(b"\x50\x03\x00\x32\x01\xf4")
        self.client.session(0x12, 0x03)

    def test_write_did_echo_is_validated(self):
        self.reply(b"\x6e\x30\x01")
        with self.assertRaises(ProtocolError):
            self.client.write_did(0x72, 0x3000, b"\x01")

        self.reply(b"\x6e\x30\x00")
        self.client.write_did(0x72, 0x3000, b"\x01")

    def test_read_dtcs_rejects_bad_header_and_partial_record(self):
        for response in (b"\x59\x03\xff", b"\x59\x02", b"\x59\x02\xff\x12\x03"):
            with self.subTest(response=response):
                self.reply(response)
                with self.assertRaises(ProtocolError):
                    self.client.read_dtcs(0x12)

    def test_clear_requires_exact_acknowledgement(self):
        for response in (b"\x54\x00", b"\x54\x01"):
            with self.subTest(response=response):
                self.reply(response)
                with self.assertRaises(ProtocolError):
                    self.client.clear_dtcs(0x12)

    def test_valid_service_flows(self):
        self.connection.request.side_effect = [
            b"\x50\x03\x00\x32\x01\xf4",
            b"\x6e\x30\x00",
            b"\x59\x02\xff\x21\xf0\xa1\x08",
            b"\x54",
        ]

        self.client.session(0x72, 0x03)
        self.client.write_did(0x72, 0x3000, b"\x01")
        self.assertEqual(self.client.read_dtcs(0x07), [(0x21F0A1, 0x08)])
        self.client.clear_dtcs(0x07)
        self.assertEqual(self.connection.request.call_args_list[0].args[:2],
                         (0x72, b"\x10\x03"))
        self.assertEqual(self.connection.request.call_args_list[1].args[:2],
                         (0x72, b"\x2e\x30\x00\x01"))
        self.assertEqual(self.connection.request.call_args_list[2].args[:2],
                         (0x07, b"\x19\x02\x0c"))
        self.assertEqual(self.connection.request.call_args_list[3].args[:2],
                         (0x07, b"\x14\xff\xff\xff"))
        self.assertEqual(self.connection.request.call_args_list[3].kwargs,
                         {"timeout": 5.0})


if __name__ == "__main__":
    unittest.main()
