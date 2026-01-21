"""
System tray icon for RM-01 Internet Connector
Provides quick access menu similar to macOS menu bar
"""

import os
from typing import Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from app_state import AppState, ConnectionStatus
from localization import loc, Language
from .widgets import get_asset_path


class TrayIcon(QObject):
    """
    System tray icon with context menu
    
    Note: Tray icons may not work on all Linux desktop environments.
    GNOME requires the AppIndicator extension.
    """
    
    # Signals
    open_panel_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._tray: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        
        self._setup_tray()
        
        # Only connect signals if tray was successfully created
        if self._tray is not None:
            self._connect_signals()
    
    def _setup_tray(self):
        """Initialize system tray icon"""
        try:
            # Allow disabling tray via environment variable
            if os.environ.get('RM01_NO_TRAY', '').lower() in ('1', 'true', 'yes'):
                print("System tray disabled via RM01_NO_TRAY environment variable")
                return
            
            # Check for Wayland - tray icons often don't work well
            session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
            if session_type == 'wayland':
                print("Note: Running on Wayland, system tray may not work")
            
            if not QSystemTrayIcon.isSystemTrayAvailable():
                print("System tray not available on this system")
                return
            
            # Create tray icon with parent to avoid segfault
            self._tray = QSystemTrayIcon(self)
            
            # Set icon
            icon_path = get_asset_path("statusIcon.png")
            if os.path.exists(icon_path):
                self._tray.setIcon(QIcon(icon_path))
            else:
                # Fallback to application icon
                icon_path = get_asset_path("icon.png")
                if os.path.exists(icon_path):
                    self._tray.setIcon(QIcon(icon_path))
            
            self._tray.setToolTip("RM-01 Internet Connector")
            
            # Create menu
            self._create_menu()
            
            # Connect tray activation
            self._tray.activated.connect(self._on_tray_activated)
            
            # Show tray icon
            self._tray.show()
        except Exception as e:
            print(f"Warning: Could not create system tray icon: {e}")
            self._tray = None
    
    def _create_menu(self):
        """Create the context menu"""
        self._menu = QMenu()
        
        # Speed display (hidden when not connected)
        self._speed_action = QAction("↑0B/s | ↓0B/s", self._menu)
        self._speed_action.setEnabled(False)
        self._speed_action.setVisible(False)
        self._menu.addAction(self._speed_action)
        
        # Separator after speed
        self._speed_separator = self._menu.addSeparator()
        self._speed_separator.setVisible(False)
        
        # Status display
        self._status_action = QAction(loc("menu_not_connected"), self._menu)
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)
        
        self._menu.addSeparator()
        
        # Connect/Disconnect
        self._connect_action = QAction(loc("menu_connect"), self._menu)
        self._connect_action.triggered.connect(self._on_connect_triggered)
        self._menu.addAction(self._connect_action)
        
        self._menu.addSeparator()
        
        # Open control panel
        self._open_action = QAction(loc("menu_open_panel"), self._menu)
        self._open_action.triggered.connect(self._on_open_triggered)
        self._menu.addAction(self._open_action)
        
        self._menu.addSeparator()
        
        # Quit
        self._quit_action = QAction(loc("menu_quit"), self._menu)
        self._quit_action.triggered.connect(self._on_quit_triggered)
        self._menu.addAction(self._quit_action)
        
        if self._tray:
            self._tray.setContextMenu(self._menu)
    
    def _connect_signals(self):
        """Connect to app state signals"""
        self.app_state.status_changed.connect(self._update_menu)
        self.app_state.speed_changed.connect(self._update_speed)
        loc.language_changed.connect(self._update_labels)
    
    def _update_menu(self, status: ConnectionStatus):
        """Update menu items based on connection status"""
        if status == ConnectionStatus.CONNECTED:
            self._status_action.setText(loc("menu_connected"))
            self._connect_action.setText(loc("menu_disconnect"))
            self._connect_action.setEnabled(True)
            self._speed_action.setVisible(True)
            self._speed_separator.setVisible(True)
        elif status == ConnectionStatus.CONNECTING:
            self._status_action.setText(loc("menu_connecting"))
            self._connect_action.setText(loc("menu_connecting"))
            self._connect_action.setEnabled(False)
            self._speed_action.setVisible(False)
            self._speed_separator.setVisible(False)
        elif status == ConnectionStatus.FAILED:
            self._status_action.setText(loc("menu_failed"))
            self._connect_action.setText(loc("menu_reconnect"))
            self._connect_action.setEnabled(True)
            self._speed_action.setVisible(False)
            self._speed_separator.setVisible(False)
        else:  # IDLE
            self._status_action.setText(loc("menu_not_connected"))
            self._connect_action.setText(loc("menu_connect"))
            self._connect_action.setEnabled(True)
            self._speed_action.setVisible(False)
            self._speed_separator.setVisible(False)
    
    def _update_speed(self, upload: float, download: float):
        """Update speed display in menu"""
        upload_str = self._format_speed(upload)
        download_str = self._format_speed(download)
        self._speed_action.setText(f"↑{upload_str}   |   ↓{download_str}")
    
    def _format_speed(self, bytes_per_second: float) -> str:
        """Format speed to human-readable string"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.0f}B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f}KB/s"
        elif bytes_per_second < 1024 * 1024 * 1024:
            return f"{bytes_per_second / 1024 / 1024:.1f}MB/s"
        else:
            return f"{bytes_per_second / 1024 / 1024 / 1024:.2f}GB/s"
    
    def _update_labels(self, language: Language):
        """Update all menu labels when language changes"""
        self._open_action.setText(loc("menu_open_panel"))
        self._quit_action.setText(loc("menu_quit"))
        self._update_menu(self.app_state.connection_status)
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - open panel
            self.open_panel_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - also open panel
            self.open_panel_requested.emit()
    
    def _on_connect_triggered(self):
        """Handle connect/disconnect menu action"""
        if self.app_state.is_connected:
            self.app_state.disconnect()
        else:
            self.app_state.connect()
    
    def _on_open_triggered(self):
        """Handle open panel menu action"""
        self.open_panel_requested.emit()
    
    def _on_quit_triggered(self):
        """Handle quit menu action"""
        self.quit_requested.emit()
    
    def is_available(self) -> bool:
        """Check if tray icon is available"""
        return self._tray is not None and self._tray.isVisible()
    
    def show_message(self, title: str, message: str, icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information):
        """Show a notification message"""
        if self._tray:
            self._tray.showMessage(title, message, icon, 3000)
    
    def hide(self):
        """Hide the tray icon"""
        if self._tray:
            self._tray.hide()
