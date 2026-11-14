"""Local FA inspection and raw NCD file comparison, independent of vehicle I/O."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import offline_files, theme


class OfflineWorkspace:
    def _build_offline_menu(self):
        bar = tk.Menu(self)
        files = tk.Menu(bar, tearoff=False)
        files.add_command(label='FA XML incele (salt okunur)…', command=self.on_inspect_fa)
        files.add_command(label='NCD / ikili dosya ham farkları…', command=self.on_compare_binary)
        bar.add_cascade(label='Dosya araçları', menu=files)
        self.configure(menu=bar)

    def _offline_window(self, title, note):
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry('1050x620')
        window.minsize(850, 440)
        window.configure(background=theme.BG)
        body = ttk.Frame(window, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=title, style='Section.TLabel').pack(anchor='w')
        ttk.Label(body, text=note, style='Muted.TLabel', wraplength=970,
                  justify='left').pack(anchor='w', pady=(8, 4))
        return body

    def on_inspect_fa(self):
        path = filedialog.askopenfilename(title='Dışa aktarılmış FA XML dosyası', filetypes=[('XML', '*.xml')])
        if not path:
            return
        try:
            result = offline_files.load_fa(path)
        except (OSError, ValueError) as error:
            messagebox.showerror('FA okunamadı', str(error))
            return
        body = self._offline_window('FA XML · Yerel dosya inceleme',
            'Araçtan okuma, FA değiştirme, VO kodlama veya donanım doğrulaması yapılmaz. '
            'Seçenek kodları ham listelenir; BMW açıklama veritabanı yoktur. '
            'VIN içeriği gösterilmez; dosya özel bilgiler içerebilir.')
        ttk.Label(body, text=f"SHA-256: {result['sha256']}", style='Muted.TLabel').pack(anchor='w', pady=6)
        tree = self._tree(body, ('name', 'value'), ('Dosya alanı', 'Kaydedilmiş değer'), (250, 620), height=7)
        for name, value in result['metadata'].items():
            tree.insert('', 'end', values=(name, value or 'Dosyada yok'))
        tree.insert('', 'end', values=('saCodes', ', '.join(result['sa_codes']) or 'Kod bulunamadı'))
        tree.insert('', 'end', values=('VIN alanı', 'Var (gizli)' if result['vin_present'] else 'Yok'))
        ttk.Label(body, text=f"{len(result['sa_codes'])} benzersiz seçenek kodu · Araçla eşleştirilmedi.",
                  style='Muted.TLabel').pack(anchor='w', pady=8)
        # Individual rows remain readable even for long option lists.
        options = ttk.Combobox(body, state='readonly', values=result['sa_codes'], width=18)
        options.pack(anchor='w')
        if result['sa_codes']:
            options.current(0)
        self.status.set('Yerel FA XML incelendi; araçla iletişim kurulmadı.')

    def on_compare_binary(self):
        first = filedialog.askopenfilename(title='Önceki NCD / ikili dosya', filetypes=[('Tüm dosyalar', '*')])
        if not first:
            return
        second = filedialog.askopenfilename(title='Sonraki NCD / ikili dosya', filetypes=[('Tüm dosyalar', '*')])
        if not second:
            return
        try:
            result = offline_files.compare_binary(first, second)
        except (OSError, ValueError) as error:
            messagebox.showerror('Dosyalar karşılaştırılamadı', str(error))
            return
        body = self._offline_window('NCD / ikili dosya · HAM BAYT FARKI',
            'FDL/NCD çözümleme DEĞİLDİR. Dosyaların NCD, aynı araç veya aynı CAFD sürümü olduğu '
            'doğrulanmaz. Ofsetler DID veya kodlama adresi değildir. '
            'Bu pencereden düzenleme veya araca yazma yapılamaz.')
        ttk.Label(body, text=(f"Boyut: {result['before_size']} → {result['after_size']} bayt · "
                             f"Değişen/eklenen/çıkarılan: {result['changed_bytes']} bayt\n"
                             f"Önce SHA-256: {result['before_sha256']}\nSonra SHA-256: {result['after_sha256']}"),
                  style='Muted.TLabel', wraplength=970).pack(anchor='w', pady=8)
        tree = self._tree(body, ('offset', 'before', 'after'), ('Dosya ofseti (hex)', 'Önceki baytlar', 'Sonraki baytlar'),
                          (150, 440, 440), height=7)
        for row in result['rows']:
            tree.insert('', 'end', values=(f"0x{row['offset']:08X}", row['before'] or '—', row['after'] or '—'))
        ttk.Label(body, text='Görünüm ilk 2000 farklı blokla sınırlı; toplam değişim sayısı tamdır.'
                  if result['display_truncated'] else 'Tüm farklı bloklar gösterildi.',
                  style='Muted.TLabel').pack(anchor='w', pady=8)
        self.status.set('Yerel ham dosya karşılaştırması tamamlandı; araçla iletişim kurulmadı.')
