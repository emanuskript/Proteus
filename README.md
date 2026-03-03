# Proteus

<p align="center">
  <img src="src/proteus/resources/Proteus.png" alt="Proteus Logo" width="180">
</p>

<p align="center">
  <strong>Proteus</strong>
</p>

---

Proteus is a desktop application for scientific image processing, built with PySide6 (Qt) and OpenCV. It provides an interactive canvas with real-time tools for enhancement, analysis, and visualization of grayscale and multi-band imagery.

## Features

- **Image Enhancement** — Histogram equalization, power-law (gamma) transform, partial inversion, pseudocolor mapping (JET colormap)
- **Sharpen / Binarize** — Unsharp mask (Original), Otsu auto-threshold (B/W Auto), fixed threshold at 128 (B/W 128), custom threshold dialog (B/W Custom)
- **Noise Reduction** — Gaussian denoising, blur-divide background correction
- **Multi-Band Pseudocolor** — Merge two images with custom band labels (e.g. UV + IR), blend 50/50, apply JET colormap
- **PCA Analysis** — Covariance and SVD-based principal component analysis for multi-band images (3–16 images), with Prev/Next result navigation
- **Drawing Tools** — Freehand brush for mask creation and region annotation
- **ROI Selection** — Region-of-interest cropping, auto-applied to PCA
- **Undo/Redo** — Full operation history with Undo/Redo support
- **Themes** — Light, Dark, and High-Contrast themes with a one-click toggle, persisted across sessions

## Requirements

- Python 3.10+
- PySide6 >= 6.5.0
- OpenCV >= 4.8.0
- NumPy >= 1.24.0

## Installation (development)

```bash
# Clone the repository
git clone https://github.com/yiyang26/Proteus.git
cd Proteus

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

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

The build scripts handle everything: creating a venv, installing dependencies, running tests, and producing an archive.

> **Note:** Build on the target platform — Linux build for Linux, macOS for macOS, Windows for Windows.

### Linux

```bash
bash packaging/build.sh

# Skip tests
bash packaging/build.sh --skip-tests
```

Output: `dist/Proteus/` + `Proteus-linux.tar.gz`

### macOS

**One-time icon prep** (requires macOS):
```bash
mkdir -p packaging/Proteus.iconset
sips -z 1024 1024 src/proteus/resources/Proteus.png \
    --out packaging/Proteus.iconset/icon_512x512@2x.png
iconutil -c icns packaging/Proteus.iconset -o packaging/Proteus.icns
```

```bash
bash packaging/build.sh

# Skip tests
bash packaging/build.sh --skip-tests
```

Output: `dist/Proteus.app` + `Proteus-macos.tar.gz`

### Windows

**One-time icon prep** (requires [ImageMagick](https://imagemagick.org)):
```bat
magick src\proteus\resources\Proteus.png ^
    -define icon:auto-resize=256,128,64,32,16 packaging\Proteus.ico
```

```bat
packaging\build.bat

:: Skip tests
packaging\build.bat --skip-tests
```

Output: `dist\Proteus\Proteus.exe` + `Proteus-windows.zip`

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
│   │   ├── main_window.py # Main application window & signal wiring
│   │   ├── canvas.py      # Interactive image canvas (QGraphicsView)
│   │   ├── top_bar.py     # Logo, title, and theme toggle button
│   │   ├── sidebar.py     # Collapsible tool panels
│   │   ├── status_bar.py  # Status text and zoom controls
│   │   ├── dialogs.py     # Parameter input dialogs
│   │   └── theme.py       # Light / Dark / High-Contrast QSS theming
│   ├── resources/          # App icon and assets
│   └── app.py             # Application entry point
├── tests/                  # Test suite
├── packaging/              # Build scripts and PyInstaller spec
│   ├── Proteus.spec        # PyInstaller configuration
│   ├── version_info.txt    # Windows EXE version metadata
│   ├── build.sh            # Linux / macOS build script
│   └── build.bat           # Windows build script
└── pyproject.toml          # Project metadata & dependencies
```

## License

See [LICENSE](LICENSE) for details.
