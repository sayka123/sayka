"""HSFZ: BMW's diagnostics-over-IP framing used by the ENET cable (F/G series).

Frame = 4-byte big-endian length (of everything after the control word)
        + 2-byte control word + payload.
Diagnostic payload = source address, target address, UDS bytes.
"""

import re
import socket
import struct
import threading
import time

DIAG_PORT = 6801
DISCOVERY_PORT = 6811
TESTER_ADDRESS = 0xF4

CTRL_DIAG = 0x0001
CTRL_ACK = 0x0002
CTRL_VEHICLE_IDENT = 0x0011
CTRL_ALIVE_CHECK = 0x0012
CTRL_ERRORS = {
    0x0040: "geçersiz test cihazı adresi",
    0x0041: "geçersiz kontrol kelimesi",
    0x0042: "geçersiz format",
    0x0043: "geçersiz hedef adres",
    0x0044: "mesaj çok uzun",
    0x0045: "ECU erişilemez",
}


class HsfzError(Exception):
    pass


class NoResponse(HsfzError):
    pass


def build_frame(control, payload=b""):
    return struct.pack(">IH", len(payload), control) + payload


def parse_ident(payload):
    text = payload.decode("ascii", errors="replace")
    vin = re.search(r"BMWVIN([A-Z0-9]{17})", text)
    mac = re.search(r"BMWMAC([0-9A-F]{12})", text)
    diag = re.search(r"DIAGADR(\d+)", text)
    return {
        "vin": vin.group(1) if vin else None,
        "mac": mac.group(1) if mac else None,
        "diag_address": int(diag.group(1)) if diag else None,
        "raw": text,
    }


def discover(target="255.255.255.255", port=DISCOVERY_PORT, timeout=2.0):
    """Broadcast a vehicle identification request; returns [{ip, vin, ...}]."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.2)
    found = {}
    try:
        sock.sendto(build_frame(CTRL_VEHICLE_IDENT), (target, port))
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            if len(data) < 6:
                continue
            length, control = struct.unpack(">IH", data[:6])
            if control != CTRL_VEHICLE_IDENT:
                continue
            info = parse_ident(data[6:6 + length])
            info["ip"] = addr[0]
            found[addr[0]] = info
    finally:
        sock.close()
    return list(found.values())


class HsfzConnection:
    def __init__(self, host, port=DIAG_PORT, tester=TESTER_ADDRESS, timeout=2.0):
        self.host = host
        self.port = port
        self.tester = tester
        self.timeout = timeout
        self.sock = None
        self._lock = threading.Lock()
        self._buf = b""

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._buf = b""

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    @property
    def connected(self):
        return self.sock is not None

    def _recv_frame(self, deadline):
        while True:
            if len(self._buf) >= 6:
                length, control = struct.unpack(">IH", self._buf[:6])
                if len(self._buf) >= 6 + length:
                    payload = self._buf[6:6 + length]
                    self._buf = self._buf[6 + length:]
                    return control, payload
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

    def request(self, ecu, data, timeout=None):
        """Send a UDS request to one ECU and return its UDS response bytes."""
        if not self.sock:
            raise HsfzError("bağlı değil")
        timeout = timeout or self.timeout
        with self._lock:
            # Drop stale frames left over from a request that timed out.
            self._buf = b""
            self.sock.setblocking(False)
            try:
                while self.sock.recv(65536):
                    pass
            except (BlockingIOError, socket.timeout):
                pass
            finally:
                self.sock.setblocking(True)

            self.sock.sendall(build_frame(CTRL_DIAG, bytes([self.tester, ecu]) + bytes(data)))
            deadline = time.monotonic() + timeout
            while True:
                control, payload = self._recv_frame(deadline)
                if control == CTRL_ACK or control == CTRL_ALIVE_CHECK:
                    continue
                if control in CTRL_ERRORS:
                    raise HsfzError(CTRL_ERRORS[control])
                if control != CTRL_DIAG or len(payload) < 3:
                    continue
                if payload[0] != ecu or payload[1] != self.tester:
                    continue
                resp = payload[2:]
                # 0x78 = response pending: the ECU needs more time.
                if resp[0] == 0x7F and len(resp) >= 3 and resp[2] == 0x78:
                    deadline = time.monotonic() + max(timeout, 5.0)
                    continue
                return resp
