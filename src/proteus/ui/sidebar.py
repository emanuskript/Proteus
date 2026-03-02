"""Sidebar widget containing all tool buttons organized in collapsible sections.

Emits signals only — all logic is handled by the main window.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QHBoxLayout,
    QPushButton, QSlider, QLabel, QGridLayout
)
from PySide6.QtCore import Qt, Signal


# ---------------------------------------------------------------------------
# Collapsible section helper
# ---------------------------------------------------------------------------
class CollapsibleSection(QWidget):
    """A section with a clickable header that toggles content visibility."""

    def __init__(self, title: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._toggle = QPushButton(f"\u25BC  {title}" if expanded else f"\u25B6  {title}")
        self._toggle.setObjectName("sectionHeader")
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.clicked.connect(self._on_toggle)
        layout.addWidget(self._toggle)

        # Content container
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(4, 6, 4, 8)
        self._content_layout.setSpacing(6)
        self._content.setVisible(expanded)
        layout.addWidget(self._content)

        self._title = title
        self._expanded = expanded

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _on_toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        arrow = "\u25BC" if self._expanded else "\u25B6"
        self._toggle.setText(f"{arrow}  {self._title}")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
class SidebarWidget(QScrollArea):
    """Left sidebar with collapsible sections for Files, View, and Processing."""

    # Section 1: Files / History
    open_requested = Signal()
    save_requested = Signal()
    clear_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()

    # Section 2: View / Annotate  (zoom moved to bottom bar)
    mode_changed = Signal(str)
    brush_size_changed = Signal(int)
    clear_drawing_requested = Signal()
    clear_roi_requested = Signal()

    # Section 3: Image Processing
    pseudocolor_requested = Signal(str)
    pseudocolor_two_requested = Signal()
    sharpen_otsu_requested = Signal()
    sharpen_fixed_requested = Signal()
    power_requested = Signal()
    invert_requested = Signal()
    rotate_requested = Signal(str)
    blur_divide_requested = Signal()
    denoise_requested = Signal()
    pca_requested = Signal()
    pca_svd_requested = Signal()
    next_pc_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(270)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(4)
        self.setWidget(container)

        self._mode_buttons = {}
        self._sub_labels: list[QLabel] = []
        self._separators: list[QWidget] = []

        self._build_files_section()
        self._build_view_section()
        self._build_processing_section()
        self._layout.addStretch()

    # ------------------------------------------------------------------ Files
    def _build_files_section(self):
        section = CollapsibleSection("Files / History")
        lay = section.content_layout

        btn_open = QPushButton("Open Image")
        btn_open.setToolTip("Open an image (common formats)")
        btn_open.clicked.connect(self.open_requested)
        lay.addWidget(btn_open)

        btn_save = QPushButton("Save Current Image")
        btn_save.setToolTip("Save the current processed result (full resolution)")
        btn_save.clicked.connect(self.save_requested)
        lay.addWidget(btn_save)

        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("destructiveButton")
        btn_clear.setToolTip("Clear the current image and overlays")
        btn_clear.clicked.connect(self.clear_requested)
        lay.addWidget(btn_clear)

        hist = QHBoxLayout()
        hist.setSpacing(6)
        btn_undo = QPushButton("Undo")
        btn_undo.setToolTip("Undo one step (Ctrl+Z)")
        btn_undo.clicked.connect(self.undo_requested)
        btn_redo = QPushButton("Redo")
        btn_redo.setToolTip("Redo one step (Ctrl+Y)")
        btn_redo.clicked.connect(self.redo_requested)
        hist.addWidget(btn_undo)
        hist.addWidget(btn_redo)
        lay.addLayout(hist)

        self._layout.addWidget(section)

    # ---------------------------------------------------------- View / Annotate
    def _build_view_section(self):
        section = CollapsibleSection("View / Annotate")
        lay = section.content_layout

        # Mode buttons
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(6)
        for label, mode_key in [("Pan", "pan"), ("Brush", "draw"), ("ROI", "roi")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setToolTip({
                "pan": "Drag to pan the image",
                "draw": "Yellow highlight brush",
                "roi": "Select region of interest"
            }[mode_key])
            btn.clicked.connect(lambda checked, m=mode_key: self.mode_changed.emit(m))
            mode_layout.addWidget(btn)
            self._mode_buttons[mode_key] = btn
        self._mode_buttons["pan"].setChecked(True)
        lay.addLayout(mode_layout)

        # Brush size
        brush_row = QHBoxLayout()
        brush_row.setSpacing(8)
        brush_lbl = QLabel("Brush")
        brush_lbl.setObjectName("subCategoryLabel")
        self._sub_labels.append(brush_lbl)
        brush_row.addWidget(brush_lbl)
        self._brush_slider = QSlider(Qt.Horizontal)
        self._brush_slider.setRange(1, 5)
        self._brush_slider.setValue(3)
        self._brush_slider.setTickPosition(QSlider.TicksBelow)
        self._brush_slider.setTickInterval(1)
        self._brush_slider.valueChanged.connect(self.brush_size_changed)
        brush_row.addWidget(self._brush_slider, stretch=1)
        lay.addLayout(brush_row)

        # Clear buttons
        clear_row = QHBoxLayout()
        clear_row.setSpacing(6)
        btn_cd = QPushButton("Clear Drawing")
        btn_cd.setToolTip("Clear yellow highlights")
        btn_cd.clicked.connect(self.clear_drawing_requested)
        btn_cr = QPushButton("Clear ROI")
        btn_cr.setToolTip("Clear ROI selection")
        btn_cr.clicked.connect(self.clear_roi_requested)
        clear_row.addWidget(btn_cd)
        clear_row.addWidget(btn_cr)
        lay.addLayout(clear_row)

        self._layout.addWidget(section)

    # ------------------------------------------------------- Image Processing
    def _build_processing_section(self):
        section = CollapsibleSection("Image Processing")
        lay = section.content_layout

        # -- Pseudocolor
        sub_lbl = QLabel("Pseudocolor")
        sub_lbl.setObjectName("subCategoryLabel")
        self._sub_labels.append(sub_lbl)
        lay.addWidget(sub_lbl)

        pc_grid = QGridLayout()
        pc_grid.setSpacing(4)
        for i, (text, ch) in enumerate([("All", "all"), ("Red", "r"),
                                         ("Green", "g"), ("Blue", "b")]):
            btn = QPushButton(text)
            btn.setToolTip(f"Pseudocolor based on {'overall' if ch == 'all' else ch.upper() + ' channel'} intensity")
            btn.clicked.connect(lambda checked, c=ch: self.pseudocolor_requested.emit(c))
            pc_grid.addWidget(btn, i // 2, i % 2)
        lay.addLayout(pc_grid)

        btn_pc2 = QPushButton("Merge Two Images")
        btn_pc2.setToolTip("Select two images, blend 50/50, apply JET colormap")
        btn_pc2.clicked.connect(self.pseudocolor_two_requested)
        lay.addWidget(btn_pc2)

        # -- Sharpen
        self._add_separator(lay)
        sub_lbl2 = QLabel("Sharpen / Binarize")
        sub_lbl2.setObjectName("subCategoryLabel")
        self._sub_labels.append(sub_lbl2)
        lay.addWidget(sub_lbl2)

        sharp = QHBoxLayout()
        sharp.setSpacing(4)
        btn_otsu = QPushButton("Otsu")
        btn_otsu.setToolTip("Auto-threshold binarization (Otsu)")
        btn_otsu.clicked.connect(self.sharpen_otsu_requested)
        btn_fix = QPushButton("Fixed 128")
        btn_fix.setToolTip("Fixed threshold binarization at 128")
        btn_fix.clicked.connect(self.sharpen_fixed_requested)
        sharp.addWidget(btn_otsu)
        sharp.addWidget(btn_fix)
        lay.addLayout(sharp)

        # -- Enhance
        self._add_separator(lay)
        sub_lbl3 = QLabel("Enhance")
        sub_lbl3.setObjectName("subCategoryLabel")
        self._sub_labels.append(sub_lbl3)
        lay.addWidget(sub_lbl3)

        btn_pow = QPushButton("Power (Gamma)")
        btn_pow.setToolTip("Gamma/power transform with optional partial inversion")
        btn_pow.clicked.connect(self.power_requested)
        lay.addWidget(btn_pow)

        btn_inv = QPushButton("Invert")
        btn_inv.setToolTip("Invert image with alpha blending")
        btn_inv.clicked.connect(self.invert_requested)
        lay.addWidget(btn_inv)

        enhance_row = QHBoxLayout()
        enhance_row.setSpacing(4)
        btn_bd = QPushButton("Blur && Divide")
        btn_bd.setToolTip("Divide by Gaussian blur, normalize, equalize")
        btn_bd.clicked.connect(self.blur_divide_requested)
        btn_dn = QPushButton("Denoise")
        btn_dn.setToolTip("Gaussian denoise filter")
        btn_dn.clicked.connect(self.denoise_requested)
        enhance_row.addWidget(btn_bd)
        enhance_row.addWidget(btn_dn)
        lay.addLayout(enhance_row)

        # -- Transform
        rot = QHBoxLayout()
        rot.setSpacing(4)
        btn_rl = QPushButton("Rotate \u2190 90\u00b0")
        btn_rl.clicked.connect(lambda: self.rotate_requested.emit("left"))
        btn_rr = QPushButton("Rotate \u2192 90\u00b0")
        btn_rr.clicked.connect(lambda: self.rotate_requested.emit("right"))
        rot.addWidget(btn_rl)
        rot.addWidget(btn_rr)
        lay.addLayout(rot)

        # -- PCA
        self._add_separator(lay)
        sub_lbl4 = QLabel("PCA")
        sub_lbl4.setObjectName("subCategoryLabel")
        self._sub_labels.append(sub_lbl4)
        lay.addWidget(sub_lbl4)

        pca_row = QHBoxLayout()
        pca_row.setSpacing(4)
        btn_pca = QPushButton("PCA")
        btn_pca.setToolTip("Principal Component Analysis (3-16 images)")
        btn_pca.clicked.connect(self.pca_requested)
        btn_svd = QPushButton("PCA-SVD")
        btn_svd.setToolTip("PCA SVD variant (3-16 images)")
        btn_svd.clicked.connect(self.pca_svd_requested)
        pca_row.addWidget(btn_pca)
        pca_row.addWidget(btn_svd)
        lay.addLayout(pca_row)

        btn_next = QPushButton("Next PC")
        btn_next.setToolTip("Cycle through principal components (run PCA first)")
        btn_next.clicked.connect(self.next_pc_requested)
        lay.addWidget(btn_next)

        self._layout.addWidget(section)

    # ---------------------------------------------------------------- Helpers
    def _add_separator(self, layout: QVBoxLayout):
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setObjectName("separator")
        self._separators.append(sep)
        layout.addWidget(sep)

    def highlight_mode(self, mode: str) -> None:
        """Visually highlight the active mode button."""
        for key, btn in self._mode_buttons.items():
            btn.setChecked(key == mode)

    def set_theme(self, theme_name: str) -> None:
        """Update inline-styled elements for the current theme."""
        from proteus.ui.theme import get_separator_color
        sep_color = get_separator_color(theme_name)
        for sep in self._separators:
            sep.setStyleSheet(f"background-color: {sep_color};")
