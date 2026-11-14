import unittest
import time
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class IdentityDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.app.uds = Mock()
        self.app.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app._on_close()

    def test_no_selection_sends_nothing(self):
        with patch('bimmertool.identification_gui.messagebox.showwarning') as warning:
            self.app.on_identify_module()
        warning.assert_called_once()
        self.assertEqual(self.app.uds.mock_calls, [])

    def test_selection_reads_exact_selected_address(self):
        self.app.uds.read_did.return_value = b'DEMO'
        self.app._add_ecu_row(0x63)
        self.app.ecu_tree.selection_set(self.app.ecu_tree.get_children()[0])
        with patch.object(self.app, '_show_identification') as show:
            self.app.on_identify_module()
            deadline = time.monotonic() + 3
            while self.app._active_jobs and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
        self.assertEqual(self.app._active_jobs, 0)
        self.assertTrue(all(call.args[0] == 0x63 for call in self.app.uds.read_did.call_args_list))
        show.assert_called_once()
        self.app.uds.write_did.assert_not_called()
        self.app.uds.session.assert_not_called()
