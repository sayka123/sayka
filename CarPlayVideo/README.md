# CarPlay Video

CarPlay ekranında video listesi gösteren ve videoyu AirPlay üzerinden araç ekranına gönderen iOS uygulaması.

## Nasıl çalışır
- Araç ekranında **Videolar** listesi çıkar; birine dokununca oynatma başlar ve Now Playing ekranı açılır.
- Görüntü araç ekranına AirPlay ile gider (Apple'ın "video in the car" özelliği, iOS 26+). **Sadece araç parktayken** ve araç bu özelliği destekliyorsa görüntü gelir; aksi halde sistem yalnızca sesi oynatır.
- Telefonda Apple TV uygulamasına benzeyen koyu temalı bir ekran var: üstte büyük "öne çıkan" afiş, altında kategori başına yatay kaydırılan 16:9 kartlar. Sağ üstteki AirPlay düğmesiyle araç ekranını oradan da seçebilirsiniz.

Videoları ve kategorilerini (`category` alanı = raf başlığı) değiştirmek için `Sources/VideoCatalog.swift` dosyasını düzenleyin. Listedeki ilk video üstteki afişte gösterilir.

## Kurulum (Mac gerekir)
1. `brew install xcodegen`
2. `cd CarPlayVideo && xcodegen generate && open CarPlayVideo.xcodeproj`
3. Xcode'da Signing & Capabilities bölümünden kendi Team'inizi seçin ve bundle id'yi değiştirin.
4. Apple'dan **CarPlay Video App** (`com.apple.developer.carplay-video`) ve **CarPlay Audio App** yetkilerini isteyin: https://developer.apple.com/carplay/ — yetki gelmeden uygulama gerçek araçta CarPlay'de görünmez.
5. Test: Xcode Simulator > I/O > External Displays > CarPlay, ya da Mac için CarPlay Simulator (video için 1920×1080 ekran).
