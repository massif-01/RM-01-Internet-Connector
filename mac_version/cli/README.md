# RM-01 Internet Connector - macOS CLI

Command-line interface for controlling RM-01 network sharing on macOS.

## Features

- 🖥️ **Command-line control** - Manage RM-01 connections without GUI
- 🌍 **Bilingual support** - Full Chinese and English localization
- 📦 **Dual modes** - Run as Python script or standalone executable
- 🔧 **Cross-platform compatible** - Same commands as Linux/Windows versions
- ⚡ **Native macOS** - Uses networksetup, pfctl, and sysctl

## Requirements

### For Python Script Mode
- Python 3.8 or later (pre-installed on macOS)
- macOS 10.15 (Catalina) or later
- Administrator privileges (sudo)

### For Executable Mode
- macOS 10.15 (Catalina) or later
- Administrator privileges (sudo)
- No Python installation required!

## Installation

### Method 1: Python Script (Developers)

1. Install dependencies:
```bash
cd mac_version/cli
pip3 install -r requirements.txt
```

2. Run the CLI:
```bash
python3 cli.py status
```

### Method 2: Standalone Executable (End Users)

1. Build the executable:
```bash
cd mac_version/cli
./build_executable.sh
```

2. The executable will be created at `dist/rm01-cli`

3. (Optional) Install globally:
```bash
sudo cp dist/rm01-cli /usr/local/bin/
# Now you can use: rm01-cli status
```

## Usage

**Important**: All network configuration commands require sudo privileges.

### Check Connection Status

```bash
# Python mode
python3 cli.py status

# Executable mode
./dist/rm01-cli status
```

Output example:
```
RM-01 Internet Connector - CLI
==============================

Adapter:
  Name:  AX88179A 5
  MAC:   00:0E:C6:xx:xx:xx
  Type:  AX88179A USB Ethernet Adapter

Status: Connected
  Upstream: Wi-Fi
  IP: 10.10.99.100
  Traffic:  RX 125.4 MB, TX 45.2 MB
```

### Detect RM-01 Adapter

```bash
python3 cli.py detect
```

Output if found:
```
✓ RM-01 adapter found!

Details:
  Interface: AX88179A 5
  MAC:       00:0E:C6:xx:xx:xx
  Chip:      AX88179A USB Ethernet Adapter

Upstream Network:
  Interface: Wi-Fi
```

### Enable Internet Sharing

```bash
# Run with sudo!
sudo python3 cli.py connect
```

Process:
1. Detects RM-01 adapter
2. Finds upstream network (Wi-Fi/Ethernet)
3. Configures static IP (10.10.99.100)
4. Enables IP forwarding
5. Sets up NAT using pfctl

Output:
```
→ Detecting RM-01 adapter...
✓ Found adapter: AX88179A 5
→ Finding upstream network...
✓ Found upstream: Wi-Fi
→ Configuring network...
  Setting static IP: 10.10.99.100
  Enabling IP forwarding
  Setting NAT: en16 → en0

✓ Internet sharing enabled!

RM-01 can now access the internet through this computer.
```

### Disable Internet Sharing

```bash
# Run with sudo!
sudo python3 cli.py disconnect
```

Output:
```
→ Disconnecting AX88179A 5...

→ Removing NAT rules...
→ Restoring DHCP...

✓ Internet sharing disabled
```

## Language Support

Change language using `--lang` flag:

```bash
# English (default)
python3 cli.py --lang en status

# Chinese
python3 cli.py --lang zh status
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
2. Check System Settings → Network for AX88179A interface
3. Try running: `networksetup -listallhardwareports` to see all interfaces

### "Permission denied" errors

All network configuration requires sudo:
```bash
sudo python3 cli.py connect
```

### Executable doesn't work

Try running the Python script directly:
```bash
python3 cli.py status
```

If it works, rebuild the executable:
```bash
./build_executable.sh
```

## Advanced Usage

### Remote Control via SSH

You can control RM-01 sharing remotely via SSH:

```bash
# On remote Mac
ssh user@mac-hostname

# Then run CLI commands
cd path/to/mac_version/cli
sudo python3 cli.py connect
```

### Scripting

Example shell script to auto-connect:

```bash
#!/bin/bash
cd ~/RM01/mac_version/cli
sudo python3 cli.py connect
if [ $? -eq 0 ]; then
    echo "Connected successfully!"
else
    echo "Failed to connect"
    exit 1
fi
```

## Comparison with GUI Version

| Feature | CLI | GUI |
|---------|-----|-----|
| Network sharing | ✅ | ✅ |
| Speed monitoring | ❌ | ✅ |
| Menu bar icon | ❌ | ✅ |
| Remote control | ✅ (via SSH) | ❌ |
| Automation | ✅ | ❌ |
| Visual feedback | ❌ | ✅ |

**Recommendation**: 
- Use **CLI** for: Remote management, automation, scripting
- Use **GUI** for: Daily use, visual monitoring, menu bar access

## Technical Details

### Network Configuration

The CLI configures the RM-01 interface with:
- **IP**: 10.10.99.100
- **Subnet**: 255.255.255.0
- **Gateway**: 10.10.99.100
- **DNS**: 8.8.8.8

### Commands Used

- `networksetup` - Network configuration
- `pfctl` - Packet filter (NAT rules)
- `sysctl` - IP forwarding control
- `ifconfig` - Interface management
- `netstat` - Network statistics

### NAT Configuration

The CLI uses pfctl to create NAT rules:
```
nat on en0 from en16:network to any -> (en0)
```

This allows RM-01 (connected to en16) to access the internet through the upstream interface (en0).

## Security Notes

- Requires sudo privileges for network configuration
- NAT rules are temporary and cleared on disconnect
- No permanent system changes are made
- All operations are reversible

## Known Limitations

1. **Single Adapter**: Only the first detected AX88179A is used
2. **Traffic Stats**: Shows total bytes, not real-time speed
3. **Sudo Required**: All configuration commands need elevated privileges

## License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

## See Also

- Main GUI application: `../Sources/RM01InternetConnector/`
- Windows CLI version: `../../win_version/cli/`
- Linux CLI version: `../../linux_version/cli.py`
- Project README: `../../README.md`
