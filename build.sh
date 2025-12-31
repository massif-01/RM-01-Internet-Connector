#!/bin/bash

# RM-01 Internet Connector Build Script
# This script builds the app and creates a proper .app bundle with icons

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="RM-01 Internet Connector"
BUNDLE_ID="com.rm01.internetconnector"
VERSION="1.0.6"

echo "🔨 Building RM-01 Internet Connector..."

# Clean previous builds
rm -rf "$PROJECT_DIR/dist"
mkdir -p "$PROJECT_DIR/dist"

# Build the Swift package for both architectures
cd "$PROJECT_DIR"

echo "Building for arm64 (Apple Silicon)..."
swift build -c release --arch arm64

echo "Building for x86_64 (Intel)..."
swift build -c release --arch x86_64

# Get the built executable paths
ARM64_EXECUTABLE=$(swift build -c release --arch arm64 --show-bin-path)/RM01InternetConnector
X86_64_EXECUTABLE=$(swift build -c release --arch x86_64 --show-bin-path)/RM01InternetConnector

if [ ! -f "$ARM64_EXECUTABLE" ]; then
    echo "❌ arm64 build failed: executable not found"
    exit 1
fi

if [ ! -f "$X86_64_EXECUTABLE" ]; then
    echo "❌ x86_64 build failed: executable not found"
    exit 1
fi

echo "✅ Both architectures built successfully"

# Create universal binary using lipo
UNIVERSAL_EXECUTABLE="$PROJECT_DIR/.build/universal/RM01InternetConnector"
mkdir -p "$PROJECT_DIR/.build/universal"

echo "Creating universal binary..."
lipo -create "$ARM64_EXECUTABLE" "$X86_64_EXECUTABLE" -output "$UNIVERSAL_EXECUTABLE"

if [ ! -f "$UNIVERSAL_EXECUTABLE" ]; then
    echo "❌ Failed to create universal binary"
    exit 1
fi

# Verify the universal binary
echo "Verifying universal binary:"
lipo -info "$UNIVERSAL_EXECUTABLE"

EXECUTABLE="$UNIVERSAL_EXECUTABLE"
echo "✅ Universal binary created successfully"

# Create app bundle structure
APP_BUNDLE="$PROJECT_DIR/dist/$APP_NAME.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy executable
cp "$EXECUTABLE" "$APP_BUNDLE/Contents/MacOS/RM01InternetConnector"

# Copy the resource bundle (required for Bundle.module to work)
# Try both architecture-specific paths and the universal path
for ARCH_PATH in "$PROJECT_DIR/.build/arm64-apple-macosx/release" "$PROJECT_DIR/.build/x86_64-apple-macosx/release" "$PROJECT_DIR/.build/release"; do
    BUILT_BUNDLE="$ARCH_PATH/RM01InternetConnector_RM01InternetConnector.bundle"
    if [ -d "$BUILT_BUNDLE" ]; then
        cp -R "$BUILT_BUNDLE" "$APP_BUNDLE/Contents/Resources/"
        echo "✅ Resource bundle copied from $ARCH_PATH"
        break
    fi
done

# Also copy all resources directly to Resources root for fallback access
cp "$PROJECT_DIR/Sources/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/AppIcon.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/statusIcon.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/statusIcon@2x.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/statusIcon@3x.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$PROJECT_DIR/Sources/Resources/body.png" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true

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

# Optional: Create DMG with custom layout
echo "📦 Creating DMG with installer layout..."
DMG_PATH="$PROJECT_DIR/dist/$APP_NAME.dmg"
rm -f "$DMG_PATH"

# Create a temporary directory for DMG contents
DMG_TEMP="$PROJECT_DIR/dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app bundle
cp -R "$APP_BUNDLE" "$DMG_TEMP/"

# Create symbolic link to Applications
ln -s /Applications "$DMG_TEMP/Applications"

# Copy fix script and make it executable
cp "$PROJECT_DIR/fix-app-damaged.sh" "$DMG_TEMP/"
chmod +x "$DMG_TEMP/fix-app-damaged.sh"

# Copy how-to-use file
cp "$PROJECT_DIR/HOW_TO_USE.txt" "$DMG_TEMP/"

# Create a temporary writable DMG
DMG_TEMP_RW="$PROJECT_DIR/dist/temp_rw.dmg"
rm -f "$DMG_TEMP_RW"

# Calculate size needed (app size + 50MB for overhead)
SIZE=$(du -sm "$DMG_TEMP" | awk '{print $1}')
SIZE=$((SIZE + 50))

echo "Creating temporary DMG (${SIZE}MB)..."
hdiutil create -srcfolder "$DMG_TEMP" -volname "$APP_NAME" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${SIZE}m "$DMG_TEMP_RW"

# Mount the temporary DMG
echo "Mounting temporary DMG..."
MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP_RW")
MOUNT_DIR=$(echo "$MOUNT_OUTPUT" | grep "/Volumes/" | awk '{print $3}')

if [ -z "$MOUNT_DIR" ]; then
    echo "❌ Failed to mount DMG"
    echo "Mount output: $MOUNT_OUTPUT"
    exit 1
fi

echo "Mounted at: $MOUNT_DIR"

# Wait for mount to complete
sleep 3

# Set custom icon positions and window properties using AppleScript
echo "Setting up DMG layout..."

# Create AppleScript to configure the DMG window
osascript <<EOF
tell application "Finder"
    tell disk "RM-01 Internet Connector"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, 900, 600}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 96
        set text size of viewOptions to 13
        
        -- Set pure white background
        set background color of viewOptions to {65535, 65535, 65535}
        
        -- Position items like the reference image
        delay 1
        set position of item "RM-01 Internet Connector.app" to {180, 180}
        set position of item "Applications" to {620, 180}
        
        -- Try to position help files
        try
            set position of item "fix-app-damaged.sh" to {180, 380}
            set position of item "HOW_TO_USE.txt" to {620, 380}
        end try
        
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
EOF

echo "✅ DMG layout configured"

# Sync and close Finder windows
sync
sleep 1

# Close the Finder window to release the mount
osascript -e 'tell application "Finder" to close every window' 2>/dev/null || true
sleep 2

# Unmount
echo "Finalizing DMG..."
# Try multiple methods to unmount
UNMOUNTED=false
for i in {1..5}; do
    # Find the device node
    DEV_NODE=$(hdiutil info | grep "/Volumes/RM-01 Internet Connector" | head -1 | awk '{print $1}')
    if [ -z "$DEV_NODE" ]; then
        echo "✅ DMG unmounted successfully"
        UNMOUNTED=true
        break
    fi
    
    echo "Attempting to unmount $DEV_NODE (attempt $i)..."
    hdiutil detach "$DEV_NODE" -force 2>/dev/null && {
        UNMOUNTED=true
        break
    }
    sleep 2
done

if [ "$UNMOUNTED" = false ]; then
    echo "⚠️  Warning: Could not unmount cleanly, forcing..."
    # Last resort - kill any processes using the mount
    lsof "/Volumes/RM-01 Internet Connector" 2>/dev/null | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null || true
    sleep 1
    DEV_NODE=$(hdiutil info | grep "/Volumes/RM-01 Internet Connector" | head -1 | awk '{print $1}')
    [ -n "$DEV_NODE" ] && hdiutil detach "$DEV_NODE" -force 2>/dev/null || true
fi

# Wait for diskimaged to release the file
echo "Waiting for disk image to be fully released..."
for i in {1..10}; do
    if lsof "$DMG_TEMP_RW" >/dev/null 2>&1; then
        echo "  Still in use... waiting ($i/10)"
        sleep 1
    else
        echo "✅ Disk image released"
        break
    fi
done

# Try to convert, but if it fails, use direct creation method
echo "Compressing DMG..."
if lsof "$DMG_TEMP_RW" >/dev/null 2>&1; then
    echo "⚠️  File still in use, using alternative DMG creation method..."
    # Kill diskimaged and wait
    pkill -9 diskimaged 2>/dev/null || true
    sleep 3
    
    # Remove the temp DMG and create final DMG directly from folder
    rm -f "$DMG_TEMP_RW"
    if hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TEMP" -ov -format UDZO -imagekey zlib-level=9 "$DMG_PATH"; then
        echo "✅ DMG created successfully (direct method)"
    else
        echo "❌ Failed to create DMG"
        exit 1
    fi
else
    # Try normal conversion
    if hdiutil convert "$DMG_TEMP_RW" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"; then
        echo "✅ DMG compression successful"
    else
        echo "⚠️  Conversion failed, using direct creation..."
        rm -f "$DMG_TEMP_RW"
        hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TEMP" -ov -format UDZO -imagekey zlib-level=9 "$DMG_PATH" || {
            echo "❌ Failed to create DMG"
            exit 1
        }
    fi
fi

# Set custom icon for the DMG
echo "Setting DMG icon..."
ICON_FILE="$PROJECT_DIR/AppIcon.icns"
if [ ! -f "$ICON_FILE" ]; then
    ICON_FILE="$PROJECT_DIR/Sources/Resources/AppIcon.icns"
fi

if [ -f "$ICON_FILE" ]; then
    # Create a temporary icon resource file
    TEMP_ICON_DIR="$PROJECT_DIR/dist/.tmp_icon"
    mkdir -p "$TEMP_ICON_DIR"
    
    # Extract icon and apply to DMG
    cp "$ICON_FILE" "$TEMP_ICON_DIR/Icon.icns"
    
    # Method 1: Using sips and SetFile
    sips -i "$TEMP_ICON_DIR/Icon.icns" >/dev/null 2>&1 || true
    
    # Method 2: Using DeRez/Rez (if available)
    if command -v DeRez >/dev/null 2>&1 && command -v Rez >/dev/null 2>&1; then
        DeRez -only icns "$TEMP_ICON_DIR/Icon.icns" > "$TEMP_ICON_DIR/icon.rsrc" 2>/dev/null || true
        if [ -f "$TEMP_ICON_DIR/icon.rsrc" ]; then
            Rez -append "$TEMP_ICON_DIR/icon.rsrc" -o "$DMG_PATH" 2>/dev/null || true
        fi
    fi
    
    # Set custom icon attribute
    SetFile -a C "$DMG_PATH" 2>/dev/null || true
    
    # Cleanup
    rm -rf "$TEMP_ICON_DIR"
    echo "✅ DMG icon set"
else
    echo "⚠️  Icon file not found, skipping DMG icon"
fi

# Cleanup temporary files
rm -f "$DMG_TEMP_RW"
rm -rf "$DMG_TEMP"
rm -f "$PROJECT_DIR/dist/dmg_setup.applescript"

echo "✅ DMG created at: $DMG_PATH"
echo ""
echo "🎉 Build complete!"
echo "   App: $APP_BUNDLE"
echo "   DMG: $DMG_PATH"
