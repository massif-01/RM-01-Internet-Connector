# RM-01 Internet Connector - Windows Version

Windows implementation of RM-01 Internet Connector with both GUI and CLI interfaces.

## What's New

### ✨ Latest Updates

**GUI Application**:
- ✅ Real-time network speed monitoring (upload/download)
- ✅ Speed display in main window when connected
- ✅ Speed display in system tray menu
- ✅ Colored status indicators (● for connected, ○ for idle)
- ✅ Improved tray menu with visual feedback
- ✅ Bilingual support (English/Chinese)

**CLI Tool**:
- ✅ Command-line interface for automation and remote control
- ✅ Python script mode and standalone executable
- ✅ Compatible with Linux CLI commands
- ✅ Bilingual support (English/Chinese)
- ✅ Perfect for SSH remote management

---

## Features

### GUI Application (`RM01InternetConnector.exe`)

- 🌐 **One-Click Connection** - Share internet with a single click
- 📊 **Real-time Speed Monitor** - Live upload/download speed display
- 🎨 **Modern UI** - Beautiful glass button design, consistent with macOS version
- 🖥️ **System Tray** - Minimize to tray, quick access menu
- 🌍 **Bilingual** - Full Chinese and English localization
- ⚡ **Auto Detection** - Automatically detects AX88179A USB Ethernet adapters

### CLI Tool (`rm01-cli.exe` or `cli.py`)

- 🖥️ **Command-line Control** - Manage connections without GUI
- 🤖 **Automation Ready** - Perfect for scripts and batch files
- 🔐 **Remote SSH Control** - Control from remote machines
- 📦 **Dual Modes** - Run as Python script or standalone executable
- 🌍 **Bilingual** - Same localization as GUI

---

## Installation

### GUI Application

#### Quick Install
1. Download the latest release
2. Extract `RM01InternetConnector.exe`
3. Double-click to run
4. No installation required!

#### Build from Source
```powershell
cd win_version
.\build.ps1
```

The built application will be in `publish/` folder.

### CLI Tool

#### Option 1: Python Script
```cmd
cd win_version\cli
pip install -r requirements.txt
python cli.py status
```

#### Option 2: Standalone Executable
```cmd
cd win_version\cli
build_exe.bat
```

Executable will be created at `dist\rm01-cli.exe`

---

## Usage

### GUI Application

1. **Connect RM-01** via USB
2. **Launch** the application
3. **Click "Connect"** button
4. **Grant** administrator privileges (UAC prompt)
5. **Done!** RM-01 now has internet access

**System Tray**:
- Double-click tray icon → Open control panel
- Right-click → Quick menu (status, connect/disconnect, quit)
- When connected → See real-time speed in tray menu

### CLI Tool

**Basic Commands**:
```cmd
# Check status
rm01-cli.exe status

# Detect RM-01 adapter
rm01-cli.exe detect

# Enable sharing (requires admin)
rm01-cli.exe connect

# Disable sharing
rm01-cli.exe disconnect

# Language support
rm01-cli.exe --lang zh status
rm01-cli.exe --lang en status
```

**Detailed CLI Guide**: See [`cli/README.md`](cli/README.md)

---

## System Requirements

- **OS**: Windows 10 or Windows 11
- **Runtime**: 
  - GUI: .NET 8.0 Runtime (included in build)
  - CLI: Python 3.8+ (for script mode) or none (for executable)
- **Privileges**: Administrator rights for network configuration
- **Hardware**: USB port for RM-01 connection

---

## Project Structure

```
win_version/
├── RM01InternetConnector.Win/    # GUI Application (C#/WPF)
│   ├── App.xaml.cs                # Application entry point
│   ├── MainWindow.xaml            # Main window UI
│   ├── AppState.cs                # State management & speed monitor
│   ├── NetworkSpeedMonitor.cs     # Network speed monitoring
│   ├── TrayController.cs          # System tray functionality
│   ├── WindowsNetworkService.cs   # Network configuration & ICS
│   └── Assets/                    # Icons and images
├── cli/                           # CLI Tool (Python)
│   ├── cli.py                     # Main CLI program
│   ├── network_service_windows.py # Windows network service
│   ├── requirements.txt           # Python dependencies
│   ├── build_exe.bat              # Build standalone executable
│   └── README.md                  # CLI documentation
├── build.ps1                      # GUI build script
├── TESTING_GUIDE.md               # Testing checklist
└── README.md                      # This file
```

---

## How It Works

RM-01 contains an AX88179A switch chip that:
1. Assigns IP `10.10.99.100` to the connected computer via DHCP
2. Expects the computer to act as its gateway

This application:
1. Detects the AX88179A USB adapter
2. Configures static IP (10.10.99.100) for stability
3. Enables Internet Connection Sharing (ICS) from Wi-Fi/Ethernet to RM-01
4. Monitors real-time network speed (GUI only)

**Network Configuration**:
- **RM-01 Interface IP**: 10.10.99.100
- **Subnet Mask**: 255.255.255.0
- **Gateway**: 10.10.99.100
- **DNS**: 8.8.8.8

---

## Comparison: GUI vs CLI

| Feature | GUI | CLI |
|---------|-----|-----|
| Internet Sharing | ✅ | ✅ |
| Speed Monitoring | ✅ | ❌ |
| System Tray | ✅ | ❌ |
| Remote Control | ❌ | ✅ (via SSH) |
| Automation | ❌ | ✅ |
| Visual Feedback | ✅ | ❌ |
| Installation | Portable EXE | Python or EXE |

**When to use**:
- **GUI**: Daily use, visual monitoring, convenience
- **CLI**: Automation, remote management, scripting

---

## Troubleshooting

### GUI Application

**Issue**: "No Device" shown even when RM-01 is connected
- **Solution**: Unplug and replug RM-01, restart application

**Issue**: Connection fails
- **Solution**: 
  1. Run as Administrator
  2. Check Device Manager for AX88179A adapter
  3. Ensure you have active internet (Wi-Fi or Ethernet)

**Issue**: Speed shows 0 B/s
- **Solution**: Speed monitoring starts after successful connection, may take 1-2 seconds

**Issue**: Application doesn't start
- **Solution**: Install .NET 8.0 Runtime from Microsoft

### CLI Tool

**Issue**: "Permission denied" error
- **Solution**: Run Command Prompt as Administrator

**Issue**: "No adapter detected"
- **Solution**: Check Device Manager, verify AX88179A is present

**Issue**: Python script import errors
- **Solution**: 
  ```cmd
  pip install -r requirements.txt
  ```

**Issue**: Executable doesn't work
- **Solution**: Try Python script mode first to diagnose

For more troubleshooting, see [`TESTING_GUIDE.md`](TESTING_GUIDE.md)

---

## Development

### Building GUI

Requirements:
- .NET 8.0 SDK
- Visual Studio 2022 or VS Code

```powershell
cd win_version
.\build.ps1
```

### Building CLI Executable

Requirements:
- Python 3.8+
- PyInstaller

```cmd
cd win_version\cli
build_exe.bat
```

### Testing

See comprehensive testing checklist in [`TESTING_GUIDE.md`](TESTING_GUIDE.md)

---

## Changelog

### Version 1.1.0 (Latest)

**GUI**:
- Added real-time network speed monitoring
- Added speed display in main window
- Added speed display in tray menu
- Added colored status indicators (●/○)
- Improved tray menu UX
- Enhanced visual feedback

**CLI**:
- New command-line interface
- Python script and executable modes
- Windows-specific network service implementation
- Bilingual support (EN/ZH)
- Compatible with Linux CLI commands

### Version 1.0.0

- Initial Windows release
- Basic internet sharing functionality
- System tray support
- Bilingual UI

---

## Known Limitations

1. **ICS Configuration**: CLI may require manual ICS setup for full functionality (GUI uses COM interface and handles this automatically)
2. **Speed Accuracy**: Speed monitoring shows computer perspective (not RM-01 internal traffic)
3. **Multi-Adapter**: Only first detected AX88179A is used

---

## Future Plans

- [ ] Enhanced ICS support in CLI
- [ ] Traffic statistics in CLI
- [ ] Connection history logging
- [ ] Auto-reconnect on adapter plug-in
- [ ] Network interface selection (if multiple upstreams)

---

## License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

---

## See Also

- **Main Project**: [`../README.md`](../README.md)
- **macOS Version**: [`../mac_version/`](../mac_version/)
- **Linux Version**: [`../linux_version/`](../linux_version/)
- **CLI Documentation**: [`cli/README.md`](cli/README.md)
- **Testing Guide**: [`TESTING_GUIDE.md`](TESTING_GUIDE.md)

---

## Support

For issues, questions, or contributions, please check the main project repository.

Built with ❤️ for RM-01 users
