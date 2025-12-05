#!/bin/bash

# RM-01 Internet Connector Build Script
# This script builds the app and creates a proper .app bundle with icons

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="RM-01 Internet Connector"
BUNDLE_ID="com.rm01.internetconnector"
VERSION="1.0.0"

echo "🔨 Building RM-01 Internet Connector..."

# Clean previous builds
rm -rf "$PROJECT_DIR/dist"
mkdir -p "$PROJECT_DIR/dist"

# Build the Swift package
cd "$PROJECT_DIR"
swift build -c release

# Get the built executable path
EXECUTABLE=$(swift build -c release --show-bin-path)/RM01InternetConnector

if [ ! -f "$EXECUTABLE" ]; then
    echo "❌ Build failed: executable not found"
    exit 1
fi

echo "✅ Build successful"

# Create app bundle structure
APP_BUNDLE="$PROJECT_DIR/dist/$APP_NAME.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy executable
cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/RM01InternetConnector"

# Copy the resource bundle (required for Bundle.module to work)
BUILT_BUNDLE="$PROJECT_DIR/.build/release/RM01InternetConnector_RM01InternetConnector.bundle"
if [ -d "$BUILT_BUNDLE" ]; then
    cp -R "$BUILT_BUNDLE" "$APP_BUNDLE/Contents/Resources/"
    echo "✅ Resource bundle copied"
fi

# Also copy icons directly to Resources root for Info.plist
cp "$PROJECT_DIR/Sources/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/AppIcon.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/statusIcon.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/statusIcon@2x.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true

# Create Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>RM01InternetConnector</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIconName</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ App bundle created at: $APP_BUNDLE"

# Optional: Create DMG
echo "📦 Creating DMG..."
DMG_PATH="$PROJECT_DIR/dist/$APP_NAME.dmg"
rm -f "$DMG_PATH"

# Create a temporary directory for DMG contents
DMG_TEMP="$PROJECT_DIR/dist/dmg_temp"
mkdir -p "$DMG_TEMP"
cp -R "$APP_BUNDLE" "$DMG_TEMP/"

# Create symbolic link to Applications
ln -s /Applications "$DMG_TEMP/Applications"

# Create DMG
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TEMP" -ov -format UDZO "$DMG_PATH"

# Cleanup
rm -rf "$DMG_TEMP"

echo "✅ DMG created at: $DMG_PATH"
echo ""
echo "🎉 Build complete!"
echo "   App: $APP_BUNDLE"
echo "   DMG: $DMG_PATH"
