#!/usr/bin/env bash
#
# Proteus Linux / macOS build script
#
# Usage:
#   bash packaging/build.sh              -- full build (venv + tests + PyInstaller)
#   bash packaging/build.sh --skip-tests -- skip pytest step
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Proteus Build Script ==="
echo ""

# ---- Parse args ----
SKIP_TESTS=0
for arg in "$@"; do
    [[ "$arg" == "--skip-tests" ]] && SKIP_TESTS=1
done

# ---- Check Python ----
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" &>/dev/null; then
    echo "ERROR: $PYTHON not found. Install Python 3.10+ and try again."
    exit 1
fi
echo "Using Python: $($PYTHON --version)"

# ---- Create/activate venv if needed ----
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv .venv
fi
PYTHON=".venv/bin/python"

# ---- Install dependencies ----
echo ""
echo "Installing dependencies..."
"$PYTHON" -m pip install --upgrade pip --quiet
"$PYTHON" -m pip install -e ".[dev]" --quiet

# ---- Run tests ----
if [ "$SKIP_TESTS" -eq 0 ]; then
    echo ""
    echo "Running tests..."
    "$PYTHON" -m pytest tests/ -v
else
    echo ""
    echo "Skipping tests."
fi

# ---- Run PyInstaller ----
echo ""
echo "Building Proteus..."
"$PYTHON" -m PyInstaller --clean --noconfirm packaging/Proteus.spec

# ---- Archive ----
echo ""
echo "Archiving..."
if [[ "$(uname)" == "Darwin" ]]; then
    ARCHIVE="Proteus-macos.tar.gz"
    # macOS: bundle the .app if it exists, else the folder
    if [ -d "dist/Proteus.app" ]; then
        tar -czf "$ARCHIVE" -C dist Proteus.app
    else
        tar -czf "$ARCHIVE" -C dist Proteus
    fi
else
    ARCHIVE="Proteus-linux.tar.gz"
    tar -czf "$ARCHIVE" -C dist Proteus
fi
echo "Archive: $ARCHIVE  ($(du -sh "$ARCHIVE" | cut -f1))"

# ---- Report ----
echo ""
echo "=== Build complete ==="
if [ -f "dist/Proteus/Proteus" ]; then
    echo "Output (onedir): dist/Proteus/"
elif [ -d "dist/Proteus.app" ]; then
    echo "Output (macOS app): dist/Proteus.app"
else
    echo "Output directory: dist/"
fi
