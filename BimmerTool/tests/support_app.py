"""Test-only injection; never included in the user bundle."""
from dataclasses import replace
from unittest.mock import patch
from bimmertool import ev
from bimmertool.gui import App


class ProfileTestApp(App):
    def _set_ev_profile(self, path):
        profile = ev.load_profile(path)
        if profile.simulator_only and not self._connection_demo:
            raise ValueError('Test source mismatch')
        with patch('bimmertool.ev_gui.ev.load_profile', return_value=replace(profile, simulator_only=False)):
            super()._set_ev_profile(path)
