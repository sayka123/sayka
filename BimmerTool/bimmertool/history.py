"""Bounded in-memory history for EV measurement samples."""

import copy
import csv
import math
from collections import deque


_CSV_FIELDS = ("source", "read_at", "key", "name", "value", "unit", "raw", "error")


def _csv_safe(value):
    if isinstance(value, str) and value.lstrip() and value.lstrip()[0] in "=+-@":
        return "'" + value
    return value


def _chart_value(row):
    if row.get("error"):
        return None
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:
        return None


class History:
    """Keep a bounded, isolated in-memory sequence of measurement samples."""

    def __init__(self, limit=300):
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be a positive integer")
        self._samples = deque(maxlen=limit)

    def append(self, timestamp, rows, source):
        """Store a deep snapshot; this method never writes to disk."""
        self._samples.append({
            "timestamp": copy.deepcopy(timestamp),
            "source": copy.deepcopy(source),
            "rows": copy.deepcopy(rows),
        })

    def clear(self):
        self._samples.clear()

    @property
    def samples(self):
        return copy.deepcopy(list(self._samples))

    def series(self, key):
        """Return ``(timestamp, value)`` pairs, using ``None`` for gaps."""
        result = []
        for sample in self._samples:
            value = None
            for row in sample["rows"]:
                if row.get("key") == key:
                    value = _chart_value(row)
                    break
            result.append((copy.deepcopy(sample["timestamp"]), value))
        return result

    def export_csv(self, path):
        """Explicitly export every stored measurement row as UTF-8 with BOM."""
        with open(path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for sample in self._samples:
                for row in sample["rows"]:
                    output = {
                        "source": sample["source"],
                        "read_at": sample["timestamp"],
                        **{field: row.get(field) for field in _CSV_FIELDS[2:]},
                    }
                    writer.writerow({field: _csv_safe(value)
                                     for field, value in output.items()})
