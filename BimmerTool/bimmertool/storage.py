"""Writable user data, separate from application and downloaded source files."""

import os
import sys
from pathlib import Path


def data_dir():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BimmerTool"
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "BimmerTool"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "BimmerTool"
