"""
Application state management for RM-01 Internet Connector
"""

import time
from enum import Enum
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

import subprocess
from network_service import NetworkService, NetworkInterface, request_password


class ConnectionStatus(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class SpeedMonitor(QThread):
    """Background thread for monitoring network speed"""
    
    speed_updated = pyqtSignal(float, float)  # upload_speed, download_speed
    
    def __init__(self, network_service: NetworkService, interface: str):
        super().__init__()
        self.network_service = network_service
        self.interface = interface
        self._running = True
        self._last_rx = 0
        self._last_tx = 0
        self._last_time = 0
    
    def run(self):
        """Monitor loop"""
        # Initial sample
        self._last_rx, self._last_tx = self.network_service.get_interface_stats(self.interface)
        self._last_time = time.time()
        
        while self._running:
            time.sleep(1.0)  # Update every second
            
            if not self._running:
                break
            
            current_rx, current_tx = self.network_service.get_interface_stats(self.interface)
            current_time = time.time()
            
            time_diff = current_time - self._last_time
            if time_diff > 0:
                # Calculate bytes per second
                rx_diff = current_rx - self._last_rx if current_rx > self._last_rx else 0
                tx_diff = current_tx - self._last_tx if current_tx > self._last_tx else 0
                
                # From RM-01's perspective:
                # - RM-01 upload = computer's RX (data coming from RM-01)
                # - RM-01 download = computer's TX (data going to RM-01)
                upload_speed = rx_diff / time_diff    # RM-01 upload
                download_speed = tx_diff / time_diff  # RM-01 download
                
                self.speed_updated.emit(upload_speed, download_speed)
            
            self._last_rx = current_rx
            self._last_tx = current_tx
            self._last_time = current_time
    
    def stop(self):
        """Stop the monitor"""
        self._running = False


class AppState(QObject):
    """
    Application state with signals for UI updates
    """
    
    # Signals
    status_changed = pyqtSignal(ConnectionStatus)
    interface_changed = pyqtSignal(object)  # NetworkInterface or None
    status_key_changed = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)
    speed_changed = pyqtSignal(float, float)  # upload, download
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self._connection_status = ConnectionStatus.IDLE
        self._current_interface: Optional[NetworkInterface] = None
        self._upstream_interface: Optional[NetworkInterface] = None
        self._status_key = "status_idle"
        self._is_busy = False
        self._upload_speed = 0.0
        self._download_speed = 0.0
        self._cached_password: Optional[str] = None
        
        self.network_service = NetworkService()
        self._speed_monitor: Optional[SpeedMonitor] = None
    
    @property
    def connection_status(self) -> ConnectionStatus:
        return self._connection_status
    
    @connection_status.setter
    def connection_status(self, value: ConnectionStatus):
        if self._connection_status != value:
            self._connection_status = value
            self.status_changed.emit(value)
    
    @property
    def current_interface(self) -> Optional[NetworkInterface]:
        return self._current_interface
    
    @current_interface.setter
    def current_interface(self, value: Optional[NetworkInterface]):
        if self._current_interface != value:
            self._current_interface = value
            self.interface_changed.emit(value)
    
    @property
    def status_key(self) -> str:
        return self._status_key
    
    @status_key.setter
    def status_key(self, value: str):
        if self._status_key != value:
            self._status_key = value
            self.status_key_changed.emit(value)
    
    @property
    def is_busy(self) -> bool:
        return self._is_busy
    
    @is_busy.setter
    def is_busy(self, value: bool):
        if self._is_busy != value:
            self._is_busy = value
            self.busy_changed.emit(value)
    
    @property
    def is_connected(self) -> bool:
        return self._connection_status == ConnectionStatus.CONNECTED
    
    @property
    def upload_speed(self) -> float:
        return self._upload_speed
    
    @property
    def download_speed(self) -> float:
        return self._download_speed
    
    def refresh_interface(self):
        """Detect and update current interface, also check actual connection status"""
        interface = self.network_service.detect_adapter()
        self.current_interface = interface
        
        if interface:
            # Check actual network configuration
            is_configured = self._check_actual_connection(interface.name)
            is_forwarding = self._check_ip_forwarding()
            
            if is_configured and is_forwarding:
                # Already connected (maybe via CLI or previous session)
                self._connection_status = ConnectionStatus.CONNECTED
                self._status_key = "status_connected"
                
                # Find upstream for speed monitoring
                self._upstream_interface = self.network_service.find_upstream_interface(interface.name)
                
                # Start speed monitor
                self._start_speed_monitor()
                
                # Emit signals so UI updates
                self.status_changed.emit(self._connection_status)
                self.status_key_changed.emit(self._status_key)
            elif is_configured and not is_forwarding:
                # Partially configured
                self._connection_status = ConnectionStatus.FAILED
                self._status_key = "status_failed"
                self.status_changed.emit(self._connection_status)
                self.status_key_changed.emit(self._status_key)
    
    def _check_actual_connection(self, interface: str) -> bool:
        """
        Check if the interface is actually configured for sharing.
        
        Note: We cannot rely on IP address alone because RM-01's DHCP server
        will always assign 10.10.99.100 to this computer when connected.
        
        The real indicator of "sharing enabled" is NAT (MASQUERADE) rules in iptables.
        """
        # Check if there are NAT rules for this interface
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
                    return True
            except:
                continue
        
        return False
    
    def _check_ip_forwarding(self) -> bool:
        """Check if IP forwarding is enabled"""
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
                return f.read().strip() == '1'
        except:
            return False
    
    def _get_interface_ip(self, interface: str) -> str:
        """Get the IP address of an interface"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('inet '):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1].split('/')[0]
        except:
            pass
        return ""
    
    def connect(self):
        """Start connection process"""
        if self._is_busy:
            return
        
        self.is_busy = True
        self.connection_status = ConnectionStatus.CONNECTING
        self.status_key = "status_connecting"
        
        # Run connection in a separate method to allow UI updates
        QTimer.singleShot(100, self._perform_connect)
    
    def _perform_connect(self):
        """Perform the actual connection"""
        try:
            # Detect adapter
            interface = self.network_service.detect_adapter()
            if not interface:
                self.status_key = "interface_none"
                self.connection_status = ConnectionStatus.FAILED
                self.error_occurred.emit("error_no_interface")
                self.is_busy = False
                return
            
            self.current_interface = interface
            
            # Find upstream interface
            upstream = self.network_service.find_upstream_interface(interface.name)
            if not upstream:
                self.status_key = "status_failed"
                self.connection_status = ConnectionStatus.FAILED
                self.error_occurred.emit("error_no_upstream")
                self.is_busy = False
                return
            
            self._upstream_interface = upstream
            
            # Request password if not cached
            if not self._cached_password:
                password = request_password()
                if not password:
                    self.status_key = "status_idle"
                    self.connection_status = ConnectionStatus.IDLE
                    self.is_busy = False
                    return
                self._cached_password = password
            
            # Enable sharing
            success, error = self.network_service.enable_sharing(
                interface.name,
                upstream.name,
                self._cached_password
            )
            
            if success:
                self.status_key = "status_connected"
                self.connection_status = ConnectionStatus.CONNECTED
                self._start_speed_monitor()
            else:
                # Clear cached password on authentication failure
                if "permission" in error.lower() or "password" in error.lower():
                    self._cached_password = None
                self.status_key = "status_failed"
                self.connection_status = ConnectionStatus.FAILED
                self.error_occurred.emit(error)
        
        except Exception as e:
            self.status_key = "status_failed"
            self.connection_status = ConnectionStatus.FAILED
            self.error_occurred.emit(str(e))
        
        finally:
            self.is_busy = False
    
    def disconnect(self):
        """Start disconnection process"""
        if self._is_busy:
            return
        
        self.is_busy = True
        self.status_key = "status_disconnecting"
        self.connection_status = ConnectionStatus.CONNECTING  # Visual feedback
        
        QTimer.singleShot(100, self._perform_disconnect)
    
    def _perform_disconnect(self):
        """Perform the actual disconnection"""
        try:
            self._stop_speed_monitor()
            
            if not self._current_interface or not self._upstream_interface:
                self.status_key = "status_idle"
                self.connection_status = ConnectionStatus.IDLE
                self.is_busy = False
                return
            
            # Request password if not cached
            if not self._cached_password:
                password = request_password()
                if not password:
                    # Keep current status if cancelled
                    self.status_key = "status_connected"
                    self.connection_status = ConnectionStatus.CONNECTED
                    self.is_busy = False
                    return
                self._cached_password = password
            
            success, error = self.network_service.disable_sharing(
                self._current_interface.name,
                self._upstream_interface.name,
                self._cached_password
            )
            
            if success:
                self.status_key = "status_idle"
                self.connection_status = ConnectionStatus.IDLE
                self.current_interface = None
                self._upstream_interface = None
            else:
                if "permission" in error.lower() or "password" in error.lower():
                    self._cached_password = None
                self.status_key = "status_failed"
                self.connection_status = ConnectionStatus.FAILED
                self.error_occurred.emit(error)
        
        except Exception as e:
            self.status_key = "status_failed"
            self.connection_status = ConnectionStatus.FAILED
            self.error_occurred.emit(str(e))
        
        finally:
            self.is_busy = False
    
    def _start_speed_monitor(self):
        """Start network speed monitoring"""
        if self._current_interface and not self._speed_monitor:
            self._speed_monitor = SpeedMonitor(
                self.network_service,
                self._current_interface.name
            )
            self._speed_monitor.speed_updated.connect(self._on_speed_updated)
            self._speed_monitor.start()
    
    def _stop_speed_monitor(self):
        """Stop network speed monitoring"""
        if self._speed_monitor:
            self._speed_monitor.stop()
            self._speed_monitor.wait(2000)  # Wait up to 2 seconds
            try:
                self._speed_monitor.speed_updated.disconnect(self._on_speed_updated)
            except (TypeError, RuntimeError):
                # Signal was already disconnected or object deleted
                pass
            self._speed_monitor = None
        
        self._upload_speed = 0.0
        self._download_speed = 0.0
        self.speed_changed.emit(0.0, 0.0)
    
    def _on_speed_updated(self, upload: float, download: float):
        """Handle speed update from monitor"""
        self._upload_speed = upload
        self._download_speed = download
        self.speed_changed.emit(upload, download)
