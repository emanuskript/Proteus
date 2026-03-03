"""Unit tests for core/pca.py."""

import numpy as np
import pytest

from proteus.core.pca import pca_multiband, pca_multiband_svd_variant


def _make_test_images(n=4, h=20, w=20):
    """Create n random grayscale test images."""
    rng = np.random.RandomState(42)
    return [rng.randint(0, 256, (h, w), dtype=np.uint8) for _ in range(n)]


class TestPcaMultiband:
    def test_basic_output(self):
        imgs = _make_test_images(4)
        result = pca_multiband(imgs)
        assert "pcs" in result
        assert "explained" in result
        assert "mean" in result
        assert len(result["pcs"]) > 0
        assert result["pcs"][0].shape == (20, 20)
        assert result["pcs"][0].dtype == np.uint8

    def test_explained_variance_sums_to_1(self):
        imgs = _make_test_images(5)
        result = pca_multiband(imgs)
        total = sum(result["explained"])
        assert abs(total - 1.0) < 1e-6

    def test_with_roi(self):
        imgs = _make_test_images(4)
        result = pca_multiband(imgs, roi=(2, 2, 15, 15))
        assert len(result["pcs"]) > 0
        assert result["pcs"][0].shape == (20, 20)  # full image output

    def test_min_3_images(self):
        imgs = _make_test_images(2)
        with pytest.raises(ValueError, match="at least 3"):
            pca_multiband(imgs)

    def test_mismatched_sizes(self):
        imgs = [
            np.zeros((20, 20), dtype=np.uint8),
            np.zeros((20, 20), dtype=np.uint8),
            np.zeros((30, 30), dtype=np.uint8),
        ]
        with pytest.raises(ValueError, match="same size"):
            pca_multiband(imgs)

    def test_max_8_components(self):
        imgs = _make_test_images(10)
        result = pca_multiband(imgs)
        assert len(result["pcs"]) <= 8


class TestPcaSvdVariant:
    def test_basic_output(self):
        imgs = _make_test_images(4)
        result = pca_multiband_svd_variant(imgs)
        assert "pcs" in result
        assert "explained" in result
        assert "U" in result
        assert "S" in result
        assert len(result["pcs"]) > 0
        assert result["pcs"][0].shape == (20, 20)

    def test_explained_variance_sums_to_1(self):
        imgs = _make_test_images(5)
        result = pca_multiband_svd_variant(imgs)
        total = sum(result["explained"])
        assert abs(total - 1.0) < 1e-6

    def test_with_roi(self):
        imgs = _make_test_images(4)
        result = pca_multiband_svd_variant(imgs, roi=(2, 2, 15, 15))
        assert len(result["pcs"]) > 0

    def test_min_3_images(self):
        imgs = _make_test_images(2)
        with pytest.raises(ValueError, match="at least 3"):
            pca_multiband_svd_variant(imgs)

    def test_max_components(self):
        imgs = _make_test_images(4)
        result = pca_multiband_svd_variant(imgs, max_components=2)
        assert len(result["pcs"]) == 2
