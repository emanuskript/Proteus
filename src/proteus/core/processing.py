"""Pure image processing functions. No UI dependencies.

All functions operate on numpy arrays with OpenCV. They are copied
verbatim from the original Refactor/main.py (lines 103-241).
"""

import numpy as np
import cv2

from proteus.core.utils import clamp


def to_uint8(img: np.ndarray) -> np.ndarray:
    if img is None:
        return img
    if img.dtype == np.uint8:
        return img
    img2 = np.clip(img, 0, 255).astype(np.uint8)
    return img2


def ensure_gray(img: np.ndarray) -> np.ndarray:
    if img is None:
        return img
    if img.ndim == 2:
        return img
    # assume BGR
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def ensure_color(img: np.ndarray) -> np.ndarray:
    if img is None:
        return img
    if img.ndim == 3:
        return img
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def normalize_0_255(img: np.ndarray) -> np.ndarray:
    if img is None:
        return img
    x = img.astype(np.float32)
    mn = float(np.min(x))
    mx = float(np.max(x))
    if mx - mn < 1e-6:
        return np.zeros_like(img, dtype=np.uint8)
    y = (x - mn) / (mx - mn) * 255.0
    return y.astype(np.uint8)


def hist_equalize(img: np.ndarray) -> np.ndarray:
    if img is None:
        return img
    if img.ndim == 2:
        return cv2.equalizeHist(img)
    # color: equalize Y channel
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def pseudocolor_jet(gray_u8: np.ndarray) -> np.ndarray:
    gray_u8 = ensure_gray(gray_u8)
    gray_u8 = to_uint8(gray_u8)
    colored = cv2.applyColorMap(gray_u8, cv2.COLORMAP_JET)
    return colored


def otsu_binarize(img: np.ndarray) -> np.ndarray:
    g = ensure_gray(img)
    g = to_uint8(g)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def fixed_binarize(img: np.ndarray, thresh: int = 128) -> np.ndarray:
    g = ensure_gray(img)
    g = to_uint8(g)
    t = int(clamp(thresh, 0, 255))
    _, th = cv2.threshold(g, t, 255, cv2.THRESH_BINARY)
    return th


def power_transform(img: np.ndarray, gamma: float, partial_invert: bool = False, pivot: int = 128) -> np.ndarray:
    """Apply a power/gamma transform; optional partial inversion (invert pixels > pivot)."""
    if img is None:
        return img
    x = img.astype(np.float32) / 255.0
    x = np.power(np.clip(x, 0, 1), gamma)
    out = (x * 255.0).astype(np.uint8)

    if partial_invert:
        if out.ndim == 2:
            mask = out > pivot
            out2 = out.copy()
            out2[mask] = 255 - out2[mask]
            return out2
        else:
            g = ensure_gray(out)
            mask = g > pivot
            out2 = out.copy()
            out2[mask] = 255 - out2[mask]
            return out2
    return out


def blur_divide(img: np.ndarray, ksize: int = 31, sigma: float = 0) -> np.ndarray:
    """Divide the image by its Gaussian-blurred version, then normalize and equalize."""
    if img is None:
        return img

    if ksize % 2 == 0:
        ksize += 1

    if img.ndim == 2:
        g = img.astype(np.float32)
        blur = cv2.GaussianBlur(g, (ksize, ksize), sigmaX=sigma)
        eps = 1e-6
        div = g / (blur + eps)
        out = normalize_0_255(div)
        out = hist_equalize(out)
        return out
    else:
        # Processing the luminance channel is more stable
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb).astype(np.float32)
        y = ycrcb[:, :, 0]
        blur = cv2.GaussianBlur(y, (ksize, ksize), sigmaX=sigma)
        div = y / (blur + 1e-6)
        y2 = normalize_0_255(div)
        y2 = cv2.equalizeHist(y2)
        ycrcb2 = ycrcb.copy()
        ycrcb2[:, :, 0] = y2
        out = cv2.cvtColor(ycrcb2.astype(np.uint8), cv2.COLOR_YCrCb2BGR)
        return out


def denoise_gaussian(img: np.ndarray, ksize: int = 5, sigma: float = 1.0) -> np.ndarray:
    if img is None:
        return img
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(img, (ksize, ksize), sigmaX=sigma)


def rotate_90(img: np.ndarray, direction: str) -> np.ndarray:
    if img is None:
        return img
    if direction == "left":
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
