"""
Localization module for RM-01 Internet Connector
Supports English and Chinese
"""

from enum import Enum
from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal


class Language(Enum):
    ENGLISH = "EN"
    CHINESE = "CN"


class LocalizationManager(QObject):
    """Singleton localization manager with signal support"""
    
    language_changed = pyqtSignal(Language)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Check using __dict__ to avoid QObject attribute access before init
        if '_initialized' in self.__dict__:
            return
        super().__init__()
        self._initialized = True
        self._language = Language.ENGLISH
        
        self._translations: Dict[Language, Dict[str, str]] = {
            Language.ENGLISH: {
                "window_title": "RM-01 Internet Connector",
                "connect": "Connect",
                "disconnect": "Disconnect",
                "status_idle": "Ready",
                "status_connecting": "Connecting...",
                "status_disconnecting": "Disconnecting...",
                "status_connected": "Connected",
                "status_failed": "Failed",
                "interface_none": "No Device",
                "interface_found": "Device Ready",
                "hint_insert": "Please connect RM-01",
                # Menu bar items
                "menu_not_connected": "○ Not Connected",
                "menu_connected": "● Connected",
                "menu_connecting": "● Connecting...",
                "menu_failed": "● Connection Failed",
                "menu_connect": "Connect",
                "menu_disconnect": "Disconnect",
                "menu_reconnect": "Reconnect",
                "menu_open_panel": "Open Control Panel",
                "menu_quit": "Quit",
                # Errors
                "error_no_interface": "No AX88179A adapter found",
                "error_no_upstream": "No internet connection found",
                "error_permission": "Permission denied",
                "error_cancelled": "Operation cancelled",
            },
            Language.CHINESE: {
                "window_title": "RM-01 互联网连接助手",
                "connect": "立即连接",
                "disconnect": "断开连接",
                "status_idle": "准备就绪",
                "status_connecting": "正在连接...",
                "status_disconnecting": "正在断开...",
                "status_connected": "已连接",
                "status_failed": "连接失败",
                "interface_none": "未检测到设备",
                "interface_found": "设备已就绪",
                "hint_insert": "请连接 RM-01",
                # Menu bar items
                "menu_not_connected": "○ 未连接",
                "menu_connected": "● 已连接",
                "menu_connecting": "● 连接中...",
                "menu_failed": "● 连接失败",
                "menu_connect": "连接",
                "menu_disconnect": "断开连接",
                "menu_reconnect": "重新连接",
                "menu_open_panel": "打开控制面板",
                "menu_quit": "退出",
                # Errors
                "error_no_interface": "未找到 AX88179A 网卡",
                "error_no_upstream": "未找到互联网连接",
                "error_permission": "权限被拒绝",
                "error_cancelled": "操作已取消",
            }
        }
    
    @property
    def language(self) -> Language:
        return self._language
    
    @language.setter
    def language(self, value: Language):
        if self._language != value:
            self._language = value
            self.language_changed.emit(value)
    
    def toggle_language(self):
        """Toggle between English and Chinese"""
        if self._language == Language.ENGLISH:
            self.language = Language.CHINESE
        else:
            self.language = Language.ENGLISH
    
    def get(self, key: str) -> str:
        """Get localized string for key"""
        return self._translations.get(self._language, {}).get(key, key)
    
    def __call__(self, key: str) -> str:
        """Shorthand for get()"""
        return self.get(key)


# Global instance
loc = LocalizationManager()
