"""Read-only electric vehicle workspace and local diagnostic exports."""

import json
import csv
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import ev, theme
from .history import History


class EvWorkspace:
    def _build_ev_tab(self):
        self.ev_profile = None
        self.ev_results = []
        self.ev_read_at = None
        self._ev_busy = False
        self._ev_running = False
        self._ev_generation = 0
        self._ev_timer = None
        self.ev_history = History(limit=300)
        f = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(f, text="iX / Elektrikli")
        ttk.Label(f, text="BATARYA VE ŞARJ  /  SALT OKUNUR", foreground=theme.ACCENT).pack(anchor="w")
        self.ev_profile_label = tk.StringVar(value="Profil yok. Gerçek iX40 ölçüm adresleri bu pakette bulunmaz.")
        ttk.Label(f, textvariable=self.ev_profile_label, style="Muted.TLabel", wraplength=820).pack(
            anchor="w", pady=(6, 8))
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        ttk.Button(bar, text="Ölçüm profili yükle", command=self.on_ev_profile).pack(side="left")
        ttk.Button(bar, text="iX demo profili", command=self.on_ev_demo).pack(side="left", padx=6)
        self.ev_read_btn = ttk.Button(bar, text="Şimdi oku", style="Accent.TButton", command=self.on_ev_read)
        self.ev_read_btn.pack(side="left")
        self.ev_watch_btn = ttk.Button(bar, text="İzlemeyi başlat", command=self.on_ev_toggle)
        self.ev_watch_btn.pack(side="left", padx=6)
        cards = ttk.Frame(f)
        cards.pack(fill="x", pady=12)
        self.ev_metrics = {}
        for key, title in [("soc", "ŞARJ SEVİYESİ / SOC"), ("charge_power", "ŞARJ GÜCÜ"),
                           ("temperature", "BATARYA SICAKLIĞI")]:
            tile = ttk.Frame(cards, style="Card.TFrame", padding=(14, 10))
            tile.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ttk.Label(tile, text=title, style="CardMuted.TLabel").pack(anchor="w")
            var = tk.StringVar(value="—")
            self.ev_metrics[key] = var
            ttk.Label(tile, textvariable=var, style="Metric.TLabel").pack(anchor="w", pady=(6, 0))
        self.ev_tree = self._tree(f, ("name", "value", "raw", "state"),
                                 ("Ölçüm", "Değer", "Ham veri", "Okuma durumu"), (220, 120, 120, 300), height=3)
        self.ev_updated = tk.StringVar(value="Henüz okuma yapılmadı. Eksik veri sıfır olarak gösterilmez.")
        ttk.Label(f, textvariable=self.ev_updated, style="Muted.TLabel").pack(anchor="w", pady=(8, 4))
        footer = ttk.Frame(f)
        footer.pack(fill="x")
        self.report_vin = tk.BooleanVar(value=False)
        ttk.Checkbutton(footer, text="Rapora VIN ekle", variable=self.report_vin).pack(side="left")
        ttk.Button(footer, text="Teşhis raporunu kaydet", command=self.on_export_report).pack(side="right")
        ttk.Button(footer, text="Ölçümleri CSV kaydet", command=self.on_export_ev_csv).pack(side="right", padx=6)
        ttk.Label(f, text="HV batarya, kontaktör veya şarj kumandası yoktur. SOH okuması servis batarya testi değildir.",
                  foreground="#EBC389", wraplength=820).pack(anchor="w", pady=(8, 0))

    def _stop_ev(self):
        self._ev_running = False
        self._ev_generation += 1
        if self._ev_timer is not None:
            self.after_cancel(self._ev_timer)
            self._ev_timer = None
        self.ev_watch_btn.configure(text="İzlemeyi başlat")

    def _reset_ev(self):
        self._stop_ev()
        self.ev_profile = None
        self.ev_results = []
        self.ev_read_at = None
        self.ev_tree.delete(*self.ev_tree.get_children())
        for var in self.ev_metrics.values():
            var.set("—")
        self.ev_profile_label.set("Profil yok. Gerçek iX40 ölçüm adresleri bu pakette bulunmaz.")
        self.ev_updated.set("Henüz okuma yapılmadı. Eksik veri sıfır olarak gösterilmez.")
        self.ev_history.clear()
        if hasattr(self, "trend_box"):
            self._refresh_trend_signals()

    def _set_ev_profile(self, path):
        profile = ev.load_profile(path)
        if profile.simulator_only and not self._connection_demo:
            raise ValueError("Demo profili yalnızca bağlı iX simülatöründe kullanılabilir.")
        self._reset_ev()
        self.ev_profile = profile
        prefix = "DEMO / SAHTE VERİ" if profile.simulator_only else "KULLANICI PROFİLİ / DOĞRULANMADI"
        self.ev_profile_label.set(f"{prefix} · {profile.name}")
        for signal in profile.signals:
            self.ev_tree.insert("", "end", iid=signal.key, values=(signal.name, "—", "—", "Okunmadı"))
        self._refresh_trend_signals()

    def on_ev_profile(self):
        if not self.require_connection():
            return
        path = filedialog.askopenfilename(title="Elektrikli araç ölçüm profili", filetypes=[("JSON", "*.json")])
        if path:
            try:
                self._set_ev_profile(path)
            except (OSError, ValueError, KeyError, TypeError) as error:
                messagebox.showerror("Profil yüklenemedi", str(error))

    def on_ev_demo(self):
        if not self._connection_demo or not self.is_ev:
            messagebox.showinfo("Yalnızca demo", "Bağlantı ekranından iX simülatörünü başlatın. Gerçek araca demo isteği gönderilmez.")
            return
        from .gui import app_dir
        self._set_ev_profile(os.path.join(app_dir(), "sim_ix_olcumler.json"))
        self.on_ev_read()

    def on_ev_toggle(self):
        if self._ev_running:
            self._stop_ev()
            return
        if not self.ev_profile or not self.require_connection():
            self.status.set("Önce bağlantı kurup bir elektrikli araç ölçüm profili yükleyin.")
            return
        self._ev_running = True
        self.ev_watch_btn.configure(text="İzlemeyi durdur")
        self.on_ev_read()

    def on_ev_read(self):
        if self._ev_timer is not None:
            self.after_cancel(self._ev_timer)
        self._ev_timer = None
        if self._ev_busy:
            return
        if self._active_jobs or self._live_running:
            self.status.set("EV ölçümü için diğer işlemin bitmesi / canlı verinin durdurulması bekleniyor.")
            if self._ev_running:
                self._ev_timer = self.after(1000, self.on_ev_read)
            return
        if not self.require_connection():
            return
        if self.ev_profile is None:
            self.status.set("Önce ölçüm profili yükleyin. Doğrulanmamış adresler otomatik denenmez.")
            return
        client, profile = self.uds, self.ev_profile
        generation = self._ev_generation
        is_demo, vin = self._connection_demo, self.vin
        self._ev_busy = True
        self.ev_read_btn.state(["disabled"])

        def work():
            try:
                return ev.read_profile(client, profile, is_simulator=is_demo, vin=vin), None
            except Exception as error:
                return None, str(error)

        def done(result):
            self._ev_busy = False
            self.ev_read_btn.state(["!disabled"])
            if generation != self._ev_generation:
                if self._ev_running:
                    self._ev_timer = self.after(1000, self.on_ev_read)
                return
            rows, error = result
            if error:
                self._stop_ev()
                self.status.set(f"Ölçüm başlatılamadı: {error}")
                return
            self.ev_results = rows
            self.ev_read_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self.ev_history.append(self.ev_read_at, rows, "simulator" if is_demo else "vehicle")
            self._refresh_trend_signals()
            for var in self.ev_metrics.values():
                var.set("—")
            for row in rows:
                value = "—" if row["value"] is None else f'{row["value"]:g} {row["unit"]}'
                self.ev_tree.item(row["key"], values=(row["name"], value, row["raw"] or "—",
                                                     row["error"] or "Okundu"))
                if row["key"] in self.ev_metrics:
                    self.ev_metrics[row["key"]].set(value)
            prefix = "DEMO" if profile.simulator_only else "Kullanıcı profili"
            self.ev_updated.set(f"{prefix} · Son okuma: {self.ev_read_at}")
            self.status.set(f"{sum(row['error'] is None for row in rows)}/{len(rows)} elektrikli araç ölçümü okundu")
            if self._ev_running:
                self._ev_timer = self.after(2000, self.on_ev_read)

        self.run_bg(work, done, "Elektrikli araç ölçümleri okunuyor...")

    def on_export_ev_csv(self):
        if not self.ev_results:
            self.status.set("CSV kaydetmeden önce ölçüm okuyun.")
            return
        path = filedialog.asksaveasfilename(title="Son EV ölçümlerini kaydet", defaultextension=".csv",
                                            initialfile="ev_olcumler.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["source", "read_at", "key", "name", "value", "unit", "raw", "error"])
                for row in self.ev_results:
                    cells = ["simulator" if self._connection_demo else "vehicle", self.ev_read_at,
                             row["key"], row["name"], row["value"], row["unit"], row["raw"], row["error"]]
                    # Untrusted profile labels must not become spreadsheet formulas.
                    writer.writerow(["'" + cell if isinstance(cell, str) and cell.lstrip().startswith(("=", "+", "-", "@"))
                                     else cell for cell in cells])
        except OSError as error:
            messagebox.showerror("CSV kaydedilemedi", str(error))
            return
        self.status.set("Son ölçümler CSV olarak kaydedildi. Ham verileri paylaşmadan önce inceleyin.")

    def on_export_report(self):
        if not self.require_connection():
            return
        path = filedialog.asksaveasfilename(title="Son okunan verileri kaydet", defaultextension=".json",
                                            initialfile="ix_teshis_raporu.json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        report = {
            "format": "bimmertool-diagnostic-report-v1",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source": "simulator" if self._connection_demo else "vehicle",
            "vehicle_selection": "BMW iX40 / EV" if self.is_ev else "F/G",
            "model_verified": False,
            "protocol": self.conn.protocol,
            "scanned_modules": self.found_ecus,
            "modules_read_at": self.modules_read_at,
            "dtcs_read_at": self.dtcs_read_at,
            "dtcs": self.last_dtcs,
            "dtc_clear_results": self.last_clear_results,
            "measurements_read_at": self.ev_read_at,
            "measurement_profile": self.ev_profile.name if self.ev_profile else None,
            "measurements": self.ev_results,
            "note": "Son okunan veriler; tam araç veya batarya sağlık testi değildir. Ham veriler kimlik bilgisi içerebilir.",
        }
        if self.report_vin.get():
            report["vin"] = self.vin
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(report, file, ensure_ascii=False, indent=2, allow_nan=False)
        except (OSError, ValueError) as error:
            messagebox.showerror("Rapor kaydedilemedi", str(error))
            return
        self.status.set("Son okunan veriler yerel rapora kaydedildi; eksik okumalar zaman bilgisi olmadan işaretlendi.")
