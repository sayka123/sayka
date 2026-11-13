"""DoIP (ISO 13400-2): diagnostics over IP used by newer BMWs (e.g. iX, i4) on port 13400."""

import socket
import struct
import threading
import time

from .hsfz import HsfzError, NoResponse

DOIP_PORT = 13400
PROTOCOL_VERSIONS = (0x02, 0x03)

T_VEHICLE_ID_REQ = 0x0001
T_VEHICLE_ANNOUNCE = 0x0004
T_ROUTING_REQ = 0x0005
T_ROUTING_RESP = 0x0006
T_ALIVE_REQ = 0x0007
T_ALIVE_RESP = 0x0008
T_DIAG = 0x8001
T_DIAG_ACK = 0x8002
T_DIAG_NACK = 0x8003

# External test equipment range per ISO 13400 is 0x0E00-0x0FFF; gateways differ in which
# they accept, so several are tried during routing activation.
TESTER_CANDIDATES = (0x0EF4, 0x0EF3, 0x0E00, 0x00F4)

ROUTING_CODES = {
    0x00: "test cihazı adresi tanınmadı",
    0x01: "tüm soketler dolu",
    0x02: "farklı adres zaten bağlı",
    0x03: "adres başka soketten bağlı",
    0x04: "kimlik doğrulama eksik",
    0x05: "onay reddedildi",
    0x06: "desteklenmeyen aktivasyon tipi",
    0x07: "TLS gerekli",
}

NACK_CODES = {
    0x02: "geçersiz kaynak adres",
    0x03: "bilinmeyen hedef adres",
    0x04: "mesaj çok büyük",
    0x05: "bellek yetersiz",
    0x06: "hedef erişilemez",
    0x07: "bilinmeyen ağ",
    0x08: "taşıma protokolü hatası",
}


def build(ptype, payload=b"", version=0x02):
    return struct.pack(">BBHI", version, version ^ 0xFF, ptype, len(payload)) + payload


def discover(target="255.255.255.255", port=DOIP_PORT, timeout=2.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.2)
    found = {}
    try:
        # 0xFF is the "any version" value the standard allows for identification requests.
        sock.sendto(build(T_VEHICLE_ID_REQ, version=0xFF), (target, port))
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            if len(data) < 8 + 19:
                continue
            _v, _iv, ptype, length = struct.unpack(">BBHI", data[:8])
            if ptype != T_VEHICLE_ANNOUNCE:
                continue
            p = data[8:8 + length]
            vin = p[:17].decode("ascii", "replace")
            logical = struct.unpack(">H", p[17:19])[0]
            found[addr[0]] = {"ip": addr[0], "vin": vin, "logical_address": logical,
                              "protocol": "doip"}
    finally:
        sock.close()
    return list(found.values())


class DoipConnection:
    """Same request() interface as HsfzConnection, ECU addresses are 0x00-0xFF as in BMW docs."""

    def __init__(self, host, port=DOIP_PORT, timeout=2.0, testers=TESTER_CANDIDATES):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.testers = testers
        self.tester = None
        self.version = 0x02
        self.sock = None
        self._buf = b""
        self._lock = threading.Lock()

    @property
    def connected(self):
        return self.sock is not None

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _send(self, ptype, payload):
        self.sock.sendall(build(ptype, payload, self.version))

    def _recv(self, deadline):
        while True:
            if len(self._buf) >= 8:
                _v, _iv, ptype, length = struct.unpack(">BBHI", self._buf[:8])
                if len(self._buf) >= 8 + length:
                    payload = self._buf[8:8 + length]
                    self._buf = self._buf[8 + length:]
                    if ptype == T_ALIVE_REQ and self.tester is not None:
                        self._send(T_ALIVE_RESP, struct.pack(">H", self.tester))
                        continue
                    return ptype, payload
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise NoResponse("yanıt yok")
            self.sock.settimeout(remaining)
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                raise NoResponse("yanıt yok")
            if not chunk:
                self.close()
                raise HsfzError("araç bağlantıyı kapattı")
            self._buf += chunk

    def connect(self):
        errors = []
        for tester in self.testers:
            for version in PROTOCOL_VERSIONS:
                self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._buf = b""
                self.version = version
                self._send(T_ROUTING_REQ, struct.pack(">HBI", tester, 0x00, 0))
                try:
                    ptype, p = self._recv(time.monotonic() + 3.0)
                except HsfzError as e:
                    errors.append(f"0x{tester:04X}/v{version}: {e}")
                    self.close()
                    continue
                if ptype == T_ROUTING_RESP and len(p) >= 5 and p[4] == 0x10:
                    self.tester = tester
                    return
                code = p[4] if ptype == T_ROUTING_RESP and len(p) >= 5 else None
                errors.append(f"0x{tester:04X}/v{version}: " +
                              (ROUTING_CODES.get(code, f"kod 0x{code:02X}") if code is not None
                               else f"beklenmeyen yanıt 0x{ptype:04X}"))
                self.close()
        raise HsfzError("DoIP bağlantısı kurulamadı: " + "; ".join(errors))

    def request(self, ecu, data, timeout=None):
        if not self.sock:
            raise HsfzError("bağlı değil")
        timeout = timeout or self.timeout
        with self._lock:
            self._buf = b""
            self._send(T_DIAG, struct.pack(">HH", self.tester, ecu) + bytes(data))
            deadline = time.monotonic() + timeout
            while True:
                ptype, p = self._recv(deadline)
                if ptype == T_DIAG_ACK:
                    continue
                if ptype == T_DIAG_NACK:
                    code = p[4] if len(p) > 4 else None
                    if code in (0x03, 0x06):
                        raise NoResponse(NACK_CODES[code])
                    raise HsfzError("DoIP reddi: " + NACK_CODES.get(code, str(code)))
                if ptype != T_DIAG or len(p) < 5:
                    continue
                src, dst = struct.unpack(">HH", p[:4])
                if src != ecu or dst != self.tester:
                    continue
                resp = p[4:]
                if resp[0] == 0x7F and len(resp) >= 3 and resp[2] == 0x78:
                    deadline = time.monotonic() + max(timeout, 5.0)
                    continue
                return resp
