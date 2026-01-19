# RM-01 Internet Connector - macOS Version

macOS 原生应用，通过 AX88179A USB 网卡将 Mac 的互联网连接共享给 RM-01 设备。

## 系统要求

- macOS 13.0 (Ventura) 或更高版本
- Xcode Command Line Tools
- AX88179A USB 网卡 (RM-01 设备)

## 构建

```bash
cd mac_version
./build.sh
```

构建完成后：
- `.app` 应用包位于 `dist/` 目录
- `.dmg` 安装器也会自动生成

## 技术栈

- **语言**: Swift 6
- **UI 框架**: SwiftUI + AppKit
- **构建系统**: Swift Package Manager
- **网络配置**: networksetup, pfctl, sysctl

## 项目结构

```
mac_version/
├── Sources/
│   ├── RM01InternetConnector/
│   │   ├── RM01InternetConnector.swift  # 主程序、菜单栏
│   │   └── UIComponents.swift           # SwiftUI 视图
│   └── Resources/
│       ├── AppIcon.icns
│       ├── statusIcon*.png
│       └── body.png
├── Package.swift
├── build.sh
└── README.md
```

## 许可证

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.
