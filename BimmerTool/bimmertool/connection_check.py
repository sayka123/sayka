"""Bounded read-only checks on an already selected diagnostic connection."""

import re
import time

from .hsfz import NoResponse
from .uds import NegativeResponse, ProtocolError


VIN_PATTERN = re.compile(r"[A-HJ-NPR-Z0-9]{17}\Z")


def decode_vin(data):
    try:
        vin = data.decode("ascii").strip("\x00 ")
    except (AttributeError, UnicodeDecodeError) as error:
        raise ValueError("VIN ASCII biçiminde değil") from error
    if not VIN_PATTERN.fullmatch(vin):
        raise ValueError("VIN 17 geçerli karakterden oluşmuyor")
    return vin


def check_connection(client, ecus, *, simulator=False):
    """Use only VIN reads; refusal proves response, never successful VIN access."""
    addresses = list(dict.fromkeys(ecus))
    if not addresses or len(addresses) > 64 or any(type(a) is not int or not 0 <= a <= 65535 for a in addresses):
        raise ValueError("Bağlantı testi 1–64 geçerli modül adresi gerektirir")
    rows = []
    for address in addresses:
        start = time.monotonic()
        row = {"ecu": address, "state": None, "latency_ms": None, "vin": None,
               "nrc": None, "error": None}
        try:
            data = client.read_did(address, 0xF190, timeout=1.0)
            row["vin"] = decode_vin(data)
            row["state"] = "vin_read"
        except NegativeResponse as error:
            row.update(state="refused", nrc=error.nrc, error=str(error))
        except NoResponse as error:
            row.update(state="no_response", error=str(error))
        except (ProtocolError, ValueError) as error:
            row.update(state="invalid_response", error=str(error))
        except OSError as error:
            row.update(state="transport_error", error=str(error))
        row["latency_ms"] = round((time.monotonic() - start) * 1000, 1)
        rows.append(row)
        if row["state"] == "transport_error":
            break
    vins = {row["vin"] for row in rows if row["vin"]}
    return {"source": "simulator" if simulator else "vehicle",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "requested_ecus": addresses, "results": rows,
            "vin_consistent": len(vins) == 1 if vins else None,
            "note": "VIN okuma testi; tüm modülleri, kabloyu fiziksel olarak veya kodlama uygunluğunu doğrulamaz."}


def public_result(result, include_vin=False):
    """Explicit VIN opt-in, including VIN values reported by individual modules."""
    return {**result, "results": [{**row, "vin": row["vin"] if include_vin else None}
                                  for row in result["results"]]}
