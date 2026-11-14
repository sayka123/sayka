"""Read-only, profile-driven EV measurements from UDS data identifiers.

Profiles describe raw byte decoding only; they do not imply that a DID is valid
for any real vehicle. The bundled iX example uses simulator-only fake addresses.
"""

import json
import math
from dataclasses import dataclass


_PROFILE_KEYS = {"version", "name", "simulator_only", "vin", "signals"}
_SIGNAL_KEYS = {
    "key", "name", "unit", "ecu", "did", "offset", "length",
    "byteorder", "signed", "scale", "add",
}


def _nonempty_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _integer(value, field, minimum, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        bounds = f"{minimum}" if maximum is None else f"{minimum}..{maximum}"
        raise ValueError(f"{field} must be an integer in range {bounds}")
    return value


def _factor(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


@dataclass(frozen=True)
class Signal:
    key: str
    name: str
    unit: str
    ecu: int
    did: int
    offset: int
    length: int
    byteorder: str
    signed: bool
    scale: float
    add: float

    def decode(self, data):
        """Decode this signal's integer bytes and apply ``raw * scale + add``."""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("signal data must be bytes-like")
        data = bytes(data)
        end = self.offset + self.length
        if len(data) < end:
            raise ValueError(
                f"short response: need bytes {self.offset}..{end - 1}, got {len(data)}")
        raw = int.from_bytes(data[self.offset:end], self.byteorder, signed=self.signed)
        return raw * self.scale + self.add


@dataclass(frozen=True)
class Profile:
    name: str
    simulator_only: bool
    vin: str | None
    signals: tuple[Signal, ...]


def _make_signal(value, index):
    if not isinstance(value, dict):
        raise ValueError(f"signals[{index}] must be an object")
    if set(value) != _SIGNAL_KEYS:
        missing = sorted(_SIGNAL_KEYS - set(value))
        extra = sorted(set(value) - _SIGNAL_KEYS)
        raise ValueError(f"signals[{index}] fields invalid (missing={missing}, extra={extra})")

    key = _nonempty_string(value["key"], f"signals[{index}].key")
    name = _nonempty_string(value["name"], f"signals[{index}].name")
    unit = _nonempty_string(value["unit"], f"signals[{index}].unit")
    ecu = _integer(value["ecu"], f"signals[{index}].ecu", 0, 0xFFFF)
    did = _integer(value["did"], f"signals[{index}].did", 0, 0xFFFF)
    offset = _integer(value["offset"], f"signals[{index}].offset", 0)
    length = _integer(value["length"], f"signals[{index}].length", 1)
    byteorder = value["byteorder"]
    if byteorder not in ("big", "little"):
        raise ValueError(f"signals[{index}].byteorder must be 'big' or 'little'")
    signed = value["signed"]
    if type(signed) is not bool:
        raise ValueError(f"signals[{index}].signed must be a boolean")

    return Signal(
        key, name, unit, ecu, did, offset, length, byteorder, signed,
        _factor(value["scale"], f"signals[{index}].scale"),
        _factor(value["add"], f"signals[{index}].add"),
    )


def load_profile(path):
    """Load and validate a version-1 EV measurement profile from JSON."""
    with open(path, encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError("profile must be an object")
    if set(value) - _PROFILE_KEYS:
        raise ValueError(f"unknown profile fields: {sorted(set(value) - _PROFILE_KEYS)}")
    required = _PROFILE_KEYS - {"vin"}
    if not required <= set(value):
        raise ValueError(f"missing profile fields: {sorted(required - set(value))}")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("profile version must be integer 1")
    name = _nonempty_string(value["name"], "name")
    simulator_only = value["simulator_only"]
    if type(simulator_only) is not bool:
        raise ValueError("simulator_only must be a boolean")
    vin = value.get("vin")
    if vin is not None:
        vin = _nonempty_string(vin, "vin")
    signals_value = value["signals"]
    if not isinstance(signals_value, list) or not signals_value:
        raise ValueError("signals must be a non-empty list")
    signals = tuple(_make_signal(signal, index) for index, signal in enumerate(signals_value))
    keys = [signal.key for signal in signals]
    if len(keys) != len(set(keys)):
        raise ValueError("signal keys must be unique")
    return Profile(name, simulator_only, vin, signals)


def read_profile(client, profile, *, is_simulator=False, vin=None):
    """Read every signal using only ``client.read_did``; isolate failures per signal."""
    if not isinstance(profile, Profile):
        raise TypeError("profile must be a Profile")
    if type(is_simulator) is not bool:
        raise ValueError("is_simulator must be a boolean")
    if profile.simulator_only and not is_simulator:
        raise ValueError("simulator-only profile cannot be used on a real connection")
    if profile.vin is not None:
        if vin is None:
            raise ValueError("this profile requires its exact VIN")
        if not isinstance(vin, str) or vin != profile.vin:
            raise ValueError("VIN does not match this profile")

    results = []
    for signal in profile.signals:
        result = {
            "key": signal.key,
            "name": signal.name,
            "unit": signal.unit,
            "value": None,
            "raw": None,
            "error": None,
        }
        try:
            raw = client.read_did(signal.ecu, signal.did)
            result["raw"] = raw
            result["value"] = signal.decode(raw)
        except Exception as error:
            result["error"] = str(error) or error.__class__.__name__
        results.append(result)
    return results
