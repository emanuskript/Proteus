# Proteus

<p align="center">
  <img src="src/proteus/resources/Proteus.png" alt="Proteus Logo" width="180">
</p>

<p align="center">
  <strong>Scientific Image Processing Desktop Application</strong>
</p>

---

Proteus is a desktop application for scientific image processing, built with PySide6 (Qt) and OpenCV. It provides an interactive canvas with real-time tools for enhancement, analysis, and visualization of grayscale and multi-band imagery.

## Features

- **Image Enhancement** — Histogram equalization, power-law (gamma) transform, partial inversion, pseudocolor mapping
- **Noise Reduction** — Gaussian denoising, blur-divide background correction
- **Segmentation** — Otsu and fixed-threshold binarization
- **PCA Analysis** — Covariance and SVD-based principal component analysis for multi-band images
- **Drawing Tools** — Freehand brush for mask creation and region annotation
- **ROI Selection** — Region-of-interest cropping
- **Undo/Redo** — Full undo history via Qt's QUndoStack
- **Dark Theme** — Built-in dark UI theme

## Requirements

- Python 3.10+
- PySide6 >= 6.5.0
- OpenCV >= 4.8.0
- NumPy >= 1.24.0

## Installation

```bash
# Clone the repository
git clone https://github.com/yiyang26/Proteus.git
cd Proteus

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Run via entry point
proteus

# Or run as a module
python -m proteus
```

## Running Tests

```bash
pytest
```

## Building a Standalone Executable

```bash
# Install dev dependencies (includes PyInstaller)
pip install -e ".[dev]"

# Build
pyinstaller --clean --noconfirm packaging/Proteus.spec

# Output is in dist/Proteus/
./dist/Proteus/Proteus
```

> **Note:** The build is platform-specific — build on Linux for Linux, on macOS for macOS, on Windows for Windows.

## Project Structure

```
Proteus/
├── src/proteus/
│   ├── core/              # Processing logic (no UI dependencies)
│   │   ├── processing.py  # Image enhancement & filtering functions
│   │   ├── pca.py         # Principal component analysis
│   │   ├── image_io.py    # Image load/save utilities
│   │   ├── state.py       # ImageState & operation logging
│   │   └── utils.py       # Shared helpers
│   ├── ui/                # PySide6 interface
│   │   ├── main_window.py # Main application window
│   │   ├── canvas.py      # Interactive image canvas (QGraphicsView)
│   │   ├── sidebar.py     # Tool buttons panel
│   │   ├── dialogs.py     # Parameter input dialogs
│   │   ├── theme.py       # Dark theme styling
│   │   └── status_bar.py  # Status bar widget
│   ├── commands/           # QUndoCommand implementations
│   ├── resources/          # App icon and assets
│   └── app.py             # Application entry point
├── tests/                  # Test suite
├── packaging/              # PyInstaller spec & build script
└── pyproject.toml          # Project metadata & dependencies
```

## License

See [LICENSE](LICENSE) for details.
