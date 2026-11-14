import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch
try:
    import tkinter as tk
    from bimmertool.gui import App
    from bimmertool.features_gui import FEATURES
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Tkinter unavailable')
class FeatureChecklist(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.app.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            self.app._on_close()

    def test_manual_observation_export_never_calls_vehicle(self):
        self.app.uds = Mock()
        self.app.nav_buttons[9].invoke()
        self.app.features_tree.selection_set('maps')
        self.app._select_feature()
        self.app.feature_observation.set('Menüde yok')
        self.app._save_feature_observation()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, 'features.json')
            with patch('bimmertool.features_gui.filedialog.asksaveasfilename', return_value=target):
                self.app.on_export_features()
            with open(target, encoding='utf-8') as file:
                data = json.load(file)
        self.assertFalse(data['activation_performed'])
        self.assertFalse(data['vehicle_verified'])
        self.assertEqual(len(data['items']), len(FEATURES))
        self.assertEqual(next(row for row in data['items'] if row['key'] == 'maps')['observation'], 'Menüde yok')
        self.assertEqual(self.app.uds.mock_calls, [])
        self.app._reset_feature_observations()
        self.assertEqual(self.app.feature_notes['maps'], 'Bilinmiyor')
