#!/usr/bin/env python3
"""
RM-01 Internet Connector - Linux Version
A tool to share your computer's internet connection with RM-01 devices

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.
"""

import sys
import os

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from app_state import AppState
from ui.main_window import MainWindow
from ui.tray_icon import TrayIcon
from ui.widgets import get_asset_path


def main():
    """Application entry point"""
    try:
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("RM-01 Internet Connector")
        app.setApplicationDisplayName("RM-01 Internet Connector")
        app.setOrganizationName("RMinte AI Technology")
        app.setOrganizationDomain("rminte.com")
        
        # Set application icon
        icon_path = get_asset_path("icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Set application style
        app.setStyle("Fusion")
        
        # Apply stylesheet for consistent look
        app.setStyleSheet("""
            QMainWindow {
                background-color: #F9FAFB;
            }
            QToolTip {
                background-color: #333;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        
        # Create app state
        app_state = AppState()
        
        # Create main window
        window = MainWindow(app_state)
        
        # Create tray icon (optional - may not work on all systems)
        tray = TrayIcon(app_state)
        if tray.is_available():
            tray.open_panel_requested.connect(window.show)
            tray.open_panel_requested.connect(window.raise_)
            tray.open_panel_requested.connect(window.activateWindow)
            tray.quit_requested.connect(app.quit)
        
        # Cleanup on quit
        def cleanup():
            """Cleanup resources before exit"""
            try:
                if hasattr(app_state, '_speed_monitor') and app_state._speed_monitor:
                    app_state._stop_speed_monitor()
                if tray.is_available():
                    tray.hide()
            except:
                pass
        
        app.aboutToQuit.connect(cleanup)
        
        # Show window
        window.show()
        
        # Run application
        return app.exec()
    
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
