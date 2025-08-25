"""
Main window for F-OSINT DWv1
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLabel, QPushButton, QMenuBar, QMenu,
                            QAction, QStatusBar, QMessageBox, QSplitter,
                            QTextEdit, QFrame, QTreeWidget, QTreeWidgetItem,
                            QGroupBox, QProgressBar, QListWidget, QComboBox,
                            QLineEdit, QSpacerItem, QSizePolicy, QToolBar,
                            QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon

from core.session import SessionManager
from core.project_manager import ProjectManager
from core.tor_handler import get_tor_handler
from gui.themes import get_theme_manager


class TorStatusWidget(QWidget):
    """Widget to display Tor connection status"""
    
    def __init__(self):
        super().__init__()
        self.tor_handler = get_tor_handler()
        self.init_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        self.update_status()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Tor: Disconnected")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_tor_connection)
        layout.addWidget(self.connect_button)
        
        self.setLayout(layout)
    
    def update_status(self):
        """Update Tor status"""
        is_running = self.tor_handler.is_tor_running()
        
        if is_running:
            self.status_label.setText("Tor: Connected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.connect_button.setText("Disconnect")
        else:
            self.status_label.setText("Tor: Disconnected")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.connect_button.setText("Connect")
    
    def toggle_tor_connection(self):
        """Toggle Tor connection"""
        if self.tor_handler.is_tor_running():
            self.tor_handler.stop_tor()
        else:
            success = self.tor_handler.start_tor()
            if not success:
                QMessageBox.warning(self, "Tor Connection Error",
                                  "Failed to connect to Tor network. Please ensure Tor is installed and running.")
        
        self.update_status()


class ProjectExplorerWidget(QWidget):
    """Project explorer widget"""
    
    project_selected = pyqtSignal(str)
    
    def __init__(self, project_manager):
        super().__init__()
        self.project_manager = project_manager
        self.init_ui()
        self.refresh_projects()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Projects")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.new_project_button = QPushButton("New")
        self.new_project_button.setMaximumWidth(60)
        header_layout.addWidget(self.new_project_button)
        
        layout.addLayout(header_layout)
        
        # Projects tree
        self.projects_tree = QTreeWidget()
        self.projects_tree.setHeaderLabels(["Name", "Targets", "Findings"])
        self.projects_tree.itemDoubleClicked.connect(self.on_project_selected)
        layout.addWidget(self.projects_tree)
        
        self.setLayout(layout)
    
    def refresh_projects(self):
        """Refresh projects list"""
        self.projects_tree.clear()
        projects = self.project_manager.list_projects()
        
        for project in projects:
            item = QTreeWidgetItem([
                project.name,
                str(project.get_target_count()),
                str(project.get_finding_count())
            ])
            item.setData(0, Qt.UserRole, project.project_id)
            self.projects_tree.addTopLevelItem(item)
    
    def on_project_selected(self, item):
        """Handle project selection"""
        project_id = item.data(0, Qt.UserRole)
        if project_id:
            self.project_selected.emit(project_id)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config, session_manager):
        super().__init__()
        self.config = config
        self.session_manager = session_manager
        self.project_manager = ProjectManager(session_manager.get_current_user_id())
        self.theme_manager = get_theme_manager()
        
        self.init_ui()
        self.setup_connections()
        
        # Apply theme
        self.theme_manager.set_theme(self.config.get('gui', {}).get('theme', 'dark'))
        
        # Show welcome message
        self.show_welcome_message()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"F-OSINT DWv1 - {self.session_manager.get_current_username()}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (Project Explorer + Tor Status)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel (Main Content)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Create toolbar
        self.create_toolbar()
    
    def create_left_panel(self):
        """Create left panel with project explorer and Tor status"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Tor Status
        tor_group = QGroupBox("Network Status")
        tor_layout = QVBoxLayout()
        self.tor_status_widget = TorStatusWidget()
        tor_layout.addWidget(self.tor_status_widget)
        tor_group.setLayout(tor_layout)
        layout.addWidget(tor_group)
        
        # Project Explorer
        project_group = QGroupBox("Project Explorer")
        project_layout = QVBoxLayout()
        self.project_explorer = ProjectExplorerWidget(self.project_manager)
        project_layout.addWidget(self.project_explorer)
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """Create right panel with main content tabs"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Tab widget for main content
        self.main_tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard_tab = self.create_dashboard_tab()
        self.main_tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Dark Web Scanner tab
        self.darkweb_tab = self.create_placeholder_tab("Dark Web Scanner")
        self.main_tabs.addTab(self.darkweb_tab, "Dark Web")
        
        # Google Dorking tab
        self.dorking_tab = self.create_placeholder_tab("Google Dorking")
        self.main_tabs.addTab(self.dorking_tab, "Google Dorking")
        
        # Leak Checker tab
        self.leak_tab = self.create_placeholder_tab("Leak Checker")
        self.main_tabs.addTab(self.leak_tab, "Leak Checker")
        
        # PGP Search tab
        self.pgp_tab = self.create_placeholder_tab("PGP Search")
        self.main_tabs.addTab(self.pgp_tab, "PGP Search")
        
        # Crypto Tracker tab
        self.crypto_tab = self.create_placeholder_tab("Crypto Tracker")
        self.main_tabs.addTab(self.crypto_tab, "Crypto Tracker")
        
        # Reports tab
        self.reports_tab = self.create_placeholder_tab("Reports")
        self.main_tabs.addTab(self.reports_tab, "Reports")
        
        layout.addWidget(self.main_tabs)
        panel.setLayout(layout)
        return panel
    
    def create_dashboard_tab(self):
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Welcome section
        welcome_group = QGroupBox("Welcome to F-OSINT DWv1")
        welcome_layout = QVBoxLayout()
        
        welcome_text = QLabel(
            f"Welcome back, {self.session_manager.get_current_username()}!\n\n"
            "F-OSINT DWv1 is your comprehensive tool for Dark Web OSINT and Analysis.\n"
            "Use the tabs above to access different OSINT modules, or start by creating a new project."
        )
        welcome_text.setWordWrap(True)
        welcome_layout.addWidget(welcome_text)
        
        welcome_group.setLayout(welcome_layout)
        layout.addWidget(welcome_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        actions_buttons_layout = QHBoxLayout()
        
        new_project_btn = QPushButton("Create New Project")
        new_project_btn.clicked.connect(self.create_new_project)
        actions_buttons_layout.addWidget(new_project_btn)
        
        connect_tor_btn = QPushButton("Connect to Tor")
        connect_tor_btn.clicked.connect(self.quick_connect_tor)
        actions_buttons_layout.addWidget(connect_tor_btn)
        
        actions_buttons_layout.addStretch()
        actions_layout.addLayout(actions_buttons_layout)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        self.activity_list.addItem("Application started")
        self.activity_list.addItem(f"User {self.session_manager.get_current_username()} logged in")
        activity_layout.addWidget(self.activity_list)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_placeholder_tab(self, title):
        """Create a placeholder tab for modules"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel(f"{title} Module")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #888888;")
        layout.addWidget(label)
        
        description = QLabel(f"The {title} module is under development.\nThis will provide advanced {title.lower()} capabilities.")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666666;")
        layout.addWidget(description)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_project_action = QAction('New Project', self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction('Open Project', self)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        toggle_theme_action = QAction('Toggle Theme', self)
        toggle_theme_action.triggered.connect(self.theme_manager.toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        tor_settings_action = QAction('Tor Settings', self)
        tools_menu.addAction(tor_settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar('Main')
        
        # New project action
        new_project_action = QAction('New Project', self)
        new_project_action.triggered.connect(self.create_new_project)
        toolbar.addAction(new_project_action)
        
        toolbar.addSeparator()
        
        # Tor connection action
        tor_action = QAction('Toggle Tor', self)
        tor_action.triggered.connect(self.tor_status_widget.toggle_tor_connection)
        toolbar.addAction(tor_action)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets
        self.status_bar.addPermanentWidget(QLabel("F-OSINT DWv1 v1.0.0"))
    
    def setup_connections(self):
        """Setup signal connections"""
        self.project_explorer.project_selected.connect(self.load_project)
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def show_welcome_message(self):
        """Show welcome message"""
        self.status_bar.showMessage(f"Welcome, {self.session_manager.get_current_username()}!")
        self.activity_list.addItem(f"Welcome message displayed for {self.session_manager.get_current_username()}")
    
    def create_new_project(self):
        """Create a new project"""
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, 'New Project', 'Enter project name:')
        if ok and name.strip():
            description, ok = QInputDialog.getText(self, 'New Project', 'Enter project description (optional):')
            if ok:
                project = self.project_manager.create_project(name.strip(), description.strip())
                if project:
                    self.project_explorer.refresh_projects()
                    self.status_bar.showMessage(f"Created project: {name}")
                    self.activity_list.addItem(f"Created new project: {name}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to create project")
    
    def load_project(self, project_id):
        """Load selected project"""
        project = self.project_manager.load_project(project_id)
        if project:
            self.status_bar.showMessage(f"Loaded project: {project.name}")
            self.activity_list.addItem(f"Loaded project: {project.name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load project")
    
    def quick_connect_tor(self):
        """Quick connect to Tor"""
        self.tor_status_widget.toggle_tor_connection()
    
    def on_theme_changed(self, theme_name):
        """Handle theme change"""
        self.status_bar.showMessage(f"Theme changed to {theme_name} mode")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About F-OSINT DWv1",
                         "F-OSINT DWv1\n"
                         "Dark Web OSINT and Analysis Tool\n\n"
                         "Version: 1.0.0\n"
                         "Developed by: 4p0ca1ypse\n\n"
                         "A comprehensive tool for open-source intelligence gathering "
                         "and analysis with focus on dark web investigations.")
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(self, 'Exit Application',
                                   'Are you sure you want to exit F-OSINT DWv1?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Clean up
            self.tor_status_widget.tor_handler.stop_tor()
            self.session_manager.end_session()
            event.accept()
        else:
            event.ignore()