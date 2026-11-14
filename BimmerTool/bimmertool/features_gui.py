"""Manual regional eligibility checklist, not vehicle coding or entitlement detection."""

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import theme

REVIEWED = "2026-11-14"
CONNECTED = "https://www.bmw.com.tr/tr/digital-services/bmw-connecteddrive.html"
TERMS = "https://www.bmw.com.tr/tr/digital-services/yasal-notlar/hukum-ve-kosullar.html"
ENTERTAINMENT = "https://www.bmw.com.tr/tr/digital-services/bmw-entertainment.html"
CODING = "https://bimmercode.app/vehicles/i20/"

FEATURES = [
    ("connected", "ConnectedDrive / uzaktan hizmetler", "Hesap, aktivasyon, donanım ve abonelik",
     "My BMW'de aracınızı seçip size sunulan hizmetleri ve aktivasyon durumunu kontrol edin. "
     "Bu araç BMW hesabınıza erişmez. Hizmetin Türkiye'de tüm araçlarda kapalı olduğu varsayılmaz.", TERMS),
    ("maps", "BMW Maps / trafik ve harita hizmetleri", "Navigasyon sürümü, hizmet kapsamı ve abonelik",
     "Araçtaki navigasyon sürümünü ve My BMW/ConnectedDrive tekliflerini kontrol edin. "
     "Harita lisansı veya bölge kodunu değiştirmek için destek yoktur; resmî BMW kanalını kullanın.", CONNECTED),
    ("key", "Digital Key", "Uyumlu araç donanımı ve telefon",
     "My BMW'de Dijital Anahtar kurulumunun sunulup sunulmadığını ve telefon uyumluluğunu kontrol edin. "
     "Menü eklemek eksik donanımı sağlamaz. Anahtar veya erişim koruması değiştirilmez.", CONNECTED),
    ("entertainment", "Park halinde eğlence / uygulamalar", "Ülke, model ve işletim sistemi",
     "BMW Türkiye içeriklerin ülkeye göre değiştiğini belirtir. Güncel tanıtımların 2022 iX40 için "
     "geçerli olduğu varsayılmaz. Araçta sunulan uygulamaları kontrol edin; hareket halinde video kilidi açılmaz.", ENTERTAINMENT),
    ("sounds", "Ses tonu / hazır sürüş sesi seçenekleri", "RAM ve araç yazılımına bağlı kodlama",
     "BimmerCode iX listesinde RAM için ses seçenekleri bulunur. Bu liste sizin ünitenizin veya "
     "yazılımınızın uygunluğunu kanıtlamaz. BimmerTool bu seçenekleri kodlayamaz; HU_MGU4 ile karıştırmayın.", CODING),
    ("lights", "Far ve uzun far davranışları", "Donanım, tip onayı ve yazılım kontrolü gerekir",
     "Açılabilir olduğuna dair bu araç için doğrulanmış kodlama tanımı yok. Donanım, ülke gereklilikleri "
     "ve yazılım uyumluluğunu BMW servisiyle doğrulayın; güvenlik veya homologasyon ayarları değiştirilmez.", TERMS),
    ("speed", "Hız limiti bilgisi / sürüş asistanları", "Donanım, bölgesel hizmet ve yazılım",
     "Menünün görünmemesi tek başına ülke kilidi kanıtı değildir. Aracın donanım listesi, kullanım "
     "kılavuzu ve BMW teklifleriyle doğrulayın. Asistan güvenlik sınırları veya hız kısıtları kaldırılmaz.", TERMS),
]
OBSERVATIONS = ("Bilinmiyor", "Menüde var", "Menüde yok", "BMW doğrulaması bekleniyor")


class FeatureWorkspace:
    def _build_features_tab(self):
        page = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(page, text="Özellik uygunluğu")
        ttk.Label(page, text="TÜRKİYE / ÖZELLİK UYGUNLUĞU", foreground=theme.ACCENT).pack(anchor="w")
        ttk.Label(page, text="Manuel kontrol listesi; araçtan tarama veya aktivasyon değildir. "
                  "Ülke kilidi, donanım ve abonelik ayrı değerlendirilmelidir.",
                  style="Muted.TLabel", wraplength=820).pack(anchor="w", pady=(6, 8))
        self.feature_notes = {key: OBSERVATIONS[0] for key, *_ in FEATURES}
        self.features_tree = self._tree(page, ("name", "dependency", "observation"),
                                         ("Özellik", "Gereksinim / kontrol alanı", "Kullanıcı gözlemi"),
                                         (280, 340, 190), height=3)
        for key, name, dependency, _detail, _url in FEATURES:
            self.features_tree.insert("", "end", iid=key, values=(name, dependency, OBSERVATIONS[0]))
        self.features_tree.bind("<<TreeviewSelect>>", self._select_feature)
        bar = ttk.Frame(page)
        bar.pack(fill="x", pady=8)
        self.feature_observation = tk.StringVar(value=OBSERVATIONS[0])
        box = ttk.Combobox(bar, state="readonly", textvariable=self.feature_observation,
                           values=OBSERVATIONS, width=32)
        box.pack(side="left")
        box.bind("<<ComboboxSelected>>", self._save_feature_observation)
        ttk.Button(bar, text="Listeyi kaydet", command=self.on_export_features).pack(side="right")
        self.feature_detail = tk.StringVar(value="Bir özellik seçin. Hiçbir özellik etkinleştirilmez.")
        ttk.Label(page, textvariable=self.feature_detail, wraplength=820,
                  justify="left").pack(anchor="w", pady=(2, 8))
        self.feature_source = tk.StringVar(value=f"Kaynak inceleme tarihi: {REVIEWED}")
        ttk.Label(page, textvariable=self.feature_source, style="Muted.TLabel",
                  wraplength=820, justify="left").pack(anchor="w")

    def _select_feature(self, _event=None):
        selected = self.features_tree.selection()
        if not selected:
            return
        key = selected[0]
        feature = next(feature for feature in FEATURES if feature[0] == key)
        self.feature_observation.set(self.feature_notes[key])
        self.feature_detail.set(feature[3])
        self.feature_source.set(f"Kaynak ({REVIEWED}): {feature[4]}\n"
                                "Araç bazında doğrulanmadı. Bu liste Türkiye için kesin kullanılabilirlik kararı değildir.")

    def _reset_feature_observations(self):
        for key, name, dependency, _detail, _url in FEATURES:
            self.feature_notes[key] = OBSERVATIONS[0]
            self.features_tree.item(key, values=(name, dependency, OBSERVATIONS[0]))
        self._select_feature()

    def _save_feature_observation(self, _event=None):
        selected = self.features_tree.selection()
        if not selected:
            return
        key = selected[0]
        self.feature_notes[key] = self.feature_observation.get()
        values = list(self.features_tree.item(key)["values"])
        values[2] = self.feature_notes[key]
        self.features_tree.item(key, values=values)

    def on_export_features(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="ozellik_kontrol_listem.json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        report = {"format": "bimmertool-manual-feature-check-v1", "reviewed_at": REVIEWED,
                  "vehicle_verified": False, "activation_performed": False,
                  "items": [{"key": key, "name": name, "requirements": dependency,
                             "observation": self.feature_notes[key], "source": url}
                            for key, name, dependency, _detail, url in FEATURES]}
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(report, file, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror("Liste kaydedilemedi", str(error))
            return
        self.status.set("Manuel uygunluk listesi kaydedildi; araçta aktivasyon veya kodlama yapılmadı.")
