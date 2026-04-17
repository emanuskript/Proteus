"""Qt image helpers that do not depend on Qt image format plugins."""

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from proteus.core.utils import resource_path


def load_resource_qimage(name: str) -> QImage:
    """Load a QImage from app resources via OpenCV, avoiding Qt plugin issues."""
    path = Path(resource_path(name))
    if not path.exists():
        return QImage()

    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return QImage()

    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        return QImage()

    if image.ndim == 2:
        return QImage(
            image.data,
            image.shape[1],
            image.shape[0],
            image.strides[0],
            QImage.Format_Grayscale8,
        ).copy()

    if image.shape[2] == 4:
        rgba = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        return QImage(
            rgba.data,
            rgba.shape[1],
            rgba.shape[0],
            rgba.strides[0],
            QImage.Format_RGBA8888,
        ).copy()

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return QImage(
        rgb.data,
        rgb.shape[1],
        rgb.shape[0],
        rgb.strides[0],
        QImage.Format_RGB888,
    ).copy()


def load_resource_pixmap(name: str) -> QPixmap:
    """Load a QPixmap from a decoded QImage."""
    qimg = load_resource_qimage(name)
    if qimg.isNull():
        return QPixmap()
    return QPixmap.fromImage(qimg)


def load_scaled_resource_pixmap(name: str, size: int) -> QPixmap:
    """Load and scale a pixmap from resources without Qt image plugins."""
    pixmap = load_resource_pixmap(name)
    if pixmap.isNull():
        return pixmap
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
