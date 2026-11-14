# BimmerUtility ile karşılaştırma — 14 Kasım 2026

Bu karşılaştırma BimmerUtility'nin üretici belgeleri ile BimmerTool 0.7.0
kaynak koduna dayanır. Ürünler gerçek bir araç üzerinde yan yana test edilmedi.
BimmerUtility, BMW'nin resmî servis yazılımı değildir.

| Alan | BimmerUtility'nin belgelediği | BimmerTool 0.7.0 |
|---|---|---|
| BMW kodlama verileri | FDL/FA düzenleme, eşlenmiş kodlama verileri | Yok; genel DID bit yazma yöntemi bunun yerine geçmez |
| Dosya karşılaştırması | Fonksiyon bazında NCD Compare | NCD yok; yerel DID kayıtları ve teşhis raporları karşılaştırılır |
| Yedekleme | Otomatik kodlama yedekleri, yedek düzenleyici | DID yazmadan önce ham blok yedeği; VIN eşleşmeli geri yükleme |
| Hata kodları | Bayi açıklamalı DTC | Sayısal UDS kod/durum; BMW'ye ait açıklama ve onarım planı yok |
| Yazma önizlemesi | FDL düzenleme iş akışı | Yeni: mevcut DID verisinde bayt/bit farkı; bağımsız salt okunur önizleme |
| Güncel araç veritabanı | Üretici düzenli eşleme güncellemesi bildirir | Doğrulanmış iX40 batarya/şarj veya HU_MGU4 veritabanı yok |
| Secure Coding 2.0 | Üretici destek dışı bildirir | Koruma aşma yok |
| Platform kanıtı | Üreticinin kendi platform desteği | Python/Tkinter; Linux sanal ekranda test, Mac/gerçek araç doğrulaması yok |
| FSC/lisans, bulut, uzaktan kodlama | Belgelenmiş ticari özellikler | Yok; otomatik BMW hesabı erişimi/veri gönderimi yok |

## Bu sürümde tamamlanan eksikler

1. **Önizle:** sadece mevcut DID bloğunu okur. Modül/DID, uzunluk ve değişen
   baytları (en fazla ilk 16 satır) gösterir; oturum değiştirme/yazma yapmaz.
   **Kodla** da önce bu önizlemeyi gösterip açık onay ister. Yazma anında blok
   tekrar okunur; değişmişse eski önizlemeyle yazılmaz. Tanımın araç için doğru
   olduğunu veya FDL desteğini kanıtlamaz. Ham uzman yazması ayrı akıştır.
2. **Raporları karşılaştır:** İşlem günlüğündeki düğmeden iki BimmerTool teşhis
   JSON'u seçilir. Yeni kayıt, artık raporlanmayan kayıt, durum değişimi ve
   karşılaştırılamayan modüller ayrılır. Kaynak (demo/araç) veya bilinen VIN'ler
   farklıysa reddedilir. VIN eksikse kimlik doğrulanmadığı belirtilir. NCD/CAFD
   dosyaları desteklenmez; silinmiş kayıt onarılmış arıza anlamına gelmez.

## Açık kalan gerçek engeller

HU_MGU4 için uygun NCD çözümleme/yazma uygulaması, sürüme uygun ve kullanım
hakkı olan BMW kodlama tanımları, gerçek araç üzerinde hata ve kurtarma testleri
gerekir. Ünite veya ayar adlarını menüye eklemek bunları tamamlamaz. Şu anki
uygulama BimmerUtility veya ISTA'nın tam karşılığı değildir.

Kaynaklar:
- https://www.bimmerutility.com/product-page/license
- https://www.bimmerutility.com/ncd-compare
- https://www.bimmerutility.com/fdl-editor
- https://www.bimmerutility.com/support
