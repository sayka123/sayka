"""Tkinter desktop interface."""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__, coding, livedata, transport
from .ecus import ECU_NAMES, ecu_name
from .uds import UdsClient, format_dtc


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_hex(text):
    return bytes.fromhex(text.replace("0x", "").replace(",", " "))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"BimmerTool {__version__}")
        self.geometry("900x600")
        self.minsize(760, 480)
        self.conn = None
        self.uds = None
        self.vin = None
        self.found_ecus = []
        self.definitions = []
        self.backup_dir = os.path.join(app_dir(), "yedekler")
        self.simulator = None
        self._results = queue.Queue()
        self._live_running = False

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=24)

        self.status = tk.StringVar(value="Bağlı değil")
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="Durum:").pack(side="left")
        ttk.Label(top, textvariable=self.status, font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=6)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._build_connection_tab()
        self._build_modules_tab()
        self._build_dtc_tab()
        self._build_live_tab()
        self._build_coding_tab()

        self.after(100, self._poll_results)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- background work -------------------------------------------------
    def run_bg(self, work, done=None, busy=None):
        """Run blocking car I/O off the UI thread; `done(result)` runs back on the UI thread."""
        if busy:
            self.status.set(busy)

        def target():
            try:
                self._results.put((done, work(), None))
            except Exception as e:
                self._results.put((done, None, e))

        threading.Thread(target=target, daemon=True).start()

    def _poll_results(self):
        try:
            while True:
                done, result, error = self._results.get_nowait()
                if error is not None:
                    self.status.set(f"Hata: {error}")
                    messagebox.showerror("Hata", str(error))
                elif done:
                    done(result)
        except queue.Empty:
            pass
        self.after(100, self._poll_results)

    def require_connection(self):
        if not self.uds:
            messagebox.showwarning("Bağlı değil", "Önce 'Bağlantı' sekmesinden araca bağlanın.")
            return False
        return True

    # ---- connection ----------------------------------------------------
    def _build_connection_tab(self):
        f = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(f, text="Bağlantı")
        ttk.Label(f, text=(
            "ENET kablosunu aracın OBD soketine, diğer ucunu bilgisayarın Ethernet girişine takın.\n"
            "Kontağı açın (motor çalışıyorsa daha iyi; uzun işlemlerde akü şarj cihazı kullanın)."),
            justify="left").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        ttk.Label(f, text="Araç IP adresi:").grid(row=1, column=0, sticky="w")
        self.ip_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.ip_var, width=22).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Button(f, text="Aracı otomatik bul", command=self.on_discover).grid(row=1, column=2, padx=4)
        ttk.Button(f, text="Bağlan", command=self.on_connect).grid(row=1, column=3, padx=4)

        self.vin_var = tk.StringVar(value="-")
        ttk.Label(f, text="Şasi numarası (VIN):").grid(row=2, column=0, sticky="w", pady=(14, 0))
        ttk.Label(f, textvariable=self.vin_var, font=("TkFixedFont", 11)).grid(
            row=2, column=1, columnspan=3, sticky="w", pady=(14, 0), padx=6)

        self.proto_var = tk.StringVar(value="-")
        ttk.Label(f, text="Protokol:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Label(f, textvariable=self.proto_var).grid(row=3, column=1, columnspan=3, sticky="w", pady=(6, 0), padx=6)

        sep = ttk.Separator(f)
        sep.grid(row=4, column=0, columnspan=4, sticky="ew", pady=18)
        ttk.Label(f, text="Araç yok mu? Programı sahte bir BMW ile deneyin:").grid(row=5, column=0, columnspan=4, sticky="w")
        sims = ttk.Frame(f)
        sims.grid(row=6, column=0, columnspan=4, sticky="w", pady=6)
        ttk.Button(sims, text="Benzinli F/G serisi simülatörü",
                   command=lambda: self.on_simulator("f")).pack(side="left")
        ttk.Button(sims, text="Elektrikli iX simülatörü",
                   command=lambda: self.on_simulator("ix")).pack(side="left", padx=8)
        self._discovered_protocol = None

    def on_discover(self):
        def done(cars):
            if not cars:
                self.status.set("Araç bulunamadı")
                messagebox.showinfo("Bulunamadı",
                                    "Araç bulunamadı. Kablo takılı ve kontak açık mı? "
                                    "Bilgisayarın Ethernet ayarı 'otomatik (DHCP)' olmalı.")
                return
            car = cars[0]
            self.ip_var.set(car["ip"])
            self.vin_var.set(car.get("vin") or "-")
            self._discovered_protocol = car.get("protocol")
            self.status.set(f"Araç bulundu: {car['ip']}")
        self.run_bg(lambda: transport.discover_all(timeout=3.0), done, "Araç aranıyor...")

    def on_connect(self, ports=None):
        host = self.ip_var.get().strip()
        if not host:
            messagebox.showwarning("IP yok", "IP adresi girin veya 'Aracı otomatik bul' düğmesine basın.")
            return
        if self.conn:
            self.conn.close()
        ports = ports or {}

        def work():
            conn = transport.open_connection(host, protocol=self._discovered_protocol, **ports)
            uds = UdsClient(conn)
            vin = None
            for ecu in (0x10, 0x40, 0x12):
                try:
                    vin = uds.read_did(ecu, 0xF190, timeout=1.5).decode("ascii", "replace").strip("\x00 ")
                    break
                except Exception:
                    continue
            return conn, uds, vin

        def done(result):
            self.conn, self.uds, self.vin = result
            self.vin_var.set(self.vin or "okunamadı")
            self.proto_var.set("DoIP (yeni nesil, örn. iX/i4)" if self.conn.protocol == "doip"
                               else "HSFZ (F/G serisi)")
            self.found_ecus = []
            self.status.set(f"Bağlı: {host}")

        self.run_bg(work, done, f"{host} adresine bağlanılıyor...")

    def on_simulator(self, model):
        from .simulator import Simulator
        if self.simulator and self.simulator.model != model:
            self.simulator.stop()
            self.simulator = None
        if not self.simulator:
            try:
                self.simulator = Simulator(port=0, discovery_port=0, model=model).start()
            except OSError as e:
                messagebox.showerror("Simülatör", f"Simülatör başlatılamadı: {e}")
                return
        self.ip_var.set("127.0.0.1")
        self._discovered_protocol = self.simulator.protocol
        self.on_connect({"hsfz_port": self.simulator.port, "doip_port": self.simulator.port})
        path = os.path.join(app_dir(), "sim_kodlama_ornek.json")
        if os.path.exists(path):
            self._load_definitions(path)

    # ---- modules -------------------------------------------------------
    def _build_modules_tab(self):
        f = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(f, text="Modüller")
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        ttk.Button(bar, text="Modülleri tara", command=self.on_scan).pack(side="left")
        self.full_scan = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Tüm adresleri tara (yavaş)", variable=self.full_scan).pack(side="left", padx=10)
        self.scan_progress = ttk.Progressbar(bar, length=220)
        self.scan_progress.pack(side="right")
        self.ecu_tree = self._tree(f, ("addr", "name"), ("Adres", "Modül"), (80, 500))

    def on_scan(self):
        if not self.require_connection():
            return
        addrs = list(range(0x00, 0x100)) if self.full_scan.get() else sorted(ECU_NAMES)
        self.ecu_tree.delete(*self.ecu_tree.get_children())
        self.scan_progress.configure(maximum=len(addrs), value=0)

        def work():
            found = []
            for i, a in enumerate(addrs):
                if a == self.conn.tester:
                    continue
                if self.uds.is_present(a, timeout=0.8):
                    found.append(a)
                    self._results.put((self._add_ecu_row, a, None))
                self._results.put((lambda v: self.scan_progress.configure(value=v), i + 1, None))
            return found

        def done(found):
            self.found_ecus = found
            self.status.set(f"{len(found)} modül bulundu")

        self.run_bg(work, done, "Modüller taranıyor...")

    def _add_ecu_row(self, addr):
        self.ecu_tree.insert("", "end", values=(f"0x{addr:02X}", ecu_name(addr)))

    # ---- fault codes ---------------------------------------------------
    def _build_dtc_tab(self):
        f = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(f, text="Hata Kodları")
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        ttk.Button(bar, text="Hata kodlarını oku", command=self.on_read_dtcs).pack(side="left")
        ttk.Button(bar, text="Tüm hata kodlarını sil", command=self.on_clear_dtcs).pack(side="left", padx=8)
        self.dtc_tree = self._tree(f, ("ecu", "code", "status"), ("Modül", "Kod", "Durum"), (330, 110, 200))

    def _modules_for_dtcs(self):
        return self.found_ecus or sorted(ECU_NAMES)

    def on_read_dtcs(self):
        if not self.require_connection():
            return
        self.dtc_tree.delete(*self.dtc_tree.get_children())
        modules = self._modules_for_dtcs()

        def work():
            total = 0
            for a in modules:
                try:
                    dtcs = self.uds.read_dtcs(a)
                except Exception:
                    continue
                for code, st in dtcs:
                    total += 1
                    state = "aktif" if st & 0x01 else ("kayıtlı" if st & 0x08 else "beklemede")
                    self._results.put((lambda row: self.dtc_tree.insert("", "end", values=row),
                                       (ecu_name(a), format_dtc(code), state), None))
            return total

        self.run_bg(work, lambda n: self.status.set(f"{n} hata kodu bulundu"), "Hata kodları okunuyor...")

    def on_clear_dtcs(self):
        if not self.require_connection():
            return
        if not messagebox.askyesno("Onay", "Tüm modüllerdeki hata kodları silinsin mi?"):
            return
        modules = self._modules_for_dtcs()

        def work():
            for a in modules:
                try:
                    self.uds.clear_dtcs(a)
                except Exception:
                    pass

        def done(_):
            self.status.set("Hata kodları silindi")
            self.on_read_dtcs()

        self.run_bg(work, done, "Hata kodları siliniyor...")

    # ---- live data -----------------------------------------------------
    def _build_live_tab(self):
        f = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(f, text="Canlı Veri")
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        self.live_btn = ttk.Button(bar, text="Başlat", command=self.on_live_toggle)
        self.live_btn.pack(side="left")
        ttk.Label(bar, text="Motor değerleri DME'den okunur; elektrikli araçlarda (iX) özel değer ekleyin.").pack(
            side="left", padx=10)

        add = ttk.Frame(f)
        add.pack(fill="x", pady=(8, 0))
        self.custom_ecu = tk.StringVar(value="0x07")
        self.custom_did = tk.StringVar(value="0x")
        ttk.Label(add, text="Özel değer:  Modül").pack(side="left")
        ttk.Entry(add, textvariable=self.custom_ecu, width=6).pack(side="left", padx=4)
        ttk.Label(add, text="DID").pack(side="left")
        ttk.Entry(add, textvariable=self.custom_did, width=8).pack(side="left", padx=4)
        ttk.Button(add, text="Ekle", command=self.on_add_custom).pack(side="left")

        self.live_tree = self._tree(f, ("name", "value", "unit"), ("Değer", "Okunan", "Birim"), (300, 260, 100))
        self._live_rows = {}
        self._custom = []  # [(row_id, ecu, did)]
        for name, unit, _did, _dec in livedata.LIVE_VALUES:
            self._live_rows[name] = self.live_tree.insert("", "end", values=(name, "-", unit))

    def on_add_custom(self):
        try:
            ecu, did = int(self.custom_ecu.get(), 0), int(self.custom_did.get(), 0)
        except ValueError:
            messagebox.showwarning("Geçersiz", "Modül ve DID değerlerini 0x12 / 0xF190 biçiminde girin.")
            return
        row = self.live_tree.insert("", "end", values=(f"{ecu_name(ecu)} / DID 0x{did:04X}", "-", "ham"))
        self._custom.append((row, ecu, did))

    def on_live_toggle(self):
        if self._live_running:
            self._live_running = False
            self.live_btn.configure(text="Başlat")
            return
        if not self.require_connection():
            return
        self._live_running = True
        self.live_btn.configure(text="Durdur")

        def loop():
            import time
            while self._live_running and self.uds:
                try:
                    values = livedata.read_all(self.uds)
                except Exception as e:
                    self._results.put((None, None, e))
                    break
                custom = []
                for row, ecu, did in list(self._custom):
                    try:
                        custom.append((row, livedata.read_custom(self.uds, ecu, did)))
                    except Exception as e:
                        custom.append((row, f"okunamadı: {e}"))
                self._results.put((self._show_live, (values, custom), None))
                time.sleep(0.5)

        threading.Thread(target=loop, daemon=True).start()

    def _show_live(self, result):
        values, custom = result
        for name, value, unit, _err in values:
            shown = "desteklenmiyor" if value is None else value
            self.live_tree.item(self._live_rows[name], values=(name, shown, unit))
        for row, text in custom:
            name, _old, unit = self.live_tree.item(row)["values"]
            self.live_tree.item(row, values=(name, text, unit))

    # ---- coding --------------------------------------------------------
    def _build_coding_tab(self):
        f = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(f, text="Kodlama")
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        ttk.Button(bar, text="Kodlama listesi yükle...", command=self.on_load_definitions).pack(side="left")
        ttk.Button(bar, text="Mevcut değerleri oku", command=self.on_read_coding).pack(side="left", padx=6)
        ttk.Button(bar, text="Yedekten geri yükle...", command=self.on_restore).pack(side="right")

        self.coding_tree = self._tree(f, ("name", "ecu", "current"), ("Ayar", "Modül", "Mevcut"),
                                      (380, 220, 140), height=8)
        self.coding_tree.bind("<<TreeviewSelect>>", self._on_coding_select)

        apply_bar = ttk.Frame(f)
        apply_bar.pack(fill="x", pady=6)
        ttk.Label(apply_bar, text="Yeni değer:").pack(side="left")
        self.option_var = tk.StringVar()
        self.option_box = ttk.Combobox(apply_bar, textvariable=self.option_var, state="readonly", width=20)
        self.option_box.pack(side="left", padx=6)
        ttk.Button(apply_bar, text="Kodla", command=self.on_apply_coding).pack(side="left")
        self.note_var = tk.StringVar()
        ttk.Label(apply_bar, textvariable=self.note_var, foreground="#555").pack(side="left", padx=10)

        raw = ttk.LabelFrame(f, text="Uzman: ham veri (DID) okuma / yazma", padding=8)
        raw.pack(fill="x", pady=(8, 0))
        self.raw_ecu = tk.StringVar(value="0x12")
        self.raw_did = tk.StringVar(value="0xF190")
        self.raw_data = tk.StringVar()
        for col, (label, var, w) in enumerate((("Modül", self.raw_ecu, 6), ("DID", self.raw_did, 8),
                                               ("Veri (hex)", self.raw_data, 40))):
            ttk.Label(raw, text=label).grid(row=0, column=col * 2, padx=(0, 4))
            ttk.Entry(raw, textvariable=var, width=w).grid(row=0, column=col * 2 + 1, padx=(0, 10))
        ttk.Button(raw, text="Oku", command=self.on_raw_read).grid(row=0, column=6)
        ttk.Button(raw, text="Yaz", command=self.on_raw_write).grid(row=0, column=7, padx=4)

    def on_load_definitions(self):
        path = filedialog.askopenfilename(initialdir=app_dir(), filetypes=[("JSON", "*.json")])
        if path:
            self._load_definitions(path)

    def _load_definitions(self, path):
        try:
            self.definitions = coding.load_definitions(path)
        except Exception as e:
            messagebox.showerror("Liste okunamadı", str(e))
            return
        self.coding_tree.delete(*self.coding_tree.get_children())
        for i, d in enumerate(self.definitions):
            self.coding_tree.insert("", "end", iid=str(i), values=(d.name, ecu_name(d.ecu), "-"))

    def _selected_definition(self):
        sel = self.coding_tree.selection()
        return (int(sel[0]), self.definitions[int(sel[0])]) if sel else (None, None)

    def _on_coding_select(self, _event=None):
        _i, d = self._selected_definition()
        if d:
            self.option_box.configure(values=list(d.options))
            self.option_var.set("")
            self.note_var.set(d.note)

    def on_read_coding(self):
        if not self.require_connection():
            return

        def work():
            out = []
            for d in self.definitions:
                try:
                    out.append(coding.read_current(self.uds, d))
                except Exception as e:
                    out.append(f"okunamadı: {e}")
            return out

        def done(labels):
            for i, label in enumerate(labels):
                d = self.definitions[i]
                self.coding_tree.item(str(i), values=(d.name, ecu_name(d.ecu), label))
            self.status.set("Kodlama değerleri okundu")

        self.run_bg(work, done, "Kodlama değerleri okunuyor...")

    def on_apply_coding(self):
        i, d = self._selected_definition()
        if d is None or not self.option_var.get():
            messagebox.showwarning("Seçim yok", "Listeden bir ayar ve yeni değer seçin.")
            return
        if not self.require_connection():
            return
        label = self.option_var.get()
        if not messagebox.askyesno("Kodlama onayı", (
                f"'{d.name}' -> '{label}' olarak yazılacak.\n\n"
                "Önce mevcut değer yedeklenir. Kontak açık olmalı ve işlem sırasında kabloyu çıkarmayın.\n"
                "Devam edilsin mi?"), icon="warning"):
            return

        def work():
            backup = coding.apply(self.uds, d, label, self.backup_dir, self.vin)
            return backup, coding.read_current(self.uds, d)

        def done(result):
            backup, current = result
            self.coding_tree.item(str(i), values=(d.name, ecu_name(d.ecu), current))
            self.status.set("Kodlama tamamlandı")
            messagebox.showinfo("Tamam", f"Kodlandı ve doğrulandı.\nYedek: {backup}\n\n"
                                         "Etkili olması için kontağı kapatıp açmanız gerekebilir.")

        self.run_bg(work, done, "Kodlanıyor...")

    def on_restore(self):
        if not self.require_connection():
            return
        path = filedialog.askopenfilename(initialdir=self.backup_dir, filetypes=[("Yedek", "*.json")])
        if not path or not messagebox.askyesno("Onay", "Bu yedek araca geri yazılsın mı?", icon="warning"):
            return
        self.run_bg(lambda: coding.restore(self.uds, path, self.backup_dir),
                    lambda _b: (self.status.set("Yedek geri yüklendi"), self.on_read_coding()),
                    "Yedek geri yükleniyor...")

    def _raw_target(self):
        return int(self.raw_ecu.get(), 0), int(self.raw_did.get(), 0)

    def on_raw_read(self):
        if not self.require_connection():
            return
        ecu, did = self._raw_target()
        self.run_bg(lambda: self.uds.read_did(ecu, did),
                    lambda data: (self.raw_data.set(data.hex(" ").upper()),
                                  self.status.set(f"Okundu: {len(data)} bayt")),
                    "Okunuyor...")

    def on_raw_write(self):
        if not self.require_connection():
            return
        ecu, did = self._raw_target()
        data = parse_hex(self.raw_data.get())
        if not messagebox.askyesno("Dikkat", (
                f"Modül 0x{ecu:02X}, DID 0x{did:04X} adresine {len(data)} bayt yazılacak.\n"
                "Yanlış veri modülün çalışmasını bozabilir. Önce mevcut değer yedeklenir.\n\nDevam?"),
                icon="warning"):
            return
        self.run_bg(lambda: coding.write_block(self.uds, ecu, did, data, self.backup_dir, self.vin),
                    lambda b: self.status.set(f"Yazıldı ve doğrulandı (yedek: {os.path.basename(b)})"),
                    "Yazılıyor...")

    # ---- helpers -------------------------------------------------------
    def _tree(self, parent, cols, headings, widths, height=None):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(8, 0))
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=height or 10)
        for c, h, w in zip(cols, headings, widths):
            tree.heading(c, text=h, anchor="w")
            tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def _on_close(self):
        self._live_running = False
        if self.conn:
            self.conn.close()
        if self.simulator:
            self.simulator.stop()
        self.destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
