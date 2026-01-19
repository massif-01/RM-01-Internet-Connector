# RM-01 Internet Connector - Linux Version

将 Linux 电脑的互联网连接共享给 RM-01 设备。

支持两种控制方式：
- **GUI 模式** - 图形界面，与 macOS 版本一致的设计
- **CLI 模式** - 命令行控制，适合 SSH 远程操作

## 系统要求

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+ 或其他主流发行版)
- Python 3.8+
- PyQt6
- 具有 sudo 权限的用户账户
- zenity (用于图形化密码对话框)

## 安装依赖

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3 python3-pip python3-pyqt6 zenity
pip3 install PyQt6
```

### Fedora

```bash
sudo dnf install python3 python3-pip python3-qt6 zenity
pip3 install PyQt6
```

### Arch Linux

```bash
sudo pacman -S python python-pip python-pyqt6 zenity
```

## 运行方式

### GUI 模式 - 图形界面

#### 方式 1: 直接运行 (开发/测试)

```bash
cd linux_version
python3 main.py
```

#### 方式 2: AppImage (推荐)

下载 AppImage 文件后:

```bash
chmod +x RM-01_Internet_Connector-*.AppImage
./RM-01_Internet_Connector-*.AppImage
```

#### 方式 3: 从源码构建 AppImage

```bash
cd linux_version
chmod +x build-appimage.sh
./build-appimage.sh
```

### CLI 模式 - 命令行控制 (适合 SSH 远程)

CLI 会自动检测系统语言，也可以手动指定：

```bash
cd linux_version

# 自动检测语言 (中文系统会显示中文)
python3 cli.py status

# 强制使用中文
python3 cli.py --lang zh status

# 强制使用英文
python3 cli.py --lang en status

# 检测 RM-01 设备
python3 cli.py detect

# 启用网络共享 (会提示输入密码)
python3 cli.py connect

# 断开网络共享
python3 cli.py disconnect

# 查看帮助
python3 cli.py help
```

#### SSH 远程使用示例

```bash
# 从其他电脑通过 SSH 控制
ssh user@linux-pc "cd /path/to/linux_version && python3 cli.py status"
ssh user@linux-pc "cd /path/to/linux_version && python3 cli.py connect"
```

#### 创建全局命令 (可选)

```bash
# 创建符号链接，这样可以在任何位置使用 rm01-cli 命令
sudo ln -s /path/to/linux_version/cli.py /usr/local/bin/rm01-cli

# 然后可以直接使用
rm01-cli status
rm01-cli connect
```

## 使用说明

1. 通过 USB 连接 RM-01 到 Linux 电脑
2. 运行应用程序
3. 点击 "Connect" / "立即连接" 按钮
4. 输入 sudo 密码 (会弹出图形化对话框)
5. 等待连接建立
6. RM-01 现在可以通过你的电脑上网了

## 工作原理

RM-01 内置 AX88179A 交换机芯片，会通过 DHCP 给连接的电脑分配 IP 地址 (10.10.99.100)。

本应用程序:
1. 检测 AX88179A USB 网卡
2. 配置静态 IP (10.10.99.100) 以确保稳定性
3. 启用 IP 转发 (`net.ipv4.ip_forward=1`)
4. 配置 iptables NAT 规则，将 RM-01 的流量转发到上游网络 (如 Wi-Fi)

## 故障排除

### 未检测到设备

- 确保 RM-01 已通过 USB 连接
- 运行 `lsusb | grep -i asix` 检查设备是否被识别
- 运行 `ip link show` 查看网络接口

### 密码对话框不弹出

- 确保已安装 zenity: `sudo apt install zenity`
- 如果在远程终端/SSH 中运行，需要在本地桌面环境中运行

### 连接后 RM-01 仍无法上网

- 检查你的电脑是否有互联网连接
- 检查 iptables 规则: `sudo iptables -t nat -L`
- 检查 IP 转发: `cat /proc/sys/net/ipv4/ip_forward` (应该是 1)

### 系统托盘图标不显示

- GNOME 桌面需要安装 AppIndicator 扩展
- 这不影响应用程序的核心功能

## 技术细节

- **GUI 框架**: PyQt6
- **网络配置**: ip, iptables, sysctl
- **权限提升**: zenity + sudo
- **打包**: PyInstaller + AppImage

## 许可证

Apache License 2.0

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.
