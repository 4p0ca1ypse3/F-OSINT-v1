"""
Theme management for F-OSINT DWv1
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication


class ThemeManager(QObject):
    """Theme manager for the application"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
    
    def set_theme(self, theme_name: str):
        """Set application theme"""
        if theme_name in ["light", "dark"]:
            self.current_theme = theme_name
            self._apply_theme()
            self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
    
    def _apply_theme(self):
        """Apply the current theme to the application"""
        app = QApplication.instance()
        if app:
            if self.current_theme == "dark":
                app.setStyleSheet(self._get_dark_theme())
            else:
                app.setStyleSheet(self._get_light_theme())
    
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet"""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #3c3c3c;
        }
        
        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #555555;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #3c3c3c;
            border-bottom: 2px solid #007acc;
        }
        
        QTabBar::tab:hover {
            background-color: #4a4a4a;
        }
        
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #005a9e;
        }
        
        QPushButton:pressed {
            background-color: #004578;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #999999;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #007acc;
        }
        
        QComboBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 3px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: url(down_arrow_white.png);
            width: 12px;
            height: 12px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #404040;
            color: #ffffff;
            selection-background-color: #007acc;
        }
        
        QListWidget, QTreeWidget, QTableWidget {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            alternate-background-color: #404040;
        }
        
        QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
            background-color: #007acc;
        }
        
        QHeaderView::section {
            background-color: #404040;
            color: #ffffff;
            padding: 8px;
            border: 1px solid #555555;
        }
        
        QScrollBar:vertical {
            background-color: #404040;
            width: 16px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: #666666;
            border-radius: 8px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #777777;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        QScrollBar:horizontal {
            background-color: #404040;
            height: 16px;
            border: none;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #666666;
            border-radius: 8px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #777777;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 4px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #007acc;
        }
        
        QMenu {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
        }
        
        QMenu::item {
            padding: 8px 16px;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
        }
        
        QStatusBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-top: 1px solid #555555;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
            background-color: #404040;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 2px;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            border: 2px solid #555555;
            background-color: #404040;
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #007acc;
            background-color: #007acc;
            image: url(check_white.png);
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
        }
        
        QRadioButton::indicator:unchecked {
            border: 2px solid #555555;
            background-color: #404040;
        }
        
        QRadioButton::indicator:checked {
            border: 2px solid #007acc;
            background-color: #007acc;
        }
        """
    
    def _get_light_theme(self) -> str:
        """Get light theme stylesheet"""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #000000;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #000000;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #cccccc;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #007acc;
        }
        
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #005a9e;
        }
        
        QPushButton:pressed {
            background-color: #004578;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #007acc;
        }
        
        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 3px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            selection-background-color: #007acc;
        }
        
        QListWidget, QTreeWidget, QTableWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            alternate-background-color: #f5f5f5;
        }
        
        QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QHeaderView::section {
            background-color: #f0f0f0;
            color: #000000;
            padding: 8px;
            border: 1px solid #cccccc;
        }
        
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 16px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 8px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #bbbbbb;
        }
        
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 16px;
            border: none;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #cccccc;
            border-radius: 8px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #bbbbbb;
        }
        
        QMenuBar {
            background-color: #ffffff;
            color: #000000;
            padding: 4px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
        }
        
        QMenu::item {
            padding: 8px 16px;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QStatusBar {
            background-color: #ffffff;
            color: #000000;
            border-top: 1px solid #cccccc;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
            background-color: #f0f0f0;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 2px;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            border: 2px solid #cccccc;
            background-color: #ffffff;
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #007acc;
            background-color: #007acc;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
        }
        
        QRadioButton::indicator:unchecked {
            border: 2px solid #cccccc;
            background-color: #ffffff;
        }
        
        QRadioButton::indicator:checked {
            border: 2px solid #007acc;
            background-color: #007acc;
        }
        """


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager