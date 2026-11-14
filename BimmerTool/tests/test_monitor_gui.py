import os
import threading
import time
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
    from bimmertool.gui import App, app_dir
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "Tkinter unavailable")
class MonitorDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.app.update()

    def tearDown(self):
        if hasattr(self, "app"):
            self.app._on_close()

    def test_history_plots_and_resets_on_profile_change(self):
        self.app._connection_demo = True
        self.app._set_ev_profile(os.path.join(app_dir(), "sim_ix_olcumler.json"))
        for number, value in enumerate([70, None, 75, 74]):
            self.app.ev_history.append(f"2026-11-14T09:00:0{number}",
                                       [{"key": "soc", "value": value, "error": None}], "simulator")
        self.app.tabs.select(7)
        self.app.update()
        self.app._draw_trend()
        self.assertIn("4 okuma / 3 geçerli", self.app.trend_summary.get())
        self.assertTrue(self.app.trend_canvas.find_all())
        self.app._reset_ev()
        self.assertEqual(self.app.ev_history.samples, [])
        self.assertEqual(self.app.trend_signal.get(), "")

    def test_journal_is_bounded_and_can_be_cleared(self):
        for number in range(205):
            self.app.status.set(f"step {number}")
        children = self.app.journal_tree.get_children()
        self.assertEqual(len(children), 200)
        self.assertEqual(self.app.journal_tree.item(children[-1])["values"][1], "step 204")
        self.app.on_clear_journal()
        self.assertEqual(self.app.journal_tree.get_children(), ())

    def test_concurrent_background_job_rejected_and_lock_released(self):
        release = threading.Event()
        result = []
        try:
            self.assertTrue(self.app.run_bg(lambda: release.wait(2), lambda _r: result.append("first")))
            self.assertFalse(self.app.run_bg(lambda: result.append("second")))
            release.set()
            deadline = time.monotonic() + 3
            while self.app._active_jobs and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
            self.assertEqual(self.app._active_jobs, 0)
            self.assertEqual(result, ["first"])
        finally:
            release.set()

    def test_background_failure_releases_lock(self):
        def fail():
            raise ValueError("test failure")
        with patch("bimmertool.gui.messagebox.showerror"):
            self.app.run_bg(fail)
            deadline = time.monotonic() + 3
            while self.app._active_jobs and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
        self.assertEqual(self.app._active_jobs, 0)
        self.assertIn("test failure", self.app.status.get())

    def test_result_callback_failure_does_not_stop_result_queue(self):
        def fail(_result):
            raise ValueError("render failure")
        seen = []
        self.app._results.put((fail, None, None))
        self.app._results.put((seen.append, "next result", None))
        with patch("bimmertool.gui.messagebox.showerror") as dialog:
            deadline = time.monotonic() + 2
            while not seen and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
        self.assertEqual(seen, ["next result"])
        dialog.assert_called_once()
