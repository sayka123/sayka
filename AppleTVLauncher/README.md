# Apple TV Görünümü (Android TV)

Android TV / Google TV için Apple TV ana ekranına benzeyen bir ana ekran (launcher) uygulaması.

- Üstte **Top Shelf** alanı: seçili uygulamanın görseli bulanık arka plan olarak, adı büyük yazıyla gösterilir.
- Altında 5 sütunlu, yuvarlak köşeli 16:9 uygulama kutuları. Kumandayla üzerine gelinen kutu büyür ve adı altında belirir (tvOS'taki gibi).
- Sağ üstte saat, siyah arka plan. Kurulu tüm TV uygulamaları otomatik listelenir; uygulama yükleyip kaldırınca liste yenilenir.

## APK'yı indirme
GitHub'da **Actions → Apple TV Launcher (Android TV) build** altındaki son başarılı çalıştırmanın **AppleTVLauncher-apk** dosyasını indirin.

Kendiniz derlemek için (JDK 17 ve Android SDK gerekir): `cd AppleTVLauncher && ./gradlew assembleRelease` → `app/build/outputs/apk/release/app-release.apk`

## TV'ye kurulum
1. TV'de **Ayarlar → Cihaz Tercihleri → Hakkında → Yapı**'ya 7 kez basıp geliştirici seçeneklerini açın, ardından **USB/Ağ hata ayıklama**'yı açın.
2. Bilgisayardan: `adb connect <TV-IP-adresi>` ve `adb install app-release.apk`
   (ya da APK'yı "Downloader" / "Send Files to TV" uygulamasıyla TV'ye atıp kurun).
3. Uygulamayı TV'nin uygulamalar listesinden **Apple TV Görünümü** adıyla açabilirsiniz.

## Ana ekran olarak ayarlama
- **Eski Android TV**: Home tuşuna basınca hangi ana ekranın kullanılacağı sorulur; **Apple TV Görünümü → Her zaman** seçin.
- **Google TV / yeni Android TV**: sistem başka ana ekran seçtirmez. İsterseniz Google'ın ana ekranını kapatabilirsiniz:
  `adb shell pm disable-user --user 0 com.google.android.apps.tv.launcherx`
  Geri almak için: `adb shell pm enable com.google.android.apps.tv.launcherx`
  ⚠️ Bu işlem bazı cihazlarda Google TV önerilerini ve bazı ayar kısayollarını devre dışı bırakır; ne yaptığınızdan emin olun.

## Test
`./gradlew testDebugUnitTest` ana ekranı 1920×1080 boyutunda örnek uygulamalarla çizer ve `app/build/screenshots/home.png` dosyasına kaydeder.
