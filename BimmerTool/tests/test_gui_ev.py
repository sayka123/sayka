import json
import csv
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

try:
    import tkinter as tk
    from bimmertool.gui import App, app_dir
    from bimmertool.simulator import build_ix
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "Tkinter unavailable")
class EvDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(f"Graphical display unavailable: {error}")
        self.app.update()
        self.client = Mock()
        blocks = build_ix()[0x07].dids
        self.client.read_did.side_effect = lambda ecu, did: blocks[did]
        self.app.uds = self.client
        self.app.conn = Mock(protocol="doip")
        self.app.vin = "WBY21CF000S123456"
        self.app._connection_demo = True
        self.profile_path = os.path.join(app_dir(), "sim_ix_olcumler.json")

    def tearDown(self):
        if hasattr(self, "app"):
            self.app._on_close()

    def read_demo(self):
        self.app._set_ev_profile(self.profile_path)
        self.app.on_ev_read()
        deadline = time.monotonic() + 3
        while self.app._ev_busy and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.01)
        self.assertFalse(self.app._ev_busy)
        self.assertEqual(len(self.app.ev_results), 6)

    def test_demo_read_and_report_vin_opt_in(self):
        self.read_demo()
        self.assertEqual(self.app.ev_metrics["soc"].get(), "78.4 %")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "report.json")
            for include_vin in (False, True):
                self.app.report_vin.set(include_vin)
                with patch("bimmertool.ev_gui.filedialog.asksaveasfilename", return_value=path):
                    self.app.on_export_report()
                with open(path, encoding="utf-8") as file:
                    report = json.load(file)
                self.assertEqual("vin" in report, include_vin)
                self.assertEqual(report["source"], "simulator")
                self.assertIsNone(report["dtcs_read_at"])
                self.assertFalse(report["model_verified"])
                self.assertEqual(len(report["measurements"]), 6)

    def test_reset_discards_demo_values_and_real_connection_rejects_profile(self):
        self.read_demo()
        self.app._connection_demo = False
        self.app._reset_ev()
        self.assertIsNone(self.app.ev_profile)
        self.assertEqual(self.app.ev_results, [])
        self.assertEqual(self.app.ev_metrics["soc"].get(), "—")
        self.client.reset_mock()
        with self.assertRaises(ValueError):
            self.app._set_ev_profile(self.profile_path)
        self.client.read_did.assert_not_called()

    def test_stop_cancels_scheduled_refresh(self):
        self.app._ev_running = True
        self.app._ev_timer = self.app.after(5000, self.app.on_ev_read)
        self.app._stop_ev()
        self.assertIsNone(self.app._ev_timer)
        self.assertFalse(self.app._ev_running)

    def test_csv_preserves_numeric_values_and_neutralizes_formula_labels(self):
        self.read_demo()
        self.app.ev_results[0]["name"] = "=1+1"
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "readings.csv")
            with patch("bimmertool.ev_gui.filedialog.asksaveasfilename", return_value=path):
                self.app.on_export_ev_csv()
            with open(path, encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]["name"], "'=1+1")
            self.assertAlmostEqual(float(rows[0]["value"]), 78.4)
            self.assertEqual(rows[0]["source"], "simulator")
            self.assertNotIn("vin", rows[0])

    def test_partial_dtc_clear_is_not_reported_as_full_success(self):
        self.app.found_ecus = [0x07, 0x63]
        self.client.clear_dtcs.side_effect = [None, RuntimeError("refused")]
        with patch("bimmertool.gui.messagebox.askyesno", return_value=True), \
                patch("bimmertool.gui.messagebox.showinfo"):
            self.app.on_clear_dtcs()
            deadline = time.monotonic() + 3
            while self.app._active_jobs and time.monotonic() < deadline:
                self.app.update()
                time.sleep(.01)
        self.assertIn("1/2", self.app.status.get())
        self.assertEqual(self.app.last_clear_results[1]["error"], "refused")
        self.assertIsNone(self.app.dtcs_read_at)

    def test_ev_live_view_never_calls_engine_reader(self):
        self.app._custom.append(("old-engine-reading", 0x12, 0xF40C))
        self.app.on_live_toggle()
        time.sleep(0.02)
        self.app.on_live_toggle()
        self.client.read_did.assert_not_called()

    def test_engine_custom_did_is_rejected_in_ev_mode(self):
        self.app.custom_ecu.set("0x12")
        self.app.custom_did.set("0xF40C")
        with patch("bimmertool.gui.messagebox.showwarning") as warning:
            self.app.on_add_custom()
        warning.assert_called_once()
        self.assertEqual(self.app._custom, [])
