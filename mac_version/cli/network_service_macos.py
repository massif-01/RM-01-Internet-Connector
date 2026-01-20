"""
macOS Network Service Implementation
Uses networksetup, pfctl, and sysctl for network sharing
"""

import subprocess
import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str           # Hardware Port name (e.g., "AX88179A 5")
    description: str    # Description
    mac: str           # MAC address
    device: str = ""   # Device name (e.g., "en16") - optional


class MacOSNetworkService:
    """
    macOS network service for managing RM-01 internet sharing
    Uses networksetup for configuration and pfctl for NAT
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
            # Use networksetup to list all hardware ports
            result = subprocess.run(
                ['/usr/sbin/networksetup', '-listallhardwareports'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output to find AX88179A
            lines = result.stdout.split('\n')
            current_port = None
            current_device = None
            current_mac = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Hardware Port:'):
                    # Save previous interface if it was AX88179A
                    if current_port and self._is_ax88179a(current_port) and current_device:
                        return NetworkInterface(
                            name=current_port,
                            description="AX88179A USB Ethernet Adapter",
                            mac=current_mac or "N/A",
                            device=current_device
                        )
                    
                    # Start new interface
                    current_port = line.replace('Hardware Port:', '').strip()
                    current_device = None
                    current_mac = None
                
                elif line.startswith('Device:'):
                    current_device = line.replace('Device:', '').strip()
                
                elif line.startswith('Ethernet Address:'):
                    current_mac = line.replace('Ethernet Address:', '').strip()
            
            # Check the last interface
            if current_port and self._is_ax88179a(current_port) and current_device:
                return NetworkInterface(
                    name=current_port,
                    description="AX88179A USB Ethernet Adapter",
                    mac=current_mac or "N/A",
                    device=current_device
                )
            
            return None
        
        except Exception as e:
            return None
    
    def _is_ax88179a(self, port_name: str) -> bool:
        """Check if hardware port name matches AX88179A identifiers"""
        lowercased = port_name.lower()
        return any(identifier in lowercased for identifier in self.KNOWN_IDENTIFIERS)
    
    def find_upstream_interface(self, exclude: str) -> Optional[NetworkInterface]:
        """
        Find the best upstream network interface (Wi-Fi, Ethernet, etc.)
        Excludes the specified interface name
        """
        try:
            # Get default route to find active internet interface
            result = subprocess.run(
                ['netstat', '-rn'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Find the default route (not through VPN or the RM-01 device)
            for line in result.stdout.split('\n'):
                if line.startswith('default'):
                    parts = line.split()
                    if len(parts) >= 6:
                        device = parts[5]  # Interface name (e.g., en0)
                        
                        # Skip if it's the excluded device
                        if device == exclude:
                            continue
                        
                        # Skip VPN interfaces
                        if device.startswith('utun') or device.startswith('ppp'):
                            continue
                        
                        # Get hardware port name for this device
                        port_name = self._get_hardware_port_for_device(device)
                        if port_name:
                            return NetworkInterface(
                                name=port_name,
                                description="Upstream Network",
                                mac="N/A",
                                device=device
                            )
            
            # Fallback: try to find Wi-Fi
            wi_fi_device = self._get_device_for_port("Wi-Fi")
            if wi_fi_device:
                return NetworkInterface(
                    name="Wi-Fi",
                    description="Wi-Fi",
                    mac="N/A",
                    device=wi_fi_device
                )
            
            return None
        
        except Exception:
            return None
    
    def _get_hardware_port_for_device(self, device: str) -> Optional[str]:
        """Get hardware port name for a device (e.g., en0 → Wi-Fi)"""
        try:
            result = subprocess.run(
                ['/usr/sbin/networksetup', '-listallhardwareports'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.split('\n')
            port_name = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Hardware Port:'):
                    port_name = line.replace('Hardware Port:', '').strip()
                elif line.startswith('Device:') and device in line:
                    return port_name
            
            return None
        
        except:
            return None
    
    def _get_device_for_port(self, port_name: str) -> Optional[str]:
        """Get device name for a hardware port (e.g., Wi-Fi → en0)"""
        try:
            result = subprocess.run(
                ['/usr/sbin/networksetup', '-listallhardwareports'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.split('\n')
            found_port = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('Hardware Port:') and port_name in line:
                    found_port = True
                elif found_port and line.startswith('Device:'):
                    device = line.replace('Device:', '').strip()
                    return device
            
            return None
        
        except:
            return None
    
    def enable_sharing(self, rm01_iface: str, upstream_iface: str, password: str = None) -> Tuple[bool, str]:
        """
        Enable internet sharing from upstream to RM-01
        Uses the exact same shell script as the GUI version (proven and tested)
        
        Note: Requires sudo privileges
        """
        try:
            # Get device name for RM-01 interface
            device = rm01_iface
            if not device.startswith('en'):
                dev = self._get_device_for_port(rm01_iface)
                if dev:
                    device = dev
                else:
                    return False, f"Could not find device for interface: {rm01_iface}"
            
            # Use the exact shell script from Mac GUI version
            # This is proven to work reliably
            script = f'''
IFACE="{rm01_iface}"
DEVICE="{device}"
IP="{self.STATIC_IP}"
MASK="{self.NETMASK}"
GW="{self.GATEWAY}"
DNS="{self.DNS}"
NAT_CONF="/tmp/rm01_nat.conf"

# Find the active internet interface (works with Wi-Fi, Ethernet, iPhone USB, etc.)
# Excludes VPN (utun) and link-local routes, finds the physical interface with a real gateway
INET_DEVICE=$(netstat -rn | grep "^default" | grep -v "utun" | grep -v "link#" | grep -v "$DEVICE" | head -1 | awk '{{print $NF}}')
if [ -z "$INET_DEVICE" ]; then
    # Fallback to Wi-Fi
    INET_DEVICE=$(/usr/sbin/networksetup -listallhardwareports | awk '/Wi-Fi/{{getline; print $2}}')
fi
if [ -z "$INET_DEVICE" ]; then
    # Last resort fallback
    INET_DEVICE="en0"
fi

# Check if network service exists, if not create it
if ! /usr/sbin/networksetup -listallnetworkservices | grep -q "^$IFACE$"; then
    /usr/sbin/networksetup -createnetworkservice "$IFACE" "$DEVICE"
fi

# Set static IP and DNS for the RM-01 interface
/usr/sbin/networksetup -setmanual "$IFACE" "$IP" "$MASK" "$GW"
/usr/sbin/networksetup -setdnsservers "$IFACE" "$DNS"

# Enable IP forwarding
/usr/sbin/sysctl -w net.inet.ip.forwarding=1

# Create NAT rule file (share internet connection to AX88179A)
echo "nat on $INET_DEVICE from $DEVICE:network to any -> ($INET_DEVICE)" > "$NAT_CONF"

# Load NAT rules using pfctl
/sbin/pfctl -d 2>/dev/null || true
/sbin/pfctl -F all 2>/dev/null || true
/sbin/pfctl -f "$NAT_CONF" -e 2>/dev/null

# Cleanup
rm -f "$NAT_CONF"
'''
            
            # Execute the script with sudo
            result = subprocess.run(
                ['sudo', 'bash', '-c', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return False, f"Failed to enable sharing: {error_msg.strip()}"
            
            return True, "Internet sharing enabled successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Command timeout - network configuration took too long"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disable_sharing(self, rm01_iface: str, upstream_iface: str, password: str = None) -> Tuple[bool, str]:
        """
        Disable internet sharing
        Uses the exact same shell script as the GUI version
        """
        try:
            # Get device name
            device = rm01_iface
            if not device.startswith('en'):
                dev = self._get_device_for_port(rm01_iface)
                if dev:
                    device = dev
                else:
                    return False, f"Could not find device for interface: {rm01_iface}"
            
            # Use the exact shell script from Mac GUI version
            script = f'''
IFACE="{rm01_iface}"
DEVICE="{device}"

# Disable IP forwarding
/usr/sbin/sysctl -w net.inet.ip.forwarding=0

# Flush NAT rules and disable pfctl
/sbin/pfctl -d 2>/dev/null || true
/sbin/pfctl -F all 2>/dev/null || true

# Restore DHCP for the interface
/usr/sbin/networksetup -setdhcp "$IFACE"

# Clear DNS settings (empty = use DHCP)
/usr/sbin/networksetup -setdnsservers "$IFACE" empty

# Refresh the interface to trigger DHCP request
/sbin/ifconfig "$DEVICE" down 2>/dev/null || true
sleep 1
/sbin/ifconfig "$DEVICE" up 2>/dev/null || true
'''
            
            # Execute the script with sudo
            result = subprocess.run(
                ['sudo', 'bash', '-c', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Disconnect doesn't fail even if some commands fail
            return True, "Internet sharing disabled successfully"
        
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_interface_stats(self, interface: str) -> Tuple[int, int]:
        """
        Get interface statistics (bytes received, bytes sent)
        Returns (rx_bytes, tx_bytes)
        """
        try:
            # Get device name if hardware port name was provided
            device = interface
            if not device.startswith('en'):
                dev = self._get_device_for_port(interface)
                if dev:
                    device = dev
                else:
                    return (0, 0)
            
            # Use netstat to get interface statistics
            result = subprocess.run(
                ['netstat', '-I', device, '-b'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return (0, 0)
            
            # Parse netstat output
            # Format: Name  Mtu   Network       Address            Ipkts Ierrs     Ibytes    Opkts Oerrs     Obytes
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return (0, 0)
            
            # Get the last line (summary)
            last_line = lines[-1]
            parts = last_line.split()
            
            if len(parts) >= 10:
                try:
                    rx_bytes = int(parts[6])  # Ibytes
                    tx_bytes = int(parts[9])  # Obytes
                    return (rx_bytes, tx_bytes)
                except (ValueError, IndexError):
                    return (0, 0)
            
            return (0, 0)
        
        except:
            return (0, 0)
