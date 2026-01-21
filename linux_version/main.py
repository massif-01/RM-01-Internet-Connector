#!/usr/bin/env python3
"""
RM-01 Internet Connector - Linux Version
A tool to share your computer's internet connection with RM-01 devices

Copyright © 2025 massif-01, RMinte AI Technology Co., Ltd.

Usage:
    python3 main.py [--no-tray]
    
Options:
    --no-tray    Disable system tray icon (useful if it causes crashes)
"""

import sys
import os
import argparse

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from app_state import AppState
from ui.main_window import MainWindow
from ui.widgets import get_asset_path


def main():
    """Application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RM-01 Internet Connector')
    parser.add_argument('--no-tray', action='store_true', 
                        help='Disable system tray icon (useful if it causes crashes)')
    args, remaining = parser.parse_known_args()
    
    # Set environment variable if --no-tray is specified
    if args.no_tray:
        os.environ['RM01_NO_TRAY'] = '1'
    
    try:
        # Enable high DPI scaling (PyQt5 style)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create application (pass remaining args, not parsed ones)
        app = QApplication([sys.argv[0]] + remaining)
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
        
        # Tray icon holder
        tray = None
        
        def setup_tray():
            """Setup tray icon after window is shown (delayed to avoid early crashes)"""
            nonlocal tray
            if os.environ.get('RM01_NO_TRAY', '').lower() in ('1', 'true', 'yes'):
                print("System tray disabled")
                return
            
            try:
                from ui.tray_icon import TrayIcon
                tray = TrayIcon(app_state)
                if tray.is_available():
                    tray.open_panel_requested.connect(window.show)
                    tray.open_panel_requested.connect(window.raise_)
                    tray.open_panel_requested.connect(window.activateWindow)
                    tray.quit_requested.connect(app.quit)
                    print("System tray icon enabled")
                else:
                    print("System tray icon not available")
            except Exception as e:
                print(f"Warning: System tray not available: {e}")
        
        # Cleanup on quit
        def cleanup():
            """Cleanup resources before exit"""
            try:
                if hasattr(app_state, '_speed_monitor') and app_state._speed_monitor:
                    app_state._stop_speed_monitor()
                if tray and tray.is_available():
                    tray.hide()
            except:
                pass
        
        app.aboutToQuit.connect(cleanup)
        
        # Show window first
        window.show()
        
        # Setup tray icon after a short delay (helps avoid segfaults on some systems)
        QTimer.singleShot(100, setup_tray)
        
        # Run application
        return app.exec_()
    
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
