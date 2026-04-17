"""Utility functions - no UI or heavy library dependencies."""

import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """Return absolute path to a resource, in dev and PyInstaller builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_root = Path(sys._MEIPASS)
        direct = bundle_root / relative_path
        if direct.exists():
            return str(direct)

        packaged = bundle_root / "proteus" / "resources" / relative_path
        if packaged.exists():
            return str(packaged)

        return str(direct)

    return str(Path(__file__).resolve().parent.parent / "resources" / relative_path)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v
