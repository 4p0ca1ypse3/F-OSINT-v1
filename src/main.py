#!/usr/bin/env python3
"""
F-OSINT DWv1 - Dark Web OSINT and Analysis Tool
Developed by 4p0ca1ypse (ApocalypseYetAgain)

Main application entry point.
"""

import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.auth_window import AuthWindow
from gui.main_window import MainWindow
from core.session import SessionManager
from utils.file_utils import ensure_directories


class FOSINTApp:
    """Main application class for F-OSINT DWv1"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("F-OSINT DWv1")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("4p0ca1ypse")
        
        # Set up high DPI scaling
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Ensure required directories exist
        ensure_directories()
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Initialize windows
        self.auth_window = None
        self.main_window = None
        
    def load_config(self):
        """Load application configuration"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(None, "Configuration Error", 
                               f"Failed to load configuration: {str(e)}")
            return {}
    
    def show_auth_window(self):
        """Show authentication window"""
        self.auth_window = AuthWindow(self.config)
        self.auth_window.authenticated.connect(self.on_authenticated)
        self.auth_window.show()
    
    def on_authenticated(self, user_data):
        """Handle successful authentication"""
        if self.auth_window:
            self.auth_window.hide()
        
        # Start session
        self.session_manager.start_session(user_data)
        
        # Show main window
        self.main_window = MainWindow(self.config, self.session_manager)
        self.main_window.show()
    
    def run(self):
        """Run the application"""
        try:
            # Check if user has valid session
            if self.session_manager.has_valid_session():
                # Show main window directly
                self.main_window = MainWindow(self.config, self.session_manager)
                self.main_window.show()
            else:
                # Show authentication window
                self.show_auth_window()
            
            return self.app.exec_()
            
        except Exception as e:
            QMessageBox.critical(None, "Application Error", 
                               f"An unexpected error occurred: {str(e)}")
            return 1


def main():
    """Main entry point"""
    try:
        app = FOSINTApp()
        sys.exit(app.run())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()