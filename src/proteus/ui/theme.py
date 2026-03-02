"""Dark theme configuration matching the original dark-blue scheme."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


DARK_STYLESHEET = """
QMainWindow {
    background-color: #1a1a2e;
}

QGroupBox {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 8px;
    color: #cccccc;
}

QPushButton {
    background-color: #1a5276;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2874a6;
}

QPushButton:pressed {
    background-color: #1b4f72;
}

QPushButton:checked {
    background-color: #2b6cb0;
    border: 1px solid #5dade2;
}

QPushButton#destructiveButton {
    background-color: #7a1f1f;
}

QPushButton#destructiveButton:hover {
    background-color: #9a2a2a;
}

QScrollArea {
    background-color: #0f3460;
    border: none;
    border-radius: 12px;
}

QScrollArea > QWidget > QWidget {
    background-color: #0f3460;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #333;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2874a6;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QLabel {
    color: #e0e0e0;
    font-size: 13px;
}

QToolTip {
    background-color: #222;
    color: #fff;
    border: 1px solid #555;
    padding: 5px 8px;
    font-size: 12px;
}

QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
}

QCheckBox {
    color: #e0e0e0;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #2b6cb0;
    border-color: #5dade2;
}

QDialog {
    background-color: #1a1a2e;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

QScrollBar:vertical {
    background: #0f3460;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2874a6;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def apply_dark_theme(app: QApplication) -> None:
    """Apply the dark theme palette and stylesheet to the application."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1a1a2e"))
    palette.setColor(QPalette.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Base, QColor("#16213e"))
    palette.setColor(QPalette.AlternateBase, QColor("#1a1a2e"))
    palette.setColor(QPalette.ToolTipBase, QColor("#222222"))
    palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.Button, QColor("#1a5276"))
    palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#2b6cb0"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(DARK_STYLESHEET)
