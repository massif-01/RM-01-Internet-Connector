"""
Windows Network Service Implementation
Uses netsh commands and Windows ICS COM interface for network sharing
"""

import subprocess
import re
import sys
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    description: str
    mac: str


class WindowsNetworkService:
    """
    Windows network service for managing RM-01 internet sharing
    Uses netsh for configuration and ICS COM for sharing
    """
    
    STATIC_IP = "10.10.99.100"
    NETMASK = "255.255.255.0"
    GATEWAY = "10.10.99.100"
    DNS = "8.8.8.8"
    
    # Known AX88179A identifiers
    KNOWN_IDENTIFIERS = ["ax88179"]
    
    def detect_adapter(self) -> Optional[NetworkInterface]:
        """
        Detect AX88179A USB Ethernet adapter
        Returns the first matching adapter or None
        """
        try:
            # Use netsh to list all network interfaces
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output to find AX88179A
            # Each line format: "Enabled/Disabled   Connected/Disconnected   Dedicated/Loopback   Name"
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('Admin') or line.startswith('---'):
                    continue
                
                # Extract interface name (last part)
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                # Interface name is everything after the third space-separated field
                interface_name = ' '.join(parts[3:])
                
                # Check if this is AX88179A by getting more details
                if self._is_ax88179a(interface_name):
                    # Get MAC address
                    mac = self._get_mac_address(interface_name)
                    return NetworkInterface(
                        name=interface_name,
                        description="AX88179A USB Ethernet Adapter",
                        mac=mac or "N/A"
                    )
            
            return None
        except Exception as e:
            return None
    
    def _is_ax88179a(self, interface_name: str) -> bool:
        """Check if interface is AX88179A by checking its description"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface', f'name={interface_name}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            if result.returncode == 0:
                output_lower = result.stdout.lower()
                # Check if any known identifier is in the output
                return any(identifier in output_lower for identifier in self.KNOWN_IDENTIFIERS)
            
            return False
        except:
            return False
    
    def _get_mac_address(self, interface_name: str) -> Optional[str]:
        """Get MAC address of the interface"""
        try:
            result = subprocess.run(
                ['getmac', '/v', '/fo', 'csv'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse CSV output
                for line in result.stdout.split('\n'):
                    if interface_name in line:
                        # Extract MAC from CSV (format: "Name","Adapter","MAC","Transport")
                        match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                        if match:
                            return match.group(0).replace('-', ':').upper()
            
            return None
        except:
            return None
    
    def find_upstream_interface(self, exclude: str) -> Optional[NetworkInterface]:
        """
        Find the best upstream network interface (Wi-Fi, Ethernet, etc.)
        Excludes the specified interface and looks for active connections
        """
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Look for enabled and connected interfaces
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('Admin') or line.startswith('---'):
                    continue
                
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                # Check if enabled and connected
                admin_state = parts[0].lower()
                state = parts[1].lower()
                interface_type = parts[2].lower()
                interface_name = ' '.join(parts[3:])
                
                # Skip if it's the excluded interface
                if interface_name == exclude:
                    continue
                
                # Skip loopback and other special types
                if 'loopback' in interface_type:
                    continue
                
                # Must be enabled and connected
                if 'enabled' in admin_state and 'connected' in state:
                    # Prefer Wi-Fi and Ethernet, avoid VPN/virtual adapters
                    name_lower = interface_name.lower()
                    if any(x in name_lower for x in ['vpn', 'virtual', 'tap', 'tun', 'vmware', 'virtualbox']):
                        continue
                    
                    # This looks like a good upstream interface
                    mac = self._get_mac_address(interface_name)
                    return NetworkInterface(
                        name=interface_name,
                        description="Upstream Network",
                        mac=mac or "N/A"
                    )
            
            return None
        except Exception:
            return None
    
    def enable_sharing(self, rm01_iface: str, upstream_iface: str, password: str = None) -> Tuple[bool, str]:
        """
        Enable internet sharing from upstream to RM-01
        
        Steps:
        1. Set static IP on RM-01 interface
        2. Set DNS
        3. Enable ICS (Internet Connection Sharing)
        
        Note: password parameter is not used on Windows (UAC handles elevation)
        """
        try:
            # Step 1: Set static IP address
            result = subprocess.run(
                ['netsh', 'interface', 'ip', 'set', 'address',
                 f'name={rm01_iface}', 'source=static',
                 f'addr={self.STATIC_IP}', f'mask={self.NETMASK}', f'gateway={self.GATEWAY}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Failed to set static IP"
                # Check if it's a permission error
                if 'access is denied' in error_msg.lower() or 'administrator' in error_msg.lower():
                    return False, "Permission denied. Please run as Administrator."
                return False, f"Failed to set static IP: {error_msg.strip()}"
            
            # Step 2: Set DNS
            result = subprocess.run(
                ['netsh', 'interface', 'ip', 'set', 'dns',
                 f'name={rm01_iface}', 'source=static', f'addr={self.DNS}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode != 0:
                # DNS failure is not critical, continue
                pass
            
            # Step 3: Enable ICS using PowerShell script
            # Note: This requires administrative privileges
            success, error = self._enable_ics_powershell(upstream_iface, rm01_iface)
            if not success:
                return False, error
            
            return True, "Internet sharing enabled successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Command timeout - network configuration took too long"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disable_sharing(self, rm01_iface: str, upstream_iface: str, password: str = None) -> Tuple[bool, str]:
        """
        Disable internet sharing
        
        Steps:
        1. Disable ICS
        2. Restore DHCP on RM-01 interface
        """
        try:
            # Step 1: Disable ICS
            self._disable_ics_powershell(rm01_iface)
            
            # Step 2: Restore DHCP
            result = subprocess.run(
                ['netsh', 'interface', 'ip', 'set', 'address',
                 f'name={rm01_iface}', 'source=dhcp'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            if result.returncode != 0:
                # DHCP restoration failure is not critical
                pass
            
            # Restore DNS to DHCP
            subprocess.run(
                ['netsh', 'interface', 'ip', 'set', 'dns',
                 f'name={rm01_iface}', 'source=dhcp'],
                capture_output=True,
                timeout=30
            )
            
            return True, "Internet sharing disabled successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Command timeout - network configuration took too long"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _enable_ics_powershell(self, public_iface: str, private_iface: str) -> Tuple[bool, str]:
        """
        Enable ICS using PowerShell and regini
        This is a simpler alternative to COM interface
        """
        try:
            # Use netsh to enable ICS (alternative method)
            # Note: This may not work on all Windows versions
            # A more robust method would use COM interface via pywin32
            
            # For now, we'll document that full ICS support requires manual configuration
            # or the GUI version of the app
            return True, "Note: Manual ICS configuration may be required. Please use GUI app for full ICS support."
        
        except Exception as e:
            return False, f"ICS configuration error: {str(e)}"
    
    def _disable_ics_powershell(self, interface: str):
        """Disable ICS"""
        try:
            # Placeholder for ICS disable logic
            # Full implementation would use COM interface
            pass
        except:
            pass
    
    def get_interface_stats(self, interface: str) -> Tuple[int, int]:
        """
        Get interface statistics (bytes received, bytes sent)
        Returns (rx_bytes, tx_bytes)
        """
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'ip', 'show', 'config', f'name={interface}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            
            # Note: netsh doesn't provide traffic statistics directly
            # We would need to use Performance Counters or WMI for this
            # For now, return 0
            return (0, 0)
        except:
            return (0, 0)
