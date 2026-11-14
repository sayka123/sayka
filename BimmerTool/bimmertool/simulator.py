"""A fake BMW that speaks HSFZ (F/G series) or DoIP (iX-style), for trying the program without a car."""

import math
import socket
import socketserver
import struct
import threading
import time

from . import doip
from .hsfz import (CTRL_ACK, CTRL_DIAG, CTRL_VEHICLE_IDENT, DIAG_PORT,
                   DISCOVERY_PORT, build_frame)

SIM_VIN = "WBA8E11000K123456"
SIM_IX_VIN = "WBY21CF000S123456"


class FakeEcu:
    def __init__(self, dids=None, dtcs=None, writable=(), secured=()):
        self.dids = dict(dids or {})
        self.dtcs = list(dtcs or [])
        self.writable = set(writable)
        self.secured = set(secured)
        self.session = 0x01

    def handle(self, req):
        sid = req[0]
        neg = lambda nrc: bytes([0x7F, sid, nrc])
        if sid == 0x3E:
            return b"\x7E\x00"
        if sid == 0x10 and len(req) == 2:
            self.session = req[1]
            return bytes([0x50, req[1], 0x00, 0x32, 0x01, 0xF4])
        if sid == 0x22 and len(req) == 3:
            did = struct.unpack(">H", req[1:3])[0]
            if did not in self.dids:
                return neg(0x31)
            value = self.dids[did]
            data = value() if callable(value) else value
            return bytes([0x62]) + req[1:3] + data
        if sid == 0x2E and len(req) > 3:
            did = struct.unpack(">H", req[1:3])[0]
            if did in self.secured:
                return neg(0x33)
            if did not in self.writable:
                return neg(0x31)
            if self.session != 0x03:
                return neg(0x7F)
            self.dids[did] = bytes(req[3:])
            return bytes([0x6E]) + req[1:3]
        if sid == 0x19 and len(req) == 3 and req[1] == 0x02:
            body = b"".join(code.to_bytes(3, "big") + bytes([st])
                            for code, st in self.dtcs if st & req[2])
            return bytes([0x59, 0x02, 0xFF]) + body
        if sid == 0x14:
            self.dtcs.clear()
            return b"\x54"
        return neg(0x11)


def _engine_values(start):
    def t():
        return time.monotonic() - start

    def rpm():
        v = int((800 + 1200 * (1 + math.sin(t() / 2)) / 2) * 4)
        return v.to_bytes(2, "big")

    return {
        0xF40C: rpm,
        0xF40D: lambda: bytes([int(30 + 20 * math.sin(t() / 3))]),
        0xF405: lambda: bytes([40 + min(90, int(60 + t()))]),
        0xF40F: bytes([40 + 24]),
        0xF404: lambda: bytes([int(60 + 40 * (1 + math.sin(t())) / 2)]),
        0xF411: lambda: bytes([int(20 + 30 * (1 + math.sin(t())) / 2)]),
        0xF40B: bytes([101]),
        0xF442: (14200).to_bytes(2, "big"),
    }


def build_car():
    start = time.monotonic()
    vin = SIM_VIN.encode()
    return {
        0x10: FakeEcu({0xF190: vin}),
        0x12: FakeEcu({0xF190: vin, **_engine_values(start)},
                      dtcs=[(0x120308, 0x08), (0x1F2F05, 0x0C)]),
        0x18: FakeEcu(),
        0x29: FakeEcu(dtcs=[(0x480A01, 0x08)]),
        0x40: FakeEcu({0xF190: vin}),
        0x60: FakeEcu(),
        0x63: FakeEcu(),
        # Sample coding block used by sim_kodlama_ornek.json.
        0x72: FakeEcu({0x3000: bytes([0x10, 0x00, 0x01, 0x00])}, writable={0x3000}),
        0x78: FakeEcu({0x3100: bytes([0x00])}, secured={0x3100}),
    }


def build_ix():
    """iX-like: no combustion engine module, and coding blocks that refuse unsigned writes."""
    vin = SIM_IX_VIN.encode()
    return {
        0x10: FakeEcu({0xF190: vin}),
        0x07: FakeEcu({0x1234: bytes([0x4E])}, dtcs=[(0x21F0A1, 0x08)]),  # SME, fake value
        0x40: FakeEcu({0xF190: vin}),
        0x60: FakeEcu(),
        0x63: FakeEcu(),
        0x72: FakeEcu({0x3000: bytes([0x10, 0x00, 0x01, 0x00])}, secured={0x3000}),
        0x78: FakeEcu({0x3100: bytes([0x00])}, secured={0x3100}),
    }


class _HsfzHandler(socketserver.BaseRequestHandler):
    def handle(self):
        car = self.server.car
        buf = b""
        while True:
            try:
                chunk = self.request.recv(65536)
            except OSError:
                return
            if not chunk:
                return
            buf += chunk
            while len(buf) >= 6:
                length, control = struct.unpack(">IH", buf[:6])
                if len(buf) < 6 + length:
                    break
                payload, buf = buf[6:6 + length], buf[6 + length:]
                if control != CTRL_DIAG or len(payload) < 3:
                    continue
                src, dst, req = payload[0], payload[1], payload[2:]
                self.request.sendall(build_frame(CTRL_ACK, payload[:6]))
                ecu = car.get(dst)
                if ecu is None:
                    continue  # like a real gateway: acknowledged, then silence
                with self.server.lock:
                    resp = ecu.handle(req)
                if req[0] == 0x2E:
                    self.request.sendall(build_frame(CTRL_DIAG, bytes([dst, src, 0x7F, 0x2E, 0x78])))
                self.request.sendall(build_frame(CTRL_DIAG, bytes([dst, src]) + resp))


class _DoipHandler(socketserver.BaseRequestHandler):
    def handle(self):
        car = self.server.car
        buf = b""
        tester = None
        while True:
            try:
                chunk = self.request.recv(65536)
            except OSError:
                return
            if not chunk:
                return
            buf += chunk
            while len(buf) >= 8:
                version, _inv, ptype, length = struct.unpack(">BBHI", buf[:8])
                if len(buf) < 8 + length:
                    break
                p, buf = buf[8:8 + length], buf[8 + length:]
                send = lambda t, payload: self.request.sendall(doip.build(t, payload, version))
                if ptype == doip.T_ROUTING_REQ:
                    src = struct.unpack(">H", p[:2])[0]
                    ok = src in self.server.accepted_testers
                    send(doip.T_ROUTING_RESP, struct.pack(">HHB", src, 0x0010, 0x10 if ok else 0x00) + b"\0" * 4)
                    if not ok:
                        return  # gateway closes the socket after a refused activation
                    tester = src
                    # Exercise the client's alive-check handling.
                    send(doip.T_ALIVE_REQ, b"")
                elif ptype == doip.T_DIAG and tester is not None:
                    src, dst = struct.unpack(">HH", p[:4])
                    req = p[4:]
                    ecu = car.get(dst)
                    if ecu is None:
                        send(doip.T_DIAG_NACK, struct.pack(">HHB", dst, src, 0x03))
                        continue
                    send(doip.T_DIAG_ACK, struct.pack(">HHB", dst, src, 0x00))
                    with self.server.lock:
                        resp = ecu.handle(req)
                    send(doip.T_DIAG, struct.pack(">HH", dst, src) + resp)


class _TcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Simulator:
    """model='f' (HSFZ, combustion F/G series) or 'ix' (DoIP, electric)."""

    def __init__(self, host="127.0.0.1", port=None, discovery_port=None, model="f",
                 accepted_testers=doip.TESTER_CANDIDATES):
        self.model = model
        self.vin = SIM_IX_VIN if model == "ix" else SIM_VIN
        is_doip = model == "ix"
        default_port = doip.DOIP_PORT if is_doip else DIAG_PORT
        default_disc = doip.DOIP_PORT if is_doip else DISCOVERY_PORT
        self.tcp = _TcpServer((host, default_port if port is None else port),
                              _DoipHandler if is_doip else _HsfzHandler)
        self.tcp.car = build_ix() if is_doip else build_car()
        self.tcp.lock = threading.Lock()
        self.tcp.accepted_testers = set(accepted_testers)
        self.port = self.tcp.server_address[1]
        self.protocol = "doip" if is_doip else "hsfz"
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.bind((host, default_disc if discovery_port is None else discovery_port))
        self.discovery_port = self.udp.getsockname()[1]
        self.udp.settimeout(0.5)
        self._running = True

    @property
    def car(self):
        return self.tcp.car

    def _ident_reply(self, data):
        if self.protocol == "hsfz":
            if len(data) >= 6 and struct.unpack(">IH", data[:6])[1] == CTRL_VEHICLE_IDENT:
                ident = f"DIAGADR10BMWMAC001A37C0FFEEBMWVIN{self.vin}".encode()
                return build_frame(CTRL_VEHICLE_IDENT, ident)
        elif len(data) >= 8 and struct.unpack(">BBHI", data[:8])[2] == doip.T_VEHICLE_ID_REQ:
            body = self.vin.encode() + struct.pack(">H", 0x0010) + b"\x00\x1A\x37\xC0\xFF\xEE" * 2 + b"\x00"
            return doip.build(doip.T_VEHICLE_ANNOUNCE, body)
        return None

    def _udp_loop(self):
        while self._running:
            try:
                data, addr = self.udp.recvfrom(1024)
            except (socket.timeout, OSError):
                continue
            reply = self._ident_reply(data)
            if reply:
                self.udp.sendto(reply, addr)

    def start(self):
        threading.Thread(target=self.tcp.serve_forever, daemon=True).start()
        threading.Thread(target=self._udp_loop, daemon=True).start()
        return self

    def stop(self):
        self._running = False
        self.tcp.shutdown()
        self.tcp.server_close()
        self.udp.close()


if __name__ == "__main__":
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "f"
    sim = Simulator(model=model).start()
    print(f"Simülatör ({model}) çalışıyor: 127.0.0.1:{sim.port} (Ctrl+C ile durdurun)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
