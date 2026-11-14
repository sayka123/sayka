"""Read-only discovery: save every readable data block of some modules, then diff two saves.

Workflow: snapshot, change one setting from the car's own menu (iDrive), snapshot again,
diff. The changed byte/bits are where that setting lives on this car.
"""

import json
import time

from .hsfz import NoResponse
from .uds import NegativeResponse, ProtocolError

DEFAULT_RANGE = (0x3000, 0x3FFF)  # BMW coding data area
MAX_SILENT = 3  # consecutive timeouts before a module is treated as absent


def take_snapshot(client, ecus, did_range=DEFAULT_RANGE, timeout=0.5, progress=None, stop=None):
    """Return {ecu: {did: bytes}} for every DID that answered positively. Only sends reads."""
    first, last = did_range
    total = len(ecus) * (last - first + 1)
    done = 0
    result = {}
    for ecu in ecus:
        blocks, silent = {}, 0
        for did in range(first, last + 1):
            if stop and stop():
                return result
            done += 1
            if progress and done % 64 == 0:
                progress(done, total, ecu)
            try:
                blocks[did] = client.read_did(ecu, did, timeout=timeout)
                silent = 0
            except (NegativeResponse, ProtocolError):
                silent = 0
            except NoResponse:
                silent += 1
                if silent >= MAX_SILENT:
                    done += last - did
                    break
        if blocks:
            result[ecu] = blocks
    return result


def save(path, snap, vin=None):
    data = {"vin": vin, "time": time.strftime("%Y%m%d-%H%M%S"),
            "modules": {f"0x{e:02X}": {f"0x{d:04X}": b.hex() for d, b in sorted(blocks.items())}
                        for e, blocks in sorted(snap.items())}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    snap = {int(e, 16): {int(d, 16): bytes.fromhex(h) for d, h in blocks.items()}
            for e, blocks in data["modules"].items()}
    return snap, data.get("vin")


class Change:
    def __init__(self, ecu, did, byte, old, new):
        self.ecu, self.did, self.byte, self.old, self.new = ecu, did, byte, old, new
        self.mask = (old ^ new) if old is not None and new is not None else 0xFF

    def describe(self):
        fmt = lambda v: "-" if v is None else f"0x{v:02X}"
        return f"bayt {self.byte}: {fmt(self.old)} -> {fmt(self.new)} (bitler 0x{self.mask:02X})"

    def to_definition(self, name, before="Önce", after="Sonra"):
        """A coding-list entry (see coding.py) that toggles only the bits that changed."""
        if self.old is None or self.new is None:
            raise ValueError("blok uzunluğu değişmiş; bu fark kodlama tanımına çevrilemez")
        return {"name": name, "ecu": f"0x{self.ecu:02X}", "did": f"0x{self.did:04X}",
                "byte": self.byte, "mask": f"0x{self.mask:02X}",
                "options": {before: f"0x{self.old & self.mask:02X}", after: f"0x{self.new & self.mask:02X}"},
                "note": "Keşif farkından oluşturuldu"}


def diff(a, b):
    """Byte-level changes from snapshot a to snapshot b, for blocks present in both."""
    changes = []
    for ecu in sorted(set(a) & set(b)):
        for did in sorted(set(a[ecu]) & set(b[ecu])):
            x, y = a[ecu][did], b[ecu][did]
            for i in range(max(len(x), len(y))):
                old = x[i] if i < len(x) else None
                new = y[i] if i < len(y) else None
                if old != new:
                    changes.append(Change(ecu, did, i, old, new))
    return changes


def append_definition(path, definition):
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        items = []
    items.append(definition)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
