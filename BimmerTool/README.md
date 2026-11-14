# BimmerTool

## 0.6.0 — Türkiye özellik uygunluğu

**Özellik uygunluğu**, ConnectedDrive, harita/traﬁk hizmetleri, Digital Key,
park halinde eğlence, RAM ses seçenekleri, farlar ve sürüş asistanları için
**manuel bir kontrol listesidir**. Araçtan özellik taraması, ülke kilidi tespiti
veya aktivasyon yapmaz. Her başlık donanım/abonelik/yazılım gereksinimini,
resmî kaynak adresini ve 14 Kasım 2026 inceleme tarihini gösterir. BMW'nin güncel
genel tanıtımlarının 2022 iX40'a uygulanabildiği varsayılmaz.

Kullanıcı menü gözlemini seçip JSON'a kaydedebilir. Dosyada VIN yoktur;
`vehicle_verified` ve `activation_performed` daima false olur. Gözlemler bu
oturumda tutulur; yeni bağlantıda sıfırlanır. Bir seçeneğin menüde olmaması
Türkiye'de yasak veya kapalı olduğunu kanıtlamaz. Ülke desteği ve hizmet
tekliflerini kendi aracınız için My BMW/ConnectedDrive veya BMW servisiyle
doğrulayın. Bu sürüm aktivasyon kodu, bölge sahteciliği, sürüşte video, far
güvenlik sınırı değişikliği veya HU_MGU4 FDL/NCD desteği içermez.

Kaynaklar: [BMW Türkiye ConnectedDrive](https://www.bmw.com.tr/tr/digital-services/bmw-connecteddrive.html),
[hizmet koşulları](https://www.bmw.com.tr/tr/digital-services/yasal-notlar/hukum-ve-kosullar.html),
[eğlence uygunluğu](https://www.bmw.com.tr/tr/digital-services/bmw-entertainment.html),
[BimmerCode iX seçenekleri](https://bimmercode.app/vehicles/i20/).

## 0.5.0 — üst seviye salt okunur sağlık kontrolü

Bağlantı ekranındaki **Üst seviye sağlık kontrolü** tek düğmeyle şunları yapar:
aday modüllerde tester-present taraması, VIN okuma/tutarlılık kontrolü, bulunan
modüllerde hata kodu özeti ve varsa seçili EV profiliyle ölçüm okuması. Sonuç tek
pencerede özetlenir ve teşhis raporuna eklenir; VIN raporda yine yalnızca açık
seçenekle yer alır.

Bu kontrol **yalnızca okur**. Onarma, yazma, silme, harita indirme, yazılım
güncelleme veya donanım programlama desteği eklemez ve bu istekleri göndermez.
Bunlar araç güvenliği ve garanti açısından risklidir; BMW yazılım/harita
güncellemeleri yalnızca resmî servis/OTA kanallarıyla yapılmalıdır. Sağlık
sonucu, tüm modüllerin, kablonun, yazılım sürümünün veya kodlama uygunluğunun
doğrulandığı anlamına gelmez.

## 0.4.0 — bağlantı doğrulama görünürlüğü

Bağlantı ekranında **Bağlantı testi**, seçili ve açık bağlantıya yalnızca VIN
okuma istekleri gönderir. Önce bulunan modülleri kullanır; tarama yoksa iX
modunda `0x10`, `0x40`, `0x07`, `0x63` adaylarını dener. Bunlar tüm araç modülleri
değildir. Test ilk 64 adayla sınırlıdır ve her istek için bir saniyelik yanıt
süresi kullanır. Taşıma hatasında devam etmez. EV düzenli izleme test başlarken
durdurulur; gerekirse panelden yeniden başlatın.

Her modül için VIN okuma, ret yanıtı, yanıt yok, geçersiz yanıt veya taşıma
hatası ayrı gösterilir. Süre ağ gecikmesiyle birlikte işlem süresidir; ret yanıtı
modülün cevap verdiğini gösterir, VIN okunabildiğini veya kodlamanın açık olduğunu
göstermez. VIN biçimi 17 karakter ve izinli karakterlerle kontrol edilir; bu bir
üretici doğrulaması veya model tespiti değildir. Birden fazla modülden okunan
VIN'ler farklıysa uyarılır; gerçek araç bağlantısında farklı VIN'ler varsa yazma
yapmayın. Sonuç, VIN ekleme tercihi korunarak teşhis raporuna dahil edilir.

İlk bağlantı artık geçersiz VIN'i kabul etmez. TCP/DoIP bağlantısı açık ama VIN
okunamamışsa üstte **TAŞIMA BAĞLI · VIN DOĞRULANMADI** gösterilir. Demo sonuçları
**SİMÜLATÖR** kaynağı olarak işaretlenir. Test, kabloyu fiziksel olarak incelemez,
uzaktaki araca erişim sağlamaz ve gerçek iX40 üstünde test edilmiş değildir.

Bu program tüm modülleri veya bütün verileri çözen bir araç değildir. BMW imza,
güvenlik erişimi ve yüksek voltaj korumaları kaldırılmaz. Yanlış araç yedeği,
geçersiz veri ve eşzamanlı işlem kontrolleri korunur. Desteklenmeyen alanlar
yerine sahte değer veya tahmini kodlama adresi üretilmez.

## 0.3.0 — oturum geçmişi ve işlem altyapısı

- **Ölçüm geçmişi:** EV profilindeki bir sinyali seçip bu oturumdaki son 300
  okumanın trendini görüntüleyin. Hatalı/eksik ölçümler çizgiyle birleştirilmez.
  Noktalar okuma sırasına göre eşit aralıklıdır; zaman ekseninde süreye orantılı
  çizim veya tıbbi/servis düzeyinde analiz değildir. Sabit değerler düz çizilir.
- **Geçmiş CSV:** Tek son okuma yerine son 300 okumanın tamamını zaman ve
  kaynak bilgisiyle dışa aktarın. Geçmiş bellektedir; profil/bağlantı değişince
  veya uygulama kapanınca silinir. Saklamak için önce CSV kaydedin.
- **İşlem günlüğü:** Son 200 durum mesajı bellekte görünür. Otomatik günlük
  dosyası veya sunucuya gönderim yoktur. Mesajlar özel veri içerebilir.
- Arka plan işlemi sürerken ikinci işlem başlatılmaz. Canlı veri izleme
  diğer işlemlerden önce durdurulmalıdır; EV izleme aradaki işlemi bekler.
  Sonucu gösterirken oluşan hata, sonraki sonuçların işlenmesini durdurmaz.
- Yeni yedekler indirilen uygulamadan ayrı kullanıcı veri klasörüne yazılır:
  macOS: `~/Library/Application Support/BimmerTool/yedekler`, Windows:
  `%LOCALAPPDATA%/BimmerTool/yedekler`, Linux: `$XDG_DATA_HOME/BimmerTool/yedekler`
  (tanımlı değilse `~/.local/share/BimmerTool/yedekler`). İşlem günlüğündeki
  **Kayıt klasörünü aç** düğmesi üst klasörü açar. Eski `yedekler` klasörleri
  taşınmaz veya silinmez; geri yükleme seçiminden elle bulunabilir. VIN eşleşmesi
  gereksinimi devam eder.

Ek bağımlılık gerekmez. Gerçek HU_MGU4 FDL/NCD kodlama ve doğrulanmış iX40
batarya/şarj adresleri bu sürümde de yoktur. Grafikler bir profilin gerçek araçta
doğru olduğunu veya bataryanın sağlıklı olduğunu kanıtlamaz.

## 0.2.0 — doğruluk ve kullanım güncellemesi

- Boş, kesilmiş veya yanlış servis/adres yanıtları başarı sayılmaz; protokol
  hatası olarak bildirilir. Eksik hata kodu kayıtları sessizce atılmaz.
- Hata kodu silme sonucu her modül için onay/ret olarak raporlanır. Kısmi
  başarısızlık artık “hepsi silindi” şeklinde gösterilmez. Sonrasında hata
  kodlarını yeniden okuyun; silme onayı arızanın giderildiğini göstermez.
- Yedekten dönüş, bağlı VIN ile yedekteki VIN eşleşmedikçe başlamaz. VIN'siz
  eski yedekler otomatik geri yüklenmez. VIN eşleşmesi tek başına yazılım
  uyumluluğunu garanti etmez.
- Genişletilmiş teşhis oturumu reddedilirse yazma denenmez. Koşul/yazma
  hataları artık imzalı kodlama gereksinimine ilişkin kanıt gibi sunulmaz.
- Son EV ölçümleri zaman, kaynak, birim, ham veri ve hata ile CSV'ye aktarılır.
  Dosya VIN alanı içermez; ham veriler yine özel bilgi içerebilir.
- Mac başlatıcısı Python sürümünü ve Tkinter varlığını açılıştan önce kontrol eder.

Bu sürümde de HU_MGU4 FDL/NCD yazma, gerçek iX40 ölçüm veritabanı veya otomatik
yazılım güncelleme yoktur. Paket sürümü, aracın yazılımının güncel olduğunu
göstermez. Eski BimmerCode PDF raporundaki I-Level canlı araç verisi olarak
uygulamaya gömülmez; rapor ve lisans bilgileri indirme paketinde bulunmaz.

BMW'lere ENET kablosuyla bağlanan Windows / Mac / Linux masaüstü programı. Şunları yapar:

Arayüz koyu tema, sol gezinme menüsü ve ayrı bağlantı kartları kullanır.
Bağlantı ekranında VIN, protokol ve son taramada bulunan modül sayısı gösterilir.
Üstteki **SİMÜLATÖR** etiketi demo bağlantısını gerçek araçtan ayırır.
Kodlama ve hata kodu silme gibi işlemlerin onayları korunmuştur.
Ek arayüz paketi gerekmez; Python'un Tkinter bileşeni kullanılır.

| Özellik | F/G serisi (≈2008–2021) | iX, i4 ve yeni nesil (2021+) |
|---|---|---|
| Aracı bulma, şasi numarası okuma | ✅ (HSFZ, port 6801) | ✅ (DoIP, port 13400) |
| Modül tarama | ✅ | ✅ |
| Hata kodu okuma / silme | ✅ | ✅ |
| Canlı veri | Motor devri, hız, sıcaklıklar, yük, voltaj | Profil tabanlı EV paneli; gerçek ölçüm tanımları ayrıca gerekir |
| Kodlama (yedekli, doğrulamalı) | ✅ Kodlama listesi dosyasıyla | ❌ Çoğu modül yalnızca BMW imzalı kodlamayı kabul eder (aşağıya bakın) |

## Gerekenler

- **ENET kablosu** (OBD2 → Ethernet RJ45). E serisi araçlar (K+DCAN kablosu) desteklenmez.
- Bilgisayarın Ethernet ayarı **otomatik (DHCP)** olmalı. Araç kendine `169.254.x.x` adresi verir.
- Kontak açık olmalı. Uzun işlemlerde akü şarj cihazı kullanın.
- Windows'ta güvenlik duvarı ilk açılışta izin isterse **izin verin**; yoksa "Aracı otomatik bul" çalışmaz. Bu durumda IP adresini elle de girebilirsiniz.

## Kurulum

**Kolay açılış (Python kuruluysa):** ZIP'i yeni bir klasöre tamamen çıkartın.
Mac'te `Mac-Baslat.command`, Windows'ta `Windows-Baslat.bat` dosyasına çift
tıklayın. Kod dosyasını düzenlemeniz gerekmez. Bunlar bağımsız EXE veya Mac
uygulaması değil, Python başlatıcılarıdır. Mac güvenlik uyarısı verirse korumayı
kapatmayın; uyarı metnini paylaşın.

**Hazır Windows programı:** GitHub'da *Actions → BimmerTool → son başarılı çalışma → Artifacts → BimmerTool-windows* dosyasını indirin, zipten çıkarın ve `BimmerTool.exe` dosyasını çalıştırın.

**Python ile (her işletim sistemi):** Python 3.10 veya daha yenisi gerekir, ek paket gerekmez.

```
python BimmerTool.py
```

## Kullanım

1. **Bağlantı:** Araç seçimini yapın → *Aracı otomatik bul* → *Bağlan*. iX40 seçiminde DoIP kullanılır; F/G seçiminde bulunan protokol denenir. Araç seçimi VIN'den model doğrulaması değildir.
2. **Modüller:** *Modülleri tara* bilinen modül adreslerini dener. *Tüm adresleri tara* daha yavaş ama hepsini bulur.
3. **Hata Kodları:** Bulunan modüllerin hata kodlarını okur ve isterseniz siler.
4. **Canlı Veri:** *Başlat* ile değerler saniyede yaklaşık iki kez güncellenir. Özel bir değer için modül adresini ve DID'i girip *Ekle*'ye basın; ham değer gösterilir.
5. **Kodlama:** Bir kodlama listesi (`.json`) yükleyin, *Mevcut değerleri oku*, bir ayar ve yeni değer seçip *Kodla*.
   - Her yazmadan önce eski değer `yedekler/` klasörüne kaydedilir. *Yedekten geri yükle* ile geri alabilirsiniz.
   - Yazdıktan sonra değer tekrar okunup doğrulanır.
   - Geçersiz adres/maske/seçenekler, boş veya farklı uzunlukta veri ve okuma
     sırasında değişen bloklar için yazma başlatılmaz. Yedek alınamazsa yazılmaz.
     Bu kontroller tanımın gerçek araç için doğru olduğunu kanıtlamaz.

Araç olmadan denemek için *Bağlantı* sekmesindeki **simülatör** düğmelerini kullanın: biri benzinli F/G serisi, biri elektrikli iX gibi davranır.

### iX40 / elektrikli araç çalışma alanı

Varsayılan seçim **BMW iX40 / elektrikli** modudur. Bu modda benzinli motor canlı
verileri gizlenir ve standart motor ölçüm istekleri gönderilmez. Varsayılan modül
taraması yanmalı motor, yakıt pompası ve klasik şanzıman adaylarını atlar.
**Tüm adresleri tara** seçeneği bu filtreyi kaldırır. Modül adları genel aday
etiketleridir; tüm iX ünitelerinin tam veya doğrulanmış listesi değildir.

**iX / Elektrikli** bölümünde şarj seviyesi (SOC), batarya gerilimi/akımı,
sıcaklık, şarj gücü ve SOH gibi ölçümler profil ile okunur. **Şimdi oku** tek
okuma yapar; **İzlemeyi başlat** her okuma bittikten yaklaşık iki saniye sonra
yeniler. Hatalı/desteklenmeyen ölçüm sıfır yerine boş değer ve hata mesajıyla
gösterilir. Her okumanın zamanı görünür. SOH gösterimi servis batarya sağlık
testi, hücre dengeleme veya kullanılabilir kapasite hesabı değildir.

**Demoyu denemek için:** Bağlantı → iX simülatörü → iX / Elektrikli → iX demo
profili. `sim_ix_olcumler.json` tamamen sentetik adres ve değerler kullanır.
Demo profili gerçek bağlantıda reddedilir. Yeniden bağlantıda profil, eski
ölçümler, özel ham okuma adresleri, hata kayıtları ve kodlama listesi temizlenir.

**Gerçek iX40 için:** Bu pakette doğrulanmış BMW batarya/şarj DID veritabanı
yoktur. Yalnızca sizin araç ve yazılımınız için doğrulanmış, kullanma hakkınız
olan ölçüm profillerini yükleyin. Etiketleri değiştirip demo adreslerini gerçek
araçta denemeyin. Profil yüklemek adresin veya ölçeklemenin doğruluğunu kanıtlamaz.

**Teşhis raporunu kaydet**, mevcut bağlantıda son okunan EV değerleri, tarama
adresleri ve hata kodlarını zamanlarıyla yerel JSON'a aktarır; yeni tarama yapmaz.
Okunamayan modüller raporda hata olarak, hiç yapılmamış okumalar zaman bilgisi
olmadan gösterilir. VIN varsayılan olarak eklenmez; **Rapora VIN ekle** ile
açılabilir. Ham ölçüm verileri de kimlik bilgisi içerebilir; raporu paylaşmadan
önce inceleyin. Tam servis teşhisi veya tüm modüllerin sağlıklı olduğuna dair
belge değildir.

#### Ölçüm profili biçimi (kodlama listesinden farklıdır)

Profil alanları: `version` (1), `name`, `simulator_only` (boolean), isteğe bağlı
`vin` ve boş olmayan `signals` listesi. Her sinyalde benzersiz `key`, `name`,
`unit`, sayısal `ecu` ve `did`, `offset`, `length`, `byteorder` (`big`/`little`),
`signed` (boolean), `scale` ve `add` zorunludur. Değer, seçilen baytların tamsayı
karşılığı × `scale` + `add` ile hesaplanır. Bu profiller yalnızca okuma yapar;
çalıştırılabilir kod içermez. VIN belirtilmişse eşleşmeyen veya VIN'i okunamayan
bağlantıda sorgu başlatılmaz. Kartlar için `soc`, `charge_power`, `temperature`
anahtarları kullanılır; diğer ölçümler tabloda görünür.

Yüksek voltaj kontaktörü kumandası, şarj başlatma/durdurma, batarya yazılımı
yazma, güç artırma veya imza/güvenlik korumasını aşma eklenmemiştir. Programın
gerçek iX40 ve macOS üzerindeki uçtan uca çalışması henüz doğrulanmamıştır.

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

### Bildirilen hedef: 2022 BMW iX40 / HU_MGU4

Bu model yılı ve ünite adı kullanıcı bildirimidir, bağlantıdan doğrulanmış kimlik
değildir. Kodlama ekranında bu hedef ve destek sınırı açıkça gösterilir.
Program şu anda **HU_MGU4 FDL/NCD çözümleme veya yazma desteği içermez**.
Mevcut yöntem, UDS ReadDataByIdentifier / WriteDataByIdentifier üzerinden genel
DID bloklarına bit değişikliği yapar; BMW FDL/NCD kodlamasının yerine geçmez.
Fotoğraflardaki `3000 HMI_SPEECH` ve `3013 AUGMENTED_REALITY` gibi FDL bölüm
başlıkları, doğrudan yazılacak DID adresleri olarak kullanılamaz.

Ünite adını seçmek veya menüye ayar adlarını eklemek gerçek kodlama desteği
sağlamaz. Uygun desteği değerlendirmek için ünitenin tam adı, CAFD kimliği ve
sürümü, araç yazılım seviyesi (I-Step) ve açılmak istenen belirli ayar gerekir.
Ürünün lisans anahtarını veya VIN'i paylaşmak gerekmez. Bu bilgiler elde edilse
bile gerçek araca uygun çözümleme, yazma yöntemi ve doğrulama ayrıca gereklidir.

Kaynaklar: [BimmerUtility FDL/NCD açıklaması](https://www.bimmerutility.com/fdl-editor),
[iX için sınırlı destek bildirimi](https://bimmercode.app/cars/bmw/ix/i20/).

### Genel DID listesi

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
- **Kodlama:** 2021 ortasından sonraki BMW'lerde (iX dahil) modüllerin çoğu yalnızca BMW'nin o şasi numarası için **imzaladığı** kodlamayı kabul eder (Secure Coding / NCD 2.0). Bu yüzden imzasız yazma reddedilir. Program ret yanıtını bildirir; bu yanıt tek başına aracın tüm durumunun değişmediğini kanıtlamaz. Sahiplerin bildirdiğine göre iX'te yerel olarak kodlanabilen modül çok azdır.
- **Güç / performans artışı:** Bu program elektrik motoru gücünü artırmaz. Motor gücü kodlama ile değil, BMW'nin imzaladığı sürüş ünitesi yazılımıyla belirlenir; BMW'nin sattığı resmi güç yükseltmeleri de ücretli lisansla açılır. Bu korumaları aşmak garanti, yüksek voltaj güvenliği ve yasal açıdan ciddi risk taşır.

## Geliştirici

```
python -m unittest        # simülatöre karşı uçtan uca testler
python -m bimmertool.simulator ix   # simülatörü ayrı çalıştır (f veya ix)
```
