"""
样式模块
~~~~~~~~~

定义GUI界面样式和主题
"""

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QRect, QSize, Qt, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QFont, QIcon
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect, QApplication, QStyleFactory, QProxyStyle,
    QWidget, QPushButton, QLabel, QProgressBar
)
import os
import sys

# 主题颜色定义
class Theme:
    """主题颜色和样式定义"""
    # 主色调
    PRIMARY = "#1a73e8"  # 蓝色
    PRIMARY_LIGHT = "#4a9bff"
    PRIMARY_DARK = "#0d47a1"
    
    # 次要色调
    SECONDARY = "#5f6368"  # 灰色
    SECONDARY_LIGHT = "#8e9295"
    SECONDARY_DARK = "#3c4043"
    
    # 强调色
    ACCENT = "#00c853"  # 绿色
    
    # 严重程度颜色
    CRITICAL = "#d32f2f"  # 深红色
    HIGH = "#f57c00"      # 橙色
    MEDIUM = "#ffb300"    # 琥珀色
    LOW = "#0288d1"       # 蓝色
    INFO = "#00897b"      # 青色
    
    # 背景色
    BACKGROUND = "#ffffff"
    CARD_BACKGROUND = "#f8f9fa"
    HOVER_BACKGROUND = "#e8f0fe"
    
    # 文本颜色
    TEXT_PRIMARY = "#202124"
    TEXT_SECONDARY = "#5f6368"
    TEXT_DISABLED = "#9aa0a6"
    TEXT_ON_PRIMARY = "#ffffff"
    
    # 边框颜色
    BORDER = "#dadce0"
    
    # 阴影颜色
    SHADOW = "#0000001A"  # 10% 黑色透明度
    
    # 图表颜色
    CHART_COLORS = [
        "#1a73e8", "#00c853", "#f57c00", "#d32f2f", "#8e24aa",
        "#0097a7", "#ffb300", "#3949ab", "#546e7a", "#ec407a"
    ]
    
    # 渐变色
    GRADIENT_START = "#1a73e8"
    GRADIENT_END = "#00c853"
    
    # 科技感背景网格颜色
    GRID_COLOR = "#e0e0e0"
    
    # 字体
    FONT_FAMILY = "Segoe UI, Microsoft YaHei, Arial, sans-serif"
    FONT_SIZE_SMALL = 11
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_LARGE = 15
    FONT_SIZE_XLARGE = 18

# 应用样式表
STYLESHEET = f"""
/* 全局样式 */
QWidget {{
    font-family: {Theme.FONT_FAMILY};
    font-size: {Theme.FONT_SIZE_NORMAL}px;
    color: {Theme.TEXT_PRIMARY};
    background-color: {Theme.BACKGROUND};
}}

/* 主窗口 */
QMainWindow {{
    background-color: {Theme.BACKGROUND};
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    background-color: {Theme.BACKGROUND};
    margin-top: -1px;
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: {Theme.BACKGROUND};
    color: {Theme.TEXT_SECONDARY};
    padding: 8px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid {Theme.BORDER};
    border-bottom: none;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    color: {Theme.PRIMARY};
    background-color: {Theme.BACKGROUND};
    border-bottom: 2px solid {Theme.PRIMARY};
}}

QTabBar::tab:hover {{
    background-color: {Theme.HOVER_BACKGROUND};
}}

/* 按钮 */
QPushButton {{
    background-color: {Theme.PRIMARY};
    color: {Theme.TEXT_ON_PRIMARY};
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 36px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {Theme.PRIMARY_LIGHT};
}}

QPushButton:pressed {{
    background-color: {Theme.PRIMARY_DARK};
}}

QPushButton:disabled {{
    background-color: {Theme.SECONDARY_LIGHT};
    color: {Theme.TEXT_DISABLED};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    color: {Theme.PRIMARY};
    border: 1px solid {Theme.PRIMARY};
}}

QPushButton#secondaryButton:hover {{
    background-color: {Theme.HOVER_BACKGROUND};
}}

/* 输入框 */
QLineEdit, QTextEdit {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    padding: 8px;
    background-color: {Theme.BACKGROUND};
    selection-background-color: {Theme.PRIMARY_LIGHT};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid {Theme.PRIMARY};
}}

/* 下拉框 */
QComboBox {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    padding: 8px;
    background-color: {Theme.BACKGROUND};
    min-height: 36px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    background-color: {Theme.BACKGROUND};
    selection-background-color: {Theme.PRIMARY_LIGHT};
    selection-color: {Theme.TEXT_ON_PRIMARY};
}}

/* 进度条 */
QProgressBar {{
    border: none;
    border-radius: 8px;
    background-color: {Theme.SECONDARY_LIGHT};
    text-align: center;
    font-weight: bold;
    color: {Theme.TEXT_ON_PRIMARY};
    min-height: 16px;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
    border-radius: 8px;
}}

/* 表格 */
QTableWidget {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    gridline-color: {Theme.BORDER};
    background-color: {Theme.BACKGROUND};
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: {Theme.PRIMARY_LIGHT};
    color: {Theme.TEXT_ON_PRIMARY};
}}

QHeaderView::section {{
    background-color: {Theme.CARD_BACKGROUND};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {Theme.BORDER};
    border-right: 1px solid {Theme.BORDER};
    font-weight: bold;
}}

/* 滚动条 */
QScrollBar:vertical {{
    border: none;
    background: {Theme.CARD_BACKGROUND};
    width: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {Theme.SECONDARY_LIGHT};
    min-height: 30px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Theme.SECONDARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background: {Theme.CARD_BACKGROUND};
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {Theme.SECONDARY_LIGHT};
    min-width: 30px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Theme.SECONDARY};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0px;
}}

/* 分组框 */
QGroupBox {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 15px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
}}

/* 菜单栏 */
QMenuBar {{
    background-color: {Theme.BACKGROUND};
    border-bottom: 1px solid {Theme.BORDER};
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 8px 12px;
}}

QMenuBar::item:selected {{
    background-color: {Theme.HOVER_BACKGROUND};
    color: {Theme.PRIMARY};
}}

QMenu {{
    background-color: {Theme.BACKGROUND};
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    padding: 4px 0px;
}}

QMenu::item {{
    padding: 6px 32px 6px 16px;
}}

QMenu::item:selected {{
    background-color: {Theme.HOVER_BACKGROUND};
    color: {Theme.PRIMARY};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {Theme.BACKGROUND};
    border-top: 1px solid {Theme.BORDER};
    color: {Theme.TEXT_SECONDARY};
}}

/* 特定颜色类 */
.critical {{ color: {Theme.CRITICAL}; }}
.high {{ color: {Theme.HIGH}; }}
.medium {{ color: {Theme.MEDIUM}; }}
.low {{ color: {Theme.LOW}; }}
.info {{ color: {Theme.INFO}; }}

/* 卡片式控件 */
QWidget[class="card"] {{
    background-color: {Theme.CARD_BACKGROUND};
    border-radius: 8px;
    padding: 16px;
}}
"""

# 自定义动画按钮
class AnimatedButton(QPushButton):
    """带有悬停动画效果的按钮"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化颜色属性
        self._normal_color = QColor(Theme.PRIMARY)
        self._hover_color = QColor(Theme.PRIMARY_LIGHT)
        self._pressed_color = QColor(Theme.PRIMARY_DARK)
        self._current_color = self._normal_color  # 确保在这里初始化
        
        # 创建动画
        self._animation = QPropertyAnimation(self, b"background_color")
        self._animation.setDuration(150)  # 150毫秒
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 设置样式
        self.setStyleSheet(f"""
        QPushButton {{
            background-color: {self._normal_color.name()};
            color: {Theme.TEXT_ON_PRIMARY};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 36px;
            font-weight: bold;
        }}
        """)
    
    def get_background_color(self):
        return self._current_color
    
    def set_background_color(self, color):
        self._current_color = color
        self.setStyleSheet(f"""
        QPushButton {{
            background-color: {color.name()};
            color: {Theme.TEXT_ON_PRIMARY};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 36px;
            font-weight: bold;
        }}
        """)
    
    background_color = pyqtProperty(QColor, get_background_color, set_background_color)
    
    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._hover_color)
        self._animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._normal_color)
        self._animation.start()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._pressed_color)
        self._animation.start()
        super().mousePressEvent(event)


# 科技感风格卡片控件
class TechCard(QWidget):
    """科技感风格的卡片控件"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.setMinimumHeight(150)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(Theme.SHADOW))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 样式设置
        self.setStyleSheet(f"""
            TechCard {{
                background-color: {Theme.CARD_BACKGROUND};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(Theme.CARD_BACKGROUND)))
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # 绘制边框
        painter.setPen(QPen(QColor(Theme.BORDER), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 8, 8)
        
        # 绘制标题
        if self.title:
            painter.setPen(QColor(Theme.PRIMARY))
            painter.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_NORMAL, QFont.Bold))
            painter.drawText(16, 26, self.title)
            
            # 分隔线
            painter.setPen(QPen(QColor(Theme.PRIMARY_LIGHT), 1))
            painter.drawLine(16, 36, self.width() - 16, 36)
        
        # 绘制科技感网格背景
        painter.setPen(QPen(QColor(Theme.GRID_COLOR), 0.5, Qt.DashLine))
        
        # 横线
        for y in range(8, self.height(), 20):
            painter.drawLine(8, y, self.width() - 8, y)
        
        # 竖线
        for x in range(8, self.width(), 20):
            painter.drawLine(x, 8, x, self.height() - 8)


# 现代风格进度条
class ModernProgressBar(QProgressBar):
    """现代风格进度条，支持动画效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
        
        # 创建动画
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(500)  # 500毫秒
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setValue(self, value):
        if self.value() != value:
            self._animation.stop()
            self._animation.setStartValue(self.value())
            self._animation.setEndValue(value)
            self._animation.start()
    
    def instantSetValue(self, value):
        """立即设置值，不使用动画"""
        super().setValue(value)


# 应用样式到应用程序
def apply_style(app):
    """应用样式到整个应用程序
    
    Args:
        app: QApplication实例
    """
    # 设置应用程序样式
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(STYLESHEET) 