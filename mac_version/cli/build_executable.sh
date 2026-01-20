#!/bin/bash
# RM-01 Internet Connector - macOS CLI Build Script
# Builds standalone executable using PyInstaller

set -e  # Exit on error

echo "========================================"
echo "RM-01 CLI - Build Executable (macOS)"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from python.org or use Homebrew:"
    echo "  brew install python3"
    exit 1
fi

echo "[1/4] Installing dependencies..."
pip3 install -r requirements.txt || {
    echo "ERROR: Failed to install dependencies"
    exit 1
}

echo ""
echo "[2/4] Installing PyInstaller..."
pip3 install pyinstaller || {
    echo "ERROR: Failed to install PyInstaller"
    exit 1
}

echo ""
echo "[3/4] Building executable..."

# Check if icon exists
ICON_PATH="../../icons/icon.png"
if [ -f "$ICON_PATH" ]; then
    ICON_PARAM="--icon=$ICON_PATH"
else
    echo "Warning: Icon file not found at $ICON_PATH"
    ICON_PARAM=""
fi

# Build with PyInstaller
pyinstaller --onefile \
    --name rm01-cli \
    $ICON_PARAM \
    --console \
    --clean \
    --noupx \
    --add-data "network_service_macos.py:." \
    cli.py || {
    echo "ERROR: PyInstaller build failed"
    exit 1
}

echo ""
echo "[4/4] Build complete!"
echo ""
echo "Executable location: dist/rm01-cli"
echo ""
echo "Usage:"
echo "  ./dist/rm01-cli status      - Show connection status"
echo "  ./dist/rm01-cli detect      - Detect RM-01 adapter"
echo "  sudo ./dist/rm01-cli connect     - Enable internet sharing"
echo "  sudo ./dist/rm01-cli disconnect  - Disable internet sharing"
echo ""
echo "Note: Network configuration requires sudo privileges"
echo ""
echo "To install globally:"
echo "  sudo cp dist/rm01-cli /usr/local/bin/"
echo "  # Then use: rm01-cli status"
echo ""
