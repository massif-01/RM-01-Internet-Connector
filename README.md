# RM-01 Internet Connector

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

RM-01 Internet Connector is a native macOS menu bar application that shares your Mac's internet connection to RM-01 devices via the AX88179A USB Ethernet adapter.

<img src="icons/screenshot.png" alt="App Screenshot" width="50%">

### Features

- 🌐 **One-Click Connection** - Share internet with a single click
- 📍 **Menu Bar Integration** - Native macOS menu bar experience
- 📊 **Real-time Speed Monitor** - Live RM-01 upload/download speed in menu dropdown (updates every second, even when menu is open)
- 🎨 **Liquid Glass UI** - Modern, beautiful interface with smooth animations
- 🌍 **Bilingual Support** - Full Chinese and English localization (menu bar items switch dynamically)
- ⚡ **Auto Detection** - Automatically detects AX88179A USB Ethernet adapters
- 🔄 **Visual Feedback** - Real-time connection status with animations

### System Requirements

- macOS 13.0 (Ventura) or later
- AX88179A USB Ethernet adapter (RM-01 device)
- Administrator privileges (for network configuration)

### Installation

#### From DMG
1. Download the latest `.dmg` from Releases
2. Open the DMG file - you'll see an installer window
3. Drag "RM-01 Internet Connector.app" to the Applications folder
4. **If macOS says the app is damaged**, double-click the `fix-app-damaged.sh` script in the DMG
   - Enter your password when prompted
   - This removes the quarantine flag set by macOS Gatekeeper
5. Launch "RM-01 Internet Connector" from Applications
6. For detailed instructions, see the `HOW_TO_USE.txt` file in the DMG

#### Build from Source
```bash
git clone <repository-url>
cd "RM-01 Internet Connector"
./build.sh
```

The build script will create:
- A complete `.app` bundle in `dist/`
- A `.dmg` installer with drag-to-install interface
- Helper scripts and documentation included in the DMG

### Usage

1. **Connect your RM-01** (AX88179A adapter) to your Mac via USB-C
2. **Launch the app** and click the menu bar icon
3. **Select "Connect"** to share your internet
4. The app will automatically:
   - Detect your active internet connection (Wi-Fi, Ethernet, iPhone USB, etc.)
   - Configure a static IP (10.10.99.100) on the adapter
   - Enable IP forwarding and NAT via pfctl
   - RM-01 can now access the internet through your Mac
5. **Monitor real-time speed** - Open the menu dropdown to see live upload/download speeds (e.g., `↑125KB/s   |   ↓2.3MB/s`)
6. **Select "Disconnect"** when finished (restores DHCP automatically)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| ⌘Q | Quit Application |
| ⌘W | Close Window |
| ⌘M | Minimize Window |
| ⌘O | Open Control Panel |

### Architecture

```
Sources/
├── RM01InternetConnector/
│   ├── RM01InternetConnector.swift  # App delegate, menu bar, window management
│   └── UIComponents.swift           # SwiftUI views, localization, animations
└── Resources/
    ├── AppIcon.icns                 # Application icon
    ├── statusIcon.png               # Menu bar icon @1x (18x18)
    ├── statusIcon@2x.png            # Menu bar icon @2x (36x36)
    ├── statusIcon@3x.png            # Menu bar icon @3x (54x54)
    └── body.png                     # RM-01 device image
```

### Technical Details

- **UI Framework**: SwiftUI + AppKit
- **Build System**: Swift Package Manager
- **Network Configuration**: Uses `networksetup`, `pfctl`, and `sysctl` via privileged shell script
- **NAT Method**: Direct pfctl NAT rules (does not modify System Settings → Sharing)
- **Speed Monitoring**: Uses `getifaddrs()` system API to read interface statistics (updates every second in RunLoop common mode)
- **Supported Adapters**: AX88179A USB Ethernet (RM-01 built-in chip)

### Troubleshooting

**macOS says the app is "damaged and can't be opened"?**
- This happens because the app is not code-signed. Run this command in Terminal:
```bash
xattr -cr /Applications/RM-01\ Internet\ Connector.app
```
- Then try opening the app again

**Menu bar icon appears as white square?**
- Rebuild the app with `./build.sh`

**Cannot connect?**
- Ensure the USB adapter is properly connected
- Check System Settings → Network for the adapter
- Try unplugging and reconnecting the adapter

**Password prompt keeps appearing?**
- The app requires admin privileges for network changes
- This is a macOS security feature

**"No Device" error?**
- Make sure the AX88179A adapter is connected
- The adapter must be recognized by macOS first

---

<a name="中文"></a>
## 中文

### 概述

RM-01 互联网连接助手是一款原生 macOS 菜单栏应用，通过 AX88179A USB 网卡将 Mac 的互联网连接共享给 RM-01 设备。

<img src="icons/screenshot.png" alt="应用截图" width="50%">

### 功能特点

- 🌐 **一键连接** - 单击即可共享网络
- 📍 **菜单栏集成** - 原生 macOS 菜单栏体验
- 📊 **实时网速监控** - 菜单下拉显示 RM-01 实时上传/下载速度（每秒更新，菜单打开时也会刷新）
- 🎨 **液态玻璃界面** - 现代美观的界面设计，流畅动画
- 🌍 **双语支持** - 完整的中英文本地化（菜单栏项目动态切换）
- ⚡ **自动检测** - 自动检测 AX88179A USB 网卡
- 🔄 **视觉反馈** - 实时连接状态动画

### 系统要求

- macOS 13.0 (Ventura) 或更高版本
- AX88179A USB 网卡 (RM-01 设备)
- 管理员权限（用于网络配置）

### 安装方法

#### 从 DMG 安装
1. 从 Releases 下载最新的 `.dmg` 文件
2. 打开 DMG 文件 - 您会看到安装器窗口
3. 将 "RM-01 Internet Connector.app" 拖到"应用程序"文件夹
4. **如果 macOS 提示"应用已损坏"**，双击 DMG 中的 `fix-app-damaged.sh` 脚本
   - 在提示时输入密码
   - 这会移除 macOS Gatekeeper 设置的隔离标志
5. 从应用程序文件夹启动 "RM-01 Internet Connector"
6. 详细说明请查看 DMG 中的 `HOW_TO_USE.txt` 文件

#### 从源码构建
```bash
git clone <repository-url>
cd "RM-01 Internet Connector"
./build.sh
```

构建脚本会创建：
- 完整的 `.app` 应用包在 `dist/` 目录
- 带拖拽安装界面的 `.dmg` 安装器
- DMG 中包含辅助脚本和使用说明

### 使用方法

1. **通过 USB-C 连接 RM-01**（AX88179A 网卡）到 Mac
2. **启动应用**并点击菜单栏图标
3. **选择"连接"**开始共享网络
4. 应用会自动完成以下配置：
   - 自动检测当前活动的网络连接（Wi-Fi、有线网络、iPhone USB 等）
   - 在网卡上配置静态 IP (10.10.99.100)
   - 通过 pfctl 启用 IP 转发和 NAT
   - RM-01 即可通过 Mac 访问互联网
5. **实时监控网速** - 打开菜单下拉可查看实时上传/下载速度（例如 `↑125KB/s   |   ↓2.3MB/s`）
6. 完成后**选择"断开连接"**（自动恢复 DHCP）

### 键盘快捷键

| 快捷键 | 操作 |
|--------|------|
| ⌘Q | 退出应用 |
| ⌘W | 关闭窗口 |
| ⌘M | 最小化窗口 |
| ⌘O | 打开控制面板 |

### 项目结构

```
Sources/
├── RM01InternetConnector/
│   ├── RM01InternetConnector.swift  # 应用代理、菜单栏、窗口管理
│   └── UIComponents.swift           # SwiftUI 视图、本地化、动画
└── Resources/
    ├── AppIcon.icns                 # 应用图标
    ├── statusIcon.png               # 菜单栏图标 @1x (18x18)
    ├── statusIcon@2x.png            # 菜单栏图标 @2x (36x36)
    ├── statusIcon@3x.png            # 菜单栏图标 @3x (54x54)
    └── body.png                     # RM-01 设备图片
```

### 技术细节

- **UI 框架**：SwiftUI + AppKit
- **构建系统**：Swift Package Manager
- **网络配置**：通过特权脚本使用 `networksetup`、`pfctl` 和 `sysctl`
- **NAT 方式**：直接配置 pfctl NAT 规则（不修改系统设置中的共享配置）
- **网速监控**：使用 `getifaddrs()` 系统 API 读取接口统计（RunLoop common mode 下每秒更新）
- **支持的网卡**：AX88179A USB 网卡（RM-01 内置芯片）

### 常见问题

**macOS 提示"已损坏，无法打开"？**
- 这是因为应用没有代码签名。在终端中运行以下命令：
```bash
xattr -cr /Applications/RM-01\ Internet\ Connector.app
```
- 然后重新打开应用即可

**菜单栏图标显示为白色方块？**
- 使用 `./build.sh` 重新构建应用

**无法连接？**
- 确保 USB 网卡正确连接
- 在系统设置 → 网络中检查网卡状态
- 尝试拔出并重新连接网卡

**密码提示反复出现？**
- 应用需要管理员权限来修改网络设置
- 这是 macOS 的安全功能

**显示"未检测到设备"？**
- 确保 AX88179A 网卡已连接
- 网卡必须先被 macOS 识别

---

## License

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

## Credits

Made with ❤️ for RM-01 users

Built with Swift, SwiftUI, and AppKit
