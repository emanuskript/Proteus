"""Image loading and saving functions. No UI dependencies."""

import os
import numpy as np
import cv2
from typing import Optional

from proteus.core.processing import normalize_0_255, to_uint8, ensure_gray, ensure_color


def load_image(path: str) -> np.ndarray:
    """Load an image from disk. Handles 16-bit, alpha channel.
    Returns BGR or grayscale uint8 ndarray.
    Raises ValueError if the file cannot be read."""
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Unable to read image: {path}")
    if img.dtype == np.uint16:
        img = normalize_0_255(img)
    elif img.dtype != np.uint8:
        img = to_uint8(img)
    if img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def load_as_gray(path: str) -> np.ndarray:
    """Load an image and ensure it is grayscale uint8."""
    img = load_image(path)
    return ensure_gray(img)


def save_image(path: str, img: np.ndarray, draw_mask: Optional[np.ndarray] = None) -> None:
    """Save image to disk. Optionally composites the draw mask overlay.
    Raises ValueError on failure."""
    out = img.copy()
    if draw_mask is not None:
        out2 = ensure_color(out)
        overlay = out2.copy()
        overlay[draw_mask > 0] = (0, 255, 255)
        out = cv2.addWeighted(out2, 0.78, overlay, 0.22, 0)

    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        ok, buf = cv2.imencode(".jpg", out, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    elif ext == ".bmp":
        ok, buf = cv2.imencode(".bmp", out)
    elif ext in (".tif", ".tiff"):
        ok, buf = cv2.imencode(".tif", out)
    else:
        ok, buf = cv2.imencode(".png", out)

    if not ok:
        raise ValueError("Image encoding failed")
    buf.tofile(path)
