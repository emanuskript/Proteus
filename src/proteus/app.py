"""Application entry point."""

import sys
import cv2
from PySide6.QtWidgets import QApplication
from proteus.ui.main_window import ProteusMainWindow
from proteus.ui.theme import apply_dark_theme


def main():
    try:
        cv2.setNumThreads(0)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Proteus")
    app.setOrganizationName("Proteus")

    apply_dark_theme(app)

    window = ProteusMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
