#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Proteus Build Script ==="
echo ""

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
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -e ".[dev]"

# ---- Run tests ----
echo ""
echo "Running tests..."
"$PYTHON" -m pytest tests/ -v

# ---- Run PyInstaller ----
echo ""
echo "Building Proteus..."
"$PYTHON" -m PyInstaller --clean --noconfirm packaging/Proteus.spec

# ---- Report ----
echo ""
echo "=== Build complete ==="
if [ -f "dist/Proteus/Proteus" ] || [ -f "dist/Proteus/Proteus.exe" ]; then
    echo "Output (onedir): dist/Proteus/"
elif [ -f "dist/Proteus" ] || [ -f "dist/Proteus.exe" ]; then
    echo "Output (onefile): dist/Proteus"
else
    echo "Output directory: dist/"
fi
