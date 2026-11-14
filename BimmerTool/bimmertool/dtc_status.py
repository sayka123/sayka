"""UDS status-byte meanings, not manufacturer-specific fault causes."""

FLAGS = (
    (0x01, 'Test başarısız (sorgu anındaki test durumu)'),
    (0x02, 'Bu çalışma döngüsünde test başarısız oldu'),
    (0x04, 'Bekleyen hata kaydı'),
    (0x08, 'Onaylanmış hata kaydı'),
    (0x10, 'Son silmeden beri test tamamlanmadı'),
    (0x20, 'Son silmeden beri test başarısız oldu'),
    (0x40, 'Bu çalışma döngüsünde test tamamlanmadı'),
    (0x80, 'Uyarı göstergesi talep edildi'),
)


def explain(status):
    if type(status) is not int or not 0 <= status <= 255:
        raise ValueError('DTC durumu 0–255 aralığında tam sayı olmalı')
    return [{'mask': mask, 'meaning': label, 'set': bool(status & mask)} for mask, label in FLAGS]


def summary(status):
    labels = [row['meaning'] for row in explain(status) if row['set']]
    return f'0x{status:02X} · ' + ('; '.join(labels) if labels else 'Durum biti yok; arıza olmadığı kanıtlanmaz')
