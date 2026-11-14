"""Coding: change bits in an ECU's data identifiers, with backup and read-back verification.

Definitions come from a JSON file so the user decides exactly which bytes are written:
[
  {"name": "...", "ecu": "0x72", "did": "0x3000", "byte": 2, "mask": "0x01",
   "options": {"Açık": "0x01", "Kapalı": "0x00"}, "note": "..."}
]
"""

import json
import os
import time

from .uds import EXTENDED_SESSION, NegativeResponse


SECURE_CODING_NRCS = {0x22, 0x33, 0x35, 0x72}


class CodingRejected(NegativeResponse):
    def __init__(self, sid, nrc):
        super().__init__(sid, nrc)
        self.args = (self.args[0] + ". Bu modül yalnızca BMW tarafından araç şasisine özel imzalanmış "
                     "kodlamayı kabul ediyor olabilir (Secure Coding / NCD 2.0, 2021 sonrası araçlar, "
                     "örn. iX). Araçta hiçbir değişiklik yapılmadı.",)


def _int(v):
    return int(v, 0) if isinstance(v, str) else int(v)


class CodingDefinition:
    def __init__(self, d):
        self.name = d["name"]
        self.ecu = _int(d["ecu"])
        self.did = _int(d["did"])
        self.byte = _int(d["byte"])
        self.mask = _int(d.get("mask", "0xFF"))
        self.options = {k: _int(v) for k, v in d["options"].items()}
        self.note = d.get("note", "")
        for label, value in self.options.items():
            if value & ~self.mask:
                raise ValueError(f"{self.name}: '{label}' değeri maskenin dışında")

    def current_label(self, block):
        if self.byte >= len(block):
            raise ValueError(f"{self.name}: veri bloğu beklenenden kısa")
        value = block[self.byte] & self.mask
        for label, v in self.options.items():
            if v == value:
                return label
        return f"bilinmeyen (0x{value:02X})"

    def apply_to(self, block, label):
        new = bytearray(block)
        new[self.byte] = (new[self.byte] & ~self.mask & 0xFF) | self.options[label]
        return bytes(new)


def load_definitions(path):
    with open(path, encoding="utf-8") as f:
        return [CodingDefinition(d) for d in json.load(f)]


def read_current(client, definition):
    block = client.read_did(definition.ecu, definition.did)
    return definition.current_label(block)


def save_backup(backup_dir, ecu, did, data, vin=None):
    os.makedirs(backup_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    base = os.path.join(backup_dir, f"yedek_{ecu:02X}_{did:04X}_{stamp}")
    path, n = base + ".json", 1
    while os.path.exists(path):  # never overwrite an earlier backup
        n += 1
        path = f"{base}_{n}.json"
    with open(path, "x", encoding="utf-8") as f:
        json.dump({"vin": vin, "ecu": f"0x{ecu:02X}", "did": f"0x{did:04X}",
                   "data": data.hex(), "time": stamp}, f, indent=2)
    return path


def write_block(client, ecu, did, data, backup_dir, vin=None):
    """Back up the current block, write the new one and verify it. Returns the backup path."""
    old = client.read_did(ecu, did)
    backup = save_backup(backup_dir, ecu, did, old, vin)
    if old == bytes(data):
        return backup
    try:
        client.session(ecu, EXTENDED_SESSION)
    except NegativeResponse:
        pass  # some modules accept writes in the default session
    try:
        client.write_did(ecu, did, data)
    except NegativeResponse as e:
        if e.nrc in SECURE_CODING_NRCS:
            raise CodingRejected(e.sid, e.nrc) from e
        raise
    check = client.read_did(ecu, did)
    if check != bytes(data):
        raise RuntimeError(
            f"doğrulama başarısız: yazılan {bytes(data).hex()} okunan {check.hex()} "
            f"(yedek: {backup})")
    return backup


def apply(client, definition, label, backup_dir, vin=None):
    block = client.read_did(definition.ecu, definition.did)
    return write_block(client, definition.ecu, definition.did,
                       definition.apply_to(block, label), backup_dir, vin)


def restore(client, backup_path, backup_dir):
    with open(backup_path, encoding="utf-8") as f:
        b = json.load(f)
    return write_block(client, _int(b["ecu"]), _int(b["did"]),
                       bytes.fromhex(b["data"]), backup_dir, b.get("vin"))
