# RM-01 Internet Connector - Windows CLI

Command-line interface for controlling RM-01 network sharing on Windows.

## Features

- 🖥️ **Command-line control** - Manage RM-01 connections without GUI
- 🌍 **Bilingual support** - Full Chinese and English localization
- 📦 **Dual modes** - Run as Python script or standalone executable
- 🔧 **Cross-platform compatible** - Same commands as Linux version

## Requirements

### For Python Script Mode
- Python 3.8 or later
- Windows 10/11
- Administrator privileges
- Windows PowerShell (included with Windows 10/11)

### For Executable Mode
- Windows 10/11
- Administrator privileges
- Windows PowerShell (included with Windows 10/11)
- No Python installation required!

## Installation

### Method 1: Python Script (Developers)

1. Install dependencies:
```cmd
cd win_version\cli
pip install -r requirements.txt
```

2. Run the CLI:
```cmd
python cli.py status
```

3. Run mocked CLI regression tests:
```cmd
python -m unittest test_windows_cli.py
```

### Method 2: Standalone Executable (End Users)

1. Build the executable:
```cmd
cd win_version\cli
build_exe.bat
```

2. The executable will be created at `dist\rm01-cli.exe`

3. (Optional) Add to PATH for global access:
```cmd
copy dist\rm01-cli.exe C:\Windows\System32\
```

## Usage

**Important**: All network configuration commands require Administrator privileges.

### Check Connection Status

```cmd
# Python mode
python cli.py status

# Executable mode
rm01-cli.exe status
```

Output example:
```
RM-01 Internet Connector - CLI
==============================

Adapter:
  Name:  Ethernet 3
  MAC:   00:0E:C6:xx:xx:xx
  Type:  AX88179A USB Ethernet Adapter

Status: Connected
  Upstream: Wi-Fi
  IP: 10.10.99.100
  Traffic:  RX 125.4 MB, TX 45.2 MB
```

### Detect RM-01 Adapter

```cmd
python cli.py detect
```

Output if found:
```
✓ RM-01 adapter found!

Details:
  Interface: Ethernet 3
  MAC:       00:0E:C6:xx:xx:xx
  Chip:      AX88179A USB Ethernet Adapter

Upstream Network:
  Interface: Wi-Fi
```

### Enable Internet Sharing

```cmd
# Run as Administrator!
python cli.py connect
```

Process:
1. Detects RM-01 adapter
2. Finds upstream network (Wi-Fi/Ethernet)
3. Configures static IP (10.10.99.100)
4. Enables Windows NAT and IPv4 forwarding

Output:
```
→ Detecting RM-01 adapter...
✓ Found adapter: Ethernet 3
→ Finding upstream network...
✓ Found upstream: Wi-Fi
→ Configuring network...
  Setting static IP: 10.10.99.100
  Preparing Windows NAT
  Enabling Windows NAT: Ethernet 3 → Wi-Fi

✓ Internet sharing enabled!

RM-01 can now access the internet through this computer.
```

### Disable Internet Sharing

```cmd
# Run as Administrator!
python cli.py disconnect
```

Output:
```
→ Disconnecting Ethernet 3...

→ Disabling Windows NAT...
→ Restoring DHCP...

✓ Internet sharing disabled
```

## Language Support

Change language using `--lang` flag:

```cmd
# English (default)
python cli.py --lang en status

# Chinese
python cli.py --lang zh status
```

The CLI auto-detects system language by default.

## Commands Reference

| Command | Description |
|---------|-------------|
| `status` | Show current connection status and statistics |
| `detect` | Detect RM-01 adapter and upstream network |
| `connect` | Enable internet sharing to RM-01 |
| `disconnect` | Disable internet sharing |
| `help` | Show help message |

## Common Options

| Option | Description |
|--------|-------------|
| `--lang en` | Force English |
| `--lang zh` | Force Chinese (中文) |

## Troubleshooting

### "No RM-01 adapter detected"

1. Make sure RM-01 is connected via USB
2. Check Device Manager for AX88179A adapter
3. Try running: `ipconfig /all` to see all interfaces

### "Permission denied" or "Access denied"

Run Command Prompt or PowerShell as Administrator:
- Right-click → "Run as Administrator"

### Executable doesn't work

Try running the Python script directly:
```cmd
python cli.py status
```

If it works, rebuild the executable:
```cmd
build_exe.bat
```

## Advanced Usage

### Remote Control via SSH

You can control RM-01 sharing remotely via SSH:

```cmd
# On remote Windows machine
ssh user@windows-pc

# Then run CLI commands
cd path\to\win_version\cli
python cli.py connect
```

### Scripting

Example batch script to auto-connect:

```batch
@echo off
cd C:\RM01\win_version\cli
python cli.py connect
if errorlevel 1 (
    echo Failed to connect
    pause
    exit /b 1
)
echo Connected successfully!
```

## Comparison with GUI Version

| Feature | CLI | GUI |
|---------|-----|-----|
| Network sharing | ✅ | ✅ |
| Speed monitoring | ❌ | ✅ |
| Tray icon | ❌ | ✅ |
| Remote control | ✅ (via SSH) | ❌ |
| Automation | ✅ | ❌ |
| Visual feedback | ❌ | ✅ |

**Recommendation**: 
- Use **CLI** for: Remote management, automation, scripting
- Use **GUI** for: Daily use, visual monitoring, tray notifications

## Notes

### Windows NAT

The Windows CLI configures the RM-01 adapter with `netsh` and uses built-in PowerShell NetTCPIP/NetNat cmdlets to enable IPv4 forwarding and NAT. It does not use Windows Internet Connection Sharing, because ICS forces private adapters to `192.168.137.1`. Run `connect` and `disconnect` from an elevated Command Prompt or PowerShell window. If the `MSFT_NetNat` provider is unavailable, the CLI fails before changing the RM-01 adapter so existing SSH sessions are not reset.

### Network Configuration

The CLI configures the RM-01 interface with:
- **IP**: 10.10.99.100
- **Subnet**: 255.255.255.0
- **Gateway**: none on the Windows RM-01 adapter
- **DNS**: 8.8.8.8

This matches RM-01's expected network configuration.

## License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

## See Also

- Main GUI application: `../RM01InternetConnector.Win/`
- Linux CLI version: `../../linux_version/cli.py`
- Project README: `../../README.md`
