"""Parameter input dialogs for image processing operations."""

from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QCheckBox, QDialogButtonBox, QLineEdit
)


class GammaDialog(QDialog):
    """Combined gamma + partial inversion + pivot input dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Power (Gamma)")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Gamma (e.g., 0.5 / 1.2 / 2.0):"))
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.01, 10.0)
        self.gamma_spin.setValue(1.6)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.setDecimals(2)
        layout.addWidget(self.gamma_spin)

        self.partial_check = QCheckBox("Enable partial inversion")
        layout.addWidget(self.partial_check)

        layout.addWidget(QLabel("Pivot (0-255, pixels > pivot inverted):"))
        self.pivot_spin = QSpinBox()
        self.pivot_spin.setRange(0, 255)
        self.pivot_spin.setValue(128)
        self.pivot_spin.setEnabled(False)
        layout.addWidget(self.pivot_spin)

        self.partial_check.toggled.connect(self.pivot_spin.setEnabled)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Optional[Tuple[float, bool, int]]:
        """Show dialog, return (gamma, partial_invert, pivot) or None."""
        if self.exec() == QDialog.Accepted:
            return (self.gamma_spin.value(), self.partial_check.isChecked(), self.pivot_spin.value())
        return None


class InvertDialog(QDialog):
    """Alpha (inversion intensity) input dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invert")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Invert intensity Alpha (0-1; 0=original, 1=fully inverted):"))
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setValue(1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setDecimals(2)
        layout.addWidget(self.alpha_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_value(self) -> Optional[float]:
        if self.exec() == QDialog.Accepted:
            return self.alpha_spin.value()
        return None


class BlurDivideDialog(QDialog):
    """Kernel size + sigma input for Blur & Divide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Blur & Divide")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Gaussian kernel size (odd, recommended 21-61):"))
        self.ksize_spin = QSpinBox()
        self.ksize_spin.setRange(3, 201)
        self.ksize_spin.setValue(31)
        self.ksize_spin.setSingleStep(2)
        layout.addWidget(self.ksize_spin)

        layout.addWidget(QLabel("Sigma (0 = auto):"))
        self.sigma_spin = QDoubleSpinBox()
        self.sigma_spin.setRange(0.0, 50.0)
        self.sigma_spin.setValue(0.0)
        self.sigma_spin.setSingleStep(0.5)
        layout.addWidget(self.sigma_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Optional[Tuple[int, float]]:
        if self.exec() == QDialog.Accepted:
            k = self.ksize_spin.value()
            if k % 2 == 0:
                k += 1
            return (k, self.sigma_spin.value())
        return None


class BandLabelDialog(QDialog):
    """Ask the user for short labels for two merged bands (e.g. UV, IR)."""

    def __init__(self, filename1: str, filename2: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Band Labels")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Label for band 1  ({filename1}):"))
        self.label1 = QLineEdit()
        self.label1.setPlaceholderText("e.g. UV")
        layout.addWidget(self.label1)

        layout.addWidget(QLabel(f"Label for band 2  ({filename2}):"))
        self.label2 = QLineEdit()
        self.label2.setPlaceholderText("e.g. IR")
        layout.addWidget(self.label2)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Optional[tuple[str, str]]:
        if self.exec() == QDialog.Accepted:
            l1 = self.label1.text().strip() or "Band1"
            l2 = self.label2.text().strip() or "Band2"
            return (l1, l2)
        return None


class ThresholdDialog(QDialog):
    """Custom binarization threshold input (0-255)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("B/W Custom Threshold")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Threshold (0-255):"))
        self.thresh_spin = QSpinBox()
        self.thresh_spin.setRange(0, 255)
        self.thresh_spin.setValue(128)
        layout.addWidget(self.thresh_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_value(self) -> Optional[int]:
        if self.exec() == QDialog.Accepted:
            return self.thresh_spin.value()
        return None


class DenoiseDialog(QDialog):
    """Kernel size + sigma input for Gaussian denoising."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Denoise (Gaussian)")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Kernel size (odd, suggested 3/5/7):"))
        self.ksize_spin = QSpinBox()
        self.ksize_spin.setRange(3, 51)
        self.ksize_spin.setValue(5)
        self.ksize_spin.setSingleStep(2)
        layout.addWidget(self.ksize_spin)

        layout.addWidget(QLabel("Sigma (suggested 0.8-2.5):"))
        self.sigma_spin = QDoubleSpinBox()
        self.sigma_spin.setRange(0.0, 10.0)
        self.sigma_spin.setValue(1.2)
        self.sigma_spin.setSingleStep(0.1)
        layout.addWidget(self.sigma_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> Optional[Tuple[int, float]]:
        if self.exec() == QDialog.Accepted:
            k = self.ksize_spin.value()
            if k % 2 == 0:
                k += 1
            return (k, self.sigma_spin.value())
        return None
