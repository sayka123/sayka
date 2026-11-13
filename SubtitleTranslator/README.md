# Altyazı Çevirmeni (Chrome / Edge uzantısı)

İnternette izlediğiniz videonun altyazısını, seçtiğiniz dile çevirip orijinal altyazının **altında** sarı renkte gösterir.

Çalıştığı yerler:

- YouTube, Netflix, Prime Video, Disney+
- Video.js ve JW Player kullanan siteler
- Altyazısı `<track>` ile verilen her normal HTML5 video

## Kurulum

1. Bu `SubtitleTranslator` klasörünü bilgisayarınıza indirin.
2. Chrome'da `chrome://extensions` adresini açın (Edge: `edge://extensions`).
3. Sağ üstten **Geliştirici modu**nu açın.
4. **Paketlenmemiş öğe yükle** düğmesine basıp `SubtitleTranslator` klasörünü seçin.

## Kullanım

1. Videoyu açın ve sitenin kendi altyazısını açın (örneğin YouTube'da **CC** düğmesi).
2. Araç çubuğundaki **Altyazı Çevirmeni** simgesine tıklayıp dili seçin.
3. Çeviri, orijinal altyazının altında görünür. Uzantıyı aynı menüden kapatabilirsiniz.

Altyazı zaten seçtiğiniz dildeyse ayrıca çeviri gösterilmez.

## Notlar

- Çeviri için Google Translate'in herkese açık uç noktası kullanılır; altyazı metni Google'a gönderilir. Bu uç nokta resmi bir API değildir ve ileride değişebilir.
- Videoda hiç altyazı yoksa çevrilecek bir metin de olmaz (ses tanıma yapılmaz).
- Siteler oynatıcılarını değiştirirse `content.js` içindeki `DOM_CAPTION_SELECTORS` listesinin güncellenmesi gerekebilir.
