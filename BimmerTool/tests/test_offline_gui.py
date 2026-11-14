from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App
    from tests.test_offline_files import FA
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class OfflineDesktop(unittest.TestCase):
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

    def test_fa_and_binary_viewers_never_contact_vehicle(self):
        with tempfile.TemporaryDirectory() as folder:
            xml = Path(folder) / 'fa.xml'
            xml.write_text(FA)
            a, b = Path(folder) / 'a.ncd', Path(folder) / 'b.ncd'
            a.write_bytes(b'\x00\x01'); b.write_bytes(b'\x00\x02')
            with patch('bimmertool.offline_gui.filedialog.askopenfilename', return_value=str(xml)):
                self.app.on_inspect_fa()
            with patch('bimmertool.offline_gui.filedialog.askopenfilename', side_effect=[str(a), str(b)]):
                self.app.on_compare_binary()
        windows = [w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertEqual(len(windows), 2)
        self.assertEqual(self.app.uds.mock_calls, [])

    def test_invalid_file_shows_error_instead_of_window(self):
        with tempfile.NamedTemporaryFile(suffix='.xml') as file:
            file.write(b'<bad/>'); file.flush()
            with patch('bimmertool.offline_gui.filedialog.askopenfilename', return_value=file.name), \
                 patch('bimmertool.offline_gui.messagebox.showerror') as error:
                self.app.on_inspect_fa()
        error.assert_called_once()
        self.assertEqual(self.app.uds.mock_calls, [])

    def test_compare_fa_uses_files_only(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a.xml', Path(folder) / 'b.xml'
            a.write_text(FA)
            b.write_text(FA.replace('5AZ', '5AC'))
            with patch('bimmertool.offline_gui.filedialog.askopenfilename', side_effect=[str(a), str(b)]):
                self.app.on_compare_fa()
        self.assertEqual(self.app.uds.mock_calls, [])
        windows = [w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertEqual(len(windows), 1)
        self.assertIn('FA XML', windows[0].title())
