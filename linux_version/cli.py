#!/usr/bin/env python3
"""
RM-01 Internet Connector - CLI Mode
Command-line interface for controlling RM-01 network sharing via SSH

Usage:
    rm01-cli status      - Show current connection status
    rm01-cli detect      - Detect RM-01 adapter
    rm01-cli connect     - Enable internet sharing to RM-01
    rm01-cli disconnect  - Disable internet sharing
    rm01-cli help        - Show this help message

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.
"""

import sys
import os
import argparse
import getpass
import time
import locale
import subprocess
from typing import Optional

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network_service import NetworkService, NetworkInterface


class I18n:
    """Simple internationalization for CLI"""
    
    def __init__(self, lang=None):
        # Auto-detect language from system locale
        if lang is None:
            try:
                # Try LANG environment variable first
                env_lang = os.environ.get('LANG', '') or os.environ.get('LC_ALL', '')
                if env_lang.startswith('zh'):
                    lang = 'zh'
                else:
                    # Fallback to locale.getlocale()
                    try:
                        system_lang = locale.getlocale()[0]
                        if system_lang and system_lang.startswith('zh'):
                            lang = 'zh'
                        else:
                            lang = 'en'
                    except:
                        lang = 'en'
            except:
                lang = 'en'
        
        self.lang = lang
        self._strings = {
            'en': {
                'header': 'RM-01 Internet Connector - CLI',
                'status': 'Show current connection status',
                'detect': 'Detect RM-01 adapter',
                'connect': 'Enable internet sharing to RM-01',
                'disconnect': 'Disable internet sharing',
                'help': 'Show this help message',
                
                'adapter': 'Adapter',
                'name': 'Name',
                'mac': 'MAC',
                'type': 'Type',
                'status_label': 'Status',
                'upstream': 'Upstream',
                'traffic': 'Traffic',
                
                'connected': 'Connected',
                'not_connected': 'Not Connected',
                'partially_connected': 'Partially Connected',
                
                'no_adapter': 'No RM-01 adapter (AX88179A) detected',
                'please_connect': 'Please connect RM-01 via USB',
                'adapter_found': 'RM-01 adapter found!',
                'details': 'Details',
                'interface': 'Interface',
                'chip': 'Chip',
                'upstream_network': 'Upstream Network',
                'no_upstream': 'No upstream network found (Wi-Fi/Ethernet)',
                
                'scanning': 'Scanning for AX88179A USB Ethernet adapter...',
                'troubleshooting': 'Troubleshooting',
                'trouble1': 'Make sure RM-01 is connected via USB',
                'trouble2': "Check 'lsusb | grep -i asix' for the device",
                'trouble3': "Check 'ip link show' for network interfaces",
                
                'detecting_adapter': 'Detecting RM-01 adapter...',
                'found_adapter': 'Found adapter',
                'finding_upstream': 'Finding upstream network...',
                'found_upstream': 'Found upstream',
                'no_upstream_found': 'No upstream network found',
                'ensure_internet': 'Please ensure your computer has internet access',
                
                'password_required': 'Administrator password required for network configuration',
                'password_prompt': 'Password',
                'cancelled': 'Cancelled',
                'password_needed': 'Password is required',
                
                'configuring_network': 'Configuring network...',
                'setting_static_ip': 'Setting static IP',
                'enabling_forwarding': 'Enabling IP forwarding',
                'setting_nat': 'Setting up NAT',
                'sharing_enabled': 'Internet sharing enabled!',
                'rm01_can_access': 'RM-01 can now access the internet through this computer.',
                
                'auth_failed': 'Authentication failed - incorrect password',
                'failed_to_enable': 'Failed to enable sharing',
                
                'disconnecting': 'Disconnecting',
                'no_active_connection': 'No active connection found',
                'removing_nat': 'Removing NAT rules...',
                'restoring_dhcp': 'Restoring DHCP...',
                'sharing_disabled': 'Internet sharing disabled',
                'failed_to_disable': 'Failed to disable sharing',
                
                'ip_forwarding_disabled': 'IP forwarding is disabled',
                
                'commands': 'Commands',
                'examples': 'Examples',
            },
            'zh': {
                'header': 'RM-01 互联网连接助手 - 命令行模式',
                'status': '显示当前连接状态',
                'detect': '检测 RM-01 设备',
                'connect': '启用网络共享给 RM-01',
                'disconnect': '禁用网络共享',
                'help': '显示此帮助信息',
                
                'adapter': '适配器',
                'name': '名称',
                'mac': 'MAC 地址',
                'type': '类型',
                'status_label': '状态',
                'upstream': '上游网络',
                'traffic': '流量',
                
                'connected': '已连接',
                'not_connected': '未连接',
                'partially_connected': '部分连接',
                
                'no_adapter': '未检测到 RM-01 适配器 (AX88179A)',
                'please_connect': '请通过 USB 连接 RM-01',
                'adapter_found': '找到 RM-01 适配器！',
                'details': '详细信息',
                'interface': '网络接口',
                'chip': '芯片',
                'upstream_network': '上游网络',
                'no_upstream': '未找到上游网络 (Wi-Fi/有线网络)',
                
                'scanning': '正在扫描 AX88179A USB 网卡...',
                'troubleshooting': '故障排除',
                'trouble1': '确保 RM-01 已通过 USB 连接',
                'trouble2': "检查 'lsusb | grep -i asix' 查看设备",
                'trouble3': "检查 'ip link show' 查看网络接口",
                
                'detecting_adapter': '正在检测 RM-01 适配器...',
                'found_adapter': '找到适配器',
                'finding_upstream': '正在查找上游网络...',
                'found_upstream': '找到上游网络',
                'no_upstream_found': '未找到上游网络',
                'ensure_internet': '请确保您的电脑已连接到互联网',
                
                'password_required': '需要管理员密码来配置网络',
                'password_prompt': '密码',
                'cancelled': '已取消',
                'password_needed': '需要密码',
                
                'configuring_network': '正在配置网络...',
                'setting_static_ip': '设置静态 IP',
                'enabling_forwarding': '启用 IP 转发',
                'setting_nat': '设置 NAT',
                'sharing_enabled': '网络共享已启用！',
                'rm01_can_access': 'RM-01 现在可以通过此电脑访问互联网。',
                
                'auth_failed': '认证失败 - 密码错误',
                'failed_to_enable': '启用共享失败',
                
                'disconnecting': '正在断开连接',
                'no_active_connection': '未找到活动连接',
                'removing_nat': '正在移除 NAT 规则...',
                'restoring_dhcp': '正在恢复 DHCP...',
                'sharing_disabled': '网络共享已禁用',
                'failed_to_disable': '禁用共享失败',
                
                'ip_forwarding_disabled': 'IP 转发已禁用',
                
                'commands': '命令',
                'examples': '示例',
            }
        }
    
    def t(self, key: str) -> str:
        """Translate a key"""
        return self._strings.get(self.lang, {}).get(key, key)


# Global i18n instance
i18n = I18n()


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    
    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)"""
        cls.RESET = ""
        cls.BOLD = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.CYAN = ""


# Disable colors if not a TTY
if not sys.stdout.isatty():
    Colors.disable()


def print_header():
    """Print application header"""
    header_text = i18n.t('header')
    print(f"\n{Colors.CYAN}{Colors.BOLD}{header_text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * len(header_text)}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}! {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}→ {message}{Colors.RESET}")


class CLI:
    """Command-line interface for RM-01 Internet Connector"""
    
    def __init__(self):
        self.network_service = NetworkService()
        self._state_file = "/tmp/rm01_connection_state"
    
    def _get_saved_state(self) -> Optional[dict]:
        """Get saved connection state"""
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        return {
                            'rm01_interface': lines[0].strip(),
                            'upstream_interface': lines[1].strip()
                        }
        except Exception:
            pass
        return None
    
    def _save_state(self, rm01_iface: str, upstream_iface: str):
        """Save connection state"""
        try:
            with open(self._state_file, 'w') as f:
                f.write(f"{rm01_iface}\n{upstream_iface}\n")
        except Exception:
            pass
    
    def _clear_state(self):
        """Clear saved connection state"""
        try:
            if os.path.exists(self._state_file):
                os.unlink(self._state_file)
        except Exception:
            pass
    
    def cmd_status(self):
        """Show current connection status"""
        print_header()
        
        # Detect adapter
        adapter = self.network_service.detect_adapter()
        
        if not adapter:
            print_error(i18n.t('no_adapter'))
            print_info(i18n.t('please_connect'))
            return 1
        
        print(f"{Colors.BOLD}{i18n.t('adapter')}:{Colors.RESET}")
        print(f"  {i18n.t('name')}:  {adapter.name}")
        print(f"  {i18n.t('mac')}:   {adapter.mac}")
        print(f"  {i18n.t('type')}:  {adapter.description}")
        print()
        
        # Check actual network configuration (not just state file)
        is_configured = self._check_actual_connection(adapter.name)
        
        # Check if IP forwarding is enabled
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
                forwarding = f.read().strip() == '1'
        except Exception:
            forwarding = False
        
        # Get saved state for upstream info
        state = self._get_saved_state()
        
        if is_configured and forwarding:
            print(f"{Colors.GREEN}{Colors.BOLD}{i18n.t('status_label')}: {i18n.t('connected')}{Colors.RESET}")
            
            # Show upstream
            if state and state.get('upstream_interface'):
                print(f"  {i18n.t('upstream')}: {state['upstream_interface']}")
            else:
                # Try to find upstream
                upstream = self.network_service.find_upstream_interface(adapter.name)
                if upstream:
                    print(f"  {i18n.t('upstream')}: {upstream.name}")
            
            # Show current IP
            current_ip = self._get_interface_ip(adapter.name)
            if current_ip:
                print(f"  IP: {current_ip}")
            
            # Show traffic stats
            rx, tx = self.network_service.get_interface_stats(adapter.name)
            print(f"  {i18n.t('traffic')}:  RX {self._format_bytes(rx)}, TX {self._format_bytes(tx)}")
            
        elif is_configured and not forwarding:
            print(f"{Colors.YELLOW}{Colors.BOLD}{i18n.t('status_label')}: {i18n.t('partially_connected')}{Colors.RESET}")
            print_warning(i18n.t('ip_forwarding_disabled'))
            
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}{i18n.t('status_label')}: {i18n.t('not_connected')}{Colors.RESET}")
        
        print()
        return 0
    
    def _check_actual_connection(self, interface: str) -> bool:
        """
        Check if the interface is actually configured for sharing.
        
        Note: We cannot rely on IP address alone because RM-01's DHCP server
        will always assign 10.10.99.100 to this computer when connected.
        
        The real indicator of "sharing enabled" is:
        1. NAT (MASQUERADE) rules are present in iptables
        2. IP forwarding is enabled
        """
        # Check if there are NAT rules for this interface
        has_nat_rules = False
        for cmd in [['sudo', '-n', 'iptables', '-t', 'nat', '-L', 'POSTROUTING', '-n'],
                    ['iptables', '-t', 'nat', '-L', 'POSTROUTING', '-n']]:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and 'MASQUERADE' in result.stdout and '10.10.99.0' in result.stdout:
                    has_nat_rules = True
                    break
            except:
                continue
        
        return has_nat_rules
    
    def _get_interface_ip(self, interface: str) -> Optional[str]:
        """Get the IP address of an interface"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Parse output for inet line
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('inet '):
                    # "inet 10.10.99.100/24 ..."
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1].split('/')[0]
        except:
            pass
        return None
    
    def cmd_detect(self):
        """Detect RM-01 adapter"""
        print_header()
        print_info(i18n.t('scanning'))
        print()
        
        adapter = self.network_service.detect_adapter()
        
        if adapter:
            print_success(i18n.t('adapter_found'))
            print(f"\n{Colors.BOLD}{i18n.t('details')}:{Colors.RESET}")
            print(f"  {i18n.t('interface')}: {adapter.name}")
            print(f"  {i18n.t('mac')}:       {adapter.mac}")
            print(f"  {i18n.t('chip')}:      {adapter.description}")
            
            # Find upstream
            upstream = self.network_service.find_upstream_interface(adapter.name)
            if upstream:
                print(f"\n{Colors.BOLD}{i18n.t('upstream_network')}:{Colors.RESET}")
                print(f"  {i18n.t('interface')}: {upstream.name}")
            else:
                print_warning(f"\n{i18n.t('no_upstream')}")
            
            print()
            return 0
        else:
            print_error(i18n.t('no_adapter'))
            print()
            print(f"{i18n.t('troubleshooting')}:")
            print(f"  1. {i18n.t('trouble1')}")
            print(f"  2. {i18n.t('trouble2')}")
            print(f"  3. {i18n.t('trouble3')}")
            print()
            return 1
    
    def cmd_connect(self, password: Optional[str] = None):
        """Enable internet sharing to RM-01"""
        print_header()
        
        # Detect adapter
        print_info(i18n.t('detecting_adapter'))
        adapter = self.network_service.detect_adapter()
        
        if not adapter:
            print_error(i18n.t('no_adapter'))
            print_info(i18n.t('please_connect'))
            return 1
        
        print_success(f"{i18n.t('found_adapter')}: {adapter.name}")
        
        # Find upstream
        print_info(i18n.t('finding_upstream'))
        upstream = self.network_service.find_upstream_interface(adapter.name)
        
        if not upstream:
            print_error(i18n.t('no_upstream_found'))
            print_info(i18n.t('ensure_internet'))
            return 1
        
        print_success(f"{i18n.t('found_upstream')}: {upstream.name}")
        
        # Get password
        if not password:
            print()
            print_info(i18n.t('password_required'))
            try:
                password = getpass.getpass(f"{i18n.t('password_prompt')}: ")
            except (KeyboardInterrupt, EOFError):
                print()
                print_warning(i18n.t('cancelled'))
                return 1
        
        if not password:
            print_error(i18n.t('password_needed'))
            return 1
        
        # Enable sharing
        print()
        print_info(i18n.t('configuring_network'))
        print_info(f"  {i18n.t('setting_static_ip')}: {self.network_service.STATIC_IP}")
        print_info(f"  {i18n.t('enabling_forwarding')}")
        print_info(f"  {i18n.t('setting_nat')}: {adapter.name} → {upstream.name}")
        
        success, error = self.network_service.enable_sharing(
            adapter.name,
            upstream.name,
            password
        )
        
        if success:
            self._save_state(adapter.name, upstream.name)
            print()
            print_success(i18n.t('sharing_enabled'))
            print()
            print(f"{Colors.GREEN}{i18n.t('rm01_can_access')}{Colors.RESET}")
            print()
            return 0
        else:
            print()
            if "permission" in error.lower() or "password" in error.lower() or "incorrect" in error.lower():
                print_error(i18n.t('auth_failed'))
            else:
                print_error(f"{i18n.t('failed_to_enable')}: {error}")
            return 1
    
    def cmd_disconnect(self, password: Optional[str] = None):
        """Disable internet sharing"""
        print_header()
        
        # Get saved state
        state = self._get_saved_state()
        
        if not state:
            # Try to detect current adapter
            adapter = self.network_service.detect_adapter()
            if adapter:
                upstream = self.network_service.find_upstream_interface(adapter.name)
                if upstream:
                    state = {
                        'rm01_interface': adapter.name,
                        'upstream_interface': upstream.name
                    }
        
        if not state:
            print_warning(i18n.t('no_active_connection'))
            return 0
        
        print_info(f"{i18n.t('disconnecting')} {state['rm01_interface']}...")
        
        # Get password
        if not password:
            print()
            print_info(i18n.t('password_required'))
            try:
                password = getpass.getpass(f"{i18n.t('password_prompt')}: ")
            except (KeyboardInterrupt, EOFError):
                print()
                print_warning(i18n.t('cancelled'))
                return 1
        
        if not password:
            print_error(i18n.t('password_needed'))
            return 1
        
        # Disable sharing
        print()
        print_info(i18n.t('removing_nat'))
        print_info(i18n.t('restoring_dhcp'))
        
        success, error = self.network_service.disable_sharing(
            state['rm01_interface'],
            state['upstream_interface'],
            password
        )
        
        if success:
            self._clear_state()
            print()
            print_success(i18n.t('sharing_disabled'))
            print()
            return 0
        else:
            print()
            if "permission" in error.lower() or "password" in error.lower():
                print_error(i18n.t('auth_failed'))
            else:
                print_error(f"{i18n.t('failed_to_disable')}: {error}")
            return 1
    
    def cmd_help(self):
        """Show help message"""
        print(__doc__)
        return 0
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string"""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / 1024 / 1024:.1f} MB"
        else:
            return f"{bytes_val / 1024 / 1024 / 1024:.2f} GB"


def main():
    """CLI entry point"""
    global i18n
    
    # Parse language argument first
    lang = None
    if '--lang' in sys.argv:
        try:
            lang_idx = sys.argv.index('--lang') + 1
            if lang_idx < len(sys.argv):
                lang = sys.argv[lang_idx]
        except:
            pass
    elif '-l' in sys.argv:
        try:
            lang_idx = sys.argv.index('-l') + 1
            if lang_idx < len(sys.argv):
                lang = sys.argv[lang_idx]
        except:
            pass
    
    # Set language before creating parser
    if lang:
        i18n = I18n(lang)
    
    parser = argparse.ArgumentParser(
        description=i18n.t('header'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{i18n.t('commands')}:
  status      {i18n.t('status')}
  detect      {i18n.t('detect')}
  connect     {i18n.t('connect')}
  disconnect  {i18n.t('disconnect')}
  help        {i18n.t('help')}

{i18n.t('examples')}:
  %(prog)s status
  %(prog)s connect
  %(prog)s disconnect
"""
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default='help',
        choices=['status', 'detect', 'connect', 'disconnect', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--password', '-p',
        help='Sudo password (not recommended, use stdin instead)'
    )
    
    parser.add_argument(
        '--lang', '-l',
        choices=['en', 'zh'],
        help='Language (en=English, zh=中文)'
    )
    
    args = parser.parse_args()
    
    cli = CLI()
    
    # Execute command
    if args.command == 'status':
        return cli.cmd_status()
    elif args.command == 'detect':
        return cli.cmd_detect()
    elif args.command == 'connect':
        return cli.cmd_connect(args.password)
    elif args.command == 'disconnect':
        return cli.cmd_disconnect(args.password)
    elif args.command == 'help':
        return cli.cmd_help()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
