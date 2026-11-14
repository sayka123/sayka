import unittest
from unittest.mock import Mock
try:
    import tkinter as tk
    from tkinter import ttk
    from bimmertool import theme
    from bimmertool.gui import App
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class ThemeDesktop(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.app.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app.theme_mode.set('Koyu')
            self.app.on_theme_change()
            self.app._on_close()

    def test_light_dark_preserves_ui_state_and_never_contacts_vehicle(self):
        self.app.uds = Mock()
        self.app.ip_var.set('169.254.1.2')
        self.app.tabs.select(7)
        for label, palette in [('Açık', theme.LIGHT), ('Koyu', theme.DARK), ('Açık', theme.LIGHT)]:
            self.app.theme_mode.set(label)
            self.app.on_theme_change()
            self.app.update()
            self.assertEqual(self.app.cget('background'), palette['BG'])
            self.assertEqual(ttk.Style(self.app).lookup('Treeview', 'foreground'), palette['TEXT'])
            self.assertEqual(self.app.trend_canvas.cget('background'), palette['PANEL'])
            self.assertEqual(self.app.ip_var.get(), '169.254.1.2')
            self.assertEqual(self.app.tabs.index(self.app.tabs.select()), 7)
        self.assertEqual(self.app.uds.mock_calls, [])
