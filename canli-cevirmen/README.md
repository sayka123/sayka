# Canlı Çevirmen

Konuşmayı veya yazılan metni anında başka bir dile çeviren, kurulum gerektirmeyen tek sayfalık web uygulaması.

## Özellikler
- 🎤 Mikrofondan sürekli dinleme, konuşurken ara (anlık) çeviri, cümle bitince kesin çeviri
- ⌨️ Yazarken anında çeviri (Enter ile kalıcı satır olarak ekler)
- 🔊 Çeviriyi sesli okuma (isteğe bağlı)
- 15 dil, dil değiştirme (⇄) ve seçimlerin hatırlanması

## Çalıştırma
Mikrofon erişimi için sayfa `localhost` veya HTTPS üzerinden açılmalıdır:

```bash
cd canli-cevirmen
python3 -m http.server 8000
```

Ardından Chrome veya Edge ile http://localhost:8000 adresini açın ve mikrofon iznini verin.

## Notlar
- Konuşma tanıma tarayıcının Web Speech API'sini kullanır (Chrome/Edge/Safari; Firefox desteklemez).
- Çeviri, anahtar gerektirmeyen ücretsiz [MyMemory API](https://mymemory.translated.net/doc/spec.php) ile yapılır; istek başına ~500 karakter ve günlük kullanım limiti vardır.
- İnternet bağlantısı gereklidir.
