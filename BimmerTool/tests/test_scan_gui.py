import threading,time,unittest
from unittest.mock import Mock
try:
    import tkinter as tk
    from bimmertool.gui import App
except ImportError:
    tk=None


@unittest.skipIf(tk is None,'Tkinter unavailable')
class ScanDesktop(unittest.TestCase):
    def test_cancelled_deep_scan_is_partial_and_exportable(self):
        try:app=App()
        except tk.TclError as error:self.skipTest(str(error))
        release=threading.Event()
        try:
            app.conn=Mock(tester=244)
            app.uds=Mock()
            app.uds.is_present.side_effect=lambda *args,**kwargs:release.wait(1)
            app.full_scan.set(True)
            app.on_scan()
            app.on_stop_scan();release.set()
            deadline=time.monotonic()+3
            while app._active_jobs and time.monotonic()<deadline:
                app.update();time.sleep(.01)
            self.assertEqual(app._active_jobs,0)
            self.assertIsNotNone(app.last_scan)
            self.assertTrue(app.last_scan['cancelled'])
            self.assertFalse(app.last_scan['complete'])
            self.assertEqual(app.found_ecus,app.last_scan['found'])
            self.assertIn('kısmi',app.status.get())
        finally:
            release.set();app._active_jobs=0;app._on_close()
