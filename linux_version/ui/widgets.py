"""
Custom widgets for RM-01 Internet Connector
Implements the liquid glass button and other custom UI components
"""

import os
from PyQt5.QtWidgets import (
    QPushButton, QWidget, QHBoxLayout, QLabel, QVBoxLayout,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, QSize
from PyQt5.QtGui import (
    QColor, QPainter, QLinearGradient, QPainterPath, QFont,
    QPixmap, QPen, QBrush
)


def get_asset_path(filename: str) -> str:
    """Get the path to an asset file"""
    # Try multiple locations
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', filename),
        os.path.join(os.path.dirname(__file__), '..', 'assets', filename),
        os.path.join('/usr/share/rm01-internet-connector/assets', filename),
    ]
    
    for path in candidates:
        if os.path.exists(path):
            return path
    
    return candidates[0]  # Return first candidate even if it doesn't exist


class LiquidGlassButton(QPushButton):
    """
    A modern button with liquid glass effect
    Matches the macOS SwiftUI version's appearance
    """
    
    def __init__(self, text: str = "", icon_name: str = "", parent=None):
        super().__init__(parent)
        self._text = text
        self._icon_name = icon_name
        self._is_destructive = False
        self._is_hovered = False
        self._is_pressed = False
        self._scale = 1.0
        
        # Setup
        self.setFixedSize(160, 46)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("", 12, QFont.DemiBold))
        
        # Animation for press effect
        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(100)
        self._scale_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
    
    @pyqtProperty(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()
    
    @property
    def is_destructive(self) -> bool:
        return self._is_destructive
    
    @is_destructive.setter
    def is_destructive(self, value: bool):
        self._is_destructive = value
        # Update shadow color
        shadow = self.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            if value:
                shadow.setColor(QColor(242, 115, 115, 100))  # Red shadow
            else:
                shadow.setColor(QColor(45, 212, 91, 80))  # Green shadow
        self.update()
    
    def set_button_text(self, text: str):
        """Set button text"""
        self._text = text
        self.update()
    
    def set_icon(self, icon_name: str):
        """Set icon name (for future use)"""
        self._icon_name = icon_name
        self.update()
    
    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        self._is_pressed = True
        self._scale_anim.setStartValue(1.0)
        self._scale_anim.setEndValue(0.98)
        self._scale_anim.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._is_pressed = False
        self._scale_anim.setStartValue(0.98)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Apply scale transform
        if self._scale != 1.0:
            painter.translate(self.width() / 2, self.height() / 2)
            painter.scale(self._scale, self._scale)
            painter.translate(-self.width() / 2, -self.height() / 2)
        
        rect = self.rect()
        radius = 12
        
        # Create rounded rect path
        path = QPainterPath()
        path.addRoundedRect(rect.x() + 1, rect.y() + 1, 
                           rect.width() - 2, rect.height() - 2, 
                           radius, radius)
        
        # Base gradient
        gradient = QLinearGradient(0, 0, 0, rect.height())
        if self._is_destructive:
            # Soft coral/salmon red
            gradient.setColorAt(0, QColor(242, 115, 115))  # #F27373
            gradient.setColorAt(1, QColor(217, 89, 89))    # #D95959
        else:
            # Finder green style
            gradient.setColorAt(0, QColor(45, 212, 91))    # #2DD45B
            gradient.setColorAt(1, QColor(32, 168, 68))    # #20A844
        
        painter.fillPath(path, gradient)
        
        # Top glossy highlight
        highlight_path = QPainterPath()
        highlight_path.addRoundedRect(rect.x() + 1, rect.y() + 1,
                                      rect.width() - 2, 20, radius, radius)
        highlight_gradient = QLinearGradient(0, 0, 0, 20)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 102))  # 40% white
        highlight_gradient.setColorAt(0.8, QColor(255, 255, 255, 25))  # 10% white
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillPath(highlight_path, highlight_gradient)
        
        # Bottom inner glow
        bottom_path = QPainterPath()
        bottom_path.addRoundedRect(rect.x() + 1, rect.height() - 11,
                                   rect.width() - 2, 10, 0, 0)
        bottom_gradient = QLinearGradient(0, rect.height() - 10, 0, rect.height())
        bottom_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        bottom_gradient.setColorAt(1, QColor(255, 255, 255, 51))  # 20% white
        painter.fillPath(bottom_path, bottom_gradient)
        
        # Hover effect
        if self._is_hovered and self.isEnabled():
            painter.fillPath(path, QColor(255, 255, 255, 25))
        
        # Press effect
        if self._is_pressed:
            painter.fillPath(path, QColor(0, 0, 0, 25))
        
        # Disabled effect
        if not self.isEnabled():
            painter.fillPath(path, QColor(255, 255, 255, 100))
        
        # Border
        border_gradient = QLinearGradient(0, 0, 0, rect.height())
        border_gradient.setColorAt(0, QColor(255, 255, 255, 128))  # 50% white
        border_gradient.setColorAt(0.5, QColor(255, 255, 255, 25))  # 10% white
        border_gradient.setColorAt(1, QColor(0, 0, 0, 13))  # 5% black
        
        painter.setPen(QPen(QBrush(border_gradient), 1))
        painter.drawRoundedRect(rect.x() + 1, rect.y() + 1,
                               rect.width() - 2, rect.height() - 2,
                               radius, radius)
        
        # Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self._text)


class NetworkSpeedDisplay(QWidget):
    """
    Display for network upload/download speeds
    Only visible when connected
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._upload_speed = 0.0
        self._download_speed = 0.0
        self._visible = False
        
        self.setFixedSize(160, 32)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        
        # Upload
        self.upload_label = QLabel("↑0B/s")
        self.upload_label.setFont(QFont("Monospace", 10, QFont.Normal))
        self.upload_label.setStyleSheet("color: #333;")
        
        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: rgba(0,0,0,0.3);")
        
        # Download
        self.download_label = QLabel("↓0B/s")
        self.download_label.setFont(QFont("Monospace", 10, QFont.Normal))
        self.download_label.setStyleSheet("color: #333;")
        
        layout.addWidget(self.upload_label)
        layout.addWidget(sep)
        layout.addWidget(self.download_label)
    
    def update_speed(self, upload: float, download: float):
        """Update the displayed speeds"""
        self._upload_speed = upload
        self._download_speed = download
        
        self.upload_label.setText(f"↑{self._format_speed(upload)}")
        self.download_label.setText(f"↓{self._format_speed(download)}")
    
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
    
    def set_visible_animated(self, visible: bool):
        """Show or hide with animation"""
        self._visible = visible
        self.setVisible(visible)
    
    def paintEvent(self, event):
        """Custom paint for background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.fillPath(path, QColor(0, 0, 0, 25))  # 10% black
        
        super().paintEvent(event)


class RM01DeviceImage(QWidget):
    """
    RM-01 device image with glow effects
    Shows red glow when disconnected, green glow when connected
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_connected = False
        self._glow_opacity = 0.0
        self._sweep_offset = -100.0
        self._is_animating_sweep = False
        
        # Fixed size with room for glow effect
        self.setFixedSize(130, 190)
        
        # Load image
        self._pixmap = QPixmap(get_asset_path("body.png"))
        if self._pixmap.isNull():
            # Create placeholder if image not found
            self._pixmap = QPixmap(90, 160)
            self._pixmap.fill(QColor(200, 200, 200, 100))
        
        # Glow animation - use a timer for pulsing effect
        self._glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self._glow_anim.setDuration(1000)
        self._glow_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._glow_anim.finished.connect(self._on_glow_finished)
        self._glow_increasing = True
        
        # Sweep animation
        self._sweep_anim = QPropertyAnimation(self, b"sweep_offset")
        self._sweep_anim.setDuration(1200)
        self._sweep_anim.setStartValue(-100.0)
        self._sweep_anim.setEndValue(100.0)
        self._sweep_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._sweep_anim.finished.connect(self._on_sweep_finished)
        
        # Start with red glow
        self._start_glow_animation()
    
    @pyqtProperty(float)
    def glow_opacity(self):
        return self._glow_opacity
    
    @glow_opacity.setter
    def glow_opacity(self, value):
        self._glow_opacity = value
        self.update()
    
    @pyqtProperty(float)
    def sweep_offset(self):
        return self._sweep_offset
    
    @sweep_offset.setter
    def sweep_offset(self, value):
        self._sweep_offset = value
        self.update()
    
    def set_connected(self, connected: bool):
        """Set connection state and update animations"""
        if self._is_connected == connected:
            return
        
        self._is_connected = connected
        
        # Stop current animations
        self._glow_anim.stop()
        self._sweep_anim.stop()
        
        if connected:
            # Start sweep animation, then green glow
            self._is_animating_sweep = True
            self._sweep_offset = -100.0
            self._sweep_anim.start()
        else:
            # Red glow
            self._is_animating_sweep = False
            self._start_glow_animation()
    
    def _on_sweep_finished(self):
        """Called when sweep animation finishes"""
        self._is_animating_sweep = False
        self._start_glow_animation()
    
    def _on_glow_finished(self):
        """Called when glow animation finishes - reverse direction for pulse effect"""
        if not self._is_animating_sweep:
            # Reverse direction
            self._glow_increasing = not self._glow_increasing
            if self._glow_increasing:
                self._glow_anim.setStartValue(0.0)
                self._glow_anim.setEndValue(0.4)
            else:
                self._glow_anim.setStartValue(0.4)
                self._glow_anim.setEndValue(0.0)
            self._glow_anim.start()
    
    def _start_glow_animation(self):
        """Start the glow pulsing animation"""
        self._glow_increasing = True
        self._glow_anim.setStartValue(0.0)
        self._glow_anim.setEndValue(0.4)
        self._glow_anim.setDuration(1000)
        self._glow_anim.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Calculate centered position (smaller image to leave room for glow)
        img_width = 90
        img_height = 160
        x = (self.width() - img_width) // 2
        y = (self.height() - img_height) // 2
        
        # Draw glow effect
        if self._glow_opacity > 0:
            glow_color = QColor(34, 204, 68) if self._is_connected else QColor(224, 68, 68)
            glow_color.setAlphaF(self._glow_opacity)
            
            # Simple glow using multiple passes
            for i in range(3):
                painter.setOpacity(self._glow_opacity * (0.3 - i * 0.1))
                offset = (i + 1) * 4
                painter.drawPixmap(x - offset, y - offset, 
                                  img_width + offset * 2, img_height + offset * 2,
                                  self._pixmap)
            
            painter.setOpacity(1.0)
        
        # Draw main image
        painter.drawPixmap(x, y, img_width, img_height, self._pixmap)
        
        # Draw sweep effect when animating
        if self._is_animating_sweep and self._is_connected:
            # Create sweep gradient
            sweep_x = x + img_width // 2 + self._sweep_offset
            gradient = QLinearGradient(sweep_x - 30, 0, sweep_x + 30, 0)
            gradient.setColorAt(0, QColor(255, 255, 255, 0))
            gradient.setColorAt(0.3, QColor(255, 255, 255, 128))
            gradient.setColorAt(0.5, QColor(255, 255, 255, 240))
            gradient.setColorAt(0.7, QColor(255, 255, 255, 128))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            # Clip to image bounds and draw
            painter.setClipRect(x, y, img_width, img_height)
            painter.fillRect(int(sweep_x - 30), y, 60, img_height, gradient)
