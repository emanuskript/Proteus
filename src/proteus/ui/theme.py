"""Theme configuration for Proteus.

Three themes matching the QuillApp suite design language:
  - Light:         neutral grays, blue accent, ghost buttons
  - Dark:          dark neutrals, brighter blue accent
  - High Contrast: pure black/white, maximum readability
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


# ---------------------------------------------------------------------------
# Colour token sets   { key: (light, dark, high_contrast) }
# ---------------------------------------------------------------------------
_TOKENS = {
    "bg":              ("#fafafa",  "#171717",  "#000000"),
    "card":            ("#ffffff",  "#222222",  "#000000"),
    "border":          ("#e2e2e2",  "#333333",  "#ffffff"),
    "border_light":    ("#efefef",  "#2a2a2a",  "#cccccc"),
    "text":            ("#1a1a1a",  "#f2f2f2",  "#ffffff"),
    "text_sec":        ("#6b7280",  "#9ca3af",  "#cccccc"),
    "accent":          ("#2563eb",  "#3b82f6",  "#5ca0ff"),
    "accent_hover":    ("#1d4ed8",  "#2563eb",  "#4090f0"),
    "accent_light":    ("rgba(37,99,235,0.08)",  "rgba(59,130,246,0.12)", "rgba(92,160,255,0.18)"),
    "accent_border":   ("rgba(37,99,235,0.35)",  "rgba(59,130,246,0.45)", "rgba(92,160,255,0.6)"),
    "destructive":     ("#dc2626",  "#ef4444",  "#ff4444"),
    "canvas_bg":       ("#e5e7eb",  "#111111",  "#1a1a1a"),
    "muted":           ("#f3f4f6",  "#2a2a2a",  "#1a1a1a"),
    "scrollbar":       ("#c4c4c4",  "#555555",  "#666666"),
    "tooltip_bg":      ("#1a1a1a",  "#f5f5f5",  "#ffffff"),
    "tooltip_fg":      ("#ffffff",  "#1a1a1a",  "#000000"),
    "input_bg":        ("#ffffff",  "#1e1e1e",  "#111111"),
    "pressed":         ("#e5e5e5",  "#3a3a3a",  "#333333"),
    "hover":           ("#d0d0d0",  "#444444",  "#555555"),
    "separator":       ("#e5e7eb",  "#2e2e2e",  "#444444"),
    "checked_text":    ("#2563eb",  "#60a5fa",  "#7fbfff"),
    "destr_border":    ("rgba(220,38,38,0.3)",  "rgba(239,68,68,0.35)", "rgba(255,68,68,0.5)"),
    "destr_hover":     ("rgba(220,38,38,0.06)", "rgba(239,68,68,0.1)",  "rgba(255,68,68,0.15)"),
    "destr_hover_bdr": ("rgba(220,38,38,0.5)",  "rgba(239,68,68,0.5)",  "rgba(255,68,68,0.7)"),
}

THEME_NAMES = ("light", "dark", "high-contrast")


def _tok(name: str, theme_index: int) -> str:
    return _TOKENS[name][theme_index]


def _build_stylesheet(i: int) -> str:
    """Build a complete stylesheet from the token set at index *i*."""
    t = {k: v[i] for k, v in _TOKENS.items()}
    return f"""
/* ---- Global ---- */
QMainWindow {{
    background-color: {t['bg']};
}}

/* ---- Sidebar, cards, panels ---- */
QGroupBox {{
    background-color: {t['card']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    margin-top: 6px;
    padding: 14px 10px 10px 10px;
    font-size: 12px;
    font-weight: 600;
    color: {t['text_sec']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 8px;
    color: {t['text_sec']};
}}

/* ---- Buttons (ghost style) ---- */
QPushButton {{
    background-color: transparent;
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {t['muted']};
    border-color: {t['hover']};
}}
QPushButton:pressed {{
    background-color: {t['pressed']};
}}
QPushButton:checked {{
    background-color: {t['accent_light']};
    border-color: {t['accent_border']};
    color: {t['checked_text']};
    font-weight: 600;
}}
QPushButton:disabled {{
    opacity: 0.5;
    color: {t['text_sec']};
}}

/* ---- Destructive / Clear button ---- */
QPushButton#destructiveButton {{
    color: {t['destructive']};
    border-color: {t['destr_border']};
}}
QPushButton#destructiveButton:hover {{
    background-color: {t['destr_hover']};
    border-color: {t['destr_hover_bdr']};
}}

/* ---- Scroll areas ---- */
QScrollArea {{
    background-color: {t['bg']};
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: {t['bg']};
}}

/* ---- Sliders ---- */
QSlider::groove:horizontal {{
    height: 4px;
    background: {t['border']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t['accent']};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}

/* ---- Labels ---- */
QLabel {{
    color: {t['text']};
    font-size: 13px;
}}

/* ---- Tooltips ---- */
QToolTip {{
    background-color: {t['tooltip_bg']};
    color: {t['tooltip_fg']};
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ---- Spinboxes ---- */
QSpinBox, QDoubleSpinBox {{
    background-color: {t['input_bg']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {t['accent']};
}}

/* ---- Line edits ---- */
QLineEdit {{
    background-color: {t['input_bg']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {t['accent']};
}}

/* ---- Checkboxes ---- */
QCheckBox {{
    color: {t['text']};
    font-size: 13px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {t['border']};
    border-radius: 4px;
    background-color: {t['input_bg']};
}}
QCheckBox::indicator:checked {{
    background-color: {t['accent']};
    border-color: {t['accent']};
}}

/* ---- Dialogs ---- */
QDialog {{
    background-color: {t['bg']};
}}
QDialogButtonBox QPushButton {{
    min-width: 80px;
    background-color: {t['accent']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
}}
QDialogButtonBox QPushButton:hover {{
    background-color: {t['accent_hover']};
}}

/* ---- Scrollbars ---- */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {t['scrollbar']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {t['scrollbar']};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ---- Collapsible section headers ---- */
QPushButton#sectionHeader {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
    font-weight: 600;
    color: {t['text_sec']};
    text-align: left;
}}
QPushButton#sectionHeader:hover {{
    background-color: {t['muted']};
}}

/* ---- Top bar ---- */
QFrame#topBar {{
    background-color: {t['card']};
    border-bottom: 1px solid {t['border']};
}}

/* ---- Bottom bar ---- */
QFrame#bottomBar {{
    background-color: {t['card']};
    border-top: 1px solid {t['border']};
}}
QFrame#bottomBar QPushButton {{
    border: none;
    padding: 4px 8px;
    font-size: 12px;
    min-width: 0;
}}
QFrame#bottomBar QLabel {{
    font-size: 12px;
    color: {t['text_sec']};
}}

/* ---- Theme toggle button ---- */
QPushButton#themeToggle {{
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 18px;
    min-width: 0;
}}
QPushButton#themeToggle:hover {{
    background-color: {t['muted']};
}}

/* ---- Sub-category labels in sidebar ---- */
QLabel#subCategoryLabel {{
    font-size: 11px;
    font-weight: 600;
    color: {t['text_sec']};
}}
"""


# Pre-built stylesheets
LIGHT_STYLESHEET = _build_stylesheet(0)
DARK_STYLESHEET = _build_stylesheet(1)
HIGH_CONTRAST_STYLESHEET = _build_stylesheet(2)

_STYLESHEETS = {
    "light": LIGHT_STYLESHEET,
    "dark": DARK_STYLESHEET,
    "high-contrast": HIGH_CONTRAST_STYLESHEET,
}

# Theme display info: (label, icon_char)
THEME_INFO = {
    "light":         ("Light",         "\u2600"),   # ☀
    "dark":          ("Dark",          "\u263E"),   # ☾
    "high-contrast": ("High Contrast", "\u25D1"),   # ◑
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _build_palette(i: int) -> QPalette:
    """Build a QPalette from the token set at index *i*."""
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(_tok("bg", i)))
    palette.setColor(QPalette.WindowText,      QColor(_tok("text", i)))
    palette.setColor(QPalette.Base,            QColor(_tok("input_bg", i)))
    palette.setColor(QPalette.AlternateBase,   QColor(_tok("muted", i)))
    palette.setColor(QPalette.ToolTipBase,     QColor(_tok("tooltip_bg", i)))
    palette.setColor(QPalette.ToolTipText,     QColor(_tok("tooltip_fg", i)))
    palette.setColor(QPalette.Text,            QColor(_tok("text", i)))
    palette.setColor(QPalette.Button,          QColor(_tok("card", i)))
    palette.setColor(QPalette.ButtonText,      QColor(_tok("text", i)))
    palette.setColor(QPalette.Highlight,       QColor(_tok("accent", i)))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor(_tok("text_sec", i)))
    return palette


def apply_theme(app: QApplication, name: str) -> None:
    """Apply the named theme (light, dark, or high-contrast)."""
    idx = THEME_NAMES.index(name) if name in THEME_NAMES else 0
    app.setPalette(_build_palette(idx))
    app.setStyleSheet(_STYLESHEETS.get(name, LIGHT_STYLESHEET))


def get_canvas_bg(name: str) -> str:
    """Return the canvas background colour for the given theme."""
    idx = THEME_NAMES.index(name) if name in THEME_NAMES else 0
    return _tok("canvas_bg", idx)


def get_text_color(name: str) -> str:
    """Return the primary text colour for the given theme."""
    idx = THEME_NAMES.index(name) if name in THEME_NAMES else 0
    return _tok("text", idx)


def get_separator_color(name: str) -> str:
    """Return the separator colour for the given theme."""
    idx = THEME_NAMES.index(name) if name in THEME_NAMES else 0
    return _tok("separator", idx)


def get_text_sec_color(name: str) -> str:
    """Return the secondary text colour for the given theme."""
    idx = THEME_NAMES.index(name) if name in THEME_NAMES else 0
    return _tok("text_sec", idx)


def next_theme(current: str) -> str:
    """Return the next theme name in the cycle."""
    idx = THEME_NAMES.index(current) if current in THEME_NAMES else 0
    return THEME_NAMES[(idx + 1) % len(THEME_NAMES)]


# Backwards compat
def apply_light_theme(app: QApplication) -> None:
    apply_theme(app, "light")


def apply_dark_theme(app: QApplication) -> None:
    apply_theme(app, "dark")
