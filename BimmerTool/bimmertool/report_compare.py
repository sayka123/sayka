"""Validate and compare saved BimmerTool diagnostic reports without vehicle I/O."""

import json
import re


FORMAT = "bimmertool-diagnostic-report-v1"
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_MODULES = 512
MAX_CODES = 10_000
_CODE_RE = re.compile(r"[0-9A-Fa-f]{6}\Z")


def _integer(value, minimum, maximum, label):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{label} aralığın dışında veya geçersiz")


def _validate_report(report):
    if not isinstance(report, dict) or report.get("format") != FORMAT:
        raise ValueError("Geçersiz tanılama raporu biçimi")
    if report.get("source") not in ("simulator", "vehicle"):
        raise ValueError("Rapor kaynağı simulator veya vehicle olmalı")
    if "vin" in report and report["vin"] is not None and not isinstance(report["vin"], str):
        raise ValueError("VIN metin veya null olmalı")

    modules = report.get("dtcs")
    if not isinstance(modules, list) or len(modules) > MAX_MODULES:
        raise ValueError("dtcs listesi geçersiz veya çok büyük")

    seen_ecus = set()
    total_codes = 0
    for module in modules:
        if not isinstance(module, dict) or not {"ecu", "error", "codes"} <= module.keys():
            raise ValueError("Modül kaydı nesne olmalı")
        ecu = module.get("ecu")
        _integer(ecu, 0, 0xFFFF, "ECU")
        if ecu in seen_ecus:
            raise ValueError("ECU adresi tekrarlanamaz")
        seen_ecus.add(ecu)

        error = module.get("error")
        codes = module.get("codes")
        if error is not None and (not isinstance(error, str) or not error.strip()):
            raise ValueError("Modül hatası boş olmayan metin veya null olmalı")
        if error is None:
            if not isinstance(codes, list):
                raise ValueError("Başarılı modül codes listesi içermeli")
        elif codes is not None:
            raise ValueError("Okuma hatası olan modül codes=null içermeli")
        if codes is None:
            continue

        total_codes += len(codes)
        if total_codes > MAX_CODES:
            raise ValueError("Toplam hata kodu sayısı sınırı aşıldı")
        seen_codes = set()
        for item in codes:
            if not isinstance(item, dict) or not {"code", "status"} <= item.keys():
                raise ValueError("Hata kodu kaydı nesne olmalı")
            code = item.get("code")
            if not isinstance(code, str) or not _CODE_RE.fullmatch(code):
                raise ValueError("Hata kodu altı onaltılık karakter olmalı")
            canonical_code = code.upper()
            if canonical_code in seen_codes:
                raise ValueError("Modül içinde hata kodu tekrarlanamaz")
            seen_codes.add(canonical_code)
            status = item.get("status")
            if status is not None:
                _integer(status, 0, 255, "Durum")
    return report


def load_report(path):
    """Load one bounded-size JSON report and validate its schema."""
    try:
        with open(path, "rb") as file:
            contents = file.read(MAX_FILE_SIZE + 1)
        if len(contents) > MAX_FILE_SIZE:
            raise ValueError("Rapor dosyası 5 MB sınırını aşıyor")
        report = json.loads(contents.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Rapor JSON olarak okunamadı") from exc
    return _validate_report(report)


def compare_reports(before, after):
    """Compare only modules successfully read in both reports."""
    before = _validate_report(before)
    after = _validate_report(after)
    if before["source"] != after["source"]:
        raise ValueError("Farklı kaynaklardaki raporlar karşılaştırılamaz")
    before_vin, after_vin = before.get("vin"), after.get("vin")
    if before_vin and after_vin and before_vin != after_vin:
        raise ValueError("VIN bilgileri farklı; raporlar karşılaştırılamaz")

    old_modules = {module["ecu"]: module for module in before["dtcs"]}
    new_modules = {module["ecu"]: module for module in after["dtcs"]}
    rows = []
    for ecu in sorted(old_modules.keys() | new_modules.keys()):
        old_module = old_modules.get(ecu)
        new_module = new_modules.get(ecu)
        old_ok = old_module is not None and old_module.get("error") is None
        new_ok = new_module is not None and new_module.get("error") is None
        if not old_ok or not new_ok:
            old_state = "Okunamadı" if old_module is None else old_module.get("error") or "Okundu"
            new_state = "Okunamadı" if new_module is None else new_module.get("error") or "Okundu"
            rows.append({"ecu": ecu, "code": "—", "before": old_state,
                         "after": new_state, "change": "Karşılaştırılamadı"})
            continue

        old_codes = {item["code"].upper(): item["status"] for item in old_module["codes"]}
        new_codes = {item["code"].upper(): item["status"] for item in new_module["codes"]}
        for code in sorted(old_codes.keys() | new_codes.keys()):
            old_status = old_codes.get(code)
            new_status = new_codes.get(code)
            if code not in old_codes:
                change = "Yeni kayıt"
            elif code not in new_codes:
                change = "Artık raporlanmıyor"
            elif old_status != new_status:
                change = "Durum değişti"
            else:
                continue
            rows.append({"ecu": ecu, "code": code, "before": old_status,
                         "after": new_status, "change": change})
    return rows
