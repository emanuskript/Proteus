"""Utility functions - no UI or heavy library dependencies."""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Return absolute path to a resource, works in dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', relative_path)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v
