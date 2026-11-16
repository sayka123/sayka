# Gary IPTV

Tarayıcıda çalışan IPTV programı: canlı TV, filmler ve diziler tek yerde.

- **Canlı TV:** Türkiye, Bulgaristan, dünya Türkçe yayınları ve dünya spor kanalları hazır gelir ([iptv-org](https://github.com/iptv-org/iptv) listelerinden, her açılışta güncellenir). Spor, Haber, Film, Çocuk… kategorileri; arama ve favoriler. Tekrarlanan kanallarda en yüksek kaliteli kopya gösterilir.
- **Sadece çalışan kanallar:** Açılışta tüm ücretsiz kanallar arka planda ~20 saniyede denenir; açılmayanlar gizlenir (🟢 çalışıyor). Aynı kanalın birden çok kalitesi varsa en yüksek olanı kalır; 4K / FHD / HD rozetleriyle gösterilir.
- **Filmler ve Diziler:** Kendi IPTV aboneliğinizi (Xtream Codes kullanıcı adı/parola ya da M3U linki) eklediğinizde tüm film ve diziler gelir. Birden çok hesap ekleyebilirsiniz; hepsi tek listede birleşir.
- **🔊 Türkçe Dublaj / 💬 Türkçe Altyazı** filtreleri: Sağlayıcının isim ve kategorilerdeki "DUBLAJ", "ALTYAZILI" vb. etiketlerine göre ayırır.
- **Oynatıcı:** Türkçe ses ve Türkçe altyazı varsa otomatik seçilir. Ses / altyazı / kalite (1080p, 720p, Otomatik) menüsü. Donmaya karşı geniş tampon ve bağlantı kopunca otomatik yeniden bağlanma.
- **Giriş ekranı:** kullanıcı adı `gary`, parola `lord`.

## Başlatma

1. [Node.js](https://nodejs.org) (LTS) kurulu olsun.
2. Windows: **`Baslat.bat`** dosyasına çift tıklayın. Mac/Linux: `baslat.command`.
3. Tarayıcıda `http://localhost:8080` açılır.

`index.html` dosyasını doğrudan da açabilirsiniz, ama Başlat dosyasıyla açınca çok daha fazla kanal çalışır: yerel sunucu, tarayıcının engellediği yayınları ve özel tarayıcı kimliği isteyen kanalları (ör. beIN Sports 1 Türk) aktarır.

Evdeki TV / telefondan izlemek için: `HOST=0.0.0.0 node server.js`, sonra cihazdan `http://BILGISAYAR-IP:8080`.

Klavye: ↑ / ↓ kanal değiştir, `F` tam ekran.

## Bilmeniz gerekenler

- **beIN Sports, S Sport, Exxen, Tivibu Spor, Max Sport, Planeta / Payner 4K, Diema Sport** gibi paralı kanallar ücretsiz listelerde ya hiç yok ya da sadece birkaçı var. Bunları izlemek için bu kanalları içeren bir aboneliği "+ Hesap ekle" ile ekleyin; program onları da aynı listede gösterir.
- Bazı ücretsiz yayınlar yalnızca kendi ülkesinden açılır ("bölge kısıtlı") veya zaman zaman kapanır; bu yayıncıdan kaynaklanır.
- Görüntü kalitesi ve donma büyük ölçüde sağlayıcının sunucusuna ve internet hızınıza bağlıdır.
- `.mkv` filmleri bazı tarayıcılar oynatamaz; Chrome veya Edge önerilir.
- Giriş ekranı, bilgisayarı kullanan başkalarının kolayca açmasını engeller; gerçek bir güvenlik kilidi değildir.

## Test

```
node --test tests/*.test.js
```
