"""PCA multiband analysis functions. No UI dependencies.

Copied verbatim from Refactor/main.py (lines 246-407).
"""

from typing import Optional, List, Tuple, Dict, Any

import numpy as np

from proteus.core.utils import clamp
from proteus.core.processing import normalize_0_255


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
