"""Session-only trend plotting and a bounded operation journal."""

import math
import os
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import theme


class MonitorWorkspace:
    def _build_monitor_tabs(self):
        page = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(page, text="Ölçüm geçmişi")
        ttk.Label(page, text="OTURUM TRENDİ  /  SON 300 OKUMA", foreground=theme.ACCENT).pack(anchor="w")
        ttk.Label(page, text="Profil veya bağlantı değiştiğinde geçmiş temizlenir. Hatalı okumalar çizgide boşluk bırakır.",
                  style="Muted.TLabel", wraplength=820).pack(anchor="w", pady=(6, 10))
        bar = ttk.Frame(page)
        bar.pack(fill="x")
        self.trend_signal = tk.StringVar()
        self.trend_box = ttk.Combobox(bar, textvariable=self.trend_signal, state="readonly", width=26)
        self.trend_box.pack(side="left")
        self.trend_box.bind("<<ComboboxSelected>>", self._draw_trend)
        ttk.Button(bar, text="Geçmişi CSV kaydet", command=self.on_export_history).pack(side="left", padx=8)
        ttk.Button(bar, text="Geçmişi temizle", command=self.on_clear_history).pack(side="right")
        self.trend_canvas = tk.Canvas(page, background=theme.PANEL, highlightthickness=0, height=180)
        self.trend_canvas.pack(fill="both", expand=True, pady=12)
        self.trend_canvas.bind("<Configure>", self._draw_trend)
        self.trend_summary = tk.StringVar(value="Önce iX / Elektrikli bölümünden ölçüm okuyun.")
        ttk.Label(page, textvariable=self.trend_summary, style="Muted.TLabel", wraplength=820).pack(anchor="w")

        log = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(log, text="İşlem günlüğü")
        bar = ttk.Frame(log)
        bar.pack(fill="x")
        ttk.Label(bar, text="BU OTURUMDAKİ İŞLEMLER", foreground=theme.ACCENT).pack(side="left")
        ttk.Button(bar, text="Kayıt klasörünü aç", command=self.on_open_data_dir).pack(side="right")
        ttk.Button(bar, text="Temizle", command=self.on_clear_journal).pack(side="right", padx=8)
        ttk.Button(bar, text="Raporları karşılaştır", command=self.on_compare_reports).pack(side="right", padx=6)
        self.journal_tree = self._tree(log, ("time", "message"), ("Saat", "İşlem / sonuç"), (90, 680), height=5)
        ttk.Label(log, text="Son 200 durum mesajı yalnızca bellekte tutulur; otomatik dosya kaydı veya veri gönderimi yoktur. "
                  "Mesajlar özel araç bilgisi içerebilir; ekran görüntüsünü paylaşmadan önce kontrol edin.",
                  style="Muted.TLabel", wraplength=820).pack(anchor="w", pady=(10, 0))
        self.status.trace_add("write", self._record_status)
        self._record_status()

    def on_compare_reports(self):
        from .report_compare import load_report, compare_reports
        first = filedialog.askopenfilename(title="Önceki BimmerTool teşhis raporu", filetypes=[("JSON", "*.json")])
        if not first:
            return
        second = filedialog.askopenfilename(title="Sonraki BimmerTool teşhis raporu", filetypes=[("JSON", "*.json")])
        if not second:
            return
        try:
            before, after = load_report(first), load_report(second)
            changes = compare_reports(before, after)
        except (OSError, ValueError, TypeError, KeyError) as error:
            messagebox.showerror("Raporlar karşılaştırılamadı", str(error))
            return
        window = tk.Toplevel(self)
        window.title("Teşhis raporu karşılaştırması · salt okunur")
        window.geometry("1000x540")
        window.configure(background=theme.BG)
        body = ttk.Frame(window, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Hata kaydı karşılaştırması", style="Section.TLabel").pack(anchor="w")
        identity = "VIN'ler eşleşiyor." if before.get("vin") and after.get("vin") else "VIN eksik: aynı araç olduğu doğrulanmadı."
        ttk.Label(body, text=f"Kaynak: {before['source']} · {identity}\n"
                  "Artık raporlanmıyor, onarıldı demek değildir. Okunamayan/eksik modüller karşılaştırılamaz. "
                  "Bu özellik BMW NCD karşılaştırması değildir.", wraplength=900,
                  style="Muted.TLabel").pack(anchor="w", pady=8)
        tree = self._tree(body, ("ecu", "code", "before", "after", "change"),
                          ("Modül", "Kod", "Önceki durum", "Sonraki durum", "Sonuç"),
                          (80, 90, 180, 180, 330), height=6)
        for row in changes:
            tree.insert("", "end", values=(f"0x{row['ecu']:04X}", row["code"],
                                           "—" if row["before"] is None else row["before"],
                                           "—" if row["after"] is None else row["after"], row["change"]))
        ttk.Label(body, text=f"{len(changes)} fark veya karşılaştırılamayan modül. Durum sayıları UDS bit maskeleridir.",
                  style="Muted.TLabel").pack(anchor="w", pady=8)
        ttk.Button(body, text="Kapat", command=window.destroy).pack(anchor="e")

    def _record_status(self, *_args):
        row = self.journal_tree.insert("", "end", values=(time.strftime("%H:%M:%S"), self.status.get()))
        children = self.journal_tree.get_children()
        if len(children) > 200:
            self.journal_tree.delete(*children[:-200])
        self.journal_tree.see(row)

    def on_clear_journal(self):
        self.journal_tree.delete(*self.journal_tree.get_children())

    def on_open_data_dir(self):
        from .storage import data_dir
        folder = data_dir()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            elif sys.platform == "win32":
                os.startfile(str(folder))
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError as error:
            messagebox.showerror("Klasör açılamadı", f"{folder}\n{error}")

    def _refresh_trend_signals(self):
        signals = self.ev_profile.signals if self.ev_profile else []
        keys = [signal.key for signal in signals]
        self.trend_box.configure(values=keys)
        if self.trend_signal.get() not in keys:
            self.trend_signal.set(keys[0] if keys else "")
        self._draw_trend()

    def _draw_trend(self, _event=None):
        if not hasattr(self, "trend_canvas"):
            return
        canvas = self.trend_canvas
        canvas.delete("all")
        key = self.trend_signal.get()
        series = self.ev_history.series(key)
        finite = [value for _stamp, value in series if value is not None]
        if not finite:
            canvas.create_text(30, 35, anchor="nw", fill=theme.MUTED,
                               text="Grafik için geçerli ölçüm bekleniyor.")
            self.trend_summary.set(f"{len(series)} okuma · geçerli değer yok")
            return
        width, height = max(canvas.winfo_width(), 220), max(canvas.winfo_height(), 140)
        low, high = min(finite), max(finite)
        unit = next((signal.unit for signal in self.ev_profile.signals if signal.key == key), "") if self.ev_profile else ""
        # Scale before subtracting so extreme but finite user values cannot overflow.
        scale = max(abs(low), abs(high), 1)
        lo, hi = low / scale, high / scale
        span = hi - lo
        points = []
        for index, (_stamp, value) in enumerate(series):
            if value is None:
                if len(points) >= 4:
                    canvas.create_line(*points, fill=theme.ACCENT, width=2)
                points = []
                continue
            x = 75 + index * (width - 100) / max(len(series) - 1, 1)
            y = height / 2 if not span else height - 36 - ((value / scale - lo) / span) * (height - 70)
            if not math.isfinite(y):
                continue
            points.extend((x, y))
            canvas.create_oval(x-2, y-2, x+2, y+2, fill=theme.ACCENT, outline="")
        if len(points) >= 4:
            canvas.create_line(*points, fill=theme.ACCENT, width=2)
        canvas.create_text(10, 20, anchor="nw", text=f"{high:g}", fill=theme.MUTED)
        canvas.create_text(10, height-40, anchor="nw", text=f"{low:g}", fill=theme.MUTED)
        canvas.create_text(75, height-14, anchor="w", text=series[0][0][11:19], fill=theme.MUTED)
        canvas.create_text(width-20, height-14, anchor="e", text=series[-1][0][11:19], fill=theme.MUTED)
        source = "DEMO" if self._connection_demo else "KULLANICI PROFİLİ / DOĞRULANMADI"
        self.trend_summary.set(f"{source} · {key} · {len(series)} okuma / {len(finite)} geçerli · "
                               f"Min {low:g} / Maks {high:g} {unit} · Noktalar okuma sırasına göre eşit aralıklıdır.")

    def on_clear_history(self):
        self.ev_history.clear()
        self._draw_trend()

    def on_export_history(self):
        if not self.ev_history.samples:
            self.status.set("Dışa aktarılacak ölçüm geçmişi yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="ev_olcum_gecmisi.csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            try:
                self.ev_history.export_csv(path)
                self.status.set("Oturum ölçüm geçmişi CSV olarak kaydedildi.")
            except OSError as error:
                messagebox.showerror("Geçmiş kaydedilemedi", str(error))
