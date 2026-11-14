import unittest
from unittest.mock import Mock,patch
from bimmertool import transport
from bimmertool.hsfz import HsfzError


class TransportSelection(unittest.TestCase):
    def test_ix_auto_tries_hsfz_after_refused_doip(self):
        events=[]
        doip=Mock();hsfz=Mock()
        doip.connect.side_effect=lambda: (events.append('doip'), (_ for _ in ()).throw(ConnectionRefusedError(61,'Connection refused')))
        hsfz.connect.side_effect=lambda:events.append('hsfz')
        with patch.object(transport.doip,'DoipConnection',return_value=doip), patch.object(transport.hsfz,'HsfzConnection',return_value=hsfz):
            self.assertIs(transport.open_connection('127.0.0.1',preferred='doip'),hsfz)
        self.assertEqual(events,['doip','hsfz'])
        doip.close.assert_called_once()
        self.assertEqual(hsfz.protocol,'hsfz')

    def test_explicit_protocol_does_not_fallback(self):
        doip=Mock();doip.connect.side_effect=ConnectionRefusedError('refused')
        with patch.object(transport.doip,'DoipConnection',return_value=doip), patch.object(transport.hsfz,'HsfzConnection') as other:
            with self.assertRaisesRegex(HsfzError,'13400'):
                transport.open_connection('127.0.0.1',protocol='doip')
        other.assert_not_called()

    def test_invalid_protocol_never_opens_socket(self):
        with self.assertRaises(ValueError):
            transport.open_connection('127.0.0.1',preferred='bad')

    def test_socket_fallback_reads_vin_over_hsfz(self):
        import socket
        from bimmertool.simulator import Simulator,SIM_VIN
        from bimmertool.uds import UdsClient
        sim=Simulator(model='f',port=0,discovery_port=0).start()
        conn=None
        # Keep a bound, non-listening port to get a deterministic TCP refusal.
        with socket.socket() as closed:
            closed.bind(('127.0.0.1',0))
            try:
                conn=transport.open_connection('127.0.0.1',preferred='doip',doip_port=closed.getsockname()[1],hsfz_port=sim.port)
                self.assertEqual(conn.protocol,'hsfz')
                self.assertEqual(UdsClient(conn).read_did(0x10,0xF190).decode(),SIM_VIN)
            finally:
                if conn:conn.close()
                sim.stop()

    def test_timeout_does_not_claim_refusal(self):
        conn=Mock();conn.connect.side_effect=TimeoutError('timed out')
        with patch.object(transport.hsfz,'HsfzConnection',return_value=conn):
            with self.assertRaises(HsfzError) as caught:
                transport.open_connection('127.0.0.1',protocol='hsfz')
        text=str(caught.exception)
        self.assertIn('Zaman aşımı',text)
        self.assertNotIn('Connection refused:',text)
        self.assertNotIn('Bağlantı reddi:',text)

    def test_wrapped_os_error_is_classified(self):
        error=HsfzError('outer')
        error.__cause__=ConnectionRefusedError(61,'refused')
        self.assertEqual(transport.connection_error_kind(error),'refused')
