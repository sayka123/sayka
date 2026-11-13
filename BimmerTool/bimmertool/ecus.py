"""Common F/G series diagnostic addresses. Fitment differs per car; scanning shows what exists."""

ECU_NAMES = {
    0x00: "JBBF - Gövde kontrol (Junction Box)",
    0x01: "ACSM - Hava yastığı",
    0x07: "SME - Yüksek voltaj aküsü",
    0x10: "ZGW - Merkezi ağ geçidi",
    0x12: "DME - Motor elektroniği",
    0x13: "DME2 - Motor elektroniği 2",
    0x18: "EGS - Şanzıman",
    0x19: "LMV - Yanal dinamik",
    0x1C: "ICM - Entegre şasi yönetimi",
    0x1E: "EKPS - Yakıt pompası",
    0x20: "RDC - Lastik basıncı",
    0x21: "FRR - Aktif hız sabitleyici radarı",
    0x29: "DSC - Dinamik denge kontrolü",
    0x30: "EPS - Elektrikli direksiyon",
    0x35: "TRSVC - Kamera sistemi",
    0x38: "EHC - Havalı süspansiyon",
    0x3C: "CDM - Üst kontrol paneli",
    0x40: "FEM/BDC - Gövde (anahtar, merkezi kilit)",
    0x41: "DME/DDE ikinci kanal",
    0x56: "FZD - Tavan fonksiyon merkezi",
    0x5D: "KAFAS - Şerit/işaret kamerası",
    0x5F: "FLA - Uzun far asistanı",
    0x60: "KOMBI - Gösterge paneli",
    0x63: "HU - Multimedya (NBT/EVO/MGU)",
    0x64: "PDC - Park sensörü",
    0x67: "ZBE - iDrive kontrolcü",
    0x6D: "FAS - Sürücü koltuğu",
    0x72: "FRM - Ayak bölmesi (aydınlatma)",
    0x73: "LHM - Sol far modülü",
    0x74: "RHM - Sağ far modülü",
    0x78: "IHKA - Klima",
    0x7A: "SZL - Direksiyon kolon anahtarı",
    0xA0: "CID - Merkezi ekran",
    0xA6: "AHM - Römork modülü",
}


def ecu_name(addr):
    return ECU_NAMES.get(addr, f"Modül 0x{addr:02X}")
