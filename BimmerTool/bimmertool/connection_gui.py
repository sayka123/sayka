"""User-initiated connection inspection; never sends write requests."""

import tkinter as tk
from tkinter import ttk

from . import connection_check, theme

STATES = {"vin_read": "VIN okundu", "refused": "Modül yanıtladı / okuma reddedildi",
          "no_response": "Yanıt yok", "invalid_response": "Geçersiz yanıt", "transport_error": "Bağlantı hatası"}


class ConnectionInspection:
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
