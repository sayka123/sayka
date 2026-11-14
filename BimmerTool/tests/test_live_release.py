import struct
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from bimmertool.doip import DoipConnection
from bimmertool.hsfz import HsfzConnection, HsfzError, NoResponse, CTRL_DIAG
from scripts.package_live import package


class LivePackage(unittest.TestCase):
    def test_package_has_no_synthetic_files(self):
        with tempfile.TemporaryDirectory() as folder:
            output = package(Path(folder) / 'live.zip')
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertFalse(any('simulator' in name or 'sim_' in name or '/tests/' in name for name in names))
                self.assertIn('BimmerTool/bimmertool/gui.py', names)
                gui = archive.read('BimmerTool/bimmertool/gui.py').decode()
                self.assertNotIn('allow_simulator', gui)
                self.assertNotIn('def on_simulator', gui)
                ev_gui = archive.read('BimmerTool/bimmertool/ev_gui.py').decode()
                self.assertNotIn('def on_ev_demo', ev_gui)
                self.assertTrue(archive.getinfo('BimmerTool/Mac-Baslat.command').external_attr >> 16 & 0o111)


class FrameLimits(unittest.TestCase):
    def test_doip_send_failure_closes_socket_and_is_not_retried(self):
        conn = DoipConnection('127.0.0.1')
        sock = conn.sock = Mock()
        sock.sendall.side_effect = OSError('network lost')
        with self.assertRaises(OSError):
            conn._send(0x8001, b'payload')
        sock.sendall.assert_called_once()
        sock.close.assert_called_once()
        self.assertIsNone(conn.sock)

    def test_socket_read_failure_closes_both_transports(self):
        for conn in [DoipConnection('127.0.0.1'), HsfzConnection('127.0.0.1')]:
            with self.subTest(transport=type(conn).__name__):
                sock = conn.sock = Mock()
                sock.recv.side_effect = ConnectionResetError('reset')
                read = conn._recv if isinstance(conn, DoipConnection) else conn._recv_frame
                with self.assertRaises(ConnectionResetError):
                    read(time.monotonic()+1)
                sock.close.assert_called_once()
                self.assertIsNone(conn.sock)
    def test_bad_doip_header_closes_connection(self):
        for header in [struct.pack('>BBHI', 2, 2, 0x8001, 0),
                       struct.pack('>BBHI', 2, 253, 0x8001, 1024*1024+1)]:
            conn = DoipConnection('127.0.0.1')
            sock = conn.sock = Mock()
            conn._buf = header
            with self.assertRaises(HsfzError):
                conn._recv(time.monotonic()+1)
            sock.close.assert_called_once()
            self.assertIsNone(conn.sock)

    def test_oversized_hsfz_closes_connection(self):
        conn = HsfzConnection('127.0.0.1')
        sock = conn.sock = Mock()
        conn._buf = struct.pack('>IH', 1024*1024+1, 1)
        with self.assertRaises(HsfzError):
            conn._recv_frame(time.monotonic()+1)
        sock.close.assert_called_once()


class PendingLimits(unittest.TestCase):
    def test_doip_repeated_pending_has_total_deadline_and_no_retry(self):
        conn = DoipConnection('127.0.0.1')
        conn.sock = Mock()
        conn.tester = 0x0EF4
        conn._send = Mock()
        conn._recv = Mock(return_value=(0x8001, struct.pack('>HH', 0x63, conn.tester) + b'\x7f\x22\x78'))
        with patch('bimmertool.doip.time.monotonic', side_effect=range(0, 100, 5)):
            with self.assertRaises(NoResponse):
                conn.request(0x63, b'\x22\xf1\x90')
        conn._send.assert_called_once()

    def test_hsfz_repeated_pending_has_total_deadline_and_no_retry(self):
        conn = HsfzConnection('127.0.0.1')
        conn.sock = Mock()
        conn.sock.recv.side_effect = BlockingIOError
        conn._recv_frame = Mock(return_value=(CTRL_DIAG, bytes([0x63, conn.tester]) + b'\x7f\x22\x78'))
        with patch('bimmertool.hsfz.time.monotonic', side_effect=range(0, 100, 5)):
            with self.assertRaises(NoResponse):
                conn.request(0x63, b'\x22\xf1\x90')
        conn.sock.sendall.assert_called_once()
