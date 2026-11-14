"""Read a selected module's standard identification without changing sessions."""

from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import json

from . import identification, theme


class IdentificationWorkspace:
    def on_identify_module(self):
        if not self.require_connection():
            return
        selected = self.ecu_tree.selection()
        if len(selected) != 1:
            messagebox.showwarning('Modül seçin', 'Önce modülleri tarayın ve listeden tek bir adres seçin.')
            return
        ecu = int(self.ecu_tree.item(selected[0])['values'][0], 16)
        client, demo = self.uds, self._connection_demo
        self._stop_ev()
        self.run_bg(lambda: identification.read_identification(client, ecu, simulator=demo),
                    self._show_identification, f'0x{ecu:04X} modül kimliği okunuyor...')

    def _show_identification(self, report):
        self.last_identification = report
        window = tk.Toplevel(self)
        window.title('Modül kimliği · salt okunur')
        window.geometry('1060x560')
        window.minsize(860, 420)
        window.configure(background=theme.BG)
        body = ttk.Frame(window, padding=18)
        body.pack(fill='both', expand=True)
        source = 'DEMO / SENTETİK' if report['source'] == 'simulator' else 'ARAÇTAN YANIT'
        ttk.Label(body, text=f"{source} · 0x{report['ecu']:04X}", style='Section.TLabel').pack(anchor='w')
        ttk.Label(body, text=report['note'], wraplength=980, style='Muted.TLabel').pack(anchor='w', pady=8)
        tree = self._tree(body, ('did', 'name', 'text', 'raw', 'state'),
                          ('DID', 'Standart alan', 'ASCII görünümü', 'Ham yanıt', 'Durum'),
                          (80, 240, 200, 280, 230), height=6)
        labels = {'read': 'Okundu', 'refused': 'Reddedildi', 'no_response': 'Yanıt yok',
                  'invalid_response': 'Geçersiz yanıt', 'transport_error': 'Taşıma hatası'}
        for row in report['results']:
            tree.insert('', 'end', values=(f"0x{row['did']:04X}", row['name'], row['ascii'] or '—',
                                          row['raw'] or '—', row['error'] or labels[row['state']]))
        ttk.Label(body, text='Kimlik dosyaları özel araç bilgisi içerebilir. Paylaşmadan önce inceleyin. '
                  'Bu işlem üniteyi programlamaz ve kilit açmaz.', wraplength=980,
                  style='Muted.TLabel').pack(anchor='w', pady=8)

        def save():
            path = filedialog.asksaveasfilename(parent=window, defaultextension='.json',
                                                initialfile='modul_kimligi.json', filetypes=[('JSON', '*.json')])
            if not path:
                return
            try:
                with open(path, 'w', encoding='utf-8') as file:
                    json.dump(report, file, ensure_ascii=False, indent=2)
            except OSError as error:
                messagebox.showerror('Kimlik kaydedilemedi', str(error), parent=window)
        ttk.Button(body, text='Yerel JSON kaydet', command=save).pack(anchor='e')
        count = sum(row['state'] == 'read' for row in report['results'])
        self.status.set(f"0x{report['ecu']:04X}: {count}/{len(report['results'])} standart kimlik alanı okundu; ünite türü doğrulanmadı.")
