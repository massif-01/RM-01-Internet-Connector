"""
Main window for RM-01 Internet Connector
Matches the macOS SwiftUI version's layout and design
"""

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

from app_state import AppState, ConnectionStatus
from localization import loc, Language
from .widgets import LiquidGlassButton, NetworkSpeedDisplay, RM01DeviceImage, get_asset_path


class MainWindow(QMainWindow):
    """
    Main application window
    Layout matches macOS version: 315x440 pixels
    """
    
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        
        # Initial state
        self.app_state.refresh_interface()
        self._update_ui()
    
    def _setup_window(self):
        """Configure window properties"""
        self.setWindowTitle(loc("window_title"))
        self.setFixedSize(315, 440)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )
        
        # Set window icon
        icon_path = get_asset_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Background color
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9FAFB;
            }
        """)
    
    def _setup_ui(self):
        """Build the user interface"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        layout.addWidget(self._create_header())
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: rgba(0,0,0,0.07); max-height: 1px;")
        layout.addWidget(divider)
        
        # Top spacer
        layout.addSpacing(10)
        
        # Status section
        layout.addWidget(self._create_status_section())
        
        # Gap
        layout.addSpacing(15)
        
        # Device image
        self.device_image = RM01DeviceImage()
        image_container = QWidget()
        image_layout = QHBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addStretch()
        image_layout.addWidget(self.device_image)
        image_layout.addStretch()
        layout.addWidget(image_container)
        
        # Gap
        layout.addSpacing(15)
        
        # Speed display
        self.speed_display = NetworkSpeedDisplay()
        self.speed_display.setVisible(False)
        speed_container = QWidget()
        speed_layout = QHBoxLayout(speed_container)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.addStretch()
        speed_layout.addWidget(self.speed_display)
        speed_layout.addStretch()
        layout.addWidget(speed_container)
        
        # Gap
        layout.addSpacing(10)
        
        # Connect button
        self.connect_button = LiquidGlassButton(loc("connect"))
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(30, 0, 30, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.connect_button)
        button_layout.addStretch()
        layout.addWidget(button_container)
        
        # Gap
        layout.addSpacing(12)
        
        # Footer
        layout.addWidget(self._create_footer())
    
    def _create_header(self) -> QWidget:
        """Create header with language toggle and title"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 16, 16, 12)
        
        # Language button
        self.lang_button = QPushButton(loc.language.value)
        self.lang_button.setFixedSize(36, 24)
        self.lang_button.setCursor(Qt.PointingHandCursor)
        self.lang_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(27, 186, 63, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                color: #1B1B1B;
            }
            QPushButton:hover {
                background-color: rgba(27, 186, 63, 0.2);
            }
        """)
        self.lang_button.clicked.connect(self._on_language_toggle)
        layout.addWidget(self.lang_button)
        
        layout.addStretch()
        
        # Icon and title
        icon_label = QLabel()
        icon_path = get_asset_path("icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, 
                                                Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🌐")
        layout.addWidget(icon_label)
        
        layout.addSpacing(8)
        
        self.title_label = QLabel(loc("window_title"))
        self.title_label.setFont(QFont("", 12, QFont.DemiBold))
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Invisible placeholder for balance
        placeholder = QWidget()
        placeholder.setFixedSize(36, 24)
        layout.addWidget(placeholder)
        
        return header
    
    def _create_status_section(self) -> QWidget:
        """Create status text section"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        # Status text
        self.status_label = QLabel(loc("status_idle"))
        self.status_label.setFont(QFont("", 16, QFont.Normal))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Device info
        self.device_label = QLabel(loc("hint_insert"))
        self.device_label.setFont(QFont("", 10))
        self.device_label.setStyleSheet("color: #666;")
        self.device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.device_label)
        
        section.setFixedHeight(45)
        return section
    
    def _create_footer(self) -> QWidget:
        """Create copyright footer"""
        footer = QWidget()
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 12)
        
        copyright_label = QLabel("Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.")
        copyright_label.setFont(QFont("", 8))
        copyright_label.setStyleSheet("color: rgba(0, 0, 0, 0.4);")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        return footer
    
    def _connect_signals(self):
        """Connect signals to slots"""
        # App state signals
        self.app_state.status_changed.connect(self._on_status_changed)
        self.app_state.interface_changed.connect(self._on_interface_changed)
        self.app_state.status_key_changed.connect(self._on_status_key_changed)
        self.app_state.busy_changed.connect(self._on_busy_changed)
        self.app_state.speed_changed.connect(self._on_speed_changed)
        self.app_state.error_occurred.connect(self._on_error_occurred)
        
        # Localization
        loc.language_changed.connect(self._on_language_changed)
        
        # Button
        self.connect_button.clicked.connect(self._on_connect_clicked)
    
    def _update_ui(self):
        """Update all UI elements based on current state"""
        status = self.app_state.connection_status
        
        # Update button
        if status == ConnectionStatus.CONNECTED:
            self.connect_button.set_button_text(loc("disconnect"))
            self.connect_button.is_destructive = True
        else:
            self.connect_button.set_button_text(loc("connect"))
            self.connect_button.is_destructive = False
        
        self.connect_button.setEnabled(not self.app_state.is_busy)
        
        # Update status
        self.status_label.setText(loc(self.app_state.status_key))
        
        # Update device info
        if self.app_state.current_interface:
            self.device_label.setText(f"🔌 {self.app_state.current_interface.name}")
        else:
            self.device_label.setText(loc("hint_insert"))
        
        # Update device image
        self.device_image.set_connected(status == ConnectionStatus.CONNECTED)
        
        # Update speed display visibility
        self.speed_display.setVisible(status == ConnectionStatus.CONNECTED)
    
    def _on_connect_clicked(self):
        """Handle connect/disconnect button click"""
        if self.app_state.is_connected:
            self.app_state.disconnect()
        else:
            self.app_state.connect()
    
    def _on_language_toggle(self):
        """Toggle language"""
        loc.toggle_language()
    
    def _on_status_changed(self, status: ConnectionStatus):
        """Handle status change"""
        self._update_ui()
    
    def _on_interface_changed(self, interface):
        """Handle interface change"""
        self._update_ui()
    
    def _on_status_key_changed(self, key: str):
        """Handle status key change"""
        self.status_label.setText(loc(key))
    
    def _on_busy_changed(self, busy: bool):
        """Handle busy state change"""
        self.connect_button.setEnabled(not busy)
    
    def _on_speed_changed(self, upload: float, download: float):
        """Handle speed update"""
        self.speed_display.update_speed(upload, download)
    
    def _on_language_changed(self, language: Language):
        """Handle language change"""
        self.setWindowTitle(loc("window_title"))
        self.title_label.setText(loc("window_title"))
        self.lang_button.setText(language.value)
        self._update_ui()
    
    def _on_error_occurred(self, error: str):
        """Handle error from app state"""
        # Translate common error keys
        error_messages = {
            "error_no_interface": loc("interface_none"),
            "error_no_upstream": loc("error_no_upstream") if hasattr(loc, "error_no_upstream") else "No internet connection found",
            "error_permission": loc("error_permission") if hasattr(loc, "error_permission") else "Permission denied",
        }
        
        display_error = error_messages.get(error, error)
        
        QMessageBox.warning(
            self,
            "RM-01 Internet Connector",
            display_error
        )
    
    def closeEvent(self, event):
        """Handle window close - minimize to tray if available"""
        # For now, just close normally
        # In the future, could hide to tray
        event.accept()
