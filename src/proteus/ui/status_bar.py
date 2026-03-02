"""Status bar widget."""

from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt


class StatusBar(QFrame):
    """Simple status bar displaying a single text label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #16213e; border-radius: 12px;")
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        self._label = QLabel("Ready: open an image to begin")
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self._label)

    def set_text(self, text: str) -> None:
        self._label.setText(text)
