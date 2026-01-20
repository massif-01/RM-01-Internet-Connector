# Windows Version Testing Guide

This guide outlines the testing checklist for both GUI and CLI versions.

## Pre-Testing Setup

### Requirements
- [ ] Windows 10 or 11
- [ ] RM-01 device with USB cable
- [ ] Active internet connection (Wi-Fi or Ethernet)
- [ ] Administrator privileges

### Build the Applications

#### GUI Application
```powershell
cd win_version
.\build.ps1
```

#### CLI Executable (Optional)
```cmd
cd win_version\cli
build_exe.bat
```

---

## GUI Application Tests

### 1. Installation and Startup
- [ ] Application starts without errors
- [ ] Window appears centered on screen
- [ ] All UI elements render correctly
- [ ] Icon shows in taskbar
- [ ] Tray icon appears in system tray

### 2. Language Switching
- [ ] Language toggle button works (EN ↔ CN)
- [ ] All text updates when language changes
- [ ] Tray menu text updates
- [ ] Window title updates

### 3. Network Detection (Without RM-01)
- [ ] Status shows "No Device" or "Please connect RM-01"
- [ ] Connect button is enabled
- [ ] No errors in UI

### 4. Network Detection (With RM-01 Connected)
- [ ] Plug in RM-01 via USB
- [ ] Interface name appears (e.g., "Ethernet 3")
- [ ] Status updates automatically or after reopening app
- [ ] Device description shows AX88179A

### 5. Connection Process
- [ ] Click "Connect" button
- [ ] Status changes to "Connecting..."
- [ ] Button becomes disabled during connection
- [ ] UAC prompt appears (if not admin)
- [ ] Status changes to "Connected" on success
- [ ] Button text changes to "Disconnect"

### 6. Network Speed Monitor
- [ ] Speed display appears below device image when connected
- [ ] Shows "↑ X.XKB/s | ↓ X.XKB/s" format
- [ ] Speed values update every second
- [ ] Speed display is hidden when not connected

### 7. Tray Menu
- [ ] Double-click tray icon opens window
- [ ] Right-click shows context menu
- [ ] Speed item shows at top when connected
- [ ] Speed item hidden when not connected
- [ ] Status shows colored dot (● for connected, ○ for idle)
- [ ] Connect/Disconnect menu item works
- [ ] "Open Control Panel" opens main window
- [ ] "Quit" closes application

### 8. Network Functionality
From RM-01:
- [ ] Can ping 10.10.99.100 (computer)
- [ ] Can ping 8.8.8.8 (Google DNS)
- [ ] Can browse websites
- [ ] Can download files

### 9. Disconnection
- [ ] Click "Disconnect" button
- [ ] Status changes to "Disconnecting..."
- [ ] Status changes to "Ready" or "Idle"
- [ ] Speed monitor disappears
- [ ] Tray menu speed item disappears
- [ ] Button text changes back to "Connect"

### 10. Window Management
- [ ] Minimize button works
- [ ] Close button hides window (app stays in tray)
- [ ] App can be reopened from tray
- [ ] Quit from tray closes app completely

### 11. Error Handling
- [ ] Unplug RM-01 while connected → shows error
- [ ] Try to connect without upstream → shows error
- [ ] Cancel UAC prompt → status returns to idle

---

## CLI Application Tests

### 1. Python Script Mode

#### Setup
```cmd
cd win_version\cli
pip install -r requirements.txt
```

#### Test Commands

- [ ] `python cli.py help` - Shows help message
- [ ] `python cli.py --lang en status` - English status
- [ ] `python cli.py --lang zh status` - Chinese status

#### Without RM-01 Connected
- [ ] `python cli.py detect` - Shows "No adapter detected"
- [ ] `python cli.py status` - Shows "No adapter"

#### With RM-01 Connected
- [ ] `python cli.py detect` - Finds adapter and shows details
- [ ] `python cli.py status` - Shows adapter info

#### Connection (Run as Administrator!)
```cmd
python cli.py connect
```
- [ ] Detects adapter
- [ ] Finds upstream network
- [ ] Shows configuration progress
- [ ] Completes successfully
- [ ] RM-01 has internet access

#### Status While Connected
```cmd
python cli.py status
```
- [ ] Shows "Connected"
- [ ] Shows upstream interface
- [ ] Shows IP address
- [ ] Shows traffic stats (if implemented)

#### Disconnection
```cmd
python cli.py disconnect
```
- [ ] Shows disconnection progress
- [ ] Completes successfully
- [ ] Status returns to idle

### 2. Executable Mode

- [ ] Build executable with `build_exe.bat`
- [ ] Executable created at `dist\rm01-cli.exe`
- [ ] Repeat all Python script tests with executable
- [ ] Executable works without Python installed

### 3. Edge Cases

- [ ] Ctrl+C during command → cancels gracefully
- [ ] Wrong password (if applicable) → shows error
- [ ] Multiple rapid commands → handles correctly
- [ ] Non-admin user → shows permission error

---

## Integration Tests

### 1. GUI and CLI Coexistence
- [ ] Start GUI, connect, then use CLI status → shows connected
- [ ] Connect via CLI, then open GUI → GUI shows connected
- [ ] Disconnect via GUI, check with CLI → shows disconnected
- [ ] Connect via CLI, disconnect via GUI → works correctly

### 2. Multiple RM-01 Devices (if available)
- [ ] Detects first device
- [ ] Handles second device appropriately

### 3. Network Changes
- [ ] Switch Wi-Fi networks while connected → maintains connection or fails gracefully
- [ ] Disable/enable upstream → handles correctly

---

## Performance Tests

- [ ] Speed monitor updates smoothly (no lag)
- [ ] Application memory usage stays reasonable
- [ ] CPU usage is low when idle
- [ ] No memory leaks after multiple connect/disconnect cycles

---

## Compatibility Tests

### Windows 10
- [ ] Application installs and runs
- [ ] All features work correctly

### Windows 11
- [ ] Application installs and runs
- [ ] All features work correctly

---

## Known Limitations

Document any discovered limitations:

1. **ICS Configuration**: CLI may require manual ICS setup through Windows Network Settings for full functionality
2. **Traffic Stats**: CLI may not show accurate traffic statistics (limitation of netsh)
3. **Multiple Adapters**: Behavior with multiple AX88179A adapters needs testing

---

## Regression Tests (After Changes)

If code changes are made, re-test:
- [ ] All critical features still work
- [ ] No new bugs introduced
- [ ] Performance hasn't degraded

---

## Test Results

### Tester Information
- **Name**: _______________
- **Date**: _______________
- **Windows Version**: _______________
- **Build Number**: _______________

### Test Summary
- **Total Tests**: ___
- **Passed**: ___
- **Failed**: ___
- **Skipped**: ___

### Issues Found
(List any issues, bugs, or unexpected behavior)

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Overall Status
- [ ] ✅ Ready for Release
- [ ] ⚠️ Minor Issues (list above)
- [ ] ❌ Major Issues - Not Ready

---

## Notes

- Run all tests as Administrator for full functionality
- Test on clean Windows installations if possible
- Document any system-specific issues
- Take screenshots of errors for bug reports
