"""Bounded, read-only vehicle health overview.

Only UDS tester-present, ReadDataByIdentifier and ReadDTCInformation requests are
used. This module never sends a write, clear, session-change, programming or
download request.
"""

import copy
import time

from . import ev
from .connection_check import check_connection

MAX_SCAN = 64
MAX_DTC_MODULES = 32


def _validate_addresses(addresses, limit):
    if type(limit) is not int or not 1 <= limit <= MAX_SCAN:
        raise ValueError(f"max_scan 1–{MAX_SCAN} aralığında tam sayı olmalı")
    addresses = list(addresses)
    if any(type(a) is not int or not 0 <= a <= 0xFFFF for a in addresses):
        raise ValueError("Modül adresleri 0x0000–0xFFFF aralığında tam sayı olmalı")
    addresses = list(dict.fromkeys(addresses))
    if not addresses or len(addresses) > limit:
        raise ValueError(f"1–{limit} benzersiz modül adresi gerekir")
    return addresses


def run_health_check(client, candidates, *, simulator=False, profile=None, vin=None,
                     max_scan=MAX_SCAN, scan_timeout=0.6, progress=None):
    """Run a bounded scan, VIN read, DTC read and optional EV profile read."""
    if type(simulator) is not bool:
        raise ValueError("simulator must be a boolean")
    scan_addresses = _validate_addresses(candidates, max_scan)[:max_scan]
    found, scan_errors = [], []
    for index, address in enumerate(scan_addresses):
        if progress:
            progress("scan", index + 1, len(scan_addresses), address)
        try:
            present = client.is_present(address, timeout=scan_timeout)
        except Exception as error:
            present = False
            scan_errors.append({"ecu": address, "error": str(error)})
        if present:
            found.append(address)

    vin_targets = found[:MAX_SCAN] or [0x10, 0x40, 0x07, 0x63][:MAX_SCAN]
    vin_report = check_connection(client, vin_targets[:MAX_SCAN], simulator=simulator)

    dtc_modules = found[:MAX_DTC_MODULES]
    dtc_scan_partial = len(found) > MAX_DTC_MODULES
    records, total, active = [], 0, 0
    for index, address in enumerate(dtc_modules):
        if progress:
            progress("dtcs", index + 1, len(dtc_modules), address)
        try:
            dtcs = client.read_dtcs(address)
            codes = [{"code": f"{code:06X}", "status": status} for code, status in dtcs]
            total += len(codes)
            active += sum(1 for item in codes if item["status"] & 0x01)
            records.append({"ecu": address, "error": None, "codes": codes})
        except Exception as error:
            records.append({"ecu": address, "error": str(error), "codes": None})

    measurements = None
    if profile is not None:
        if progress:
            progress("measurements", 1, 1, None)
        try:
            measurements = {
                "profile": profile.name,
                "read_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "results": ev.read_profile(client, profile, is_simulator=simulator, vin=vin),
            }
        except Exception as error:
            measurements = {"profile": profile.name, "read_at": None,
                            "results": [], "error": str(error)}

    warnings = []
    if vin_report["vin_consistent"] is False:
        warnings.append("Modüller farklı VIN bildirdi; yazma yapmayın.")
    if vin_report["vin_consistent"] is None:
        warnings.append("Hiçbir modülden geçerli VIN okunamadı.")
    if any(row["state"] == "invalid_response" for row in vin_report["results"]):
        warnings.append("Bazı modüllerin VIN yanıtı geçersiz veya eksik.")
    if any(row["state"] == "transport_error" for row in vin_report["results"]):
        warnings.append("VIN okuması taşıma/bağlantı hatası nedeniyle tamamlanamadı.")
    if not found:
        warnings.append("Hiçbir modül tester-present yanıt vermedi.")
    if scan_errors:
        warnings.append(f"{len(scan_errors)} modül taraması hata verdi.")
    if any(record["error"] for record in records):
        warnings.append("Bazı modüllerin hata kodları okunamadı.")
    if dtc_scan_partial:
        warnings.append(f"Hata kodları yalnızca ilk {MAX_DTC_MODULES} modülden okundu; tarama kısmi.")
    if total:
        warnings.append(f"{total} hata kodu bildirildi (aktif: {active}, diğer durumlar dahil).")
    if active:
        warnings.append(f"{active} aktif hata kodu bulundu; bu arızanın nedenini belirtmez.")
    if measurements and measurements.get("error"):
        warnings.append("EV ölçüm profili okunamadı: " + measurements["error"])
    elif measurements:
        signal_errors = sum(bool(row.get("error")) for row in measurements.get("results", []))
        if signal_errors:
            warnings.append(f"{signal_errors} EV sinyalinin ölçümü okunamadı.")

    status = "attention" if warnings else "ok"
    return {
        "format": "bimmertool-health-check-v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": "simulator" if simulator else "vehicle",
        "status": status,
        "scan": {"requested": scan_addresses, "found": found, "errors": scan_errors,
                 "exhaustive": False},
        "vin": vin_report,
        "dtcs": {"read_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "modules": dtc_modules, "records": records,
                 "modules_tried": len(dtc_modules), "modules_available": len(found),
                 "partial": dtc_scan_partial,
                 "modules_read": sum(r["error"] is None for r in records),
                 "total_codes": total, "active_codes": active},
        "measurements": measurements,
        "warnings": warnings,
        "limits": "Salt okunur özet. Tüm modülleri, kabloyu fiziksel olarak, yazılım sürümünü, "
                  "batarya sağlığını veya kodlama uygunluğunu doğrulamaz.",
    }


def public_health(result, include_vin=False):
    """Redact VIN unless the user explicitly opted in for the report."""
    result = copy.deepcopy(result)
    vin = result.get("vin", {})
    if not include_vin:
        vin["results"] = [{**row, "vin": None} for row in vin.get("results", [])]
    return result
