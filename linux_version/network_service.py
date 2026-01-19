"""
Network service for RM-01 Internet Connector on Linux
Handles adapter detection, IP configuration, and NAT setup
"""

import os
import subprocess
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple
from pathlib import Path


@dataclass
class NetworkInterface:
    """Represents a network interface"""
    name: str           # e.g., "enxc8a3627e8d4d"
    mac: str            # e.g., "c8:a3:62:7e:8d:4d"
    description: str    # e.g., "AX88179 Gigabit Ethernet"


class NetworkService:
    """
    Linux network service for RM-01 Internet Connector
    
    RM-01 contains an AX88179A switch chip that:
    - Assigns IP 10.10.99.100 to connected computer via DHCP
    - Expects the computer (10.10.99.100) to be its gateway
    
    This service enables internet sharing by:
    1. Detecting the AX88179A adapter
    2. Configuring static IP (10.10.99.100) for stability
    3. Enabling IP forwarding
    4. Setting up NAT via iptables
    """
    
    # AX88179 USB identifiers
    VENDOR_ID = "0b95"
    PRODUCT_IDS = ["1790", "178a"]  # AX88179 variants
    
    # Network configuration
    STATIC_IP = "10.10.99.100"
    NETMASK = "24"
    NETWORK = "10.10.99.0/24"
    DNS = "8.8.8.8"
    
    def __init__(self):
        self._cached_password: Optional[str] = None
    
    def detect_adapter(self) -> Optional[NetworkInterface]:
        """
        Detect AX88179A USB Ethernet adapter
        Returns the first matching interface or None
        """
        interfaces = self._detect_all_adapters()
        return interfaces[0] if interfaces else None
    
    def _detect_all_adapters(self) -> List[NetworkInterface]:
        """Detect all AX88179A adapters"""
        interfaces = []
        net_path = Path("/sys/class/net")
        
        if not net_path.exists():
            return interfaces
        
        for iface_path in net_path.iterdir():
            iface_name = iface_path.name
            
            # Skip loopback and virtual interfaces
            if iface_name.startswith(('lo', 'docker', 'br-', 'veth', 'virbr')):
                continue
            
            # Check if this is a USB device
            device_path = iface_path / "device"
            if not device_path.exists():
                continue
            
            # Try to read USB vendor/product from uevent
            uevent_path = device_path / "uevent"
            if uevent_path.exists():
                try:
                    uevent_content = uevent_path.read_text()
                    # Look for USB product string
                    if self._is_ax88179_uevent(uevent_content):
                        mac = self._get_mac_address(iface_name)
                        interfaces.append(NetworkInterface(
                            name=iface_name,
                            mac=mac,
                            description="AX88179 Gigabit Ethernet"
                        ))
                        continue
                except (PermissionError, IOError):
                    pass
            
            # Alternative: check via lsusb mapping
            # Interface names starting with 'enx' are based on MAC address
            # which we can correlate with USB devices
            # Only use this fallback if we haven't found any AX88179 adapter yet
            # and only for the first enx interface to avoid false positives
            if iface_name.startswith('enx') and not interfaces:
                if self._check_usb_device_with_mac(iface_name):
                    mac = self._get_mac_address(iface_name)
                    interfaces.append(NetworkInterface(
                        name=iface_name,
                        mac=mac,
                        description="AX88179 Gigabit Ethernet"
                    ))
        
        return interfaces
    
    def _is_ax88179_uevent(self, content: str) -> bool:
        """Check if uevent content indicates AX88179"""
        content_lower = content.lower()
        # Check for ASIX vendor ID
        if f"vendor={self.VENDOR_ID}" in content_lower:
            return True
        if "ax88179" in content_lower:
            return True
        return False
    
    def _check_usb_device_exists(self) -> bool:
        """Check if AX88179 USB device exists via lsusb"""
        try:
            result = subprocess.run(
                ['lsusb'],
                capture_output=True,
                text=True,
                timeout=5
            )
            output_lower = result.stdout.lower()
            # Check for ASIX vendor ID and AX88179 product
            return 'asix' in output_lower and ('ax88179' in output_lower or '0b95:1790' in output_lower)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_usb_device_with_mac(self, iface_name: str) -> bool:
        """
        Check if the interface is likely an AX88179 by correlating MAC address
        with USB device information. More accurate than just checking if USB device exists.
        """
        # First check if the USB device exists at all
        if not self._check_usb_device_exists():
            return False
        
        # Get MAC address from interface name (enx format is enx + MAC without colons)
        # e.g., enxc8a3627e8d4d -> c8:a3:62:7e:8d:4d
        if iface_name.startswith('enx') and len(iface_name) == 15:
            mac_from_name = ':'.join(iface_name[3:][i:i+2] for i in range(0, 12, 2))
            actual_mac = self._get_mac_address(iface_name)
            
            # Verify the MAC matches (as a sanity check)
            if actual_mac.lower() == mac_from_name.lower():
                return True
        
        # Fallback: if we can't verify MAC, but USB device exists, assume it's the one
        return True
    
    def _get_mac_address(self, interface: str) -> str:
        """Get MAC address of interface"""
        try:
            mac_path = Path(f"/sys/class/net/{interface}/address")
            if mac_path.exists():
                return mac_path.read_text().strip()
        except (PermissionError, IOError):
            pass
        return "N/A"
    
    def find_upstream_interface(self, exclude: str) -> Optional[NetworkInterface]:
        """
        Find the best upstream interface (with internet access)
        Excludes the RM-01 adapter and virtual interfaces
        """
        try:
            # Get default route to find the interface with internet access
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                # Parse: "default via 192.168.0.12 dev wlp2s0 proto dhcp metric 600"
                match = re.search(r'dev\s+(\S+)', line)
                if match:
                    iface_name = match.group(1)
                    # Skip the excluded interface (RM-01)
                    if iface_name == exclude:
                        continue
                    # Skip virtual interfaces
                    if iface_name.startswith(('lo', 'docker', 'br-', 'veth', 'virbr', 'tun', 'tap')):
                        continue
                    
                    mac = self._get_mac_address(iface_name)
                    return NetworkInterface(
                        name=iface_name,
                        mac=mac,
                        description="Upstream Network"
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def enable_sharing(self, rm01_interface: str, upstream_interface: str, password: str) -> Tuple[bool, str]:
        """
        Enable internet sharing from upstream to RM-01
        
        Args:
            rm01_interface: The AX88179A interface name (e.g., "enxc8a3627e8d4d")
            upstream_interface: The upstream interface name (e.g., "wlp2s0")
            password: sudo password
        
        Returns:
            Tuple of (success, error_message)
        """
        script = self._generate_enable_script(rm01_interface, upstream_interface)
        return self._run_privileged(script, password)
    
    def disable_sharing(self, rm01_interface: str, upstream_interface: str, password: str) -> Tuple[bool, str]:
        """
        Disable internet sharing and restore DHCP
        
        Args:
            rm01_interface: The AX88179A interface name
            upstream_interface: The upstream interface name
            password: sudo password
        
        Returns:
            Tuple of (success, error_message)
        """
        script = self._generate_disable_script(rm01_interface, upstream_interface)
        return self._run_privileged(script, password)
    
    def _generate_enable_script(self, rm01_iface: str, upstream_iface: str) -> str:
        """Generate the shell script to enable internet sharing"""
        return f'''#!/bin/bash
set -e

DEVICE="{rm01_iface}"
UPSTREAM="{upstream_iface}"
IP="{self.STATIC_IP}"
NETMASK="{self.NETMASK}"
NETWORK="{self.NETWORK}"

# Flush existing IP on the interface
ip addr flush dev "$DEVICE" 2>/dev/null || true

# Set static IP
ip addr add "$IP/$NETMASK" dev "$DEVICE" 2>/dev/null || true

# Bring interface up
ip link set "$DEVICE" up

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1 > /dev/null

# Clear existing NAT rules for this interface (to avoid duplicates)
iptables -t nat -D POSTROUTING -o "$UPSTREAM" -s "$NETWORK" -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i "$DEVICE" -o "$UPSTREAM" -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i "$UPSTREAM" -o "$DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true

# Add NAT rules
iptables -t nat -A POSTROUTING -o "$UPSTREAM" -s "$NETWORK" -j MASQUERADE
iptables -A FORWARD -i "$DEVICE" -o "$UPSTREAM" -j ACCEPT
iptables -A FORWARD -i "$UPSTREAM" -o "$DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "Internet sharing enabled: $DEVICE -> $UPSTREAM"
'''
    
    def _generate_disable_script(self, rm01_iface: str, upstream_iface: str) -> str:
        """Generate the shell script to disable internet sharing"""
        return f'''#!/bin/bash
set -e

DEVICE="{rm01_iface}"
UPSTREAM="{upstream_iface}"
NETWORK="{self.NETWORK}"

# Remove NAT rules
iptables -t nat -D POSTROUTING -o "$UPSTREAM" -s "$NETWORK" -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i "$DEVICE" -o "$UPSTREAM" -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i "$UPSTREAM" -o "$DEVICE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true

# Disable IP forwarding (optional - might affect other services)
# sysctl -w net.ipv4.ip_forward=0 > /dev/null

# Flush IP and restore DHCP
ip addr flush dev "$DEVICE" 2>/dev/null || true

# Bring interface down and up to trigger DHCP
ip link set "$DEVICE" down 2>/dev/null || true
sleep 1
ip link set "$DEVICE" up 2>/dev/null || true

# Request new DHCP lease if dhclient is available
if command -v dhclient &> /dev/null; then
    dhclient "$DEVICE" 2>/dev/null || true
elif command -v dhcpcd &> /dev/null; then
    dhcpcd "$DEVICE" 2>/dev/null || true
fi

echo "Internet sharing disabled for: $DEVICE"
'''
    
    def _run_privileged(self, script: str, password: str) -> Tuple[bool, str]:
        """
        Run a script with sudo privileges
        
        Args:
            script: Shell script content
            password: sudo password
        
        Returns:
            Tuple of (success, error_message)
        """
        import tempfile
        script_path = None
        
        try:
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            os.chmod(script_path, 0o700)
            
            # Run with sudo
            process = subprocess.Popen(
                ['sudo', '-S', 'bash', script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=password + '\n', timeout=30)
            
            if process.returncode == 0:
                return True, ""
            else:
                # Check for common errors
                error_msg = stderr.strip() or stdout.strip()
                if "incorrect password" in error_msg.lower() or "authentication failure" in error_msg.lower():
                    return False, "error_permission"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, "Operation timed out"
        except Exception as e:
            return False, str(e)
        finally:
            # Always clean up temporary file
            if script_path and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except:
                    pass
    
    def get_interface_stats(self, interface: str) -> Tuple[int, int]:
        """
        Get network interface statistics (bytes received/transmitted)
        
        Args:
            interface: Interface name
        
        Returns:
            Tuple of (rx_bytes, tx_bytes)
        """
        try:
            rx_path = Path(f"/sys/class/net/{interface}/statistics/rx_bytes")
            tx_path = Path(f"/sys/class/net/{interface}/statistics/tx_bytes")
            
            rx_bytes = int(rx_path.read_text().strip()) if rx_path.exists() else 0
            tx_bytes = int(tx_path.read_text().strip()) if tx_path.exists() else 0
            
            return rx_bytes, tx_bytes
        except (ValueError, IOError):
            return 0, 0


def request_password() -> Optional[str]:
    """
    Request password from user using zenity (GUI) or kdialog as fallback
    Returns password or None if cancelled
    """
    # Try zenity first (most common on GNOME-based systems)
    try:
        result = subprocess.run(
            [
                'zenity', '--password',
                '--title=RM-01 Internet Connector',
                '--text=需要管理员权限来配置网络\nAdministrator password required'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except FileNotFoundError:
        pass  # zenity not available, try alternatives
    except subprocess.TimeoutExpired:
        return None
    
    # Try kdialog (KDE systems)
    try:
        result = subprocess.run(
            [
                'kdialog', '--password',
                'RM-01 需要管理员权限 / Administrator password required'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except FileNotFoundError:
        pass  # kdialog not available
    except subprocess.TimeoutExpired:
        return None
    
    # No GUI password dialog available
    # Return None and let the caller handle it (e.g., show error message)
    return None


def check_password_dialog_available() -> bool:
    """Check if a GUI password dialog is available"""
    for cmd in ['zenity', 'kdialog']:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False
