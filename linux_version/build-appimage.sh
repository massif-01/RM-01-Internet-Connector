#!/bin/bash
#
# RM-01 Internet Connector - AppImage Build Script
# Builds a fully self-contained AppImage with all dependencies
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

echo "📦 Installing Python dependencies..."
pip3 install --user PyQt5 pyinstaller

echo "🔧 Building with PyInstaller (onedir mode for AppImage)..."
cd "$SCRIPT_DIR"

# Use onedir mode so we can bundle everything properly
pyinstaller --clean --noconfirm \
    --name rm01-internet-connector \
    --onedir \
    --windowed \
    --add-data "assets:assets" \
    --hidden-import PyQt5.sip \
    --hidden-import PyQt5.QtCore \
    --hidden-import PyQt5.QtGui \
    --hidden-import PyQt5.QtWidgets \
    --distpath "$BUILD_DIR/pyinstaller_dist" \
    --workpath "$BUILD_DIR/pyinstaller_work" \
    --specpath "$BUILD_DIR" \
    main.py

echo "📁 Creating AppDir structure..."

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy the entire PyInstaller output directory
cp -r "$BUILD_DIR/pyinstaller_dist/rm01-internet-connector/"* "$APPDIR/usr/bin/"

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

# Create AppRun script that sets up the environment properly
cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Set up library paths
export LD_LIBRARY_PATH="${HERE}/usr/bin:${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Set Qt plugin path
export QT_PLUGIN_PATH="${HERE}/usr/bin/PyQt5/Qt5/plugins:${QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/bin/PyQt5/Qt5/plugins/platforms"

# Set XDG paths
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"

# Run the application
exec "${HERE}/usr/bin/rm01-internet-connector" "$@"
APPRUN_EOF
chmod +x "$APPDIR/AppRun"

# Bundle additional system libraries that might be missing
echo "📚 Bundling additional libraries..."

# Find and copy libxcb-xinerama if available on the system
for lib in libxcb-xinerama.so.0 libxcb-cursor.so.0 libxcb-util.so.1; do
    LIB_PATH=$(ldconfig -p | grep "$lib" | head -1 | awk '{print $NF}')
    if [ -n "$LIB_PATH" ] && [ -f "$LIB_PATH" ]; then
        echo "   Bundling $lib"
        cp "$LIB_PATH" "$APPDIR/usr/bin/" 2>/dev/null || true
    fi
done

echo "📦 Creating AppImage..."

# Download appimagetool if not available
APPIMAGETOOL="$BUILD_DIR/appimagetool"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "   Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "${APPIMAGETOOL}.AppImage"
    chmod +x "${APPIMAGETOOL}.AppImage"
    
    # Extract it to avoid FUSE requirement
    cd "$BUILD_DIR"
    ./"appimagetool.AppImage" --appimage-extract > /dev/null 2>&1
    mv squashfs-root appimagetool_extracted
    APPIMAGETOOL="$BUILD_DIR/appimagetool_extracted/AppRun"
    cd "$SCRIPT_DIR"
fi

# Create AppImage
OUTPUT_APPIMAGE="$DIST_DIR/RM-01_Internet_Connector-$VERSION-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT_APPIMAGE"

# Make it executable
chmod +x "$OUTPUT_APPIMAGE"

echo ""
echo "✅ Build complete!"
echo "   AppImage: $OUTPUT_APPIMAGE"
echo ""
echo "To run the AppImage:"
echo "   $OUTPUT_APPIMAGE"
echo ""
echo "Or copy it anywhere and run:"
echo "   chmod +x RM-01_Internet_Connector-$VERSION-x86_64.AppImage"
echo "   ./RM-01_Internet_Connector-$VERSION-x86_64.AppImage"
