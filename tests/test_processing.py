"""Unit tests for core/processing.py."""

import numpy as np
import pytest

from proteus.core.processing import (
    to_uint8, ensure_gray, ensure_color, normalize_0_255,
    hist_equalize, pseudocolor_jet, otsu_binarize, fixed_binarize,
    power_transform, blur_divide, denoise_gaussian, rotate_90,
)


class TestToUint8:
    def test_already_uint8(self):
        img = np.array([[0, 128, 255]], dtype=np.uint8)
        result = to_uint8(img)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, img)

    def test_float_image(self):
        img = np.array([[0.0, 128.5, 300.0]], dtype=np.float32)
        result = to_uint8(img)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, [[0, 128, 255]])

    def test_none_returns_none(self):
        assert to_uint8(None) is None


class TestEnsureGray:
    def test_already_gray(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        result = ensure_gray(img)
        assert result.ndim == 2

    def test_bgr_to_gray(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        result = ensure_gray(img)
        assert result.ndim == 2
        assert result.shape == (10, 10)

    def test_none_returns_none(self):
        assert ensure_gray(None) is None


class TestEnsureColor:
    def test_already_color(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        result = ensure_color(img)
        assert result.ndim == 3

    def test_gray_to_bgr(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        result = ensure_color(img)
        assert result.ndim == 3
        assert result.shape == (10, 10, 3)

    def test_none_returns_none(self):
        assert ensure_color(None) is None


class TestNormalize:
    def test_basic(self):
        img = np.array([[0, 50, 100]], dtype=np.uint8)
        result = normalize_0_255(img)
        assert result.dtype == np.uint8
        assert result.min() == 0
        assert result.max() == 255

    def test_constant_image(self):
        img = np.full((5, 5), 128, dtype=np.uint8)
        result = normalize_0_255(img)
        np.testing.assert_array_equal(result, np.zeros((5, 5), dtype=np.uint8))

    def test_none_returns_none(self):
        assert normalize_0_255(None) is None


class TestHistEqualize:
    def test_grayscale(self):
        img = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
        result = hist_equalize(img)
        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_color(self):
        img = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        result = hist_equalize(img)
        assert result.shape == img.shape


class TestPseudocolorJet:
    def test_output_is_color(self):
        gray = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        result = pseudocolor_jet(gray)
        assert result.ndim == 3
        assert result.shape == (20, 20, 3)


class TestBinarize:
    def test_otsu(self):
        img = np.random.randint(0, 256, (30, 30), dtype=np.uint8)
        result = otsu_binarize(img)
        assert set(np.unique(result)).issubset({0, 255})

    def test_fixed(self):
        img = np.array([[50, 150]], dtype=np.uint8)
        result = fixed_binarize(img, thresh=128)
        np.testing.assert_array_equal(result, [[0, 255]])


class TestPowerTransform:
    def test_gamma_1(self):
        img = np.array([[100, 200]], dtype=np.uint8)
        result = power_transform(img, gamma=1.0)
        np.testing.assert_array_equal(result, img)

    def test_gamma_greater_than_1(self):
        img = np.array([[128]], dtype=np.uint8)
        result = power_transform(img, gamma=2.0)
        assert result[0, 0] < 128  # darker

    def test_partial_invert(self):
        img = np.array([[100, 200]], dtype=np.uint8)
        result = power_transform(img, gamma=1.0, partial_invert=True, pivot=128)
        assert result[0, 0] == 100  # below pivot, unchanged
        assert result[0, 1] == 55   # above pivot, inverted


class TestBlurDivide:
    def test_output_shape(self):
        img = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
        result = blur_divide(img, ksize=5)
        assert result.shape == img.shape

    def test_even_ksize_corrected(self):
        img = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
        result = blur_divide(img, ksize=4)  # should become 5
        assert result.shape == img.shape


class TestDenoiseGaussian:
    def test_output_shape(self):
        img = np.random.randint(0, 256, (30, 30), dtype=np.uint8)
        result = denoise_gaussian(img, ksize=3)
        assert result.shape == img.shape


class TestRotate90:
    def test_rotate_left(self):
        img = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        result = rotate_90(img, "left")
        assert result.shape == (2, 2)

    def test_rotate_right(self):
        img = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        result = rotate_90(img, "right")
        assert result.shape == (2, 2)

    def test_none_returns_none(self):
        assert rotate_90(None, "left") is None
