import os
import unittest
from pathlib import Path
from unittest.mock import patch

from bimmertool.storage import data_dir


class UserStorage(unittest.TestCase):
    def test_mac_path_is_separate_from_application(self):
        with patch('bimmertool.storage.sys.platform', 'darwin'), patch('pathlib.Path.home', return_value=Path('/home/test')):
            self.assertEqual(data_dir(), Path('/home/test/Library/Application Support/BimmerTool'))

    def test_windows_and_xdg(self):
        with patch('bimmertool.storage.sys.platform', 'win32'), patch.dict(os.environ, {'LOCALAPPDATA': '/local'}):
            self.assertEqual(data_dir(), Path('/local/BimmerTool'))
        with patch('bimmertool.storage.sys.platform', 'linux'), patch.dict(os.environ, {'XDG_DATA_HOME': '/data'}):
            self.assertEqual(data_dir(), Path('/data/BimmerTool'))
