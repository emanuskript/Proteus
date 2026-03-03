"""Core processing module - no UI dependencies."""

from proteus.core.utils import resource_path, clamp
from proteus.core.processing import (
    to_uint8, ensure_gray, ensure_color, normalize_0_255,
    hist_equalize, pseudocolor_jet, otsu_binarize, fixed_binarize,
    power_transform, blur_divide, denoise_gaussian, rotate_90,
)
from proteus.core.pca import pca_multiband, pca_multiband_svd_variant
from proteus.core.image_io import load_image, load_as_gray, save_image
from proteus.core.state import ImageState, OperationLog
