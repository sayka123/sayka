"""UDS (ISO 14229) services used for BMW diagnostics."""

import struct

from .hsfz import NoResponse

NRC_NAMES = {
    0x10: "genel ret",
    0x11: "servis desteklenmiyor",
    0x12: "alt fonksiyon desteklenmiyor",
    0x13: "yanlış mesaj uzunluğu",
    0x22: "koşullar uygun değil (kontak/motor durumunu kontrol edin)",
    0x24: "istek sırası hatalı",
    0x31: "değer aralık dışında / desteklenmeyen kimlik",
    0x33: "güvenlik erişimi gerekli",
    0x35: "geçersiz anahtar",
    0x72: "yazma hatası",
    0x7E: "bu oturumda alt fonksiyon desteklenmiyor",
    0x7F: "bu oturumda servis desteklenmiyor",
}

DEFAULT_SESSION = 0x01
EXTENDED_SESSION = 0x03


class NegativeResponse(Exception):
    def __init__(self, sid, nrc):
        self.sid = sid
        self.nrc = nrc
        name = NRC_NAMES.get(nrc, "bilinmeyen hata")
        super().__init__(f"modül reddetti (0x{nrc:02X}: {name})")


class ProtocolError(Exception):
    pass


def format_dtc(code):
    return f"{code:06X}"


class UdsClient:
    def __init__(self, connection):
        self.conn = connection

    def _request(self, ecu, data, timeout=None):
        resp = self.conn.request(ecu, data, timeout=timeout)
        if not resp:
            raise ProtocolError("boş yanıt")
        if resp[0] == 0x7F:
            if len(resp) < 3 or resp[1] != data[0]:
                raise ProtocolError(f"geçersiz negatif yanıt: {resp.hex(' ')}")
            raise NegativeResponse(resp[1], resp[2])
        if resp[0] != data[0] + 0x40:
            raise ProtocolError(f"beklenmeyen yanıt: {resp.hex(' ')}")
        return resp

    def raw(self, ecu, data, timeout=None):
        return self.conn.request(ecu, bytes(data), timeout=timeout)

    def is_present(self, ecu, timeout=1.0):
        try:
            self._request(ecu, b"\x3E\x00", timeout=timeout)
            return True
        except NoResponse:
            return False
        except NegativeResponse:
            # It answered, so it exists.
            return True

    def session(self, ecu, session):
        resp = self._request(ecu, bytes([0x10, session]))
        if len(resp) < 2 or resp[1] != session:
            raise ProtocolError(f"yanlış oturum yanıtı: {resp.hex(' ')}")

    def read_did(self, ecu, did, timeout=None):
        resp = self._request(ecu, struct.pack(">BH", 0x22, did), timeout=timeout)
        if len(resp) < 3 or struct.unpack(">H", resp[1:3])[0] != did:
            raise ProtocolError(f"yanlış kimlik yanıtı: {resp.hex(' ')}")
        return resp[3:]

    def write_did(self, ecu, did, data):
        resp = self._request(ecu, struct.pack(">BH", 0x2E, did) + bytes(data))
        if len(resp) < 3 or struct.unpack(">H", resp[1:3])[0] != did:
            raise ProtocolError(f"yanlış kimlik yanıtı: {resp.hex(' ')}")

    def read_dtcs(self, ecu, status_mask=0x0C):
        resp = self._request(ecu, bytes([0x19, 0x02, status_mask]))
        if len(resp) < 3 or resp[1] != 0x02:
            raise ProtocolError(f"yanlış DTC yanıt başlığı: {resp.hex(' ')}")
        records = resp[3:]
        if len(records) % 4:
            raise ProtocolError(f"kesik DTC kaydı: {resp.hex(' ')}")
        dtcs = []
        for i in range(0, len(records), 4):
            code = int.from_bytes(records[i:i + 3], "big")
            dtcs.append((code, records[i + 3]))
        return dtcs

    def clear_dtcs(self, ecu):
        resp = self._request(ecu, b"\x14\xFF\xFF\xFF", timeout=5.0)
        if resp != b"\x54":
            raise ProtocolError(f"yanlış silme onayı: {resp.hex(' ')}")
