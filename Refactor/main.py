#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dependencies:
  pip install customtkinter pillow opencv-python numpy

Run:
  python proteus_single.py
"""

import os
import sys
import math
import time
import json
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

import numpy as np
import cv2
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk


# =========================
# Utility: Tooltip
# =========================
class Tooltip:
    def __init__(self, widget, text: str, delay_ms=450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _evt=None):
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, _evt=None):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._hide()

    def _show(self):
        if self._tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.attributes("-topmost", True)
        self._tip.geometry(f"+{x}+{y}")

        lbl = tk.Label(
            self._tip,
            text=self.text,
            bg="#222",
            fg="#fff",
            padx=8,
            pady=5,
            font=("Arial", 10),
            relief="solid",
            bd=1
        )
        lbl.pack()

    def _hide(self):
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


# =========================
# Image processing helper functions
# =========================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


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


# =========================
# PCA multiband (3–16 grayscale images)
# =========================
def pca_multiband(images_gray_u8: List[np.ndarray], roi: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
    """
    images_gray_u8: list of HxW uint8 gray images, length = N (3..16)
    roi: (x0,y0,x1,y1) in image coords, used to fit PCA; then applied to full image.
    return dict:
      {
        'pcs': [pc1_u8, pc2_u8, ...],  # each HxW uint8
        'explained': [ratio1, ratio2, ...],
        'mean': mean_vec,
        'components': comps,
      }
    """
    if not images_gray_u8 or len(images_gray_u8) < 3:
        raise ValueError("PCA requires at least 3 grayscale images")
    if len(images_gray_u8) > 16:
        images_gray_u8 = images_gray_u8[:16]

    # Same size
    H, W = images_gray_u8[0].shape[:2]
    imgs = []
    for im in images_gray_u8:
        if im.shape[:2] != (H, W):
            raise ValueError("PCA input images must have the same size (selected files differ in dimensions)")
        imgs.append(im.astype(np.float32))

    # stack -> (H*W, N)
    X = np.stack(imgs, axis=-1)  # (H,W,N)

    if roi is not None:
        x0, y0, x1, y1 = roi
        x0, x1 = sorted([int(x0), int(x1)])
        y0, y1 = sorted([int(y0), int(y1)])
        x0 = clamp(x0, 0, W - 1)
        x1 = clamp(x1, 1, W)
        y0 = clamp(y0, 0, H - 1)
        y1 = clamp(y1, 1, H)
        X_fit = X[y0:y1, x0:x1, :].reshape(-1, X.shape[-1])
    else:
        X_fit = X.reshape(-1, X.shape[-1])

    # Mean-centering
    mean = np.mean(X_fit, axis=0, keepdims=True)
    Xc = X_fit - mean

    # Covariance and eigen-decomposition (N<=16 is small)
    cov = (Xc.T @ Xc) / max(1, (Xc.shape[0] - 1))
    eigvals, eigvecs = np.linalg.eigh(cov)  # ascending
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    total = float(np.sum(eigvals)) if float(np.sum(eigvals)) > 1e-12 else 1.0
    explained = (eigvals / total).tolist()

    # Project full image
    X_all = X.reshape(-1, X.shape[-1]).astype(np.float32)
    X_all_c = X_all - mean
    scores = X_all_c @ eigvecs  # (H*W, N)

    pcs = []
    for k in range(min(len(images_gray_u8), 8)):  # take the first 8 components for display
        pc = scores[:, k].reshape(H, W)
        pcs.append(normalize_0_255(pc))

    return {
        "pcs": pcs,
        "explained": explained[:len(pcs)],
        "mean": mean.flatten(),
        "components": eigvecs
    }


def pca_multiband_svd_variant(
    images_gray_u8: List[np.ndarray],
    roi: Optional[Tuple[int, int, int, int]] = None,
    max_components: int = 8
) -> Dict[str, Any]:
    """
    SVD-variant implementation of multiband PCA (based on PCA.m)
    Perform PCA across bands using an SVD-based approach:
      - Z is d x n, where d is the number of bands and n is the number of samples (pixels)
      - First center each row (band), then compute the SVD
    The return structure is similar to pca_multiband:
      {
        'pcs': [pc1_u8, pc2_u8, ...],
        'explained': [ratio1, ratio2, ...],
        'mean': mean_vec,          # d dims
        'U': U,                    # d x r
        'S': S,                    # r
      }
    """
    if not images_gray_u8 or len(images_gray_u8) < 3:
        raise ValueError("PCA (SVD) requires at least 3 grayscale images")

    # Limit to at most 16 bands
    if len(images_gray_u8) > 16:
        images_gray_u8 = images_gray_u8[:16]

    # Check sizes & convert to float32
    H, W = images_gray_u8[0].shape[:2]
    imgs = []
    for im in images_gray_u8:
        if im.shape[:2] != (H, W):
            raise ValueError("PCA (SVD) input images must have the same size (selected files differ in dimensions)")
        imgs.append(im.astype(np.float32))

    # Choose the region used to fit PCA: ROI or full image
    stack = np.stack(imgs, axis=0)  # (N_bands, H, W)
    if roi is not None:
        x0, y0, x1, y1 = roi
        x0, x1 = sorted([int(x0), int(x1)])
        y0, y1 = sorted([int(y0), int(y1)])
        x0 = clamp(x0, 0, W - 1)
        x1 = clamp(x1, 1, W)
        y0 = clamp(y0, 0, H - 1)
        y1 = clamp(y1, 1, H)
        sub = stack[:, y0:y1, x0:x1]
    else:
        sub = stack

    # Z: d x n (d=bands, n=pixels)
    d = sub.shape[0]
    Z = sub.reshape(d, -1)  # (d, n)

    # Center each row (non-standard centering, matches PCA.m centerRows)
    mu = np.mean(Z, axis=1, keepdims=True)  # (d,1)
    Zc = Z - mu

    # SVD decomposition (econ)
    # Zc = U @ S_diag @ Vt
    U, S, Vt = np.linalg.svd(Zc, full_matrices=False)

    # Truncate principal components
    r = int(max_components)
    r = max(1, min(r, d, U.shape[1]))
    U_r = U[:, :r]              # (d, r)
    S_r = S[:r]                 # (r,)
    Vt_r = Vt[:r, :]            # (r, n)

    # Explained variance (proportional to eigenvalues; here eigenvalues ~ S^2)
    eigvals = (S_r ** 2)
    total = float(np.sum(eigvals)) if float(np.sum(eigvals)) > 1e-12 else 1.0
    explained = (eigvals / total).tolist()

    # Project onto the full image to obtain component images
    Z_all = stack.reshape(d, -1)        # (d, H*W)
    Z_all_c = Z_all - mu               # Use the same mean
    # scores_all: r x (H*W)
    scores_all = U_r.T @ Z_all_c

    pcs = []
    for k in range(r):
        pc = scores_all[k, :].reshape(H, W)
        pcs.append(normalize_0_255(pc))

    return {
        "pcs": pcs,
        "explained": explained[:len(pcs)],
        "mean": mu.flatten(),
        "U": U_r,
        "S": S_r,
    }


# =========================
# State stack (Undo/Redo)
# =========================
@dataclass
class ImageState:
    img: Optional[np.ndarray]              # processed full-res image (BGR or GRAY)
    draw_mask: Optional[np.ndarray]        # HxW mask uint8 (0/255) for highlight
    roi: Optional[Tuple[int, int, int, int]]
    zoom: float
    pan_x: float
    pan_y: float
    meta: Dict[str, Any]


# =========================
# Main application
# =========================
class ProteusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Proteus - Image Processing (Single File)")
        try:
            self.state("zoomed")
        except Exception:
            self.geometry("1200x760")

        # ---- Data ----
        self.base_img: Optional[np.ndarray] = None     # original (or currently loaded) full-res
        self.img: Optional[np.ndarray] = None          # current processed full-res
        self.draw_mask: Optional[np.ndarray] = None    # brush highlight mask
        self.roi: Optional[Tuple[int, int, int, int]] = None

        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

        self._pyramid: List[np.ndarray] = []
        self._tk_img = None

        self._mode = "pan"  # pan | draw | roi
        self._drawing = False
        self._roi_dragging = False
        self._last_xy = None
        self._roi_start = None
        self._roi_rect_id = None

        self.brush_size = 3  # 1-5
        self._pc_cache: Optional[Dict[str, Any]] = None
        self._pc_index = 0

        # Undo/Redo
        self._history: List[ImageState] = []
        self._hist_i = -1

        # Operation log (exported to txt)
        self.ops_log: List[Dict[str, Any]] = []

        # App logo (top-left)
        self.logo_image = None
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, "Proteus.png")
            if os.path.exists(logo_path):
                _logo = Image.open(logo_path)
                _logo = _logo.resize((80, 80), Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(_logo)
        except Exception:
            self.logo_image = None

        # ---- UI ----
        self._build_ui()
        self._bind_shortcuts()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left toolbar (scrollable)
        self.sidebar = ctk.CTkScrollableFrame(self, width=260, corner_radius=12)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=12, pady=12)
        self.sidebar.grid_rowconfigure(99, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Title + logo
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=14, pady=(14, 10), sticky="w")
        if self.logo_image is not None:
            logo_label = ctk.CTkLabel(title_frame, image=self.logo_image, text="")
            logo_label.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="w")
        title = ctk.CTkLabel(title_frame, text="Proteus Toolbox", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=1, sticky="w")

        # File area
        file_lbl = ctk.CTkLabel(self.sidebar, text="Files / History", font=ctk.CTkFont(size=14, weight="bold"))
        file_lbl.grid(row=1, column=0, padx=14, pady=(8, 6), sticky="w")

        row = 2
        btn_open = ctk.CTkButton(self.sidebar, text="Open Image", command=self.open_image, width=220)
        btn_open.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_open, "Open an image (common formats)")

        row += 1
        btn_save = ctk.CTkButton(self.sidebar, text="Save Current Image", command=self.save_image, width=220)
        btn_save.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_save, "Save the current processed result (full resolution)")

        row += 1
        btn_clear = ctk.CTkButton(self.sidebar, text="Clear", fg_color="#7a1f1f", hover_color="#9a2a2a", command=self.clear_image, width=220)
        btn_clear.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_clear, "Clear the current image and overlays")

        row += 1
        hist_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        hist_frame.grid(row=row, column=0, padx=14, pady=8)
        hist_frame.grid_columnconfigure((0, 1), weight=1)

        btn_undo = ctk.CTkButton(hist_frame, text="Undo", command=self.undo, width=90)
        btn_undo.grid(row=0, column=0, padx=6, pady=8)
        Tooltip(btn_undo, "Undo one step (Ctrl+Z)")

        btn_redo = ctk.CTkButton(hist_frame, text="Redo", command=self.redo, width=90)
        btn_redo.grid(row=0, column=1, padx=6, pady=8)
        Tooltip(btn_redo, "Redo one step (Ctrl+Y)")

        # View/Edit
        row += 1
        view_lbl = ctk.CTkLabel(self.sidebar, text="View / Annotate", font=ctk.CTkFont(size=14, weight="bold"))
        view_lbl.grid(row=row, column=0, padx=14, pady=(12, 6), sticky="w")

        row += 1
        view_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        view_frame.grid(row=row, column=0, padx=14, pady=8)
        view_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_zi = ctk.CTkButton(view_frame, text="Zoom In +", command=self.zoom_in, width=60)
        btn_zi.grid(row=0, column=0, padx=4, pady=8)
        Tooltip(btn_zi, "Zoom in (shortcut +)")

        btn_zo = ctk.CTkButton(view_frame, text="Zoom Out -", command=self.zoom_out, width=60)
        btn_zo.grid(row=0, column=1, padx=4, pady=8)
        Tooltip(btn_zo, "Zoom out (shortcut -)")

        btn_zr = ctk.CTkButton(view_frame, text="Reset 0", command=self.reset_zoom, width=60)
        btn_zr.grid(row=0, column=2, padx=4, pady=8)
        Tooltip(btn_zr, "Reset zoom (shortcut 0)")

        row += 1
        mode_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        mode_frame.grid(row=row, column=0, padx=14, pady=8)
        mode_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_pan = ctk.CTkButton(mode_frame, text="Pan", command=lambda: self.set_mode("pan"), width=60)
        self.btn_pan.grid(row=0, column=0, padx=4, pady=8)
        Tooltip(self.btn_pan, "Drag to pan")

        self.btn_draw = ctk.CTkButton(mode_frame, text="Brush", command=lambda: self.set_mode("draw"), width=60)
        self.btn_draw.grid(row=0, column=1, padx=4, pady=8)
        Tooltip(self.btn_draw, "Yellow highlight (erasable)")

        self.btn_roi = ctk.CTkButton(mode_frame, text="ROI", command=lambda: self.set_mode("roi"), width=60)
        self.btn_roi.grid(row=0, column=2, padx=4, pady=8)
        Tooltip(self.btn_roi, "Select ROI (for PCA, etc.)")

        row += 1
        brush_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        brush_frame.grid(row=row, column=0, padx=14, pady=8)
        brush_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(brush_frame, text="Brush Size (1–5)").grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.brush_slider = ctk.CTkSlider(brush_frame, from_=1, to=5, number_of_steps=4, command=self._on_brush_change)
        self.brush_slider.set(self.brush_size)
        self.brush_slider.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        row += 1
        btn_clear_draw = ctk.CTkButton(self.sidebar, text="Clear Drawing", command=self.clear_drawing, width=220)
        btn_clear_draw.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_clear_draw, "Clear yellow highlights (does not affect the image)")

        row += 1
        btn_clear_roi = ctk.CTkButton(self.sidebar, text="Clear ROI", command=self.clear_roi, width=220)
        btn_clear_roi.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_clear_roi, "Clear ROI selection")

        # Image Processing
        row += 1
        proc_lbl = ctk.CTkLabel(self.sidebar, text="Image Processing", font=ctk.CTkFont(size=14, weight="bold"))
        proc_lbl.grid(row=row, column=0, padx=14, pady=(14, 6), sticky="w")

        # Pseudocolor mode buttons: All / R / G / B
        row += 1
        pc_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        pc_frame.grid(row=row, column=0, padx=14, pady=8)
        pc_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        btn_pc_all = ctk.CTkButton(pc_frame, text="Pseudocolor-All", command=lambda: self.apply_pseudocolor_channel("all"), width=60)
        btn_pc_all.grid(row=0, column=0, padx=4, pady=8)
        Tooltip(btn_pc_all, "Pseudocolor (All): based on overall intensity")

        btn_pc_r = ctk.CTkButton(pc_frame, text="Pseudocolor-R", command=lambda: self.apply_pseudocolor_channel("r"), width=60)
        btn_pc_r.grid(row=0, column=1, padx=4, pady=8)
        Tooltip(btn_pc_r, "Pseudocolor (R): based on R channel intensity")

        btn_pc_g = ctk.CTkButton(pc_frame, text="Pseudocolor-G", command=lambda: self.apply_pseudocolor_channel("g"), width=60)
        btn_pc_g.grid(row=1, column=0, padx=4, pady=8)
        Tooltip(btn_pc_g, "Pseudocolor (G): based on G channel intensity")

        btn_pc_b = ctk.CTkButton(pc_frame, text="Pseudocolor-B", command=lambda: self.apply_pseudocolor_channel("b"), width=60)
        btn_pc_b.grid(row=1, column=1, padx=4, pady=8)
        Tooltip(btn_pc_b, "Pseudocolor (B): based on B channel intensity")

        row += 1
        btn_pc2 = ctk.CTkButton(self.sidebar, text="Pseudocolor (Merge Two Images)", command=self.apply_pseudocolor_two, width=220)
        btn_pc2.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_pc2, "Select two grayscale images, merge them, then apply JET (All mode)")

        # Sharpen (keep Otsu + fixed threshold 128)
        row += 1
        sharp_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        sharp_frame.grid(row=row, column=0, padx=14, pady=8)
        sharp_frame.grid_columnconfigure((0, 1), weight=1)

        btn_sharp_otsu = ctk.CTkButton(sharp_frame, text="Sharpen(Otsu)", command=self.apply_sharpen_otsu, width=100)
        btn_sharp_otsu.grid(row=0, column=0, padx=6, pady=8)
        Tooltip(btn_sharp_otsu, "Sharpen: Otsu automatic threshold")

        btn_sharp_fix = ctk.CTkButton(sharp_frame, text="Sharpen(128)", command=self.apply_sharpen_fixed, width=100)
        btn_sharp_fix.grid(row=0, column=1, padx=6, pady=8)
        Tooltip(btn_sharp_fix, "Sharpen: fixed threshold 128")

        row += 1
        btn_pow = ctk.CTkButton(self.sidebar, text="Power (Gamma)", command=self.apply_power, width=220)
        btn_pow.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_pow, "Gamma/power transform + optional partial inversion")

        row += 1
        btn_inv = ctk.CTkButton(self.sidebar, text="Invert", command=self.apply_invert, width=220)
        btn_inv.grid(row=row, column=0, padx=14, pady=6)

        row += 1
        rot_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        rot_frame.grid(row=row, column=0, padx=14, pady=8)
        rot_frame.grid_columnconfigure((0, 1), weight=1)

        btn_rl = ctk.CTkButton(rot_frame, text="Rotate Left 90°", command=lambda: self.apply_rotate("left"), width=90)
        btn_rl.grid(row=0, column=0, padx=6, pady=8)

        btn_rr = ctk.CTkButton(rot_frame, text="Rotate Right 90°", command=lambda: self.apply_rotate("right"), width=90)
        btn_rr.grid(row=0, column=1, padx=6, pady=8)

        row += 1
        btn_bd = ctk.CTkButton(self.sidebar, text="Blur & Divide", command=self.apply_blur_divide, width=220)
        btn_bd.grid(row=row, column=0, padx=14, pady=6)
        Tooltip(btn_bd, "Divide after Gaussian blur + normalize + equalize")

        row += 1
        btn_dn = ctk.CTkButton(self.sidebar, text="Denoise (Gaussian)", command=self.apply_denoise, width=220)
        btn_dn.grid(row=row, column=0, padx=14, pady=6)

        row += 1
        pca_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        pca_frame.grid(row=row, column=0, padx=14, pady=10)
        pca_frame.grid_columnconfigure((0, 1, 2), weight=1)

        btn_pca = ctk.CTkButton(pca_frame, text="PCA", command=self.apply_pca, width=70)
        btn_pca.grid(row=0, column=0, padx=4, pady=8)
        Tooltip(btn_pca, "Select multiple grayscale images for PCA (covariance method, 3–16 images; ROI can be used for fitting)")

        btn_pca_svd = ctk.CTkButton(pca_frame, text="PCA-SVD", command=self.apply_pca_svd, width=80)
        btn_pca_svd.grid(row=0, column=1, padx=4, pady=8)
        Tooltip(btn_pca_svd, "PCA SVD variant (based on PCA.m, 3–16 images; ROI can be used for fitting)")

        btn_pc_next = ctk.CTkButton(pca_frame, text="Next PC", command=self.next_pc, width=70)
        btn_pc_next.grid(row=0, column=2, padx=4, pady=8)
        Tooltip(btn_pc_next, "Cycle PC1/PC2/… (run PCA or PCA-SVD first)")

        # Right-side canvas
        self.viewer = ctk.CTkFrame(self, corner_radius=12)
        self.viewer.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        self.viewer.grid_columnconfigure(0, weight=1)
        self.viewer.grid_rowconfigure(1, weight=1)

        info_bar = ctk.CTkFrame(self.viewer, corner_radius=12)
        info_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        info_bar.grid_columnconfigure(0, weight=1)

        self.status = ctk.CTkLabel(info_bar, text="Ready: open an image to begin", anchor="w")
        self.status.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Canvas (tk.Canvas works best for pan/roi/draw)
        self.canvas = tk.Canvas(self.viewer, bg="#111", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self.canvas.bind("<Configure>", lambda e: self.render())
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<MouseWheel>", self.on_wheel)          # Windows/macOS
        self.canvas.bind("<Button-4>", self.on_wheel_linux)      # Linux up
        self.canvas.bind("<Button-5>", self.on_wheel_linux)      # Linux down

        self.set_mode("pan")

    def _bind_shortcuts(self):
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-y>", lambda e: self.redo())
        self.bind_all("<Key-plus>", lambda e: self.zoom_in())
        self.bind_all("<Key-equal>", lambda e: self.zoom_in())   # On most keyboards, '+' requires Shift
        self.bind_all("<Key-minus>", lambda e: self.zoom_out())
        self.bind_all("<Key-0>", lambda e: self.reset_zoom())

    # ---------------- State & Rendering ----------------
    def set_status(self, text: str):
        self.status.configure(text=text)

    def _on_brush_change(self, v):
        self.brush_size = int(round(float(v)))

    def set_mode(self, mode: str):
        self._mode = mode
        # Simple highlight: change the active button color
        def style(btn, active: bool):
            if active:
                btn.configure(fg_color="#2b6cb0")
            else:
                btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        style(self.btn_pan, mode == "pan")
        style(self.btn_draw, mode == "draw")
        style(self.btn_roi, mode == "roi")
        self.set_status(f"Mode:{mode}（Pan/Brush/ROI）")

    def _push_history(self, meta: Optional[Dict[str, Any]] = None):
        """Push the current state onto the stack (for Undo/Redo)."""
        if self.img is None:
            return
        st = ImageState(
            img=self.img.copy(),
            draw_mask=None if self.draw_mask is None else self.draw_mask.copy(),
            roi=None if self.roi is None else tuple(self.roi),
            zoom=float(self.zoom),
            pan_x=float(self.pan_x),
            pan_y=float(self.pan_y),
            meta=meta or {}
        )
        # Discard redo branch
        if self._hist_i < len(self._history) - 1:
            self._history = self._history[: self._hist_i + 1]
        self._history.append(st)
        self._hist_i = len(self._history) - 1

        # Record operation log (only image-processing operations)
        if meta is not None:
            op = meta.get("op")
            if op not in ("open", "draw", "roi", "clear_draw", "clear_roi"):
                # Store a shallow copy to avoid later mutation
                self.ops_log.append(dict(meta))

    def undo(self):
        if len(self._history) == 0:
            self.set_status("Undo: history is empty (perform an operation first)")
            return
        if self._hist_i <= 0:
            self.set_status("Undo: no earlier history (already at the initial state)")
            return
        self._hist_i -= 1
        self._apply_state(self._history[self._hist_i])
        self.set_status(f"Undo complete ({self._hist_i + 1}/{len(self._history)})")

    def redo(self):
        if len(self._history) == 0:
            self.set_status("Redo: history is empty (perform an operation first)")
            return
        if self._hist_i >= len(self._history) - 1:
            self.set_status(f"Redo: already at the latest state (history: {len(self._history)} items, position: {self._hist_i + 1})")
            return
        self._hist_i += 1
        self._apply_state(self._history[self._hist_i])
        self.set_status(f"Redo complete ({self._hist_i + 1}/{len(self._history)})")

    def _apply_state(self, st: ImageState):
        self.img = None if st.img is None else st.img.copy()
        self.draw_mask = None if st.draw_mask is None else st.draw_mask.copy()
        self.roi = None if st.roi is None else tuple(st.roi)
        self.zoom = float(st.zoom)
        self.pan_x = float(st.pan_x)
        self.pan_y = float(st.pan_y)
        self._rebuild_pyramid()
        self.render()

    def _rebuild_pyramid(self):
        """Pyramid cache: for faster zoom rendering"""
        self._pyramid = []
        if self.img is None:
            return
        im = self.img
        self._pyramid.append(im)
        # Downsample level by level (until the shortest side < 256 or up to 6 levels)
        for _ in range(6):
            h, w = im.shape[:2]
            if min(h, w) < 256:
                break
            im = cv2.pyrDown(im)
            self._pyramid.append(im)

    def _pick_pyramid_level(self, zoom: float) -> Tuple[np.ndarray, float]:
        """
        zoom=1 uses level0
        zoom=0.5 -> can use level1 as the base (because level1 is half size)
        Returns: selected level image & zoom relative to that level
        """
        if not self._pyramid:
            return self.img, zoom
        # When zoom < 1, choose a smaller pyramid level as the base
        level = 0
        z = zoom
        while z < 0.75 and level + 1 < len(self._pyramid):
            z *= 2.0
            level += 1
        return self._pyramid[level], z

    def render(self):
        self.canvas.delete("all")
        if self.img is None:
            self.canvas.create_text(
                20, 20, anchor="nw",
                fill="#aaa",
                font=("Arial", 14),
                text="No image loaded: click [Open Image] on the left"
            )
            return

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        base, rel_zoom = self._pick_pyramid_level(self.zoom)
        H, W = base.shape[:2]

        # Display size
        disp_w = int(W * rel_zoom)
        disp_h = int(H * rel_zoom)
        disp_w = max(1, disp_w)
        disp_h = max(1, disp_h)

        # Compute pan (in screen coordinates)
        cx = canvas_w / 2.0 + self.pan_x
        cy = canvas_h / 2.0 + self.pan_y

        # Top-left corner of the target region in the displayed image
        x0 = int(cx - disp_w / 2)
        y0 = int(cy - disp_h / 2)

        # Generate the scaled display image
        interp = cv2.INTER_AREA if rel_zoom < 1 else cv2.INTER_LINEAR
        disp = cv2.resize(base, (disp_w, disp_h), interpolation=interp)

        # Overlay brush (yellow)
        if self.draw_mask is not None:
            # Mask is full-res; map it via pyramid level + zoom
            # First resize the full-res mask to the selected base size
            # Base corresponds to pyramid level L, i.e., full-res scaled by 1/(2^L)
            # For simplicity and robustness, just resize (mirroring the pyrDown logic)
            mask_base = cv2.resize(self.draw_mask, (W, H), interpolation=cv2.INTER_NEAREST)
            mask_disp = cv2.resize(mask_base, (disp_w, disp_h), interpolation=cv2.INTER_NEAREST)
            if disp.ndim == 2:
                disp = ensure_color(disp)
            overlay = disp.copy()
            overlay[mask_disp > 0] = (0, 255, 255)  # BGR: yellow
            disp = cv2.addWeighted(disp, 0.78, overlay, 0.22, 0)

        # Convert to PIL / Tk
        disp_rgb = disp
        if disp_rgb.ndim == 2:
            disp_rgb = cv2.cvtColor(disp_rgb, cv2.COLOR_GRAY2RGB)
        else:
            disp_rgb = cv2.cvtColor(disp_rgb, cv2.COLOR_BGR2RGB)

        pil = Image.fromarray(disp_rgb)
        self._tk_img = ImageTk.PhotoImage(pil)

        # Draw image on the canvas
        self.canvas.create_image(x0, y0, anchor="nw", image=self._tk_img)

        # ROI rectangle (drawn on the canvas)
        if self.roi is not None:
            # ROI is in full-res coords -> map to canvas coords (full-res is more accurate)
            self._draw_roi_rect()

    def _draw_roi_rect(self):
        if self.img is None or self.roi is None:
            return
        # Compute full-res -> canvas coordinate mapping first
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        base, rel_zoom = self._pick_pyramid_level(self.zoom)
        H, W = base.shape[:2]
        disp_w = int(W * rel_zoom)
        disp_h = int(H * rel_zoom)
        disp_w = max(1, disp_w)
        disp_h = max(1, disp_h)

        cx = canvas_w / 2.0 + self.pan_x
        cy = canvas_h / 2.0 + self.pan_y
        x0 = int(cx - disp_w / 2)
        y0 = int(cy - disp_h / 2)

        # roi is in full-res; map to base size
        full_h, full_w = self.img.shape[:2]
        rx0, ry0, rx1, ry1 = self.roi
        rx0, rx1 = sorted([rx0, rx1])
        ry0, ry1 = sorted([ry0, ry1])

        # map full -> base
        bx0 = rx0 / full_w * W
        bx1 = rx1 / full_w * W
        by0 = ry0 / full_h * H
        by1 = ry1 / full_h * H

        # base -> disp
        dx0 = bx0 * rel_zoom
        dx1 = bx1 * rel_zoom
        dy0 = by0 * rel_zoom
        dy1 = by1 * rel_zoom

        # disp -> canvas
        cx0 = x0 + dx0
        cx1 = x0 + dx1
        cy0 = y0 + dy0
        cy1 = y0 + dy1

        self.canvas.create_rectangle(cx0, cy0, cx1, cy1, outline="#00ff99", width=2, dash=(6, 3))

    # ---------------- Coordinate mapping ----------------
    def canvas_to_image_xy(self, cx: float, cy: float) -> Optional[Tuple[int, int]]:
        """Canvas coordinates -> full-res image coordinates"""
        if self.img is None:
            return None

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        base, rel_zoom = self._pick_pyramid_level(self.zoom)
        H, W = base.shape[:2]
        disp_w = max(1, int(W * rel_zoom))
        disp_h = max(1, int(H * rel_zoom))

        center_x = canvas_w / 2.0 + self.pan_x
        center_y = canvas_h / 2.0 + self.pan_y
        top_left_x = center_x - disp_w / 2.0
        top_left_y = center_y - disp_h / 2.0

        # canvas -> disp
        dx = cx - top_left_x
        dy = cy - top_left_y
        if dx < 0 or dy < 0 or dx >= disp_w or dy >= disp_h:
            return None

        # disp -> base
        bx = dx / rel_zoom
        by = dy / rel_zoom

        # base -> full-res
        full_h, full_w = self.img.shape[:2]
        fx = int(bx / W * full_w)
        fy = int(by / H * full_h)
        fx = clamp(fx, 0, full_w - 1)
        fy = clamp(fy, 0, full_h - 1)
        return fx, fy

    # ---------------- Mouse interaction ----------------
    def on_mouse_down(self, e):
        if self.img is None:
            return
        self._last_xy = (e.x, e.y)

        if self._mode == "draw":
            self._drawing = True
            self._draw_at(e.x, e.y)
        elif self._mode == "roi":
            self._roi_dragging = True
            pt = self.canvas_to_image_xy(e.x, e.y)
            if pt is not None:
                self._roi_start = pt
                self.roi = (pt[0], pt[1], pt[0], pt[1])
        else:
            # pan
            pass

    def on_mouse_drag(self, e):
        if self.img is None or self._last_xy is None:
            return
        lx, ly = self._last_xy
        dx = e.x - lx
        dy = e.y - ly
        self._last_xy = (e.x, e.y)

        if self._mode == "draw" and self._drawing:
            self._draw_at(e.x, e.y)
        elif self._mode == "roi" and self._roi_dragging:
            pt = self.canvas_to_image_xy(e.x, e.y)
            if pt is not None and self._roi_start is not None:
                x0, y0 = self._roi_start
                self.roi = (x0, y0, pt[0], pt[1])
                self.render()
        else:
            # pan
            self.pan_x += dx
            self.pan_y += dy
            self.render()

    def on_mouse_up(self, e):
        if self.img is None:
            return
        if self._mode == "draw" and self._drawing:
            self._drawing = False
            self._push_history({"op": "draw"})
        if self._mode == "roi" and self._roi_dragging:
            self._roi_dragging = False
            if self.roi is not None:
                self._push_history({"op": "roi"})
                self.set_status("ROI set (PCA will prefer ROI for fitting)")
        self._last_xy = None

    def on_wheel(self, e):
        # Windows/macOS: delta positive=up
        if e.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def on_wheel_linux(self, e):
        if e.num == 4:
            self.zoom_in()
        else:
            self.zoom_out()

    def _draw_at(self, cx, cy):
        if self.img is None:
            return
        pt = self.canvas_to_image_xy(cx, cy)
        if pt is None:
            return
        x, y = pt
        h, w = self.img.shape[:2]
        if self.draw_mask is None or self.draw_mask.shape[:2] != (h, w):
            self.draw_mask = np.zeros((h, w), dtype=np.uint8)

        # Brush radius: inversely proportional to zoom so the on-screen brush size stays roughly constant
        radius = int(round(self.brush_size * 6 / max(0.25, self.zoom)))
        radius = clamp(radius, 2, 40)
        cv2.circle(self.draw_mask, (x, y), radius, 255, thickness=-1)
        self.render()

    # ---------------- Zoom ----------------
    def zoom_in(self):
        self.zoom = clamp(self.zoom * 1.25, 0.25, 4.0)
        self.render()
        self.set_status(f"Zoom: {self.zoom:.2f}x")

    def zoom_out(self):
        self.zoom = clamp(self.zoom / 1.25, 0.25, 4.0)
        self.render()
        self.set_status(f"Zoom: {self.zoom:.2f}x")

    def reset_zoom(self):
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.render()
        self.set_status("Zoom reset: 1.00x")

    # ---------------- Files ----------------
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All", "*.*")
            ]
        )
        if not path:
            return
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            messagebox.showerror("Error", "Unable to read this image")
            return

        # Normalize to uint8 (simple scaling for 16-bit)
        if img.dtype == np.uint16:
            img = normalize_0_255(img)
        elif img.dtype != np.uint8:
            img = to_uint8(img)

        # Support alpha channel
        if img.ndim == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        self.base_img = img.copy()
        self.img = img.copy()
        self.draw_mask = None
        self.roi = None
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._pc_cache = None
        self._pc_index = 0
        self._rebuild_pyramid()
        self._history = []
        self._hist_i = -1
        self.ops_log = []
        self._push_history({"op": "open", "path": path})
        self.render()
        self.set_status(f"Opened: {os.path.basename(path)}  |  {self.img.shape[1]}x{self.img.shape[0]}")

    def save_image(self):
        if self.img is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("BMP", "*.bmp"), ("TIFF", "*.tif *.tiff")]
        )
        if not path:
            return

        out = self.img.copy()

        # Overlay drawing?
        if self.draw_mask is not None:
            out2 = ensure_color(out)
            overlay = out2.copy()
            overlay[self.draw_mask > 0] = (0, 255, 255)
            out = cv2.addWeighted(out2, 0.78, overlay, 0.22, 0)

        # Use imencode for non-ASCII paths
        ext = os.path.splitext(path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            ok, buf = cv2.imencode(".jpg", out, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        elif ext in [".bmp"]:
            ok, buf = cv2.imencode(".bmp", out)
        elif ext in [".tif", ".tiff"]:
            ok, buf = cv2.imencode(".tif", out)
        else:
            ok, buf = cv2.imencode(".png", out)

        if not ok:
            messagebox.showerror("Error", "Save failed")
            return
        try:
            buf.tofile(path)
        except Exception as e:
            messagebox.showerror("Error", f"Save failed：{e}")
            return

        # Same-name txt log: record processing steps and parameters
        try:
            txt_path = os.path.splitext(path)[0] + ".txt"

            lines: List[str] = []
            # Follow the header structure of 1.txt
            lines.append("Technical")
            lines.append("System Manufacturer: ")
            lines.append("Lights used: ")
            lines.append("Name of photographer: ")
            lines.append("Name of processor: ")
            lines.append("")
            lines.append("Object")
            lines.append("Name (if any): ")
            lines.append("Shelfmark: ")
            lines.append("Material: ")
            lines.append("Institution/owner: ")
            lines.append("")

            # Summarize the 'Processes used' overview
            from collections import Counter

            def _friendly_name(meta: Dict[str, Any]) -> str:
                op = meta.get("op", "")
                if op in ("pseudocolor_current", "pseudocolor_two", "pseudocolor_channel"):
                    ch = meta.get("channel")
                    if ch in ("r", "g", "b", "all"):
                        return f"Pseudocolor-{ch.upper()}"
                    return "Pseudocolor"
                if op in ("sharpen_otsu", "sharpie_binarize"):
                    return "Sharpen(Otsu)"
                if op == "sharpen_fixed":
                    return "Sharpen(128)"
                if op == "power":
                    return "Power"
                if op == "invert":
                    return "Invert"
                if op == "blur_divide":
                    return "Blur&Divide"
                if op == "denoise_gaussian":
                    return "Denoise(Gaussian)"
                if op == "pca":
                    return "PCA"
                if op == "pca_svd":
                    return "PCA-SVD"
                if op == "rotate_90":
                    direction = meta.get("direction", "")
                    return f"Rotate90({direction})"
                return op or "Unknown"

            friendly_ops = [_friendly_name(m) for m in self.ops_log]
            if friendly_ops:
                cnt = Counter(friendly_ops)
                summary_parts = [f"{name} x{c}" for name, c in cnt.items()]
                summary = ", ".join(summary_parts)
            else:
                summary = "None"

            lines.append(f"Processes used: {summary}")
            lines.append("")
            lines.append("Process details:")

            for i, meta in enumerate(self.ops_log, start=1):
                name = _friendly_name(meta)
                params = {k: v for k, v in meta.items() if k != "op"}
                if params:
                    lines.append(f"{i}. {name} | params: {json.dumps(params, ensure_ascii=False)}")
                else:
                    lines.append(f"{i}. {name}")

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            # Only show a warning; do not block successful image saving
            messagebox.showwarning("Warning", f"Image saved, but failed to write log txt: {e}")

        self.set_status(f"Saved: {path}")

    def clear_image(self):
        self.base_img = None
        self.img = None
        self.draw_mask = None
        self.roi = None
        self._pyramid = []
        self._pc_cache = None
        self._pc_index = 0
        self._history = []
        self._hist_i = -1
        self.render()
        self.set_status("Cleared")

    def clear_drawing(self):
        if self.img is None:
            return
        self.draw_mask = None
        self._push_history({"op": "clear_draw"})
        self.render()
        self.set_status("Drawing cleared")

    def clear_roi(self):
        if self.img is None:
            return
        self.roi = None
        self._push_history({"op": "clear_roi"})
        self.render()
        self.set_status("ROI cleared")

    # ---------------- Operation wrapper ----------------
    def _apply_op(self, fn, meta: Dict[str, Any]):
        if self.img is None:
            messagebox.showinfo("Info", "Please open an image first")
            return
        try:
            self.img = fn(self.img)
            if self.img is None:
                raise ValueError("Processing result is empty")
            self._pc_cache = None  # Non-PCA operations clear PCA results
            self._pc_index = 0
            self._rebuild_pyramid()
            self._push_history(meta)
            self.render()
            self.set_status(f"Done: {meta.get('op', 'operation')}")
        except Exception as e:
            messagebox.showerror("Error", f"Operation failed: {e}")

    # ---------------- Image Processing functions ----------------
    def apply_pseudocolor_current(self):
        # Backward compatibility: equivalent to the All channel
        self.apply_pseudocolor_channel("all")

    def apply_pseudocolor_channel(self, channel: str):
        """
        Pseudocolor supports four modes: R / G / B / All:
          - All: based on overall intensity (grayscale)
          - R/G/B: generate pseudocolor based on the selected channel intensity
        """

        ch = str(channel).lower()

        def op(img):
            if ch == "all":
                g = ensure_gray(img)
                return pseudocolor_jet(g)

            # Based on the selected color channel
            color = ensure_color(img)
            if ch == "r":
                src = color[:, :, 2]  # BGR -> R
            elif ch == "g":
                src = color[:, :, 1]
            elif ch == "b":
                src = color[:, :, 0]
            else:
                g = ensure_gray(color)
                return pseudocolor_jet(g)
            src_u8 = to_uint8(src)
            return pseudocolor_jet(src_u8)

        self._apply_op(op, {"op": "pseudocolor_channel", "channel": ch})

    def apply_pseudocolor_two(self):
        paths = filedialog.askopenfilenames(
            title="Select two grayscale images (or any images; they will be converted to grayscale)",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All", "*.*")]
        )
        if not paths or len(paths) < 2:
            return
        p1, p2 = paths[0], paths[1]

        def read_gray(p):
            im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if im is None:
                raise ValueError(f"Cannot read: {p}")
            if im.dtype == np.uint16:
                im = normalize_0_255(im)
            im = to_uint8(im)
            if im.ndim == 3 and im.shape[2] == 4:
                im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
            return ensure_gray(im)

        try:
            g1 = read_gray(p1)
            g2 = read_gray(p2)
            if g1.shape != g2.shape:
                messagebox.showerror("Error", "The two images must have the same size (currently they do not match)")
                return
            mix = cv2.addWeighted(g1, 0.5, g2, 0.5, 0)
            out = pseudocolor_jet(mix)
            self.img = out
            self.base_img = out.copy()
            self.draw_mask = None
            self.roi = None
            self._pc_cache = None
            self._pc_index = 0
            self.zoom = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
            self._rebuild_pyramid()
            self._history = []
            self._hist_i = -1
            self.ops_log = []
            self._push_history({"op": "pseudocolor_two", "p1": p1, "p2": p2})
            self.render()
            self.set_status("Done: Pseudocolor (Merge Two Images)")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def apply_sharpen_otsu(self):
        """Sharpen: Otsu automatic threshold"""

        def op(img):
            return otsu_binarize(img)

        self._apply_op(op, {"op": "sharpen_otsu"})

    def apply_sharpen_fixed(self):
        """Sharpen: fixed threshold 128"""

        def op(img):
            return fixed_binarize(img, thresh=128)

        self._apply_op(op, {"op": "sharpen_fixed", "thresh": 128})

    def apply_power(self):
        if self.img is None:
            return
        gamma = simpledialog.askfloat("Power (Gamma)", "Enter gamma (e.g., 0.5 / 1.2 / 2.0):", initialvalue=1.6, minvalue=0.01, maxvalue=10.0)
        if gamma is None:
            return
        partial = messagebox.askyesno("Partial inversion", "Enable partial inversion?")
        pivot = 128
        if partial:
            pv = simpledialog.askinteger("Partial inversion threshold", "pivot (0–255); pixels > pivot will be inverted:", initialvalue=128, minvalue=0, maxvalue=255)
            if pv is not None:
                pivot = int(pv)

        def op(img):
            return power_transform(img, gamma=float(gamma), partial_invert=bool(partial), pivot=int(pivot))
        self._apply_op(op, {"op": "power", "gamma": gamma, "partial": partial, "pivot": pivot})

    def apply_invert(self):
        """Invert (with Alpha intensity parameter)"""
        if self.img is None:
            return
        alpha = simpledialog.askfloat(
            "Invert",
            "Invert intensity Alpha (0–1; 0 = original, 1 = fully inverted):",
            initialvalue=1.0,
            minvalue=0.0,
            maxvalue=1.0,
        )
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

    def apply_rotate(self, direction: str):
        def op(img):
            return rotate_90(img, direction=direction)
        self._apply_op(op, {"op": "rotate_90", "direction": direction})

    def apply_blur_divide(self):
        if self.img is None:
            return
        k = simpledialog.askinteger("Blur & Divide", "Gaussian kernel size (recommended 21–61, must be odd):", initialvalue=31, minvalue=3, maxvalue=201)
        if k is None:
            return
        sigma = simpledialog.askfloat("Blur & Divide", "sigma (0 = auto):", initialvalue=0.0, minvalue=0.0, maxvalue=50.0)
        if sigma is None:
            return

        def op(img):
            return blur_divide(img, ksize=int(k), sigma=float(sigma))
        self._apply_op(op, {"op": "blur_divide", "ksize": k, "sigma": sigma})

    def apply_denoise(self):
        if self.img is None:
            return
        k = simpledialog.askinteger("Denoise (Gaussian)", "Kernel size (odd, suggested 3/5/7):", initialvalue=5, minvalue=3, maxvalue=51)
        if k is None:
            return
        sigma = simpledialog.askfloat("Denoise (Gaussian)", "sigma (suggested 0.8–2.5):", initialvalue=1.2, minvalue=0.0, maxvalue=10.0)
        if sigma is None:
            return

        def op(img):
            return denoise_gaussian(img, ksize=int(k), sigma=float(sigma))
        self._apply_op(op, {"op": "denoise_gaussian", "ksize": k, "sigma": sigma})

    def apply_pca(self):
        paths = filedialog.askopenfilenames(
            title="Select 3–16 grayscale images (sizes must match)",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All", "*.*")]
        )
        if not paths:
            return
        if len(paths) < 3:
            messagebox.showinfo("Info", "PCA: select at least 3 images")
            return
        if len(paths) > 16:
            messagebox.showinfo("Info", "Maximum 16 images; only the first 16 will be used")
            paths = paths[:16]

        def read_gray(p):
            im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if im is None:
                raise ValueError(f"Cannot read: {p}")
            if im.dtype == np.uint16:
                im = normalize_0_255(im)
            im = to_uint8(im)
            if im.ndim == 3 and im.shape[2] == 4:
                im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
            return ensure_gray(im)

        try:
            imgs = [read_gray(p) for p in paths]
            roi = self.roi  # full-res ROI (for PCA input files, assuming same size and coordinates)
            self.set_status("Computing PCA… (may take a few seconds)")
            self.update_idletasks()

            result = pca_multiband(imgs, roi=roi)
            self._pc_cache = result
            self._pc_index = 0
            pc1 = result["pcs"][0]
            self.img = pc1  # Default to showing PC1
            self.draw_mask = None
            self._rebuild_pyramid()
            self._push_history({"op": "pca", "files": list(paths), "roi": roi})
            self.render()

            ratios = result.get("explained", [])
            tip = ""
            if ratios:
                tip = " | ".join([f"PC{i+1}:{ratios[i]*100:.1f}%" for i in range(min(4, len(ratios)))])
            self.set_status(f"PCA done: showing PC1 (explained variance: {tip})")

        except Exception as e:
            messagebox.showerror("Error", f"PCA failed: {e}")
            self.set_status("PCA failed")

    def apply_pca_svd(self):
        """PCA: SVD-variant implementation"""
        paths = filedialog.askopenfilenames(
            title="Select 3–16 grayscale images (sizes must match; for PCA-SVD)",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All", "*.*")]
        )
        if not paths:
            return
        if len(paths) < 3:
            messagebox.showinfo("Info", "PCA (SVD): select at least 3 images")
            return
        if len(paths) > 16:
            messagebox.showinfo("Info", "Maximum 16 images; only the first 16 will be used")
            paths = paths[:16]

        def read_gray(p):
            im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if im is None:
                raise ValueError(f"Cannot read: {p}")
            if im.dtype == np.uint16:
                im = normalize_0_255(im)
            im = to_uint8(im)
            if im.ndim == 3 and im.shape[2] == 4:
                im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
            return ensure_gray(im)

        try:
            imgs = [read_gray(p) for p in paths]
            roi = self.roi
            self.set_status("Computing PCA (SVD)… (may take a few seconds)")
            self.update_idletasks()

            result = pca_multiband_svd_variant(imgs, roi=roi)
            self._pc_cache = result
            self._pc_index = 0
            pc1 = result["pcs"][0]
            self.img = pc1
            self.draw_mask = None
            self._rebuild_pyramid()
            self._push_history({"op": "pca_svd", "files": list(paths), "roi": roi})
            self.render()

            ratios = result.get("explained", [])
            tip = ""
            if ratios:
                tip = " | ".join([f"PC{i+1}:{ratios[i]*100:.1f}%" for i in range(min(4, len(ratios)))])
            self.set_status(f"PCA (SVD) done: showing PC1 (explained variance: {tip})")

        except Exception as e:
            messagebox.showerror("Error", f"PCA (SVD) failed: {e}")
            self.set_status("PCA (SVD) failed")

    def next_pc(self):
        if not self._pc_cache or "pcs" not in self._pc_cache:
            self.set_status("No PCA result found: run PCA first")
            return
        pcs = self._pc_cache["pcs"]
        self._pc_index = (self._pc_index + 1) % len(pcs)
        self.img = pcs[self._pc_index].copy()
        self.draw_mask = None
        self._rebuild_pyramid()
        self._push_history({"op": "pca_switch", "pc_index": self._pc_index})
        self.render()

        ratios = self._pc_cache.get("explained", [])
        r = ratios[self._pc_index] * 100.0 if self._pc_index < len(ratios) else None
        if r is None:
            self.set_status(f"Showing: PC{self._pc_index+1}")
        else:
            self.set_status(f"Showing: PC{self._pc_index+1} (explained variance {r:.1f}%)")


def main():
    try:
        cv2.setNumThreads(0)
    except Exception:
        pass

    app = ProteusApp()
    app.mainloop()


if __name__ == "__main__":
    main()
