"""Bottom bar with status text (left) and zoom controls (right)."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal


class StatusBar(QFrame):
    """Bottom bar: status message on the left, zoom controls on the right."""

    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    zoom_reset_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bottomBar")
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(6)

        # Left: status text
        self._label = QLabel("Ready")
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self._label, stretch=1)

        # Right: zoom controls
        btn_out = QPushButton("\u2212")  # minus sign
        btn_out.setToolTip("Zoom out")
        btn_out.setFixedSize(26, 26)
        btn_out.clicked.connect(self.zoom_out_clicked)
        layout.addWidget(btn_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setFixedWidth(48)
        self._zoom_label.setStyleSheet("font-weight: 500;")
        layout.addWidget(self._zoom_label)

        btn_in = QPushButton("+")
        btn_in.setToolTip("Zoom in")
        btn_in.setFixedSize(26, 26)
        btn_in.clicked.connect(self.zoom_in_clicked)
        layout.addWidget(btn_in)

        btn_reset = QPushButton("Reset")
        btn_reset.setToolTip("Reset zoom to 100%")
        btn_reset.clicked.connect(self.zoom_reset_clicked)
        layout.addWidget(btn_reset)

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def set_zoom_level(self, factor: float) -> None:
        self._zoom_label.setText(f"{factor * 100:.0f}%")
