"""Main application window - orchestrates sidebar, canvas, and core logic."""

import os

import numpy as np
import cv2
from PySide6.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QUndoStack, QShortcut, QKeySequence

from proteus.core.processing import (
    ensure_gray, ensure_color, to_uint8,
    pseudocolor_jet, otsu_binarize, fixed_binarize, unsharp_mask,
    power_transform, blur_divide, denoise_gaussian, rotate_90,
)
from proteus.core.pca import pca_multiband, pca_multiband_svd_variant
from proteus.core.image_io import load_image, load_as_gray, save_image
from proteus.core.state import ImageState, OperationLog
from proteus.core.utils import clamp

from proteus.ui.canvas import ImageCanvas
from proteus.ui.sidebar import SidebarWidget
from proteus.ui.status_bar import StatusBar
from proteus.ui.top_bar import TopBar
from proteus.ui.dialogs import GammaDialog, InvertDialog, BlurDivideDialog, DenoiseDialog, ThresholdDialog, BandLabelDialog
from proteus.commands.undo_commands import ImageOperationCommand, DrawStrokeCommand, RoiChangeCommand

IMAGE_FILTER = "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*.*)"


class ProteusMainWindow(QMainWindow):
    """Main application window. Owns all state and coordinates components."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proteus")
        self.resize(1200, 760)
        self.showMaximized()

        # ---- State ----
        self.img: np.ndarray | None = None
        self.draw_mask: np.ndarray | None = None
        self.roi: tuple | None = None
        self.brush_size: int = 3
        self._pc_cache: dict | None = None
        self._pc_index: int = 0
        self._band_labels: tuple | None = None
        self.ops_log = OperationLog()

        # For brush undo: snapshot mask at stroke start
        self._mask_before_draw: np.ndarray | None = None

        # For ROI undo: snapshot ROI at drag start
        self._roi_before: tuple | None = None

        # Undo stack
        self._undo_stack = QUndoStack(self)

        # ---- Build UI ----
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Content area: sidebar + canvas + bottom bar
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.top_bar = TopBar()
        left_layout.addWidget(self.top_bar)

        self.sidebar = SidebarWidget()
        self.top_bar.setFixedWidth(self.sidebar.minimumWidth())
        left_layout.addWidget(self.sidebar, stretch=1)

        content.addWidget(left)

        # Right column: canvas + bottom bar
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.canvas = ImageCanvas()
        right_layout.addWidget(self.canvas, stretch=1)

        self.status_bar = StatusBar()
        right_layout.addWidget(self.status_bar)

        content.addWidget(right, stretch=1)
        outer.addLayout(content)

        # ---- Connect signals ----
        self._connect_sidebar()
        self._connect_canvas()
        self._connect_bottom_bar()
        self._connect_shortcuts()

        # ---- Theme ----
        self._current_theme = "light"
        self.top_bar.theme_toggle_clicked.connect(self._cycle_theme)
        self._load_saved_theme()

        self.set_status("Ready: open an image to begin")

    # ---- Signal wiring ----

    def _connect_sidebar(self):
        s = self.sidebar
        s.open_requested.connect(self.open_image)
        s.save_requested.connect(self.save_image)
        s.clear_requested.connect(self.clear_image)
        s.undo_requested.connect(self._undo_stack.undo)
        s.redo_requested.connect(self._undo_stack.redo)

        s.mode_changed.connect(self._on_mode_changed)
        s.brush_size_changed.connect(self._on_brush_size_changed)
        s.clear_drawing_requested.connect(self.clear_drawing)
        s.clear_roi_requested.connect(self.clear_roi)

        s.pseudocolor_requested.connect(self.apply_pseudocolor_channel)
        s.pseudocolor_two_requested.connect(self.apply_pseudocolor_two)
        s.sharpen_original_requested.connect(self.apply_sharpen_original)
        s.sharpen_bw_auto_requested.connect(self.apply_sharpen_bw_auto)
        s.sharpen_bw_128_requested.connect(self.apply_sharpen_bw_128)
        s.sharpen_bw_custom_requested.connect(self.apply_sharpen_bw_custom)
        s.power_requested.connect(self.apply_power)
        s.invert_requested.connect(self.apply_invert)
        s.rotate_requested.connect(self.apply_rotate)
        s.blur_divide_requested.connect(self.apply_blur_divide)
        s.denoise_requested.connect(self.apply_denoise)
        s.pca_requested.connect(self.apply_pca)
        s.pca_svd_requested.connect(self.apply_pca_svd)
        s.prev_pc_requested.connect(self.prev_pc)
        s.next_pc_requested.connect(self.next_pc)

    def _connect_canvas(self):
        self.canvas.brush_stroke.connect(self._on_brush_stroke)
        self.canvas.draw_finished.connect(self._on_draw_finished)
        self.canvas.roi_changed.connect(self._on_roi_changed)
        self.canvas.roi_finished.connect(self._on_roi_finished)
        self.canvas.status_message.connect(self.set_status)
        self.canvas.zoom_changed.connect(self.status_bar.set_zoom_level)

    def _connect_bottom_bar(self):
        self.status_bar.zoom_in_clicked.connect(self.canvas.zoom_in)
        self.status_bar.zoom_out_clicked.connect(self.canvas.zoom_out)
        self.status_bar.zoom_reset_clicked.connect(self.canvas.reset_view)

    def _connect_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._undo_stack.redo)
        QShortcut(QKeySequence("+"), self, self.canvas.zoom_in)
        QShortcut(QKeySequence("="), self, self.canvas.zoom_in)
        QShortcut(QKeySequence("-"), self, self.canvas.zoom_out)
        QShortcut(QKeySequence("0"), self, self.canvas.reset_view)

    # ---- State management ----

    def _snapshot(self) -> ImageState:
        return ImageState(
            img=self.img.copy() if self.img is not None else None,
            draw_mask=self.draw_mask.copy() if self.draw_mask is not None else None,
            roi=tuple(self.roi) if self.roi is not None else None,
            zoom=self.canvas.zoom_factor,
            pan_x=0, pan_y=0,
            meta={},
        )

    def restore_state(self, state: ImageState) -> None:
        """Restore the application to a previous state (called by undo commands)."""
        self.img = state.img.copy() if state.img is not None else None
        self.draw_mask = state.draw_mask.copy() if state.draw_mask is not None else None
        self.roi = state.roi
        self._update_canvas()

    def _update_canvas(self) -> None:
        if self.img is not None:
            self.canvas.set_image(self.img)
        else:
            self.canvas.clear()
        self.canvas.set_draw_mask(self.draw_mask)
        self.canvas.set_roi(self.roi)

    def set_status(self, text: str) -> None:
        self.status_bar.set_text(text)

    # ---- Mode handling ----

    def _on_mode_changed(self, mode: str) -> None:
        self.canvas.set_mode(mode)
        self.sidebar.highlight_mode(mode)

    def _on_brush_size_changed(self, value: int) -> None:
        self.brush_size = value

    # ---- Generic operation wrapper ----

    def _apply_op(self, fn, meta: dict) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        before = self._snapshot()
        try:
            result = fn(self.img)
            if result is None:
                raise ValueError("Processing result is empty")
            self.img = result
            self._pc_cache = None
            self._pc_index = 0
            self.ops_log.record(meta)
            after = self._snapshot()
            cmd = ImageOperationCommand(self, before, after, meta.get("op", "operation"))
            self._undo_stack.push(cmd)
            self._update_canvas()
            self.set_status(f"Done: {meta.get('op', 'operation')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Operation failed: {e}")

    # ---- File operations ----

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTER)
        if not path:
            return
        try:
            img = load_image(path)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.img = img
        self.draw_mask = None
        self.roi = None
        self._pc_cache = None
        self._pc_index = 0
        self._undo_stack.clear()
        self.ops_log.clear()

        self._update_canvas()
        self.canvas.reset_view()
        self.set_status(f"Opened: {os.path.basename(path)}  |  {img.shape[1]}x{img.shape[0]}")

    def save_image(self) -> None:
        if self.img is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG (*.png);;JPG (*.jpg);;BMP (*.bmp);;TIFF (*.tif *.tiff)"
        )
        if not path:
            return
        try:
            save_image(path, self.img, self.draw_mask)
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")
            return

        # Write log
        try:
            txt_path = os.path.splitext(path)[0] + ".txt"
            self.ops_log.export_txt(txt_path)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Image saved, but failed to write log: {e}")

        self.set_status(f"Saved: {path}")

    def clear_image(self) -> None:
        self.img = None
        self.draw_mask = None
        self.roi = None
        self._pc_cache = None
        self._pc_index = 0
        self._undo_stack.clear()
        self.ops_log.clear()
        self._update_canvas()
        self.set_status("Cleared")

    # ---- Brush handling ----

    def _on_brush_stroke(self, ix: int, iy: int) -> None:
        if self.img is None:
            return
        h, w = self.img.shape[:2]
        if self.draw_mask is None or self.draw_mask.shape[:2] != (h, w):
            self.draw_mask = np.zeros((h, w), dtype=np.uint8)
        # Snapshot mask at start of stroke
        if self._mask_before_draw is None:
            self._mask_before_draw = self.draw_mask.copy()
        radius = int(round(self.brush_size * 6 / max(0.25, self.canvas.zoom_factor)))
        radius = clamp(radius, 2, 40)
        cv2.circle(self.draw_mask, (ix, iy), radius, 255, thickness=-1)
        self.canvas.set_draw_mask(self.draw_mask)

    def _on_draw_finished(self) -> None:
        if self.draw_mask is not None and self._mask_before_draw is not None:
            cmd = DrawStrokeCommand(self, self._mask_before_draw, self.draw_mask)
            self._undo_stack.push(cmd)
        self._mask_before_draw = None

    def set_draw_mask(self, mask: np.ndarray | None) -> None:
        """Called by undo commands to restore mask state."""
        self.draw_mask = mask.copy() if mask is not None else None
        self.canvas.set_draw_mask(self.draw_mask)

    # ---- Drawing/ROI clearing ----

    def clear_drawing(self) -> None:
        if self.draw_mask is not None:
            before = self.draw_mask.copy()
            self.draw_mask = None
            cmd = DrawStrokeCommand(self, before, np.zeros_like(before))
            self._undo_stack.push(cmd)
            self.canvas.set_draw_mask(self.draw_mask)
            self.set_status("Drawing cleared")

    def clear_roi(self) -> None:
        if self.roi is not None:
            before = self.roi
            self.roi = None
            cmd = RoiChangeCommand(self, before, None)
            self._undo_stack.push(cmd)
            self.canvas.set_roi(None)
            self.set_status("ROI cleared")

    # ---- ROI handling ----

    def _on_roi_changed(self, x0: int, y0: int, x1: int, y1: int) -> None:
        if self._roi_before is None:
            self._roi_before = self.roi
        self.roi = (x0, y0, x1, y1)
        self.canvas.set_roi(self.roi)

    def _on_roi_finished(self) -> None:
        cmd = RoiChangeCommand(self, self._roi_before, self.roi)
        self._undo_stack.push(cmd)
        self._roi_before = None

    def set_roi(self, roi: tuple | None) -> None:
        """Called by undo commands to restore ROI state."""
        self.roi = roi
        self.canvas.set_roi(self.roi)

    # ---- Image processing operations ----

    def apply_pseudocolor_channel(self, channel: str) -> None:
        ch = str(channel).lower()

        def op(img):
            if ch == "all":
                return pseudocolor_jet(ensure_gray(img))
            color = ensure_color(img)
            if ch == "r":
                src = color[:, :, 2]
            elif ch == "g":
                src = color[:, :, 1]
            elif ch == "b":
                src = color[:, :, 0]
            else:
                return pseudocolor_jet(ensure_gray(color))
            return pseudocolor_jet(to_uint8(src))

        self._apply_op(op, {"op": "pseudocolor_channel", "channel": ch})

    def apply_pseudocolor_two(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select two grayscale images (they will be converted to grayscale)",
            "", IMAGE_FILTER
        )
        if not paths or len(paths) < 2:
            return

        f1 = os.path.basename(paths[0])
        f2 = os.path.basename(paths[1])
        dlg = BandLabelDialog(f1, f2, self)
        labels = dlg.get_values()
        if labels is None:
            return

        try:
            g1 = load_as_gray(paths[0])
            g2 = load_as_gray(paths[1])
            if g1.shape != g2.shape:
                QMessageBox.critical(self, "Error", "The two images must have the same size")
                return
            mix = cv2.addWeighted(g1, 0.5, g2, 0.5, 0)
            out = pseudocolor_jet(mix)

            self.img = out
            self.draw_mask = None
            self.roi = None
            self._pc_cache = None
            self._pc_index = 0
            self._band_labels = labels
            self._undo_stack.clear()
            self.ops_log.clear()
            self.ops_log.record({
                "op": "pseudocolor_two",
                "p1": paths[0], "p2": paths[1],
                "band1_label": labels[0], "band2_label": labels[1],
            })
            self._update_canvas()
            self.canvas.reset_view()
            self.set_status(f"Done: Pseudocolor (Merge) [{labels[0]} + {labels[1]}]")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def apply_sharpen_original(self) -> None:
        self._apply_op(lambda img: unsharp_mask(img), {"op": "sharpen_original"})

    def apply_sharpen_bw_auto(self) -> None:
        self._apply_op(lambda img: otsu_binarize(img), {"op": "sharpen_bw_auto"})

    def apply_sharpen_bw_128(self) -> None:
        self._apply_op(lambda img: fixed_binarize(img, thresh=128), {"op": "sharpen_bw_128", "thresh": 128})

    def apply_sharpen_bw_custom(self) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        dlg = ThresholdDialog(self)
        thresh = dlg.get_value()
        if thresh is None:
            return
        self._apply_op(lambda img: fixed_binarize(img, thresh=thresh), {"op": "sharpen_bw_custom", "thresh": thresh})

    def apply_power(self) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        dlg = GammaDialog(self)
        result = dlg.get_values()
        if result is None:
            return
        gamma, partial, pivot = result

        def op(img):
            return power_transform(img, gamma=gamma, partial_invert=partial, pivot=pivot)

        self._apply_op(op, {"op": "power", "gamma": gamma, "partial": partial, "pivot": pivot})

    def apply_invert(self) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        dlg = InvertDialog(self)
        alpha = dlg.get_value()
        if alpha is None:
            return
        a = float(alpha)

        def op(img):
            inv = 255 - img
            x = img.astype(np.float32)
            y = inv.astype(np.float32)
            out = (1.0 - a) * x + a * y
            return out.clip(0, 255).astype(np.uint8)

        self._apply_op(op, {"op": "invert", "alpha": a})

    def apply_rotate(self, direction: str) -> None:
        self._apply_op(lambda img: rotate_90(img, direction=direction), {"op": "rotate_90", "direction": direction})

    def apply_blur_divide(self) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        dlg = BlurDivideDialog(self)
        result = dlg.get_values()
        if result is None:
            return
        k, sigma = result

        def op(img):
            return blur_divide(img, ksize=k, sigma=sigma)

        self._apply_op(op, {"op": "blur_divide", "ksize": k, "sigma": sigma})

    def apply_denoise(self) -> None:
        if self.img is None:
            QMessageBox.information(self, "Info", "Please open an image first")
            return
        dlg = DenoiseDialog(self)
        result = dlg.get_values()
        if result is None:
            return
        k, sigma = result

        def op(img):
            return denoise_gaussian(img, ksize=k, sigma=sigma)

        self._apply_op(op, {"op": "denoise_gaussian", "ksize": k, "sigma": sigma})

    def apply_pca(self) -> None:
        self._run_pca(pca_multiband, "PCA", "pca")

    def apply_pca_svd(self) -> None:
        self._run_pca(pca_multiband_svd_variant, "PCA (SVD)", "pca_svd")

    def _run_pca(self, pca_fn, label: str, op_name: str) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select 3-16 grayscale images (sizes must match) for {label}",
            "", IMAGE_FILTER
        )
        if not paths:
            return
        if len(paths) < 3:
            QMessageBox.information(self, "Info", f"{label}: select at least 3 images")
            return
        if len(paths) > 16:
            QMessageBox.information(self, "Info", "Maximum 16 images; only the first 16 will be used")
            paths = paths[:16]

        try:
            imgs = [load_as_gray(p) for p in paths]
            self.set_status(f"Computing {label}... (may take a few seconds)")

            result = pca_fn(imgs, roi=self.roi)
            self._pc_cache = result
            self._pc_index = 0
            pc1 = result["pcs"][0]
            self.img = pc1
            self.draw_mask = None
            self.ops_log.record({"op": op_name, "files": list(paths), "roi": self.roi})

            after = self._snapshot()
            cmd = ImageOperationCommand(self, self._snapshot(), after, op_name)
            self._undo_stack.push(cmd)
            self._update_canvas()

            ratios = result.get("explained", [])
            tip = ""
            if ratios:
                tip = " | ".join([f"C{i+1}:{ratios[i]*100:.1f}%" for i in range(min(4, len(ratios)))])
            self.set_status(f"{label} done: showing Band 1 (explained variance: {tip})")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"{label} failed: {e}")
            self.set_status(f"{label} failed")

    def next_pc(self) -> None:
        self._switch_pc(+1)

    def prev_pc(self) -> None:
        self._switch_pc(-1)

    def _switch_pc(self, direction: int) -> None:
        if not self._pc_cache or "pcs" not in self._pc_cache:
            self.set_status("No PCA band found: run PCA first")
            return
        pcs = self._pc_cache["pcs"]
        before = self._snapshot()
        self._pc_index = (self._pc_index + direction) % len(pcs)
        self.img = pcs[self._pc_index].copy()
        self.draw_mask = None

        after = self._snapshot()
        cmd = ImageOperationCommand(self, before, after, "pca_switch")
        self._undo_stack.push(cmd)
        self._update_canvas()

        ratios = self._pc_cache.get("explained", [])
        r = ratios[self._pc_index] * 100.0 if self._pc_index < len(ratios) else None
        n = len(pcs)
        if r is None:
            self.set_status(f"Showing: Band {self._pc_index+1} of {n}")
        else:
            self.set_status(f"Showing: Band {self._pc_index+1} of {n} (explained variance {r:.1f}%)")

    # ---- Theme management ----

    def _load_saved_theme(self) -> None:
        settings = QSettings()
        saved = settings.value("theme", "light")
        if saved not in ("light", "dark", "high-contrast"):
            saved = "light"
        self._apply_theme(saved)

    def _cycle_theme(self) -> None:
        from proteus.ui.theme import next_theme
        new_theme = next_theme(self._current_theme)
        self._apply_theme(new_theme)

    def _apply_theme(self, name: str) -> None:
        from proteus.ui.theme import apply_theme, THEME_INFO
        app = QApplication.instance()
        if app:
            apply_theme(app, name)
        self._current_theme = name
        self.top_bar.set_theme(name)
        self.canvas.set_theme(name)
        self.sidebar.set_theme(name)
        QSettings().setValue("theme", name)
        label = THEME_INFO.get(name, ("",))[0]
        self.set_status(f"Theme: {label}")
