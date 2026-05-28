"""
Windows Network Service Implementation
Uses PowerShell Windows NAT cmdlets and netsh for RM-01 network sharing.
"""

import json
import locale
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    description: str
    mac: str


class WindowsNetworkService:
    """
    Windows network service for managing RM-01 internet sharing.

    Adapter discovery and sharing status use structured PowerShell output so the
    CLI does not depend on localized netsh table text.
    """

    STATIC_IP = "10.10.99.100"
    NETMASK = "255.255.255.0"
    DNS = "8.8.8.8"
    NAT_NAME = "RM01InternetConnector"
    PRIVATE_PREFIX = "10.10.99.0/24"

    KNOWN_IDENTIFIERS = ("ax88179",)

    def __init__(self):
        self.last_error: Optional[str] = None
        self.address_configured_by_app = False

    def detect_adapter(self) -> Optional[NetworkInterface]:
        """Detect AX88179A USB Ethernet adapter."""
        self._clear_last_error()
        script = """
$adapter = $null
if (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue) {
    $adapter = Get-NetAdapter -ErrorAction SilentlyContinue |
        Where-Object {
            $_.InterfaceDescription -match '(?i)ax88179' -or
            $_.Name -match '(?i)ax88179'
        } |
        Sort-Object @{ Expression = { if ($_.Status -eq 'Up') { 0 } else { 1 } } }, Name |
        Select-Object -First 1
}

if ($null -ne $adapter) {
    [pscustomobject]@{
        Name = $adapter.Name
        Description = $adapter.InterfaceDescription
        MacAddress = $adapter.MacAddress
    } | ConvertTo-Json -Compress
    return
}

$cimAdapter = Get-CimInstance Win32_NetworkAdapter -ErrorAction SilentlyContinue |
    Where-Object {
        $_.NetConnectionID -and (
            $_.Name -match '(?i)ax88179' -or
            $_.Description -match '(?i)ax88179' -or
            $_.PNPDeviceID -match '(?i)ax88179'
        )
    } |
    Select-Object -First 1

if ($null -ne $cimAdapter) {
    [pscustomobject]@{
        Name = $cimAdapter.NetConnectionID
        Description = $cimAdapter.Description
        MacAddress = $cimAdapter.MACAddress
    } | ConvertTo-Json -Compress
}
"""
        payload = self._run_powershell_json(script, timeout=15)
        return self._interface_from_payload(payload, "AX88179A USB Ethernet Adapter")

    def find_upstream_interface(self, exclude: str) -> Optional[NetworkInterface]:
        """
        Find the best upstream network interface.

        Prefer the interface that owns the IPv4 default route, then fall back to
        an active physical adapter with a non-link-local IPv4 address.
        """
        self._clear_last_error()
        exclude_ps = self._ps_quote(exclude)
        script = f"""
$exclude = {exclude_ps}

function Test-UsableAdapter($adapter) {{
    if ($null -eq $adapter) {{ return $false }}
    if ($adapter.Name -ieq $exclude) {{ return $false }}
    if ($adapter.Status -ne 'Up') {{ return $false }}

    $text = (($adapter.Name, $adapter.InterfaceDescription) -join ' ')
    if ($text -match '(?i)vpn|virtual|tap|tun|vmware|virtualbox|loopback|hyper-v') {{
        return $false
    }}

    $ipv4 = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {{ $_.IPAddress -notlike '169.254.*' }} |
        Select-Object -First 1
    return $null -ne $ipv4
}}

$candidate = $null
if ((Get-Command Get-NetRoute -ErrorAction SilentlyContinue) -and
    (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {{
    $routes = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
        Where-Object {{ $_.NextHop -and $_.NextHop -ne '0.0.0.0' }} |
        Sort-Object RouteMetric, InterfaceMetric

    foreach ($route in $routes) {{
        $adapter = Get-NetAdapter -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue
        if (Test-UsableAdapter $adapter) {{
            $candidate = $adapter
            break
        }}
    }}
}}

if ($null -eq $candidate -and (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {{
    foreach ($adapter in (Get-NetAdapter -ErrorAction SilentlyContinue |
        Sort-Object @{{
            Expression = {{
                if ($_.InterfaceDescription -match '(?i)wi-?fi|wireless|802\\.11') {{ 0 }}
                elseif ($_.InterfaceDescription -match '(?i)ethernet|gigabit') {{ 1 }}
                else {{ 2 }}
            }}
        }}, Name)) {{
        if (Test-UsableAdapter $adapter) {{
            $candidate = $adapter
            break
        }}
    }}
}}

if ($null -ne $candidate) {{
    [pscustomobject]@{{
        Name = $candidate.Name
        Description = $candidate.InterfaceDescription
        MacAddress = $candidate.MacAddress
    }} | ConvertTo-Json -Compress
}}
"""
        payload = self._run_powershell_json(script, timeout=15)
        return self._interface_from_payload(payload, "Upstream Network")

    def enable_sharing(self, rm01_iface: str, upstream_iface: str, password: str = None) -> Tuple[bool, str]:
        """
        Enable internet sharing from upstream to RM-01.

        The password parameter is ignored on Windows. The process must already
        be elevated by UAC.
        """
        self._clear_last_error()
        self.address_configured_by_app = False
        try:
            success, error = self._assert_nat_available()
            if not success:
                return False, error

            success, error = self._disable_nat(rm01_iface, upstream_iface)
            if not success:
                return False, error

            address_changed = False
            if not self._has_target_address(rm01_iface):
                address_changed = True
                result = self._run_netsh(
                    [
                        "interface", "ip", "set", "address",
                        f"name={rm01_iface}", "source=static",
                        f"addr={self.STATIC_IP}", f"mask={self.NETMASK}", "gateway=none",
                    ],
                    timeout=30,
                )

                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Failed to set static IP"
                    if self._looks_like_permission_error(error_msg):
                        return False, "Permission denied. Please run as Administrator."
                    return False, f"Failed to set static IP: {error_msg.strip()}"

                result = self._run_netsh(
                    [
                        "interface", "ip", "set", "dns",
                        f"name={rm01_iface}", "source=static", f"addr={self.DNS}",
                    ],
                    timeout=30,
                )
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Failed to set DNS"
                    rollback_error = self._restore_dhcp(rm01_iface)
                    if rollback_error:
                        return False, f"Failed to set DNS: {error_msg.strip()}. Also failed to restore DHCP: {rollback_error}"
                    return False, f"Failed to set DNS: {error_msg.strip()}"

            success, error = self._enable_nat(upstream_iface, rm01_iface)
            if not success:
                cleanup_success, cleanup_error = self._disable_nat(rm01_iface, upstream_iface)
                rollback_error = self._restore_dhcp(rm01_iface) if address_changed else None
                if not cleanup_success and rollback_error:
                    return False, f"{error}. Also failed to clean NAT: {cleanup_error}. Also failed to restore DHCP: {rollback_error}"
                if not cleanup_success:
                    return False, f"{error}. Also failed to clean NAT: {cleanup_error}"
                if rollback_error:
                    return False, f"{error}. Also failed to restore DHCP: {rollback_error}"
                return False, error

            self.address_configured_by_app = address_changed
            return True, "Internet sharing enabled successfully"

        except subprocess.TimeoutExpired:
            return False, "Command timeout - network configuration took too long"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def disable_sharing(
        self,
        rm01_iface: str,
        upstream_iface: str = None,
        password: str = None,
        restore_dhcp: bool = False,
    ) -> Tuple[bool, str]:
        """Disable internet sharing and restore DHCP on the RM-01 interface."""
        self._clear_last_error()
        try:
            success, error = self._disable_nat(rm01_iface, upstream_iface)
            if not success:
                return False, error

            if restore_dhcp:
                restore_error = self._restore_dhcp(rm01_iface)
                if restore_error:
                    return False, restore_error

            return True, "Internet sharing disabled successfully"

        except subprocess.TimeoutExpired:
            return False, "Command timeout - network configuration took too long"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _restore_dhcp(self, rm01_iface: str) -> Optional[str]:
        """Restore DHCP/DNS on the RM-01 interface."""
        result = self._run_netsh(
            ["interface", "ip", "set", "address", f"name={rm01_iface}", "source=dhcp"],
            timeout=30,
        )
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Failed to restore DHCP"
            if self._looks_like_permission_error(error_msg):
                return "Permission denied. Please run as Administrator."
            return f"Failed to restore DHCP: {error_msg.strip()}"

        result = self._run_netsh(
            ["interface", "ip", "set", "dns", f"name={rm01_iface}", "source=dhcp"],
            timeout=30,
        )
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Failed to restore DNS"
            return f"Failed to restore DNS: {error_msg.strip()}"

        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=15)
        return None

    def is_admin(self) -> bool:
        """Return whether the current process is elevated."""
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    def _has_target_address(self, private_iface: str) -> bool:
        private_ps = self._ps_quote(private_iface)
        static_ip_ps = self._ps_quote(self.STATIC_IP)
        script = f"""
$privateName = {private_ps}
$staticIp = {static_ip_ps}
$ip = Get-NetIPAddress -InterfaceAlias $privateName -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {{ $_.IPAddress -eq $staticIp -and [int]$_.PrefixLength -eq 24 }} |
    Select-Object -First 1

[pscustomobject]@{{
    HasTargetAddress = ($null -ne $ip)
}} | ConvertTo-Json -Compress
"""
        payload = self._run_powershell_json(script, timeout=10)
        if isinstance(payload, dict):
            return bool(payload.get("HasTargetAddress"))
        return False

    def is_sharing_enabled(self, private_iface: str, public_iface: str = None) -> bool:
        """Check whether Windows NAT sharing is enabled for the RM-01 interface."""
        self._clear_last_error()
        private_ps = self._ps_quote(private_iface)
        nat_name_ps = self._ps_quote(self.NAT_NAME)
        static_ip_ps = self._ps_quote(self.STATIC_IP)
        script = f"""
$privateName = {private_ps}
$natName = {nat_name_ps}
$staticIp = {static_ip_ps}

if (-not (Get-Command Get-NetNat -ErrorAction SilentlyContinue) -or
    -not (Get-Command Get-NetIPAddress -ErrorAction SilentlyContinue)) {{
    [pscustomobject]@{{ SharingEnabled = $false }} | ConvertTo-Json -Compress
    return
}}

$nat = Get-NetNat -Name $natName -ErrorAction SilentlyContinue
$ip = Get-NetIPAddress -InterfaceAlias $privateName -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {{ $_.IPAddress -eq $staticIp }} |
    Select-Object -First 1
$forwarding = $null
if (Get-Command Get-NetIPInterface -ErrorAction SilentlyContinue) {{
    $forwarding = Get-NetIPInterface -InterfaceAlias $privateName -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Select-Object -First 1
}}
$forwardingEnabled = ($null -ne $forwarding -and [string]$forwarding.Forwarding -eq 'Enabled')

[pscustomobject]@{{
    SharingEnabled = ($null -ne $nat -and $null -ne $ip -and $forwardingEnabled)
}} | ConvertTo-Json -Compress
"""
        payload = self._run_powershell_json(script, timeout=15)
        if isinstance(payload, dict):
            return bool(payload.get("SharingEnabled"))
        return False

    def get_interface_ip(self, interface: str) -> Optional[str]:
        """Get the primary IPv4 address of an interface."""
        interface_ps = self._ps_quote(interface)
        script = f"""
$name = {interface_ps}
if (Get-Command Get-NetIPAddress -ErrorAction SilentlyContinue) {{
    $ip = Get-NetIPAddress -InterfaceAlias $name -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {{ $_.IPAddress -notlike '169.254.*' }} |
        Select-Object -First 1 -ExpandProperty IPAddress
    if ($ip) {{ $ip }}
}}
"""
        result = self._run_powershell(script, timeout=10)
        if result.returncode != 0:
            return None
        value = result.stdout.strip().splitlines()
        return value[0].strip() if value else None

    def get_interface_stats(self, interface: str) -> Tuple[int, int]:
        """
        Get interface statistics (bytes received, bytes sent).
        Returns (rx_bytes, tx_bytes).
        """
        interface_ps = self._ps_quote(interface)
        script = f"""
$name = {interface_ps}
if (Get-Command Get-NetAdapterStatistics -ErrorAction SilentlyContinue) {{
    $stats = Get-NetAdapterStatistics -Name $name -ErrorAction SilentlyContinue
    if ($stats) {{
        [pscustomobject]@{{
            ReceivedBytes = $stats.ReceivedBytes
            SentBytes = $stats.SentBytes
        }} | ConvertTo-Json -Compress
    }}
}}
"""
        payload = self._run_powershell_json(script, timeout=10)
        if isinstance(payload, dict):
            return (
                self._safe_int(payload.get("ReceivedBytes")),
                self._safe_int(payload.get("SentBytes")),
            )
        return (0, 0)

    def _enable_nat(self, public_iface: str, private_iface: str) -> Tuple[bool, str]:
        public_ps = self._ps_quote(public_iface)
        private_ps = self._ps_quote(private_iface)
        nat_name_ps = self._ps_quote(self.NAT_NAME)
        prefix_ps = self._ps_quote(self.PRIVATE_PREFIX)
        script = self._nat_common_script() + f"""
$publicName = {public_ps}
$privateName = {private_ps}
$natName = {nat_name_ps}
$prefix = {prefix_ps}

Assert-NatCommands
Assert-NatProvider

$publicAdapter = Get-NetAdapter -Name $publicName -ErrorAction SilentlyContinue
$privateAdapter = Get-NetAdapter -Name $privateName -ErrorAction SilentlyContinue
if ($null -eq $publicAdapter) {{ throw "Upstream interface not found: $publicName" }}
if ($null -eq $privateAdapter) {{ throw "RM-01 interface not found: $privateName" }}

Get-NetNat -Name $natName -ErrorAction SilentlyContinue | Remove-NetNat -Confirm:$false
Get-NetNat -ErrorAction SilentlyContinue |
    Where-Object {{ $_.InternalIPInterfaceAddressPrefix -eq $prefix -and $_.Name -ne $natName }} |
    Remove-NetNat -Confirm:$false

Set-NetIPInterface -InterfaceAlias $privateName -AddressFamily IPv4 -Forwarding Enabled
Set-NetIPInterface -InterfaceAlias $publicName -AddressFamily IPv4 -Forwarding Enabled
New-NetNat -Name $natName -InternalIPInterfaceAddressPrefix $prefix | Out-Null

"OK"
"""
        result = self._run_powershell(script, timeout=30)
        if result.returncode != 0:
            return False, self._powershell_error(result, "Failed to enable Windows NAT")
        return True, "Windows NAT enabled"

    def _assert_nat_available(self) -> Tuple[bool, str]:
        script = self._nat_common_script() + """
Assert-NatCommands
Assert-NatProvider
"OK"
"""
        result = self._run_powershell(script, timeout=10)
        if result.returncode != 0:
            return False, self._powershell_error(result, "Windows NAT provider is not available")
        return True, "Windows NAT provider available"

    def _disable_nat(self, private_iface: str, public_iface: str = None) -> Tuple[bool, str]:
        private_ps = self._ps_quote(private_iface)
        public_ps = self._ps_quote(public_iface or "")
        nat_name_ps = self._ps_quote(self.NAT_NAME)
        prefix_ps = self._ps_quote(self.PRIVATE_PREFIX)
        script = self._nat_common_script() + self._legacy_ics_common_script() + f"""
$privateName = {private_ps}
$publicName = {public_ps}
$natName = {nat_name_ps}
$prefix = {prefix_ps}

if (Get-Command Get-NetNat -ErrorAction SilentlyContinue) {{
    Get-NetNat -Name $natName -ErrorAction SilentlyContinue | Remove-NetNat -Confirm:$false
    Get-NetNat -ErrorAction SilentlyContinue |
        Where-Object {{ $_.InternalIPInterfaceAddressPrefix -eq $prefix -and $_.Name -ne $natName }} |
        Remove-NetNat -Confirm:$false
}}

if ((Get-Command Set-NetIPInterface -ErrorAction SilentlyContinue) -and
    (Get-Command Get-NetAdapter -ErrorAction SilentlyContinue)) {{
    foreach ($name in @($privateName, $publicName)) {{
        if ([string]::IsNullOrWhiteSpace($name)) {{ continue }}
        $adapter = Get-NetAdapter -Name $name -ErrorAction SilentlyContinue
        if ($null -ne $adapter) {{
            Set-NetIPInterface -InterfaceAlias $name -AddressFamily IPv4 -Forwarding Disabled -ErrorAction SilentlyContinue
        }}
    }}
}}

Disable-LegacyIcsSharing $privateName $publicName

"OK"
"""
        result = self._run_powershell(script, timeout=30)
        if result.returncode != 0:
            return False, self._powershell_error(result, "Failed to disable Windows NAT")
        return True, "Windows NAT disabled"

    def _run_netsh(self, args, timeout: int) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["netsh", *args],
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False) or "utf-8",
            errors="replace",
            timeout=timeout,
        )

    def _run_powershell(self, script: str, timeout: int) -> subprocess.CompletedProcess:
        wrapped = (
            "$ErrorActionPreference = 'Stop'; "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            + script
        )
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                wrapped,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def _run_powershell_json(self, script: str, timeout: int):
        try:
            result = self._run_powershell(script, timeout=timeout)
        except Exception as e:
            self._set_last_error(f"PowerShell execution failed: {e}")
            return None

        if result.returncode != 0:
            self._powershell_error(result, "PowerShell command failed")
            return None

        output = result.stdout.strip()
        if not output:
            return None

        try:
            payload = json.loads(output)
        except json.JSONDecodeError as e:
            self._set_last_error(f"PowerShell returned invalid JSON: {e}")
            return None

        if isinstance(payload, list):
            return payload[0] if payload else None
        return payload

    def _interface_from_payload(self, payload, fallback_description: str) -> Optional[NetworkInterface]:
        if not isinstance(payload, dict):
            return None

        name = str(payload.get("Name") or "").strip()
        if not name:
            return None

        description = str(payload.get("Description") or fallback_description).strip()
        mac = self._normalize_mac(str(payload.get("MacAddress") or ""))
        return NetworkInterface(name=name, description=description, mac=mac or "N/A")

    def _nat_common_script(self) -> str:
        return """
function Assert-NatCommands {
    foreach ($command in @('Get-NetNat', 'New-NetNat', 'Remove-NetNat', 'Set-NetIPInterface', 'Get-NetAdapter')) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
            throw "Windows NAT command is not available: $command"
        }
    }
}

function Assert-NatProvider {
    try {
        Get-CimClass -Namespace root/StandardCimv2 -ClassName MSFT_NetNat -ErrorAction Stop | Out-Null
    } catch {
        throw "Windows NAT provider is not available: MSFT_NetNat cannot be loaded. $($_.Exception.Message)"
    }
}
"""

    def _legacy_ics_common_script(self) -> str:
        return """
function Get-ConnectionByName($manager, [string]$name) {
    foreach ($conn in @($manager.EnumEveryConnection)) {
        $props = $manager.NetConnectionProps($conn)
        if ($props.Name -ieq $name) {
            return $conn
        }
    }
    return $null
}

function Get-SharingConfig($manager, $connection) {
    try {
        return $manager.INetSharingConfigurationForINetConnection($connection)
    } catch {
        return $manager.NetSharingConfigurationForINetConnection($connection)
    }
}

function Disable-LegacyIcsSharing([string]$privateName, [string]$publicName) {
    try {
        $manager = New-Object -ComObject HNetCfg.HNetShare
    } catch {
        return
    }
    if (-not $manager.SharingInstalled) {
        return
    }

    $disabledPrivate = $false
    $privateConn = Get-ConnectionByName $manager $privateName
    if ($null -ne $privateConn) {
        $privateCfg = Get-SharingConfig $manager $privateConn
        if ($privateCfg.SharingEnabled) {
            $privateCfg.DisableSharing()
            $disabledPrivate = $true
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($publicName)) {
        $publicConn = Get-ConnectionByName $manager $publicName
        if ($null -ne $publicConn) {
            $publicCfg = Get-SharingConfig $manager $publicConn
            if ($publicCfg.SharingEnabled) {
                $publicCfg.DisableSharing()
            }
        }
    } elseif ($disabledPrivate) {
        foreach ($conn in @($manager.EnumEveryConnection)) {
            $cfg = Get-SharingConfig $manager $conn
            if ($cfg.SharingEnabled -and ([int]$cfg.SharingConnectionType -eq 0)) {
                $cfg.DisableSharing()
            }
        }
    }
}
"""

    def _powershell_error(self, result: subprocess.CompletedProcess, fallback: str) -> str:
        message = (result.stderr or result.stdout or fallback).strip()
        if self._looks_like_permission_error(message):
            message = "Permission denied. Please run as Administrator."
        message = message or fallback
        self._set_last_error(message)
        return message

    def _clear_last_error(self):
        self.last_error = None

    def _set_last_error(self, message: str):
        self.last_error = message.strip() if message else None

    def _looks_like_permission_error(self, message: str) -> bool:
        lower = message.lower()
        return (
            "access is denied" in lower
            or "administrator" in lower
            or "elevated" in lower
            or "permission" in lower
            or "权限" in message
            or "拒绝访问" in message
        )

    def _normalize_mac(self, value: str) -> Optional[str]:
        match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", value)
        if not match:
            return None
        return match.group(0).replace("-", ":").upper()

    def _safe_int(self, value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _ps_quote(self, value: str) -> str:
        return "'" + str(value).replace("'", "''") + "'"
