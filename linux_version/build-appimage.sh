#!/bin/bash
#
# RM-01 Internet Connector - AppImage Build Script
# Builds a standalone AppImage for Linux distribution
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="RM-01 Internet Connector"
APP_ID="com.rminte.rm01-internet-connector"
VERSION="1.1.1"

echo "🔨 Building RM-01 Internet Connector AppImage..."
echo "   Version: $VERSION"
echo ""

# Check dependencies
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ Required command not found: $1"
        echo "   Please install it first."
        exit 1
    fi
}

check_command python3
check_command pip3

# Create build directory
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"
APPDIR="$BUILD_DIR/AppDir"

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR" "$APPDIR"

echo "📦 Installing dependencies..."
pip3 install --user PyQt5 pyinstaller

echo "🔧 Building with PyInstaller..."
cd "$SCRIPT_DIR"

# Create PyInstaller spec for better control
# Use absolute paths directly
cat > "$BUILD_DIR/rm01.spec" << EOF
# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Use absolute paths
SRC_DIR = '$SCRIPT_DIR'

a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[
        (os.path.join(SRC_DIR, 'assets'), 'assets'),
    ],
    hiddenimports=['PyQt5.sip', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='rm01-internet-connector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SRC_DIR, 'assets', 'icon.png') if os.path.exists(os.path.join(SRC_DIR, 'assets', 'icon.png')) else None,
)
EOF

pyinstaller --clean --noconfirm "$BUILD_DIR/rm01.spec"

echo "📁 Creating AppDir structure..."

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/64x64/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/32x32/apps"

# Copy executable
cp "$SCRIPT_DIR/dist/rm01-internet-connector" "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/rm01-internet-connector"

# Copy icon
if [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
    cp "$SCRIPT_DIR/assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/rm01-internet-connector.png"
    cp "$SCRIPT_DIR/assets/icon.png" "$APPDIR/rm01-internet-connector.png"
fi

# Create .desktop file
cat > "$APPDIR/usr/share/applications/rm01-internet-connector.desktop" << EOF
[Desktop Entry]
Type=Application
Name=RM-01 Internet Connector
Comment=Share internet connection with RM-01 devices
Exec=rm01-internet-connector
Icon=rm01-internet-connector
Categories=Network;Utility;
Keywords=RM-01;Internet;Network;Sharing;
StartupNotify=true
Terminal=false
EOF

# Copy to AppDir root
cp "$APPDIR/usr/share/applications/rm01-internet-connector.desktop" "$APPDIR/"

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/rm01-internet-connector" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo "📦 Creating AppImage..."

# Download appimagetool if not available
APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "   Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Create AppImage
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$DIST_DIR/RM-01_Internet_Connector-$VERSION-x86_64.AppImage"

echo ""
echo "✅ Build complete!"
echo "   AppImage: $DIST_DIR/RM-01_Internet_Connector-$VERSION-x86_64.AppImage"
echo ""
echo "To run the AppImage:"
echo "   chmod +x '$DIST_DIR/RM-01_Internet_Connector-$VERSION-x86_64.AppImage'"
echo "   '$DIST_DIR/RM-01_Internet_Connector-$VERSION-x86_64.AppImage'"
