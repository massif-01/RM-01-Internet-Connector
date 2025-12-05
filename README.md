# RM-01 Internet Connector

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

RM-01 Internet Connector is a native macOS menu bar application that shares your Mac's internet connection to RM-01 devices via the AX88179A USB Ethernet adapter.

![App Screenshot](icons/screenshot.png)

### Features

- 🌐 **One-Click Connection** - Share internet with a single click
- 📍 **Menu Bar Integration** - Native macOS menu bar experience
- 🎨 **Liquid Glass UI** - Modern, beautiful interface with smooth animations
- 🌍 **Bilingual Support** - Full Chinese and English localization
- ⚡ **Auto Detection** - Automatically detects AX88179A USB Ethernet adapters
- 🔄 **Visual Feedback** - Real-time connection status with animations

### System Requirements

- macOS 13.0 (Ventura) or later
- AX88179A USB Ethernet adapter (RM-01 device)
- Administrator privileges (for network configuration)

### Installation

#### From DMG
1. Download the latest `.dmg` from Releases
2. Open the DMG and drag the app to Applications
3. Launch "RM-01 Internet Connector"

#### Build from Source
```bash
git clone <repository-url>
cd "RM-01 Internet Connector"
./build.sh
```

### Usage

1. **Connect your RM-01** (AX88179A adapter) to your Mac
2. **Click the menu bar icon** to access the dropdown menu
3. **Select "Connect"** to share your internet
4. The app will:
   - Configure a static IP (10.10.99.100) on the adapter
   - Enable NAT and Internet Sharing
5. **Select "Disconnect"** when finished

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
    ├── statusIcon.png               # Menu bar icon (16x16)
    ├── statusIcon@2x.png            # Menu bar icon @2x (32x32)
    └── body.png                     # RM-01 device image
```

### Technical Details

- **UI Framework**: SwiftUI + AppKit
- **Build System**: Swift Package Manager
- **Network Configuration**: Uses `networksetup` and `launchctl` via privileged AppleScript
- **Supported Adapters**: AX88179A, USB 10/100/1000 LAN, USB Gigabit Ethernet

### Troubleshooting

**Menu bar icon appears as white square?**
- Rebuild the app with `./build.sh`

**Cannot connect?**
- Ensure the USB adapter is properly connected
- Check System Preferences → Network for the adapter
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

![应用截图](icons/screenshot.png)

### 功能特点

- 🌐 **一键连接** - 单击即可共享网络
- 📍 **菜单栏集成** - 原生 macOS 菜单栏体验
- 🎨 **液态玻璃界面** - 现代美观的界面设计，流畅动画
- 🌍 **双语支持** - 完整的中英文本地化
- ⚡ **自动检测** - 自动检测 AX88179A USB 网卡
- 🔄 **视觉反馈** - 实时连接状态动画

### 系统要求

- macOS 13.0 (Ventura) 或更高版本
- AX88179A USB 网卡 (RM-01 设备)
- 管理员权限（用于网络配置）

### 安装方法

#### 从 DMG 安装
1. 从 Releases 下载最新的 `.dmg` 文件
2. 打开 DMG 并将应用拖到"应用程序"
3. 启动 "RM-01 Internet Connector"

#### 从源码构建
```bash
git clone <repository-url>
cd "RM-01 Internet Connector"
./build.sh
```

### 使用方法

1. **连接 RM-01**（AX88179A 网卡）到 Mac
2. **点击菜单栏图标**打开下拉菜单
3. **选择"连接"**开始共享网络
4. 应用会自动：
   - 在网卡上配置静态 IP (10.10.99.100)
   - 启用 NAT 和互联网共享
5. 完成后**选择"断开连接"**

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
    ├── statusIcon.png               # 菜单栏图标 (16x16)
    ├── statusIcon@2x.png            # 菜单栏图标 @2x (32x32)
    └── body.png                     # RM-01 设备图片
```

### 技术细节

- **UI 框架**：SwiftUI + AppKit
- **构建系统**：Swift Package Manager
- **网络配置**：通过特权 AppleScript 使用 `networksetup` 和 `launchctl`
- **支持的网卡**：AX88179A、USB 10/100/1000 LAN、USB Gigabit Ethernet

### 常见问题

**菜单栏图标显示为白色方块？**
- 使用 `./build.sh` 重新构建应用

**无法连接？**
- 确保 USB 网卡正确连接
- 在系统偏好设置 → 网络中检查网卡状态
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
