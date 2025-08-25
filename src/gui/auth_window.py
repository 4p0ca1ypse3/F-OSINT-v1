"""
Authentication window for F-OSINT DWv1
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTabWidget, QWidget, 
                            QCheckBox, QMessageBox, QFrame, QSpacerItem,
                            QSizePolicy, QApplication)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap

from core.auth import AuthManager
from gui.themes import get_theme_manager


class AuthWindow(QDialog):
    """Authentication window with sign in and sign up tabs"""
    
    authenticated = pyqtSignal(dict)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.auth_manager = AuthManager()
        self.theme_manager = get_theme_manager()
        
        self.init_ui()
        self.setup_connections()
        
        # Apply theme
        self.theme_manager.set_theme(self.config.get('gui', {}).get('theme', 'dark'))
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("F-OSINT DWv1 - Authentication")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("F-OSINT DWv1")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Dark Web OSINT & Analysis Tool")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #888888;")
        main_layout.addWidget(subtitle_label)
        
        # Developer credit
        developer_label = QLabel("Developed by 4p0ca1ypse")
        developer_font = QFont()
        developer_font.setPointSize(10)
        developer_label.setFont(developer_font)
        developer_label.setAlignment(Qt.AlignCenter)
        developer_label.setStyleSheet("color: #666666;")
        main_layout.addWidget(developer_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Sign In tab
        self.signin_tab = self.create_signin_tab()
        self.tab_widget.addTab(self.signin_tab, "Sign In")
        
        # Sign Up tab
        self.signup_tab = self.create_signup_tab()
        self.tab_widget.addTab(self.signup_tab, "Sign Up")
        
        main_layout.addWidget(self.tab_widget)
        
        # Theme toggle button
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        
        self.theme_button = QPushButton("🌙 Dark Mode")
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #666666;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_button)
        
        main_layout.addLayout(theme_layout)
        
        self.setLayout(main_layout)
    
    def create_signin_tab(self):
        """Create sign in tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Username field
        layout.addWidget(QLabel("Username:"))
        self.signin_username = QLineEdit()
        self.signin_username.setPlaceholderText("Enter your username")
        layout.addWidget(self.signin_username)
        
        # Password field
        layout.addWidget(QLabel("Password:"))
        self.signin_password = QLineEdit()
        self.signin_password.setPlaceholderText("Enter your password")
        self.signin_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.signin_password)
        
        # Remember me checkbox
        self.remember_me = QCheckBox("Remember me")
        layout.addWidget(self.remember_me)
        
        # Sign in button
        self.signin_button = QPushButton("Sign In")
        self.signin_button.setDefault(True)
        layout.addWidget(self.signin_button)
        
        # Status label
        self.signin_status = QLabel("")
        self.signin_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.signin_status)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_signup_tab(self):
        """Create sign up tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Username field
        layout.addWidget(QLabel("Username:"))
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username")
        layout.addWidget(self.signup_username)
        
        # Email field
        layout.addWidget(QLabel("Email:"))
        self.signup_email = QLineEdit()
        self.signup_email.setPlaceholderText("Enter your email address")
        layout.addWidget(self.signup_email)
        
        # Password field
        layout.addWidget(QLabel("Password:"))
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Create a strong password")
        self.signup_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.signup_password)
        
        # Confirm password field
        layout.addWidget(QLabel("Confirm Password:"))
        self.signup_confirm_password = QLineEdit()
        self.signup_confirm_password.setPlaceholderText("Confirm your password")
        self.signup_confirm_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.signup_confirm_password)
        
        # Password requirements
        requirements_label = QLabel(
            "Password must contain:\n"
            "• At least 8 characters\n"
            "• Uppercase and lowercase letters\n"
            "• At least one number\n"
            "• At least one special character"
        )
        requirements_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(requirements_label)
        
        # Sign up button
        self.signup_button = QPushButton("Sign Up")
        layout.addWidget(self.signup_button)
        
        # Status label
        self.signup_status = QLabel("")
        self.signup_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.signup_status)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        self.signin_button.clicked.connect(self.handle_signin)
        self.signup_button.clicked.connect(self.handle_signup)
        
        # Enter key handling
        self.signin_password.returnPressed.connect(self.handle_signin)
        self.signup_confirm_password.returnPressed.connect(self.handle_signup)
    
    def handle_signin(self):
        """Handle sign in attempt"""
        username = self.signin_username.text().strip()
        password = self.signin_password.text()
        
        if not username or not password:
            self.show_signin_status("Please enter both username and password", "error")
            return
        
        try:
            user = self.auth_manager.authenticate_user(username, password)
            if user:
                user_data = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'remember_me': self.remember_me.isChecked()
                }
                self.show_signin_status("Authentication successful!", "success")
                self.authenticated.emit(user_data)
            else:
                self.show_signin_status("Invalid username or password", "error")
                
        except Exception as e:
            self.show_signin_status(f"Authentication error: {str(e)}", "error")
    
    def handle_signup(self):
        """Handle sign up attempt"""
        username = self.signup_username.text().strip()
        email = self.signup_email.text().strip()
        password = self.signup_password.text()
        confirm_password = self.signup_confirm_password.text()
        
        # Validation
        if not all([username, email, password, confirm_password]):
            self.show_signup_status("Please fill in all fields", "error")
            return
        
        if password != confirm_password:
            self.show_signup_status("Passwords do not match", "error")
            return
        
        if '@' not in email or '.' not in email.split('@')[-1]:
            self.show_signup_status("Please enter a valid email address", "error")
            return
        
        try:
            user = self.auth_manager.register_user(username, email, password)
            if user:
                self.show_signup_status("Account created successfully! You can now sign in.", "success")
                # Switch to sign in tab
                self.tab_widget.setCurrentIndex(0)
                self.signin_username.setText(username)
                self.signin_password.setFocus()
            else:
                self.show_signup_status("Failed to create account. Please try again.", "error")
                
        except ValueError as e:
            self.show_signup_status(str(e), "error")
        except Exception as e:
            self.show_signup_status(f"Registration error: {str(e)}", "error")
    
    def show_signin_status(self, message, status_type):
        """Show status message for sign in"""
        if status_type == "success":
            self.signin_status.setStyleSheet("color: #4CAF50;")
        else:
            self.signin_status.setStyleSheet("color: #F44336;")
        self.signin_status.setText(message)
    
    def show_signup_status(self, message, status_type):
        """Show status message for sign up"""
        if status_type == "success":
            self.signup_status.setStyleSheet("color: #4CAF50;")
        else:
            self.signup_status.setStyleSheet("color: #F44336;")
        self.signup_status.setText(message)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.theme_manager.toggle_theme()
        current_theme = self.theme_manager.current_theme
        if current_theme == "dark":
            self.theme_button.setText("🌙 Dark Mode")
        else:
            self.theme_button.setText("☀️ Light Mode")
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(self, 'Exit Application', 
                                   'Are you sure you want to exit F-OSINT DWv1?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            QApplication.instance().quit()
        else:
            event.ignore()