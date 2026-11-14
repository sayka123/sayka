import time
import unittest
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class DtcDetailDesktop(unittest.TestCase):
    def test_reads_status_and_explains_without_second_vehicle_request(self):
        try:
            app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        try:
            app.uds = Mock()
            app.uds.read_dtcs.return_value = [(0xABCDEF, 0x89)]
            app.found_ecus = [7]
            app.on_read_dtcs()
            deadline = time.monotonic()+3
            while app._active_jobs and time.monotonic()<deadline:
                app.update(); time.sleep(.01)
            self.assertEqual(app._active_jobs, 0)
            app.dtc_tree.selection_set(app.dtc_tree.get_children()[0])
            with patch('bimmertool.gui.messagebox.showinfo') as info:
                app.on_dtc_detail()
            self.assertIn('0x80: 1', info.call_args.args[1])
            self.assertIn('0x89', info.call_args.args[1])
            self.assertIn('onarım planı değildir', info.call_args.args[1])
            self.assertEqual([call[0] for call in app.uds.mock_calls], ['read_dtcs'])
        finally:
            app._on_close()
