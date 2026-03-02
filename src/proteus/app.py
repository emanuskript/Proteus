"""Application entry point."""

import sys
import cv2
from PySide6.QtWidgets import QApplication
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

    # Apply default light theme; main window will load saved preference
    apply_theme(app, "light")

    window = ProteusMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
