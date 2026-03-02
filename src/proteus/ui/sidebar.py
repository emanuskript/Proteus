"""Sidebar widget containing all tool buttons organized in 3 sections.

Emits signals only — all logic is handled by the main window.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QHBoxLayout,
    QPushButton, QSlider, QLabel, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from proteus.core.utils import resource_path


class SidebarWidget(QScrollArea):
    """Left sidebar with Files/History, View/Annotate, and Image Processing sections."""

    # Section 1: Files / History
    open_requested = Signal()
    save_requested = Signal()
    clear_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()

    # Section 2: View / Annotate
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
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
        self.setFixedWidth(290)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)
        self.setWidget(container)

        self._mode_buttons = {}

        self._build_title()
        self._build_files_section()
        self._build_view_section()
        self._build_processing_section()
        self._layout.addStretch()

    def _build_title(self):
        title_frame = QHBoxLayout()
        title_frame.setContentsMargins(0, 0, 0, 4)

        # Try to load logo
        try:
            logo_path = resource_path("Proteus.png")
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo_label = QLabel()
                logo_label.setPixmap(pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                title_frame.addWidget(logo_label)
        except Exception:
            pass

        title_label = QLabel("Proteus Toolbox")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_frame.addWidget(title_label)
        title_frame.addStretch()
        self._layout.addLayout(title_frame)

    def _build_files_section(self):
        group = QGroupBox("Files / History")
        layout = QVBoxLayout()

        btn_open = QPushButton("Open Image")
        btn_open.setToolTip("Open an image (common formats)")
        btn_open.clicked.connect(self.open_requested)
        layout.addWidget(btn_open)

        btn_save = QPushButton("Save Current Image")
        btn_save.setToolTip("Save the current processed result (full resolution)")
        btn_save.clicked.connect(self.save_requested)
        layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("destructiveButton")
        btn_clear.setToolTip("Clear the current image and overlays")
        btn_clear.clicked.connect(self.clear_requested)
        layout.addWidget(btn_clear)

        hist_layout = QHBoxLayout()
        btn_undo = QPushButton("Undo")
        btn_undo.setToolTip("Undo one step (Ctrl+Z)")
        btn_undo.clicked.connect(self.undo_requested)
        btn_redo = QPushButton("Redo")
        btn_redo.setToolTip("Redo one step (Ctrl+Y)")
        btn_redo.clicked.connect(self.redo_requested)
        hist_layout.addWidget(btn_undo)
        hist_layout.addWidget(btn_redo)
        layout.addLayout(hist_layout)

        group.setLayout(layout)
        self._layout.addWidget(group)

    def _build_view_section(self):
        group = QGroupBox("View / Annotate")
        layout = QVBoxLayout()

        # Zoom buttons
        zoom_layout = QHBoxLayout()
        for text, signal in [("Zoom In +", self.zoom_in_requested),
                              ("Zoom Out -", self.zoom_out_requested),
                              ("Reset 0", self.zoom_reset_requested)]:
            btn = QPushButton(text)
            btn.clicked.connect(signal)
            zoom_layout.addWidget(btn)
        layout.addLayout(zoom_layout)

        # Mode buttons
        mode_layout = QHBoxLayout()
        for label, mode_key in [("Pan", "pan"), ("Brush", "draw"), ("ROI", "roi")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setToolTip({
                "pan": "Drag to pan",
                "draw": "Yellow highlight (erasable)",
                "roi": "Select ROI (for PCA, etc.)"
            }[mode_key])
            btn.clicked.connect(lambda checked, m=mode_key: self.mode_changed.emit(m))
            mode_layout.addWidget(btn)
            self._mode_buttons[mode_key] = btn
        self._mode_buttons["pan"].setChecked(True)
        layout.addLayout(mode_layout)

        # Brush size slider
        brush_label = QLabel("Brush Size (1-5)")
        layout.addWidget(brush_label)
        self._brush_slider = QSlider(Qt.Horizontal)
        self._brush_slider.setRange(1, 5)
        self._brush_slider.setValue(3)
        self._brush_slider.setTickPosition(QSlider.TicksBelow)
        self._brush_slider.setTickInterval(1)
        self._brush_slider.valueChanged.connect(self.brush_size_changed)
        layout.addWidget(self._brush_slider)

        btn_clear_draw = QPushButton("Clear Drawing")
        btn_clear_draw.setToolTip("Clear yellow highlights (does not affect the image)")
        btn_clear_draw.clicked.connect(self.clear_drawing_requested)
        layout.addWidget(btn_clear_draw)

        btn_clear_roi = QPushButton("Clear ROI")
        btn_clear_roi.setToolTip("Clear ROI selection")
        btn_clear_roi.clicked.connect(self.clear_roi_requested)
        layout.addWidget(btn_clear_roi)

        group.setLayout(layout)
        self._layout.addWidget(group)

    def _build_processing_section(self):
        group = QGroupBox("Image Processing")
        layout = QVBoxLayout()

        # Pseudocolor grid
        pc_grid = QGridLayout()
        for i, (text, ch) in enumerate([("Pseudocolor-All", "all"), ("Pseudocolor-R", "r"),
                                         ("Pseudocolor-G", "g"), ("Pseudocolor-B", "b")]):
            btn = QPushButton(text)
            btn.setToolTip(f"Pseudocolor ({ch.upper()}): based on {'overall' if ch == 'all' else ch.upper() + ' channel'} intensity")
            btn.clicked.connect(lambda checked, c=ch: self.pseudocolor_requested.emit(c))
            pc_grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(pc_grid)

        btn_pc2 = QPushButton("Pseudocolor (Merge Two Images)")
        btn_pc2.setToolTip("Select two grayscale images, merge them, then apply JET")
        btn_pc2.clicked.connect(self.pseudocolor_two_requested)
        layout.addWidget(btn_pc2)

        # Sharpen
        sharp_layout = QHBoxLayout()
        btn_otsu = QPushButton("Sharpen(Otsu)")
        btn_otsu.setToolTip("Sharpen: Otsu automatic threshold")
        btn_otsu.clicked.connect(self.sharpen_otsu_requested)
        btn_fix = QPushButton("Sharpen(128)")
        btn_fix.setToolTip("Sharpen: fixed threshold 128")
        btn_fix.clicked.connect(self.sharpen_fixed_requested)
        sharp_layout.addWidget(btn_otsu)
        sharp_layout.addWidget(btn_fix)
        layout.addLayout(sharp_layout)

        # Power, Invert
        btn_pow = QPushButton("Power (Gamma)")
        btn_pow.setToolTip("Gamma/power transform + optional partial inversion")
        btn_pow.clicked.connect(self.power_requested)
        layout.addWidget(btn_pow)

        btn_inv = QPushButton("Invert")
        btn_inv.clicked.connect(self.invert_requested)
        layout.addWidget(btn_inv)

        # Rotate
        rot_layout = QHBoxLayout()
        btn_rl = QPushButton("Rotate Left 90\u00b0")
        btn_rl.clicked.connect(lambda: self.rotate_requested.emit("left"))
        btn_rr = QPushButton("Rotate Right 90\u00b0")
        btn_rr.clicked.connect(lambda: self.rotate_requested.emit("right"))
        rot_layout.addWidget(btn_rl)
        rot_layout.addWidget(btn_rr)
        layout.addLayout(rot_layout)

        # Blur & Divide, Denoise
        btn_bd = QPushButton("Blur && Divide")
        btn_bd.setToolTip("Divide after Gaussian blur + normalize + equalize")
        btn_bd.clicked.connect(self.blur_divide_requested)
        layout.addWidget(btn_bd)

        btn_dn = QPushButton("Denoise (Gaussian)")
        btn_dn.clicked.connect(self.denoise_requested)
        layout.addWidget(btn_dn)

        # PCA
        pca_layout = QHBoxLayout()
        btn_pca = QPushButton("PCA")
        btn_pca.setToolTip("Select multiple grayscale images for PCA (3-16 images)")
        btn_pca.clicked.connect(self.pca_requested)
        btn_svd = QPushButton("PCA-SVD")
        btn_svd.setToolTip("PCA SVD variant (3-16 images)")
        btn_svd.clicked.connect(self.pca_svd_requested)
        btn_next = QPushButton("Next PC")
        btn_next.setToolTip("Cycle PC1/PC2/... (run PCA or PCA-SVD first)")
        btn_next.clicked.connect(self.next_pc_requested)
        pca_layout.addWidget(btn_pca)
        pca_layout.addWidget(btn_svd)
        pca_layout.addWidget(btn_next)
        layout.addLayout(pca_layout)

        group.setLayout(layout)
        self._layout.addWidget(group)

    def highlight_mode(self, mode: str) -> None:
        """Visually highlight the active mode button."""
        for key, btn in self._mode_buttons.items():
            btn.setChecked(key == mode)
