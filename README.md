# RM-01 Internet Connector

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

RM-01 Internet Connector is a cross-platform application that shares your computer's internet connection with RM-01 devices via the AX88179A USB Ethernet adapter.

<img src="icons/screenshot.png" alt="App Screenshot" width="50%">

### Supported Platforms

| Platform | GUI | CLI | Status |
|----------|-----|-----|--------|
| macOS | ✅ | - | Stable |
| Windows | ✅ | - | Stable |
| Linux | ✅ | ✅ | Stable |

### Features

- 🌐 **One-Click Connection** - Share internet with a single click
- 📊 **Real-time Speed Monitor** - Live upload/download speed display
- 🎨 **Consistent UI** - Same beautiful design across all platforms
- 🌍 **Bilingual Support** - Full Chinese and English localization
- ⚡ **Auto Detection** - Automatically detects AX88179A USB Ethernet adapters
- 🖥️ **CLI Support** (Linux) - Command-line control for SSH remote access

### Project Structure

```
RM-01 Internet Connector/
├── mac_version/           # macOS version (Swift/SwiftUI)
│   ├── Sources/
│   ├── Package.swift
│   └── build.sh
├── win_version/           # Windows version (C#/WPF)
│   ├── RM01InternetConnector.Win/
│   └── build.ps1
├── linux_version/         # Linux version (Python/PyQt6)
│   ├── main.py            # GUI entry
│   ├── cli.py             # CLI entry
│   └── build-appimage.sh
├── icons/                 # Shared icon resources
└── README.md
```

### Quick Start

#### macOS

```bash
cd mac_version
./build.sh
# App will be created in mac_version/dist/
```

#### Windows

```powershell
cd win_version
.\build.ps1
# App will be created in win_version\publish\
```

#### Linux

**GUI Mode:**
```bash
cd linux_version
python3 main.py
```

**CLI Mode** (for SSH remote control):
```bash
cd linux_version

# Check connection status
python3 cli.py status

# Connect RM-01 to internet
python3 cli.py connect

# Disconnect
python3 cli.py disconnect

# Detect RM-01 adapter
python3 cli.py detect

# Language support
python3 cli.py --lang zh status    # Chinese
python3 cli.py --lang en status    # English
```

**Global CLI Command** (optional):
```bash
cd linux_version
sudo ln -s "$(pwd)/cli.py" /usr/local/bin/rm01-cli
sudo chmod +x /usr/local/bin/rm01-cli

# Now you can use from anywhere
rm01-cli status
rm01-cli connect
rm01-cli disconnect
```

**Build AppImage:**
```bash
./build-appimage.sh
```

### How It Works

RM-01 contains an AX88179A switch chip that:
1. Assigns IP `10.10.99.100` to the connected computer via DHCP
2. Expects the computer to act as its gateway

This application:
1. Detects the AX88179A USB adapter
2. Configures static IP (10.10.99.100) for stability
3. Enables IP forwarding
4. Sets up NAT to share internet with RM-01

### System Requirements

- **macOS**: 13.0 (Ventura) or later
- **Windows**: 10/11 with .NET 8.0
- **Linux**: Ubuntu 20.04+ / Debian 11+ / Fedora 35+ or equivalent

### License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

---

<a name="中文"></a>
## 中文

### 概述

RM-01 互联网连接助手是一款跨平台应用，通过 AX88179A USB 网卡将电脑的互联网连接共享给 RM-01 设备。

<img src="icons/screenshot.png" alt="应用截图" width="50%">

### 支持平台

| 平台 | 图形界面 | 命令行 | 状态 |
|------|---------|--------|------|
| macOS | ✅ | - | 稳定 |
| Windows | ✅ | - | 稳定 |
| Linux | ✅ | ✅ | 稳定 |

### 功能特点

- 🌐 **一键连接** - 单击即可共享网络
- 📊 **实时网速监控** - 实时显示上传/下载速度
- 🎨 **统一界面** - 所有平台保持一致的精美设计
- 🌍 **双语支持** - 完整的中英文本地化
- ⚡ **自动检测** - 自动检测 AX88179A USB 网卡
- 🖥️ **命令行支持** (Linux) - 支持 SSH 远程控制

### 项目结构

```
RM-01 Internet Connector/
├── mac_version/           # macOS 版本 (Swift/SwiftUI)
│   ├── Sources/
│   ├── Package.swift
│   └── build.sh
├── win_version/           # Windows 版本 (C#/WPF)
│   ├── RM01InternetConnector.Win/
│   └── build.ps1
├── linux_version/         # Linux 版本 (Python/PyQt6)
│   ├── main.py            # 图形界面入口
│   ├── cli.py             # 命令行入口
│   └── build-appimage.sh
├── icons/                 # 共享图标资源
└── README.md
```

### 快速开始

#### macOS

```bash
cd mac_version
./build.sh
# 应用将创建在 mac_version/dist/
```

#### Windows

```powershell
cd win_version
.\build.ps1
# 应用将创建在 win_version\publish\
```

#### Linux

**图形界面模式：**
```bash
cd linux_version
python3 main.py
```

**命令行模式** (适合 SSH 远程控制)：
```bash
cd linux_version

# 查看连接状态
python3 cli.py status

# 连接 RM-01 到互联网
python3 cli.py connect

# 断开连接
python3 cli.py disconnect

# 检测 RM-01 适配器
python3 cli.py detect

# 语言支持
python3 cli.py --lang zh status    # 中文
python3 cli.py --lang en status    # 英文
```

**全局命令安装**（可选）：
```bash
cd linux_version
sudo ln -s "$(pwd)/cli.py" /usr/local/bin/rm01-cli
sudo chmod +x /usr/local/bin/rm01-cli

# 现在可以在任何地方使用
rm01-cli status
rm01-cli connect
rm01-cli disconnect
```

**构建 AppImage：**
```bash
./build-appimage.sh
```

### 工作原理

RM-01 内置 AX88179A 交换机芯片：
1. 通过 DHCP 给连接的电脑分配 IP `10.10.99.100`
2. 期望电脑作为其网关

本应用程序：
1. 检测 AX88179A USB 网卡
2. 配置静态 IP (10.10.99.100) 以确保稳定性
3. 启用 IP 转发
4. 设置 NAT 将网络共享给 RM-01

### 系统要求

- **macOS**: 13.0 (Ventura) 或更高版本
- **Windows**: 10/11，需要 .NET 8.0
- **Linux**: Ubuntu 20.04+ / Debian 11+ / Fedora 35+ 或同等版本

### 许可证

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

---

## Credits

Made with ❤️ for RM-01 users

Built with Swift, C#, and Python
