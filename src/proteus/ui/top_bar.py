"""Top application bar with logo and theme toggle."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from proteus.ui.qt_image import load_scaled_resource_pixmap
from proteus.ui.theme import THEME_INFO, next_theme


class TopBar(QFrame):
    """Slim header bar: logo on the left, theme toggle on the right."""

    theme_toggle_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self._brand = QLabel()
        self._brand.setObjectName("appLogo")
        self._brand.setToolTip("Proteus")
        self._brand.setAlignment(Qt.AlignCenter)
        self._brand.setFixedSize(40, 40)
        brand_pixmap = load_scaled_resource_pixmap("Proteus-logo.png", 32)
        if not brand_pixmap.isNull():
            self._brand.setPixmap(brand_pixmap)
        layout.addWidget(self._brand)

        if self._brand.pixmap() is None or self._brand.pixmap().isNull():
            self._brand_fallback = QLabel("Proteus")
            self._brand_fallback.setObjectName("appLogoText")
            layout.addWidget(self._brand_fallback)

        layout.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton()
        self._theme_btn.setObjectName("themeToggle")
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.setFixedSize(36, 36)
        self._theme_btn.clicked.connect(self.theme_toggle_clicked)
        layout.addWidget(self._theme_btn)

        self._current_theme = "light"
        self._update_theme_button("light")

    def _update_theme_button(self, theme_name: str) -> None:
        info = THEME_INFO.get(theme_name, THEME_INFO["light"])
        label, icon = info
        nxt = next_theme(theme_name)
        nxt_label = THEME_INFO.get(nxt, THEME_INFO["light"])[0]
        self._theme_btn.setText(icon)
        self._theme_btn.setToolTip(f"Current: {label} — click for {nxt_label}")

    def set_theme(self, theme_name: str) -> None:
        """Update the toggle button for the current theme."""
        self._current_theme = theme_name
        self._update_theme_button(theme_name)
