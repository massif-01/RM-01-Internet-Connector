# RM-01 Internet Connector - Windows Version

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

RM-01 Internet Connector is a Windows application that shares your PC's internet connection to RM-01 devices via the AX88179A USB Ethernet adapter.

### Features

- 🌐 **One-Click Connection** - Share internet with a single click
- 📍 **System Tray Integration** - Runs in the system tray for easy access
- 🎨 **Modern UI** - Beautiful WPF interface with animations
- 🌍 **Bilingual Support** - Full Chinese and English localization
- ⚡ **Auto Detection** - Automatically detects AX88179A USB Ethernet adapters
- 🔄 **Auto Network Detection** - Works with Wi-Fi, Ethernet, USB tethering, etc.

### System Requirements

- Windows 10/11 (64-bit)
- .NET 8.0 Runtime
- AX88179A USB Ethernet adapter (RM-01 device)
- Administrator privileges

### Installation

1. Download the latest release
2. Extract to a folder
3. Run `RM01InternetConnector.exe` (will prompt for admin privileges)

### Build from Source

```powershell
cd win_version
.\build.ps1 -Publish
```

Output will be in: `RM01InternetConnector.Win/bin/Release/net8.0-windows10.0.19041.0/win10-x64/publish`

### Usage

1. **Connect your RM-01** (AX88179A adapter) to your PC via USB-C
2. **Launch the app** (will request admin privileges)
3. **Click "Connect"** to share your internet
4. The app will automatically:
   - Detect your active internet connection (Wi-Fi, Ethernet, USB tethering, etc.)
   - Configure a static IP (10.10.99.100) on the adapter
   - Enable Windows Internet Connection Sharing (ICS)
   - RM-01 can now access the internet through your PC
5. **Click "Disconnect"** when finished (restores DHCP automatically)

### Technical Details

- **UI Framework**: WPF (Windows Presentation Foundation)
- **Build System**: .NET 8.0 SDK
- **Network Configuration**: Uses `netsh` and Windows ICS COM interfaces
- **Supported Adapters**: AX88179A USB Ethernet (RM-01 built-in chip)

---

<a name="中文"></a>
## 中文

### 概述

RM-01 互联网连接助手是一款 Windows 应用，通过 AX88179A USB 网卡将 PC 的互联网连接共享给 RM-01 设备。

### 功能特点

- 🌐 **一键连接** - 单击即可共享网络
- 📍 **系统托盘集成** - 在系统托盘运行，方便访问
- 🎨 **现代化界面** - 精美的 WPF 界面和动画
- 🌍 **双语支持** - 完整的中英文本地化
- ⚡ **自动检测** - 自动检测 AX88179A USB 网卡
- 🔄 **智能网络检测** - 支持 Wi-Fi、有线网络、USB 共享等任意上网方式

### 系统要求

- Windows 10/11 (64位)
- .NET 8.0 运行时
- AX88179A USB 网卡 (RM-01 设备)
- 管理员权限

### 安装方法

1. 下载最新版本
2. 解压到文件夹
3. 运行 `RM01InternetConnector.exe`（会提示请求管理员权限）

### 从源码构建

```powershell
cd win_version
.\build.ps1 -Publish
```

输出目录：`RM01InternetConnector.Win/bin/Release/net8.0-windows10.0.19041.0/win10-x64/publish`

### 使用方法

1. **通过 USB-C 连接 RM-01**（AX88179A 网卡）到 PC
2. **启动应用**（会请求管理员权限）
3. **点击"连接"**开始共享网络
4. 应用会自动完成以下配置：
   - 自动检测当前活动的网络连接（Wi-Fi、有线网络、USB 共享等）
   - 在网卡上配置静态 IP (10.10.99.100)
   - 启用 Windows 互联网连接共享 (ICS)
   - RM-01 即可通过 PC 访问互联网
5. 完成后**点击"断开连接"**（自动恢复 DHCP）

### 技术细节

- **UI 框架**：WPF (Windows Presentation Foundation)
- **构建系统**：.NET 8.0 SDK
- **网络配置**：使用 `netsh` 和 Windows ICS COM 接口
- **支持的网卡**：AX88179A USB 网卡（RM-01 内置芯片）

---

## License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.
