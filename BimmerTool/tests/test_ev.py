import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from bimmertool.ev import Profile, Signal, load_profile, read_profile


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "sim_ix_olcumler.json"


def signal(**changes):
    data = {
        "key": "soc", "name": "State of charge", "unit": "%",
        "ecu": 7, "did": 0xD001, "offset": 0, "length": 2,
        "byteorder": "big", "signed": False, "scale": 0.1, "add": 0,
    }
    data.update(changes)
    return data


def profile_data(**changes):
    data = {"version": 1, "name": "test", "simulator_only": False,
            "signals": [signal()]}
    data.update(changes)
    return data


def save_json(data):
    temp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
    with temp:
        json.dump(data, temp)
    return temp.name


class EVProfileTests(unittest.TestCase):
    def test_decode_big_endian_scaled_and_signed_values(self):
        unsigned = load_profile(save_json(profile_data())).signals[0]
        self.assertEqual(unsigned.decode(b"\x01\x2c"), 30.0)
        signed_data = profile_data(signals=[signal(signed=True, scale=0.1, add=-2)])
        signed = load_profile(save_json(signed_data)).signals[0]
        self.assertAlmostEqual(signed.decode(b"\xff\x9c"), -12.0)

    def test_decode_offset_little_endian(self):
        value = load_profile(save_json(profile_data(
            signals=[signal(offset=1, byteorder="little", scale=1)]))).signals[0]
        self.assertEqual(value.decode(b"\x00\x34\x12"), 0x1234)

    def test_decode_rejects_short_and_non_bytes(self):
        decoder = load_profile(save_json(profile_data())).signals[0]
        with self.assertRaises(ValueError):
            decoder.decode(b"\x01")
        with self.assertRaises(TypeError):
            decoder.decode("\x00\x01")

    def test_decode_rejects_non_finite_result(self):
        decoder = load_profile(save_json(profile_data(
            signals=[signal(length=8, scale=1e308)]))).signals[0]
        with self.assertRaisesRegex(ValueError, "finite"):
            decoder.decode(b"\xff" * 8)

    def test_loads_demo_with_expected_simulator_only_signals(self):
        profile = load_profile(DEMO)
        self.assertTrue(profile.simulator_only)
        self.assertEqual(profile.name, "iX40 DEMO · Sahte ölçüm adresleri")
        self.assertEqual([s.key for s in profile.signals],
                         ["soc", "voltage", "current", "temperature", "charge_power", "soh"])
        self.assertEqual([s.did for s in profile.signals], list(range(0xD001, 0xD007)))
        self.assertEqual({s.ecu for s in profile.signals}, {7})
        self.assertEqual([s.signed for s in profile.signals],
                         [False, False, True, True, False, False])

    def test_invalid_profile_and_signal_fields(self):
        invalid_profiles = [
            [],
            profile_data(version=True),
            profile_data(version=2),
            profile_data(simulator_only=1),
            profile_data(signals=[]),
            profile_data(signals=[signal(), signal(did=0xD002)]),
            profile_data(vin="  "),
            profile_data(extra=True),
        ]
        for data in invalid_profiles:
            with self.subTest(data=data), self.assertRaises(ValueError):
                load_profile(save_json(data))

        invalid_signals = [
            signal(ecu=True), signal(ecu=0x10000), signal(did=-1),
            signal(offset=-1), signal(offset=0x10000), signal(length=0),
            signal(length=9), signal(byteorder="middle"),
            signal(signed=0), signal(scale=float("nan")), signal(add=float("inf")),
            signal(key=""), signal(unit=" "), signal(extra="no"),
        ]
        for item in invalid_signals:
            with self.subTest(signal=item), self.assertRaises(ValueError):
                load_profile(save_json(profile_data(signals=[item])))

    def test_simulator_only_and_vin_gates_do_no_io(self):
        simulator_profile = load_profile(save_json(profile_data(simulator_only=True)))
        vin_profile = load_profile(save_json(profile_data(vin="WBY12345678901234")))
        for target, kwargs in [
            (simulator_profile, {}),
            (vin_profile, {}),
            (vin_profile, {"vin": "WBY00000000000000"}),
        ]:
            client = Mock()
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                read_profile(client, target, **kwargs)
            self.assertEqual(client.mock_calls, [])

    def test_per_signal_read_and_decode_errors_are_isolated(self):
        data = profile_data(signals=[signal(), signal(key="next", did=0xD002)])
        profile = load_profile(save_json(data))
        client = Mock()
        client.read_did.side_effect = [RuntimeError("unsupported"), b"\x00"]
        values = read_profile(client, profile)
        self.assertEqual([v["value"] for v in values], [None, None])
        self.assertEqual(values[0]["error"], "unsupported")
        self.assertEqual(values[0]["raw"], None)
        self.assertIn("short response", values[1]["error"])
        self.assertEqual(values[1]["raw"], "00")
        self.assertEqual([call.args for call in client.read_did.call_args_list],
                         [(7, 0xD001), (7, 0xD002)])

    def test_reads_only_and_reports_values_and_formatted_raw(self):
        profile = load_profile(DEMO)
        client = Mock()
        client.read_did.return_value = b"\x01\x2c"
        values = read_profile(client, profile, is_simulator=True)
        self.assertEqual(values[0], {
            "key": "soc", "name": "Batarya doluluk oranı", "unit": "%",
            "value": 30.0, "raw": "01 2C", "error": None,
        })
        self.assertTrue(all(value["value"] == 30.0 for value in values))
        self.assertEqual([call[0] for call in client.mock_calls], ["read_did"] * 6)

    def test_exact_vin_allows_reads(self):
        profile = load_profile(save_json(profile_data(vin="WBY12345678901234")))
        client = Mock()
        client.read_did.return_value = b"\x00\x01"
        self.assertEqual(read_profile(client, profile, vin="WBY12345678901234")[0]["value"], 0.1)
        self.assertEqual(client.read_did.call_count, 1)


if __name__ == "__main__":
    unittest.main()
