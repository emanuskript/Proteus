"""Image canvas widget using QGraphicsView.

Replaces the tkinter Canvas + manual image pyramid system.
QGraphicsView handles zoom/pan/coordinate mapping natively.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QPainter, QBrush, QWheelEvent, QMouseEvent

import numpy as np
import cv2


class DrawOverlayItem(QGraphicsPixmapItem):
    """Transparent overlay that renders the brush mask as yellow highlights."""
    pass


class RoiRectItem(QGraphicsRectItem):
    """Dashed cyan rectangle for ROI selection."""

    def __init__(self):
        super().__init__()
        pen = QPen(QColor("#00ff99"), 2, Qt.DashLine)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.NoBrush))


class ImageCanvas(QGraphicsView):
    """Central image display widget.

    Handles zoom (scroll wheel), pan (drag in pan mode),
    brush drawing, and ROI selection via mouse events.
    Emits signals for the main window to handle state changes.
    """

    # Signals
    status_message = Signal(str)
    brush_stroke = Signal(int, int)
    roi_changed = Signal(int, int, int, int)
    roi_finished = Signal()
    draw_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Rendering
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor("#111111")))

        # Scene items (layered)
        self._image_item = QGraphicsPixmapItem()
        self._overlay_item = DrawOverlayItem()
        self._roi_item = RoiRectItem()
        self._scene.addItem(self._image_item)
        self._scene.addItem(self._overlay_item)
        self._scene.addItem(self._roi_item)
        self._overlay_item.setZValue(1)
        self._roi_item.setZValue(2)
        self._roi_item.setVisible(False)

        # Interaction state
        self._mode: str = "pan"
        self._zoom_factor: float = 1.0
        self._drawing: bool = False
        self._roi_origin: QPointF = QPointF()
        self._image_size: tuple = (0, 0)

        # Start in pan mode
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        # Placeholder text
        self._placeholder = self._scene.addText(
            "No image loaded: click [Open Image] on the left"
        )
        self._placeholder.setDefaultTextColor(QColor("#aaaaaa"))
        font = self._placeholder.font()
        font.setPointSize(14)
        self._placeholder.setFont(font)

    def set_image(self, img: np.ndarray) -> None:
        """Display an OpenCV image (BGR or grayscale uint8)."""
        self._placeholder.setVisible(False)
        if img.ndim == 2:
            h, w = img.shape
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            h, w = img.shape[:2]
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg.copy())
        self._image_item.setPixmap(pixmap)
        self._image_size = (w, h)
        self._scene.setSceneRect(0, 0, w, h)

    def set_draw_mask(self, mask: np.ndarray | None) -> None:
        """Update the draw overlay from a full-resolution mask."""
        if mask is None:
            self._overlay_item.setPixmap(QPixmap())
            return
        h, w = mask.shape
        # ARGB32: yellow at 22% opacity where mask > 0
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        overlay[mask > 0] = [255, 255, 0, 56]  # R, G, B, A for RGBA
        qimg = QImage(overlay.data, w, h, 4 * w, QImage.Format_RGBA8888)
        self._overlay_item.setPixmap(QPixmap.fromImage(qimg.copy()))

    def set_roi(self, roi: tuple | None) -> None:
        """Display or hide the ROI rectangle."""
        if roi is None:
            self._roi_item.setVisible(False)
            return
        x0, y0, x1, y1 = roi
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        self._roi_item.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        self._roi_item.setVisible(True)

    def set_mode(self, mode: str) -> None:
        """Switch interaction mode: 'pan', 'draw', or 'roi'."""
        self._mode = mode
        if mode == "pan":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    def zoom_in(self) -> None:
        new_zoom = min(self._zoom_factor * 1.25, 10.0)
        self._set_zoom(new_zoom)

    def zoom_out(self) -> None:
        new_zoom = max(self._zoom_factor / 1.25, 0.1)
        self._set_zoom(new_zoom)

    def reset_view(self) -> None:
        """Reset zoom and pan to defaults."""
        self.resetTransform()
        self._zoom_factor = 1.0
        self.centerOn(self._image_item)
        self.status_message.emit("Zoom reset: 1.00x")

    def clear(self) -> None:
        """Remove the displayed image and overlays."""
        self._image_item.setPixmap(QPixmap())
        self._overlay_item.setPixmap(QPixmap())
        self._roi_item.setVisible(False)
        self._image_size = (0, 0)
        self._placeholder.setVisible(True)

    @property
    def zoom_factor(self) -> float:
        return self._zoom_factor

    # ---- Private ----

    def _set_zoom(self, factor: float) -> None:
        scale_change = factor / self._zoom_factor
        self._zoom_factor = factor
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(scale_change, scale_change)
        self.status_message.emit(f"Zoom: {factor:.2f}x")

    # ---- Event handlers ----

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._mode == "pan":
            super().mousePressEvent(event)
            return
        if event.button() != Qt.LeftButton:
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        ix, iy = int(scene_pos.x()), int(scene_pos.y())
        if self._mode == "draw":
            self._drawing = True
            self.brush_stroke.emit(ix, iy)
        elif self._mode == "roi":
            self._roi_origin = scene_pos
            self.roi_changed.emit(ix, iy, ix, iy)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._mode == "pan":
            super().mouseMoveEvent(event)
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        ix, iy = int(scene_pos.x()), int(scene_pos.y())
        if self._mode == "draw" and self._drawing:
            self.brush_stroke.emit(ix, iy)
        elif self._mode == "roi":
            ox, oy = int(self._roi_origin.x()), int(self._roi_origin.y())
            self.roi_changed.emit(ox, oy, ix, iy)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._mode == "pan":
            super().mouseReleaseEvent(event)
            return
        if self._mode == "draw":
            self._drawing = False
            self.draw_finished.emit()
        elif self._mode == "roi":
            self.roi_finished.emit()
