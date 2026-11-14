import unittest
from unittest.mock import Mock
from bimmertool.hsfz import HsfzConnection,NoResponse,HsfzError,CTRL_DIAG
from bimmertool.uds import UdsClient
from bimmertool.scanning import scan


class TargetRejection(unittest.TestCase):
    def connection(self):
        conn=HsfzConnection('127.0.0.1')
        conn.sock=Mock()
        conn.sock.recv.side_effect=BlockingIOError
        return conn

    def test_unreachable_target_does_not_abort_scan(self):
        for code in (0x43,0x45):
            with self.subTest(control=code):
                conn=self.connection()
                conn._recv_frame=Mock(side_effect=[(code,b''),(CTRL_DIAG,bytes([0x10,conn.tester,0x7E,0]))])
                result=scan(UdsClient(conn),[0,0x10])
                self.assertEqual(result['found'],[0x10])
                self.assertTrue(result['complete'])
                self.assertEqual(result['results'][0]['state'],'no_response')
                conn.sock.close.assert_not_called()

    def test_bad_source_remains_fatal(self):
        conn=self.connection()
        conn._recv_frame=Mock(return_value=(0x40,b''))
        result=scan(UdsClient(conn),[0,0x10])
        self.assertFalse(result['complete'])
        self.assertEqual(len(result['results']),1)
        self.assertEqual(result['results'][0]['state'],'transport_error')
