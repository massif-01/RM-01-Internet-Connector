#!/bin/bash
# Enhanced DMG creation script with proper layout
set -e

PROJECT_DIR="$1"
APP_NAME="$2"
DMG_TEMP="$3"
DMG_PATH="$4"

echo "📦 Creating beautifully formatted DMG..."

# Create a temporary read-write DMG
DMG_TEMP_RW="${DMG_PATH%.dmg}_temp.dmg"
rm -f "$DMG_TEMP_RW"

# Calculate size
SIZE=$(du -sm "$DMG_TEMP" | awk '{print $1}')
SIZE=$((SIZE + 50))

echo "Creating temporary DMG (${SIZE}MB)..."
hdiutil create -srcfolder "$DMG_TEMP" -volname "$APP_NAME" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${SIZE}m "$DMG_TEMP_RW"

# Mount it
echo "Mounting DMG..."
MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP_RW")
DEVICE=$(echo "$MOUNT_OUTPUT" | grep "^/dev/" | head -1 | awk '{print $1}')
MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | grep "/Volumes/" | sed 's/^.*\/Volumes/\/Volumes/')

echo "Mounted at: $MOUNT_POINT"
sleep 2

# Configure with AppleScript  
echo "Configuring window layout..."
osascript <<EOF
tell application "Finder"
    tell disk "$APP_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, 900, 600}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set text size of viewOptions to 14
        
        -- Try to set background
        try
            set background picture of viewOptions to file ".background:dmg-background.png"
        on error
            set background color of viewOptions to {65535, 65535, 65535}
        end try
        
        -- Position items
        delay 1
        set position of item "$APP_NAME.app" to {180, 180}
        set position of item "Applications" to {620, 180}
        
        try
            set position of item "fix-app-damaged.sh" to {180, 400}
            set position of item "HOW_TO_USE.txt" to {620, 400}
        end try
        
        close
        open
        update without registering applications
        delay 3
        close
    end tell
end tell
EOF

# Sync
sync
sleep 2

# Close all Finder windows to release the volume
osascript -e 'tell application "Finder" to close every window' 2>/dev/null || true
sleep 2

# Unmount
echo "Unmounting..."
hdiutil detach "$DEVICE" -force || hdiutil detach "$MOUNT_POINT" -force || true
sleep 3

# Kill diskimaged to ensure file is released
pkill -9 diskimaged 2>/dev/null || true
sleep 2

# Convert to compressed read-only DMG
echo "Creating final compressed DMG..."
rm -f "$DMG_PATH"
if hdiutil convert "$DMG_TEMP_RW" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH" 2>/dev/null; then
    echo "✅ DMG created with conversion"
else
    echo "⚠️  Conversion failed, creating new compressed DMG..."
    rm -f "$DMG_TEMP_RW"
    hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TEMP" -ov -format UDZO -imagekey zlib-level=9 "$DMG_PATH"
    echo "✅ DMG created directly"
fi

# Cleanup
rm -f "$DMG_TEMP_RW"

echo "✅ DMG ready: $DMG_PATH"







