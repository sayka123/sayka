"""User-initiated connection inspection; never sends write requests."""

import tkinter as tk
from tkinter import ttk

from . import connection_check, health_check, theme

STATES = {"vin_read": "VIN okundu", "refused": "Modül yanıtladı / okuma reddedildi",
          "no_response": "Yanıt yok", "invalid_response": "Geçersiz yanıt", "transport_error": "Bağlantı hatası"}


class ConnectionInspection:
    def on_health_check(self):
        if not self.require_connection():
            return
        self._stop_ev()
        client, is_demo = self.uds, self._connection_demo
        candidates = self._candidate_ecus()
        profile = self.ev_profile if self.is_ev else None
        vin = self.vin

        def work():
            return health_check.run_health_check(
                client, candidates, simulator=is_demo, profile=profile, vin=vin,
                progress=lambda *args: self._results.put(
                    (lambda p: self.status.set(
                        f"Sağlık kontrolü: {p[0]} {p[1]}/{p[2]}"), args, None)))

        def done(report):
            self.last_health_check = report
            self.found_ecus = list(report["scan"]["found"])
            self.module_count.set(str(len(self.found_ecus)))
            self.modules_read_at = report["created_at"]
            self.last_dtcs = report["dtcs"]["records"]
            self.dtcs_read_at = report["dtcs"]["read_at"]
            if report.get("measurements") and report["measurements"].get("results"):
                self.ev_results = report["measurements"]["results"]
                self.ev_read_at = report["measurements"]["read_at"]
            self._show_health_check(report)
            prefix = "DEMO" if is_demo else "ARAÇ"
            self.status.set(f"{prefix} sağlık kontrolü tamamlandı: {report['status']} · "
                            f"{len(self.found_ecus)} modül · {report['dtcs']['total_codes']} hata kodu")

        self.run_bg(work, done, "Salt okunur sağlık kontrolü yapılıyor...")

    def _show_health_check(self, report):
        window = tk.Toplevel(self)
        source = "DEMO / SİMÜLATÖR" if report["source"] == "simulator" else "ARAÇ YANITLARI"
        window.title(f"{source} · Üst seviye sağlık kontrolü")
        window.geometry("1040x560")
        window.minsize(860, 430)
        window.configure(background=theme.BG)
        body = ttk.Frame(window, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=f"{source} · Sağlık özeti: {report['status'].upper()}",
                  style="Section.TLabel").pack(anchor="w")
        vin_state = "okundu" if report["vin"]["vin_consistent"] else "tutarsız/yok"
        ttk.Label(body, text=(f"{report['created_at']} · VIN: {vin_state} · Modül: "
                              f"{len(report['scan']['found'])}/{len(report['scan']['requested'])} · "
                              f"Hata kodu: {report['dtcs']['total_codes']} ({report['dtcs']['active_codes']} aktif)"),
                  style="Muted.TLabel", wraplength=940).pack(anchor="w", pady=(8, 0))
        tree = self._tree(body, ("section", "item", "detail"),
                          ("Bölüm", "Öğe", "Ayrıntı"), (110, 260, 520), height=8)
        for address in report["scan"]["found"]:
            tree.insert("", "end", values=("modül", f"0x{address:02X}", "tester-present"))
        for record in report["dtcs"]["records"]:
            if record["error"]:
                tree.insert("", "end", values=("hata kodu", f"0x{record['ecu']:02X}", record["error"]))
            for code in record["codes"] or []:
                state = "aktif" if code["status"] & 0x01 else ("kayıtlı" if code["status"] & 0x08 else "beklemede")
                tree.insert("", "end", values=("hata kodu", f"0x{record['ecu']:02X}", f"{code['code']} · {state}"))
        if report.get("measurements"):
            for row in report["measurements"].get("results", []):
                detail = "okundu" if row["error"] is None else row["error"]
                tree.insert("", "end", values=("ölçüm", row["key"], f"{row['value']} {row['unit']} · {detail}"))
        for warning in report["warnings"]:
            tree.insert("", "end", values=("uyarı", "-", warning))
        ttk.Label(body, text=report["limits"] + " Bu rapora VIN yalnızca VIN seçeneği açıksa eklenir.",
                  style="Muted.TLabel", wraplength=940).pack(anchor="w", pady=8)
        ttk.Button(body, text="Kapat", command=window.destroy).pack(anchor="e")

    def on_check_connection(self):
        if not self.require_connection():
            return
        self._stop_ev()
        client, is_demo = self.uds, self._connection_demo
        addresses = list(self.found_ecus) if self.found_ecus else [0x10, 0x40, 0x07, 0x63]
        if not self.is_ev and not self.found_ecus:
            addresses = [0x10, 0x40, 0x12, 0x63]
        if len(addresses) > 64:
            self.status.set("Bağlantı testinde en fazla ilk 64 bulunan adres kontrol edilecek.")

        def done(result):
            self.last_connection_check = result
            self._show_connection_check(result)
            count = sum(row["state"] == "vin_read" for row in result["results"])
            prefix = "DEMO" if is_demo else "ARAÇTAN ALINAN YANITLAR"
            self.status.set(f"{prefix}: {count}/{len(result['results'])} VIN okuması başarılı; ayrıntıları inceleyin.")

        self.run_bg(lambda: connection_check.check_connection(client, addresses[:64], simulator=is_demo),
                    done, "Bağlantı salt okunur VIN istekleriyle kontrol ediliyor...")

    def _show_connection_check(self, result):
        window = tk.Toplevel(self)
        window.title("Bağlantı kontrolü · " + ("DEMO" if result["source"] == "simulator" else "ARAÇ"))
        window.geometry("1000x480")
        window.minsize(800, 380)
        window.configure(background=theme.BG)
        body = ttk.Frame(window, padding=20)
        body.pack(fill="both", expand=True)
        prefix = "DEMO / SİMÜLATÖR" if result["source"] == "simulator" else "ARAÇ YANITLARI"
        ttk.Label(body, text=f"{prefix} · Bağlantı kontrol sonucu", style="Section.TLabel").pack(anchor="w")
        ttk.Label(body, text=f"{result['checked_at']} · " + result["note"], wraplength=900,
                  style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
        tree = self._tree(body, ("ecu", "state", "latency", "detail"),
                          ("Modül", "Sonuç", "Süre (ms)", "Ayrıntı"), (80, 270, 90, 420), height=5)
        for row in result["results"]:
            detail = "17 karakterli VIN geçerli" if row["state"] == "vin_read" else row["error"]
            tree.insert("", "end", values=(f"0x{row['ecu']:04X}", STATES[row["state"]], row["latency_ms"], detail))
        consistency = result["vin_consistent"]
        label = ("Okunan VIN değerleri tutarlı." if consistency else "UYARI: Modüller farklı VIN bildirdi.") if consistency is not None else "Geçerli VIN okunamadı."
        ttk.Label(body, text=label, foreground=theme.ACCENT if consistency else "#EBC389").pack(anchor="w", pady=10)
        ttk.Label(body, text="Bu sonuç son teşhis raporuna eklenir. VIN yalnızca rapordaki VIN seçeneği açıksa eklenir.",
                  style="Muted.TLabel", wraplength=900).pack(anchor="w")
        ttk.Button(body, text="Kapat", command=window.destroy).pack(anchor="e", pady=(8, 0))
