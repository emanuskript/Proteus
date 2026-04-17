"""Application entry point."""

import sys
from pathlib import Path

import cv2
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from proteus.core.utils import resource_path
from proteus.ui.main_window import ProteusMainWindow
from proteus.ui.theme import apply_theme


def main():
    try:
        cv2.setNumThreads(0)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Proteus")
    app.setOrganizationName("Proteus")

    icon_path = resource_path("Proteus.png")
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    apply_theme(app, "light")

    window = ProteusMainWindow()
    if Path(icon_path).exists():
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
