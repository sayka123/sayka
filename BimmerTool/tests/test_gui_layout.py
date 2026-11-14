import os
import unittest

try:
    import tkinter as tk
    from bimmertool.gui import App, app_dir
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "Tkinter unavailable")
class DesktopLayout(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(f"Graphical display unavailable: {error}")
        self.app.update()

    def tearDown(self):
        if hasattr(self, "app"):
            self.app._on_close()

    def test_sidebar_selects_each_workspace(self):
        for index, button in enumerate(self.app.nav_buttons):
            button.invoke()
            self.app.update()
            self.assertEqual(self.app.tabs.index(self.app.tabs.select()), index)
            self.assertEqual(button.cget("style"), "Selected.Nav.TButton")
            self.assertTrue(self.app.page_title.get())

    def test_minimum_window_fits_workspaces(self):
        self.app._load_definitions(os.path.join(app_dir(), "sim_kodlama_ornek.json"))
        self.app.coding_tree.selection_set("0")
        self.app._on_coding_select()
        self.app.geometry("1160x740")
        for index in range(len(self.app.nav_buttons)):
            self.app.tabs.select(index)
            self.app.update()
            page = self.app.nametowidget(self.app.tabs.select())
            with self.subTest(page=index):
                self.assertLessEqual(page.winfo_reqwidth(), page.winfo_width())
                self.assertLessEqual(page.winfo_reqheight(), page.winfo_height())

    def test_ev_mode_hides_engine_rows_and_excludes_engine_candidates(self):
        self.assertTrue(self.app.is_ev)
        self.assertEqual(self.app.live_tree.get_children(), ())
        self.assertNotIn(0x12, self.app._candidate_ecus())
        self.assertIn(0x07, self.app._candidate_ecus())
        self.app.is_ev = False
        self.app._configure_vehicle_view()
        self.assertTrue(self.app.live_tree.get_children())
        self.assertIn(0x12, self.app._candidate_ecus())
