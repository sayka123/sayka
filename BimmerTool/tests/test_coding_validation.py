import json
import os
import tempfile
import unittest
from unittest.mock import Mock

from bimmertool import coding


def definition(**overrides):
    data = dict(name="Test", ecu="0x72", did="0x3000", byte=0,
                mask="0x01", options={"Açık": 1, "Kapalı": 0})
    data.update(overrides)
    return coding.CodingDefinition(data)


class CodingValidation(unittest.TestCase):
    def test_restore_requires_matching_known_vin_before_io(self):
        client = Mock()
        with tempfile.TemporaryDirectory() as directory:
            path = coding.save_backup(directory, 0x72, 0x3000, b"\x00", "VIN-A")
            for vin in (None, "VIN-B"):
                with self.subTest(vin=vin), self.assertRaises(ValueError):
                    coding.restore(client, path, directory, vin=vin)
            self.assertEqual(client.mock_calls, [])

    def test_rejected_session_never_attempts_write(self):
        client = Mock()
        client.read_did.return_value = b"\x00"
        client.session.side_effect = coding.NegativeResponse(0x10, 0x22)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(coding.NegativeResponse):
            coding.apply(client, definition(), "Açık", directory)
        client.write_did.assert_not_called()

    def test_invalid_definitions(self):
        for values in [dict(byte=-1), dict(mask=0), dict(mask=256),
                       dict(ecu=-1), dict(did=65536), dict(options={}),
                       dict(options={"bad": -1}), dict(options={"bad": 2})]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                definition(**values)

    def test_short_block_and_unknown_option(self):
        for block, label in [(b"", "Açık"), (b"\x00", "unknown")]:
            with self.assertRaises(ValueError):
                definition().apply_to(block, label)

    def test_wrong_length_never_writes(self):
        client = Mock()
        client.read_did.return_value = b"\x00"
        with tempfile.TemporaryDirectory() as directory:
            for data in [b"", b"\x01\x02"]:
                with self.assertRaises(ValueError):
                    coding.write_block(client, 0x72, 0x3000, data, directory)
            self.assertEqual(os.listdir(directory), [])
        client.write_did.assert_not_called()
        client.session.assert_not_called()

    def test_changed_block_never_writes(self):
        client = Mock()
        client.read_did.side_effect = [b"\x00", b"\x02"]
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            coding.apply(client, definition(), "Açık", directory)
        client.write_did.assert_not_called()

    def test_backup_failure_never_writes(self):
        client = Mock()
        client.read_did.return_value = b"\x00"
        with tempfile.NamedTemporaryFile() as file, self.assertRaises(OSError):
            coding.apply(client, definition(), "Açık", file.name)
        client.write_did.assert_not_called()

    def test_verification_failure_keeps_backup(self):
        client = Mock()
        client.read_did.return_value = b"\x00"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "doğrulama başarısız"):
                coding.apply(client, definition(), "Açık", directory)
            with open(os.path.join(directory, os.listdir(directory)[0])) as file:
                self.assertEqual(json.load(file)["data"], "00")
        client.write_did.assert_called_once_with(0x72, 0x3000, b"\x01")
