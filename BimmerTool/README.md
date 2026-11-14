# BimmerTool

BMW'lere ENET kablosuyla bağlanan Windows / Mac / Linux masaüstü programı. Şunları yapar:

| Özellik | F/G serisi (≈2008–2021) | iX, i4 ve yeni nesil (2021+) |
|---|---|---|
| Aracı bulma, şasi numarası okuma | ✅ (HSFZ, port 6801) | ✅ (DoIP, port 13400) |
| Modül tarama | ✅ | ✅ |
| Hata kodu okuma / silme | ✅ | ✅ |
| Canlı veri | ✅ Motor devri, hız, sıcaklıklar, yük, voltaj | ⚠️ Motor modülü yok; batarya/motor değerleri için modül + DID'i kendiniz eklersiniz |
| Kodlama (yedekli, doğrulamalı) | ✅ Kodlama listesi dosyasıyla | ❌ Çoğu modül yalnızca BMW imzalı kodlamayı kabul eder (aşağıya bakın) |

## Gerekenler

- **ENET kablosu** (OBD2 → Ethernet RJ45). E serisi araçlar (K+DCAN kablosu) desteklenmez.
- Bilgisayarın Ethernet ayarı **otomatik (DHCP)** olmalı. Araç kendine `169.254.x.x` adresi verir.
- Kontak açık olmalı. Uzun işlemlerde akü şarj cihazı kullanın.
- Windows'ta güvenlik duvarı ilk açılışta izin isterse **izin verin**; yoksa "Aracı otomatik bul" çalışmaz. Bu durumda IP adresini elle de girebilirsiniz.

## Kurulum

**Hazır Windows programı:** GitHub'da *Actions → BimmerTool → son başarılı çalışma → Artifacts → BimmerTool-windows* dosyasını indirin, zipten çıkarın ve `BimmerTool.exe` dosyasını çalıştırın.

**Python ile (her işletim sistemi):** Python 3.10 veya daha yenisi gerekir, ek paket gerekmez.

```
python BimmerTool.py
```

## Kullanım

1. **Bağlantı:** *Aracı otomatik bul* → *Bağlan*. Program aracın HSFZ mi DoIP mi kullandığını kendisi seçer.
2. **Modüller:** *Modülleri tara* bilinen modül adreslerini dener. *Tüm adresleri tara* daha yavaş ama hepsini bulur.
3. **Hata Kodları:** Bulunan modüllerin hata kodlarını okur ve isterseniz siler.
4. **Canlı Veri:** *Başlat* ile değerler saniyede yaklaşık iki kez güncellenir. Özel bir değer için modül adresini ve DID'i girip *Ekle*'ye basın; ham değer gösterilir.
5. **Kodlama:** Bir kodlama listesi (`.json`) yükleyin, *Mevcut değerleri oku*, bir ayar ve yeni değer seçip *Kodla*.
   - Her yazmadan önce eski değer `yedekler/` klasörüne kaydedilir. *Yedekten geri yükle* ile geri alabilirsiniz.
   - Yazdıktan sonra değer tekrar okunup doğrulanır.

Araç olmadan denemek için *Bağlantı* sekmesindeki **simülatör** düğmelerini kullanın: biri benzinli F/G serisi, biri elektrikli iX gibi davranır.

### Keşif: salt okunur kayıt ve karşılaştırma

**Keşif** sekmesinde modül adreslerini (örneğin `0x10, 0x40`) ve bilinen DID
aralığını girerek **Kayıt al** düğmesiyle JSON kaydedebilirsiniz. Modül alanı boşsa
Modüller sekmesinde bulunan adresler kullanılır. Varsayılan DID `0xF190` şasi
numarası okumasıdır; gizli özellik veya kodlama adresi değildir.

**İki kaydı karşılaştır** ortak veri bloklarındaki bayt farklarını gösterir.
Yalnızca bir kayıtta bulunan bloklar bu karşılaştırmaya dahil değildir. Farklı
şasi numaraları için uyarı gösterilir. Kaydedilen dosyalar VIN ve ham araç
verilerini içerir; paylaşmadan önce kişisel bilgileri temizleyin.

Bu sekme yalnızca okuma isteği gönderir. Bir baytın değişmesi, belirli bir ayarı
kontrol ettiğini veya o adrese yazmanın güvenli olduğunu **kanıtlamaz**. Bu nedenle
farklardan otomatik kodlama listesi üretilmez. Güvenlik erişimini veya imza
kontrolünü zorlama yoktur. Gerçek iX40 uyumluluğu doğrulanmamıştır; testler
HSFZ ve iX benzeri DoIP simülatöründe yapılır.

## Kodlama listesi formatı

```json
[
  {
    "name": "Ayarın adı",
    "ecu": "0x72",
    "did": "0x3000",
    "byte": 2,
    "mask": "0x01",
    "options": {"Açık": "0x01", "Kapalı": "0x00"},
    "note": "Kısa açıklama"
  }
]
```

Program yalnızca `mask` içindeki bitleri değiştirir, aynı bayttaki diğer bitlere dokunmaz.

`sim_kodlama_ornek.json` **yalnızca simülatör içindir**. Gerçek araçların kodlama adresleri modele ve yazılım sürümüne göre değişir. BMW bunları ücretli ve lisanslı PSdZData paketinde dağıtır, bu yüzden programa eklenmedi. Yanlış adrese yazmak modülü bozabilir. Yalnızca kendi aracınızda doğrulanmış tanımları kullanın.

## BMW iX hakkında önemli notlar

- **Bağlantı, tarama, hata kodları:** Çalışması beklenir; iX, DoIP protokolüyle konuşur.
- **Kodlama:** 2021 ortasından sonraki BMW'lerde (iX dahil) modüllerin çoğu yalnızca BMW'nin o şasi numarası için **imzaladığı** kodlamayı kabul eder (Secure Coding / NCD 2.0). Bu yüzden imzasız yazma reddedilir. Program bu durumda araçta hiçbir şeyi değiştirmeden açık bir hata mesajı gösterir. Sahiplerin bildirdiğine göre iX'te yerel olarak kodlanabilen modül çok azdır.
- **Güç / performans artışı:** Bu program elektrik motoru gücünü artırmaz. Motor gücü kodlama ile değil, BMW'nin imzaladığı sürüş ünitesi yazılımıyla belirlenir; BMW'nin sattığı resmi güç yükseltmeleri de ücretli lisansla açılır. Bu korumaları aşmak garanti, yüksek voltaj güvenliği ve yasal açıdan ciddi risk taşır.

## Geliştirici

```
python -m unittest        # simülatöre karşı uçtan uca testler
python -m bimmertool.simulator ix   # simülatörü ayrı çalıştır (f veya ix)
```
