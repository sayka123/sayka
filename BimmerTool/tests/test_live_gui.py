import unittest
import time
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class LiveDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.app.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app._active_jobs = 0
            self.app._on_close()

    def test_default_has_no_simulator_start(self):
        self.assertNotIn('on_simulator', type(self.app).__dict__)
        self.assertFalse(hasattr(type(self.app), 'on_ev_demo'))
        self.assertNotIn('allow_simulator', self.app.__dict__)

    def test_poll_detects_closed_socket_and_clears_cards_without_user_action(self):
        self.app.conn = Mock(connected=False)
        self.app.uds = Mock()
        self.app.ev_metrics['soc'].set('88 %')
        self.app.ev_results = [{'key': 'soc', 'value': 88}]
        deadline = time.monotonic() + 2
        while self.app.uds is not None and time.monotonic() < deadline:
            self.app.update()
            time.sleep(.01)
        self.assertIsNone(self.app.uds)
        self.assertEqual(self.app.ev_metrics['soc'].get(), '—')
        self.assertEqual(self.app.ev_results, [])

    def test_synthetic_profile_is_rejected_even_when_source_flag_injected(self):
        from bimmertool.gui import app_dir
        import os
        self.app._connection_demo = True
        with self.assertRaises(ValueError):
            self.app._set_ev_profile(os.path.join(app_dir(), 'sim_ix_olcumler.json'))
        self.assertIsNone(self.app.ev_profile)

    def test_disconnect_clears_live_values_and_results(self):
        conn = self.app.conn = Mock()
        self.app.uds = Mock()
        self.app.vin = 'WBY21CF000S123456'
        self.app.ev_results = [{'key': 'soc', 'value': 80}]
        self.app.ev_metrics['soc'].set('80 %')
        self.app.last_health_check = {'old': True}
        self.app.raw_data.set('FF')
        self.app.on_disconnect()
        conn.close.assert_called_once()
        self.assertIsNone(self.app.uds)
        self.assertIsNone(self.app.vin)
        self.assertEqual(self.app.ev_metrics['soc'].get(), '—')
        self.assertEqual(self.app.ev_results, [])
        self.assertIsNone(self.app.last_health_check)
        self.assertEqual(self.app.raw_data.get(), '')

    def test_close_during_job_keeps_connection(self):
        self.app.conn = Mock()
        self.app._active_jobs = 1
        self.app._on_close()
        self.app.conn.close.assert_not_called()
        self.assertTrue(self.app.winfo_exists())

    def test_multiple_discovered_cars_require_explicit_selection(self):
        self.app.ip_var.set('169.254.1.10')
        self.app.vin_var.set('Previously connected identity')
        cars = [{'ip': '169.254.1.1', 'vin': 'NEW-A', 'protocol': 'doip'},
                {'ip': '169.254.1.2', 'vin': 'NEW-B', 'protocol': 'doip'}]
        with patch('bimmertool.gui.transport.discover_all', return_value=cars):
            self.app.on_discover()
            deadline = time.monotonic() + 3
            while self.app._active_jobs and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
        self.assertEqual(self.app.ip_var.get(), '169.254.1.10')
        self.assertEqual(self.app.vin_var.get(), 'Previously connected identity')
        windows = [child for child in self.app.winfo_children() if isinstance(child, tk.Toplevel)]
        self.assertEqual(len(windows), 1)

    def test_closed_transport_clears_old_values_before_next_operation(self):
        self.app.conn = Mock(connected=False)
        self.app.uds = Mock()
        self.app.ev_metrics['soc'].set('78 %')
        self.assertFalse(self.app.require_connection())
        self.assertEqual(self.app.ev_metrics['soc'].get(), '—')
        self.assertIsNone(self.app.uds)

    def test_local_source_cannot_be_used_as_vehicle_target(self):
        self.app.discovery_source='169.254.173.19'
        self.app.ip_var.set('169.254.173.19')
        with patch('bimmertool.gui.messagebox.showerror') as dialog, patch('bimmertool.gui.transport.open_connection') as connect:
            self.app.on_connect()
        dialog.assert_called_once()
        connect.assert_not_called()
        self.assertEqual(self.app._active_jobs,0)
