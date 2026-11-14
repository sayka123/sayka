import os
import time
import unittest
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App, app_dir
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class PreviewDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.client = Mock()
        self.client.read_did.return_value = bytes([16, 0, 1, 0])
        self.app.uds = self.client
        self.app._load_definitions(os.path.join(app_dir(), 'sim_kodlama_ornek.json'))
        self.app.coding_tree.selection_set('0')
        self.app._on_coding_select()
        self.app.update()
        self.app.option_var.set('Kapalı')

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app._on_close()

    def idle(self):
        deadline = time.monotonic() + 3
        while self.app._active_jobs and time.monotonic() < deadline:
            self.app.update()
            time.sleep(.01)
        self.assertEqual(self.app._active_jobs, 0)

    def test_preview_displays_byte_change_without_write(self):
        with patch('bimmertool.gui.messagebox.showinfo') as dialog:
            self.app.on_preview_coding()
            self.idle()
        self.assertIn('Bayt 2: 01 → 00', dialog.call_args.args[1])
        self.client.write_did.assert_not_called()
        self.client.session.assert_not_called()

    def test_cancel_after_preview_never_writes(self):
        with patch('bimmertool.gui.messagebox.askyesno', return_value=False) as dialog:
            self.app.on_apply_coding()
            self.idle()
        self.assertIn('Bayt 2', dialog.call_args.args[1])
        self.client.write_did.assert_not_called()
        self.client.session.assert_not_called()
