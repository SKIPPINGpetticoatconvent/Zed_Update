#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Update Manager - PyQt5 GUI Frontend
Integrated with Go backend API and original Zed updater functionality
"""

import sys
import os
import json
import logging
import requests
import threading
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QTextEdit, QProgressBar, QTabWidget, QGroupBox,
    QFileDialog, QMessageBox, QSystemTrayIcon, QMenu, QAction,
    QTimeEdit, QListWidget, QSplitter, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QTime, QTextCodec
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QFontDatabase, QTextCursor

# UTF-8 compatibility setup
if sys.platform == 'win32':
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zed_updater_gui.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BackendWorker(QThread):
    """Backend communication worker thread"""

    connection_changed = pyqtSignal(bool, str)
    version_info_received = pyqtSignal(dict)
    system_info_received = pyqtSignal(dict)
    update_progress = pyqtSignal(float, str)
    update_completed = pyqtSignal(bool, str)

    def __init__(self, backend_url="http://localhost:8080/api/v1"):
        super().__init__()
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZedUpdater-GUI/1.0.0',
            'Content-Type': 'application/json'
        })
        self.running = False
        self.operation = None
        self.operation_data = None

    def run(self):
        """Main worker thread loop"""
        self.running = True
        while self.running:
            if self.operation == "check_connection":
                self._check_connection()
            elif self.operation == "get_system_info":
                self._get_system_info()
            elif self.operation == "check_updates":
                self._check_updates()
            elif self.operation == "download_update":
                self._download_update()
            elif self.operation == "install_update":
                self._install_update()

            self.operation = None
            self.msleep(100)

    def stop(self):
        """Stop the worker thread"""
        self.running = False

    def check_connection(self):
        """Request connection check"""
        self.operation = "check_connection"

    def get_system_info(self):
        """Request system info"""
        self.operation = "get_system_info"

    def check_updates(self):
        """Request update check"""
        self.operation = "check_updates"

    def download_update(self, data=None):
        """Request update download"""
        self.operation = "download_update"
        self.operation_data = data or {}

    def install_update(self, data=None):
        """Request update installation"""
        self.operation = "install_update"
        self.operation_data = data or {}

    def _check_connection(self):
        """Check backend connection"""
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('version', 'Unknown')
                self.connection_changed.emit(True, f"Connected (v{version})")
            else:
                self.connection_changed.emit(False, f"Error {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.connection_changed.emit(False, f"Connection failed: {str(e)}")

    def _get_system_info(self):
        """Get system information"""
        try:
            response = self.session.get(f"{self.backend_url}/system/info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.system_info_received.emit(data.get('data', {}))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get system info: {e}")

    def _check_updates(self):
        """Check for updates"""
        try:
            response = self.session.get(f"{self.backend_url}/updates/check", timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.version_info_received.emit(data.get('data', {}))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check updates: {e}")

    def _download_update(self):
        """Download update"""
        try:
            payload = self.operation_data or {"action": "download"}
            response = self.session.post(f"{self.backend_url}/updates/download",
                                       json=payload, timeout=30)
            if response.status_code == 200:
                # Simulate download progress
                for i in range(0, 101, 10):
                    self.update_progress.emit(i, f"Downloading... {i}%")
                    self.msleep(500)
                self.update_completed.emit(True, "Download completed")
            else:
                self.update_completed.emit(False, f"Download failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.update_completed.emit(False, f"Download error: {str(e)}")

    def _install_update(self):
        """Install update"""
        try:
            payload = self.operation_data or {"action": "install"}
            response = self.session.post(f"{self.backend_url}/updates/install",
                                       json=payload, timeout=30)
            if response.status_code == 200:
                # Simulate installation progress
                for i in range(0, 101, 5):
                    self.update_progress.emit(i, f"Installing... {i}%")
                    self.msleep(300)
                self.update_completed.emit(True, "Installation completed")
            else:
                self.update_completed.emit(False, f"Installation failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.update_completed.emit(False, f"Installation error: {str(e)}")


class ZedUpdaterConfig:
    """Configuration management for Zed updater"""

    DEFAULT_CONFIG = {
        'zed_install_path': r'D:\Zed.exe',
        'backup_enabled': True,
        'backup_count': 3,
        'github_repo': 'TC999/zed-loc',
        'auto_check_enabled': True,
        'check_interval_hours': 24,
        'check_on_startup': True,
        'auto_download': True,
        'auto_install': False,
        'auto_start_after_update': True,
        'force_download_latest': True,
        'notification_enabled': True,
        'minimize_to_tray': True,
        'start_minimized': False,
        'download_timeout': 300,
        'retry_count': 3,
        'check_time': '09:00',
        'proxy_enabled': False,
        'proxy_url': '',
        'language': 'zh_CN'
    }

    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                    logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_setting(self, key, default=None):
        """Get configuration setting"""
        return self.config.get(key, default)

    def set_setting(self, key, value):
        """Set configuration setting"""
        self.config[key] = value


class ZedUpdaterGUI(QMainWindow):
    """Main Zed Updater GUI window"""

    def __init__(self):
        super().__init__()
        self.config = ZedUpdaterConfig()
        self.backend_worker = BackendWorker()
        self.tray_icon = None
        self.current_version = "Unknown"
        self.latest_version = "Unknown"
        self.last_check_time = None

        # Setup GUI
        self.init_ui()
        self.setup_tray_icon()
        self.setup_connections()
        self.setup_timers()

        # Start backend worker
        self.backend_worker.start()

        # Initial connection check
        self.check_backend_connection()

        # Load settings
        self.load_settings()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Zed Editor 自动更新程序 v2.0")
        self.setGeometry(100, 100, 900, 700)

        # Setup fonts for UTF-8 display
        self.setup_fonts()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_schedule_tab()
        self.create_log_tab()
        self.create_about_tab()

        # Status bar
        self.statusBar().showMessage("Ready")

    def setup_fonts(self):
        """Setup fonts for proper UTF-8 display"""
        try:
            font = QFont()
            if sys.platform == 'win32':
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
                for font_name in chinese_fonts:
                    available_fonts = QFontDatabase().families()
                    if font_name in available_fonts:
                        font.setFamily(font_name)
                        break
                else:
                    font.setFamily("Arial")

            font.setPointSize(9)
            QApplication.instance().setFont(font)

            # Set text encoding
            try:
                codec = QTextCodec.codecForName("UTF-8")
                if codec:
                    QTextCodec.setCodecForLocale(codec)
            except:
                pass

        except Exception as e:
            logger.warning(f"Font setup failed: {e}")

    def create_main_tab(self):
        """Create main interface tab"""
        main_tab = QWidget()
        self.tab_widget.addTab(main_tab, "主界面")

        layout = QVBoxLayout(main_tab)

        # Connection status group
        connection_group = QGroupBox("连接状态")
        connection_layout = QGridLayout(connection_group)

        connection_layout.addWidget(QLabel("Backend状态:"), 0, 0)
        self.backend_status_label = QLabel("检查中...")
        connection_layout.addWidget(self.backend_status_label, 0, 1)

        self.reconnect_button = QPushButton("重新连接")
        self.reconnect_button.clicked.connect(self.check_backend_connection)
        connection_layout.addWidget(self.reconnect_button, 0, 2)

        layout.addWidget(connection_group)

        # Version info group
        version_group = QGroupBox("版本信息")
        version_layout = QGridLayout(version_group)

        version_layout.addWidget(QLabel("当前版本:"), 0, 0)
        self.current_version_label = QLabel("检查中...")
        version_layout.addWidget(self.current_version_label, 0, 1)

        version_layout.addWidget(QLabel("最新版本:"), 1, 0)
        self.latest_version_label = QLabel("检查中...")
        version_layout.addWidget(self.latest_version_label, 1, 1)

        version_layout.addWidget(QLabel("上次检查:"), 2, 0)
        self.last_check_label = QLabel("从未")
        version_layout.addWidget(self.last_check_label, 2, 1)

        layout.addWidget(version_group)

        # Action buttons group
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout(action_group)

        self.check_updates_button = QPushButton("检查更新")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        action_layout.addWidget(self.check_updates_button)

        self.download_button = QPushButton("下载更新")
        self.download_button.clicked.connect(self.download_update)
        self.download_button.setEnabled(False)
        action_layout.addWidget(self.download_button)

        self.install_button = QPushButton("安装更新")
        self.install_button.clicked.connect(self.install_update)
        self.install_button.setEnabled(False)
        action_layout.addWidget(self.install_button)

        self.start_zed_button = QPushButton("启动 Zed")
        self.start_zed_button.clicked.connect(self.start_zed)
        action_layout.addWidget(self.start_zed_button)

        layout.addWidget(action_group)

        # Progress group
        self.progress_group = QGroupBox("操作进度")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(self.progress_group)
        self.progress_group.hide()

        # Release notes group
        notes_group = QGroupBox("更新说明")
        notes_layout = QVBoxLayout(notes_group)

        self.release_notes = QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setMaximumHeight(150)
        notes_layout.addWidget(self.release_notes)

        layout.addWidget(notes_group)

        # System info group
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout(system_group)

        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(100)
        system_layout.addWidget(self.system_info_text)

        refresh_system_button = QPushButton("刷新系统信息")
        refresh_system_button.clicked.connect(self.refresh_system_info)
        system_layout.addWidget(refresh_system_button)

        layout.addWidget(system_group)

    def create_settings_tab(self):
        """Create settings tab"""
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "设置")

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        main_layout = QVBoxLayout(settings_tab)
        main_layout.addWidget(scroll)

        layout = QVBoxLayout(scroll_widget)

        # Basic settings group
        basic_group = QGroupBox("基本设置")
        basic_layout = QGridLayout(basic_group)

        basic_layout.addWidget(QLabel("Zed安装路径:"), 0, 0)
        self.zed_path_edit = QLineEdit()
        basic_layout.addWidget(self.zed_path_edit, 0, 1)

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_zed_path)
        basic_layout.addWidget(browse_button, 0, 2)

        basic_layout.addWidget(QLabel("GitHub仓库:"), 1, 0)
        self.github_repo_edit = QLineEdit()
        basic_layout.addWidget(self.github_repo_edit, 1, 1, 1, 2)

        layout.addWidget(basic_group)

        # Auto update settings group
        auto_group = QGroupBox("自动更新设置")
        auto_layout = QGridLayout(auto_group)

        self.auto_check_enabled = QCheckBox("启用自动检查")
        auto_layout.addWidget(self.auto_check_enabled, 0, 0, 1, 2)

        auto_layout.addWidget(QLabel("检查间隔(小时):"), 1, 0)
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 168)  # 1 hour to 1 week
        auto_layout.addWidget(self.check_interval_spin, 1, 1)

        self.check_on_startup = QCheckBox("启动时检查更新")
        auto_layout.addWidget(self.check_on_startup, 2, 0, 1, 2)

        self.auto_download = QCheckBox("自动下载更新")
        auto_layout.addWidget(self.auto_download, 3, 0, 1, 2)

        self.auto_install = QCheckBox("自动安装更新")
        auto_layout.addWidget(self.auto_install, 4, 0, 1, 2)

        self.auto_start_after_update = QCheckBox("更新后自动启动Zed")
        auto_layout.addWidget(self.auto_start_after_update, 5, 0, 1, 2)

        layout.addWidget(auto_group)

        # Backup settings group
        backup_group = QGroupBox("备份设置")
        backup_layout = QGridLayout(backup_group)

        self.backup_enabled = QCheckBox("启用备份")
        backup_layout.addWidget(self.backup_enabled, 0, 0, 1, 2)

        backup_layout.addWidget(QLabel("保留备份数:"), 1, 0)
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 10)
        backup_layout.addWidget(self.backup_count_spin, 1, 1)

        layout.addWidget(backup_group)

        # UI settings group
        ui_group = QGroupBox("界面设置")
        ui_layout = QGridLayout(ui_group)

        self.minimize_to_tray = QCheckBox("最小化到系统托盘")
        ui_layout.addWidget(self.minimize_to_tray, 0, 0, 1, 2)

        self.start_minimized = QCheckBox("启动时最小化")
        ui_layout.addWidget(self.start_minimized, 1, 0, 1, 2)

        self.notification_enabled = QCheckBox("启用通知")
        ui_layout.addWidget(self.notification_enabled, 2, 0, 1, 2)

        layout.addWidget(ui_group)

        # Save settings button
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def create_schedule_tab(self):
        """Create schedule tab"""
        schedule_tab = QWidget()
        self.tab_widget.addTab(schedule_tab, "定时任务")

        layout = QVBoxLayout(schedule_tab)

        # Schedule settings group
        schedule_group = QGroupBox("定时设置")
        schedule_layout = QGridLayout(schedule_group)

        schedule_layout.addWidget(QLabel("检查时间:"), 0, 0)
        self.check_time_edit = QTimeEdit()
        self.check_time_edit.setTime(QTime.fromString("09:00", "hh:mm"))
        schedule_layout.addWidget(self.check_time_edit, 0, 1)

        self.schedule_enabled = QCheckBox("启用定时检查")
        schedule_layout.addWidget(self.schedule_enabled, 1, 0, 1, 2)

        layout.addWidget(schedule_group)

        # Schedule status group
        status_group = QGroupBox("运行状态")
        status_layout = QGridLayout(status_group)

        status_layout.addWidget(QLabel("当前状态:"), 0, 0)
        self.schedule_status_label = QLabel("未启用")
        status_layout.addWidget(self.schedule_status_label, 0, 1)

        status_layout.addWidget(QLabel("下次运行:"), 1, 0)
        self.next_run_label = QLabel("未设置")
        status_layout.addWidget(self.next_run_label, 1, 1)

        layout.addWidget(status_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_schedule_button = QPushButton("启动定时任务")
        self.start_schedule_button.clicked.connect(self.toggle_schedule)
        control_layout.addWidget(self.start_schedule_button)

        self.run_now_button = QPushButton("立即运行检查")
        self.run_now_button.clicked.connect(self.run_check_now)
        control_layout.addWidget(self.run_now_button)

        layout.addLayout(control_layout)

    def create_log_tab(self):
        """Create log tab"""
        log_tab = QWidget()
        self.tab_widget.addTab(log_tab, "日志")

        layout = QVBoxLayout(log_tab)

        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        layout.addWidget(self.log_text)

        # Log controls
        log_controls = QHBoxLayout()

        clear_log_button = QPushButton("清空日志")
        clear_log_button.clicked.connect(self.clear_log)
        log_controls.addWidget(clear_log_button)

        refresh_log_button = QPushButton("刷新日志")
        refresh_log_button.clicked.connect(self.refresh_log)
        log_controls.addWidget(refresh_log_button)

        log_controls.addStretch()

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        log_controls.addWidget(self.auto_scroll_check)

        layout.addLayout(log_controls)

    def create_about_tab(self):
        """Create about tab"""
        about_tab = QWidget()
        self.tab_widget.addTab(about_tab, "关于")

        layout = QVBoxLayout(about_tab)

        # Application info
        info_group = QGroupBox("应用程序信息")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("应用名称:"), 0, 0)
        info_layout.addWidget(QLabel("Zed Editor 自动更新程序"), 0, 1)

        info_layout.addWidget(QLabel("版本:"), 1, 0)
        info_layout.addWidget(QLabel("2.0.0"), 1, 1)

        info_layout.addWidget(QLabel("架构:"), 2, 0)
        info_layout.addWidget(QLabel("Go Backend + PyQt5 Frontend"), 2, 1)

        info_layout.addWidget(QLabel("作者:"), 3, 0)
        info_layout.addWidget(QLabel("Zed Update Team"), 3, 1)

        layout.addWidget(info_group)

        # Backend info
        backend_group = QGroupBox("Backend信息")
        backend_layout = QVBoxLayout(backend_group)

        self.backend_info_text = QTextEdit()
        self.backend_info_text.setReadOnly(True)
        self.backend_info_text.setMaximumHeight(100)
        backend_layout.addWidget(self.backend_info_text)

        layout.addWidget(backend_group)

    def setup_tray_icon(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # Create tray menu
            tray_menu = QMenu()

            show_action = QAction("显示窗口", self)
            show_action.triggered.connect(self.show_window)
            tray_menu.addAction(show_action)

            check_action = QAction("检查更新", self)
            check_action.triggered.connect(self.check_for_updates)
            tray_menu.addAction(check_action)

            tray_menu.addSeparator()

            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)

            # Set icon (you may want to add an actual icon file)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            self.tray_icon.show()

    def setup_connections(self):
        """Setup signal connections"""
        self.backend_worker.connection_changed.connect(self.on_connection_changed)
        self.backend_worker.version_info_received.connect(self.on_version_info_received)
        self.backend_worker.system_info_received.connect(self.on_system_info_received)
        self.backend_worker.update_progress.connect(self.on_update_progress)
        self.backend_worker.update_completed.connect(self.on_update_completed)

    def setup_timers(self):
        """Setup periodic timers"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(30000)  # Every 30 seconds

        # Auto check timer
        self.auto_check_timer = QTimer()
        self.auto_check_timer.timeout.connect(self.auto_check_updates)

        # Log refresh timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_log)
        self.log_timer.start(5000)  # Every 5 seconds

    def check_backend_connection(self):
        """Check backend connection"""
        self.backend_worker.check_connection()
        self.log_message("Checking backend connection...")

    def check_for_updates(self):
        """Check for updates"""
        self.backend_worker.check_updates()
        self.log_message("Checking for updates...")
        self.last_check_time = datetime.now()
        self.update_last_check_label()

    def download_update(self):
        """Download update"""
        self.progress_group.show()
        self.backend_worker.download_update()
        self.log_message("Starting download...")

    def install_update(self):
        """Install update"""
        reply = QMessageBox.question(self, "确认安装",
                                   "确定要安装更新吗？这将关闭当前的Zed进程。",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.progress_group.show()
            self.backend_worker.install_update()
            self.log_message("Starting installation...")

    def start_zed(self):
        """Start Zed application"""
        zed_path = self.config.get_setting('zed_install_path')
        if Path(zed_path).exists():
            try:
                subprocess.Popen([zed_path])
                self.log_message(f"Started Zed from: {zed_path}")
                QMessageBox.information(self, "启动成功", "Zed已启动")
            except Exception as e:
                self.log_message(f"Failed to start Zed: {e}")
                QMessageBox.critical(self, "启动失败", f"无法启动Zed: {e}")
        else:
            QMessageBox.warning(self, "文件不存在", f"Zed可执行文件不存在: {zed_path}")

    def refresh_system_info(self):
        """Refresh system information"""
        self.backend_worker.get_system_info()

    def browse_zed_path(self):
        """Browse for Zed executable path"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Zed.exe", "", "Executable files (*.exe)"
        )
        if file_path:
            self.zed_path_edit.setText(file_path)

    def load_settings(self):
        """Load settings from configuration"""
        try:
            # Basic settings
            self.zed_path_edit.setText(self.config.get_setting('zed_install_path', ''))
            self.github_repo_edit.setText(self.config.get_setting('github_repo', ''))

            # Auto update settings
            self.auto_check_enabled.setChecked(self.config.get_setting('auto_check_enabled', True))
            self.check_interval_spin.setValue(self.config.get_setting('check_interval_hours', 24))
            self.check_on_startup.setChecked(self.config.get_setting('check_on_startup', True))
            self.auto_download.setChecked(self.config.get_setting('auto_download', True))
            self.auto_install.setChecked(self.config.get_setting('auto_install', False))
            self.auto_start_after_update.setChecked(self.config.get_setting('auto_start_after_update', True))

            # Backup settings
            self.backup_enabled.setChecked(self.config.get_setting('backup_enabled', True))
            self.backup_count_spin.setValue(self.config.get_setting('backup_count', 3))

            # UI settings
            self.minimize_to_tray.setChecked(self.config.get_setting('minimize_to_tray', True))
            self.start_minimized.setChecked(self.config.get_setting('start_minimized', False))
            self.notification_enabled.setChecked(self.config.get_setting('notification_enabled', True))

            # Schedule settings
            check_time = self.config.get_setting('check_time', '09:00')
            self.check_time_edit.setTime(QTime.fromString(check_time, "hh:mm"))
            self.schedule_enabled.setChecked(self.config.get_setting('auto_check_enabled', True))

            self.log_message("Settings loaded successfully")

        except Exception as e:
            self.log_message(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Basic settings
            self.config.set_setting('zed_install_path', self.zed_path_edit.text())
            self.config.set_setting('github_repo', self.github_repo_edit.text())

            # Auto update settings
            self.config.set_setting('auto_check_enabled', self.auto_check_enabled.isChecked())
            self.config.set_setting('check_interval_hours', self.check_interval_spin.value())
            self.config.set_setting('check_on_startup', self.check_on_startup.isChecked())
            self.config.set_setting('auto_download', self.auto_download.isChecked())
            self.config.set_setting('auto_install', self.auto_install.isChecked())
            self.config.set_setting('auto_start_after_update', self.auto_start_after_update.isChecked())

            # Backup settings
            self.config.set_setting('backup_enabled', self.backup_enabled.isChecked())
            self.config.set_setting('backup_count', self.backup_count_spin.value())

            # UI settings
            self.config.set_setting('minimize_to_tray', self.minimize_to_tray.isChecked())
            self.config.set_setting('start_minimized', self.start_minimized.isChecked())
            self.config.set_setting('notification_enabled', self.notification_enabled.isChecked())

            # Schedule settings
            check_time = self.check_time_edit.time().toString("hh:mm")
            self.config.set_setting('check_time', check_time)

            self.config.save_config()
            self.log_message("Settings saved successfully")
            QMessageBox.information(self, "保存成功", "设置已保存")

        except Exception as e:
            self.log_message(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {e}")

    def toggle_schedule(self):
        """Toggle schedule on/off"""
        if self.schedule_enabled.isChecked():
            self.start_schedule_button.setText("停止定时任务")
            self.schedule_status_label.setText("运行中")
            self.update_auto_check_timer()
            self.log_message("Schedule started")
        else:
            self.start_schedule_button.setText("启动定时任务")
            self.schedule_status_label.setText("已停止")
            self.auto_check_timer.stop()
            self.next_run_label.setText("未设置")
            self.log_message("Schedule stopped")

    def run_check_now(self):
        """Run check immediately"""
        self.check_for_updates()

    def update_auto_check_timer(self):
        """Update auto check timer"""
        if self.auto_check_enabled.isChecked():
            interval_ms = self.check_interval_spin.value() * 60 * 60 * 1000  # Convert hours to milliseconds
            self.auto_check_timer.start(interval_ms)

            next_run = datetime.now() + timedelta(hours=self.check_interval_spin.value())
            self.next_run_label.setText(next_run.strftime("%Y-%m-%d %H:%M:%S"))

    def auto_check_updates(self):
        """Auto check for updates"""
        if self.auto_check_enabled.isChecked():
            self.check_for_updates()

    def update_status(self):
        """Update status information"""
        self.update_last_check_label()

    def update_last_check_label(self):
        """Update last check time label"""
        if self.last_check_time:
            self.last_check_label.setText(self.last_check_time.strftime("%Y-%m-%d %H:%M:%S"))

    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.log_text.append(log_entry)

        if self.auto_scroll_check.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """Clear log display"""
        self.log_text.clear()

    def refresh_log(self):
        """Refresh log display"""
        # In a real implementation, this would read from log file
        pass

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """Show main window"""
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_application(self):
        """Quit application"""
        reply = QMessageBox.question(self, "确认退出",
                                   "确定要退出程序吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.backend_worker.stop()
            self.backend_worker.wait()
            QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.minimize_to_tray.isChecked() and self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
            event.accept()

    # Signal handlers
    def on_connection_changed(self, connected, message):
        """Handle backend connection change"""
        self.backend_status_label.setText(message)
        if connected:
            self.statusBar().showMessage("Backend连接正常")
            self.log_message("Backend connection established")
            # Get initial system info
            self.refresh_system_info()
        else:
            self.statusBar().showMessage("Backend连接失败")
            self.log_message(f"Backend connection failed: {message}")

    def on_version_info_received(self, version_data):
        """Handle version information received"""
        self.latest_version = version_data.get('version', 'Unknown')
        self.latest_version_label.setText(self.latest_version)

        description = version_data.get('description', 'No description available')
        self.release_notes.setText(description)

        # Enable download button
        self.download_button.setEnabled(True)

        self.log_message(f"Latest version available: {self.latest_version}")

    def on_system_info_received(self, system_data):
        """Handle system information received"""
        info_text = "系统信息:\n"
        info_text += f"操作系统: {system_data.get('os', 'Unknown')}\n"
        info_text += f"架构: {system_data.get('architecture', 'Unknown')}\n"
        info_text += f"Go版本: {system_data.get('go_version', 'Unknown')}\n"
        info_text += f"服务器端口: {system_data.get('server_port', 'Unknown')}"

        self.system_info_text.setText(info_text)
        self.backend_info_text.setText(json.dumps(system_data, indent=2, ensure_ascii=False))

    def on_update_progress(self, progress, message):
        """Handle update progress"""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
        self.log_message(f"Progress: {progress}% - {message}")

    def on_update_completed(self, success, message):
        """Handle update completion"""
        self.progress_group.hide()

        if success:
            self.log_message(f"Operation completed: {message}")
            if "download" in message.lower():
                self.install_button.setEnabled(True)
                QMessageBox.information(self, "下载完成", "更新下载完成，可以进行安装了")
            elif "install" in message.lower():
                QMessageBox.information(self, "安装完成", "更新安装完成！")
                if self.auto_start_after_update.isChecked():
                    self.start_zed()
        else:
            self.log_message(f"Operation failed: {message}")
            QMessageBox.warning(self, "操作失败", f"操作失败: {message}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Zed Editor 自动更新程序")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("ZedUpdater")

    # Setup UTF-8 encoding
    try:
        codec = QTextCodec.codecForName("UTF-8")
        if codec:
            QTextCodec.setCodecForLocale(codec)
    except:
        pass

    # Create and show main window
    window = ZedUpdaterGUI()

    # Check if should start minimized
    if not window.config.get_setting('start_minimized', False):
        window.show()

    # Start the application
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
