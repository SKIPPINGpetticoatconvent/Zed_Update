#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Zed Updater GUI
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QProgressBar, QTextEdit,
    QGroupBox, QSystemTrayIcon, QMenu, QAction, QMessageBox,
    QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from ..core.config import ConfigManager
from ..core.updater import ZedUpdater, UpdateResult
from ..core.scheduler import UpdateScheduler
from ..services.system_service import SystemService
from ..services.notification_service import NotificationService
from ..utils.logger import get_logger
from ..utils.encoding import EncodingUtils

from .updater_gui import UpdaterGUI
from .system_tray import SystemTrayIcon
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    update_progress = pyqtSignal(float, str)
    update_completed = pyqtSignal(bool, str)

    def __init__(self, config: ConfigManager, updater: ZedUpdater,
                 scheduler: UpdateScheduler):
        super().__init__()

        self.config = config
        self.updater = updater
        self.scheduler = scheduler
        self.system_service = SystemService()
        self.notification_service = NotificationService()

        self.logger = get_logger(__name__)

        # Initialize components
        self.updater_gui = None
        self.tray_icon = None
        self.settings_dialog = None

        # Setup UI
        self.init_ui()
        self.setup_tray_icon()
        self.setup_connections()
        self.setup_timers()

        # Setup notifications
        if self.tray_icon:
            self.notification_service.set_tray_icon(self.tray_icon)

        # Load settings
        self.load_settings()

        # Initial checks
        self.check_current_version()
        if self.config.get('check_on_startup'):
            QTimer.singleShot(1000, self.check_for_updates)

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Zed Editor 自动更新程序 v2.1")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)

        # Setup fonts for UTF-8 display
        self.setup_fonts()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_system_tab()
        self.create_log_tab()
        self.create_about_tab()

        # Status bar
        self.statusBar().showMessage("就绪")

        # Menu bar
        self.create_menu_bar()

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
            else:
                font.setFamily("Sans Serif")

            font.setPointSize(9)
            QApplication.instance().setFont(font)

        except Exception as e:
            self.logger.warning(f"Font setup failed: {e}")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("文件(&F)")

        settings_action = QAction("设置(&S)", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("工具(&T)")

        check_update_action = QAction("检查更新(&C)", self)
        check_update_action.triggered.connect(self.check_for_updates)
        tools_menu.addAction(check_update_action)

        start_scheduler_action = QAction("启动定时任务(&R)", self)
        start_scheduler_action.triggered.connect(self.toggle_scheduler)
        tools_menu.addAction(start_scheduler_action)

        tools_menu.addSeparator()

        clear_temp_action = QAction("清理临时文件(&L)", self)
        clear_temp_action.triggered.connect(self.clear_temp_files)
        tools_menu.addAction(clear_temp_action)

        # Help menu
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_main_tab(self):
        """Create main interface tab"""
        main_tab = QWidget()
        self.tab_widget.addTab(main_tab, "主界面")

        layout = QVBoxLayout(main_tab)

        # Updater GUI component
        self.updater_gui = UpdaterGUI(self.config, self.updater, self.scheduler)
        layout.addWidget(self.updater_gui)

        # System info section
        system_group = QGroupBox("系统信息")
        system_layout = QVBoxLayout(system_group)

        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(150)
        system_layout.addWidget(self.system_info_text)

        refresh_system_button = QPushButton("刷新系统信息")
        refresh_system_button.clicked.connect(self.refresh_system_info)
        system_layout.addWidget(refresh_system_button)

        layout.addWidget(system_group)

    def create_settings_tab(self):
        """Create settings tab"""
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "设置")

        layout = QVBoxLayout(settings_tab)

        # Settings dialog component
        self.settings_dialog = SettingsDialog(self.config)
        layout.addWidget(self.settings_dialog)

    def create_system_tab(self):
        """Create system tab"""
        system_tab = QWidget()
        self.tab_widget.addTab(system_tab, "系统")

        layout = QVBoxLayout(system_tab)

        # System status group
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        self.system_status_text = QTextEdit()
        self.system_status_text.setReadOnly(True)
        status_layout.addWidget(self.system_status_text)

        refresh_status_button = QPushButton("刷新状态")
        refresh_status_button.clicked.connect(self.refresh_system_status)
        status_layout.addWidget(refresh_status_button)

        layout.addWidget(status_group)

        # Process monitor group
        process_group = QGroupBox("进程监控")
        process_layout = QVBoxLayout(process_group)

        self.process_text = QTextEdit()
        self.process_text.setReadOnly(True)
        process_layout.addWidget(self.process_text)

        refresh_process_button = QPushButton("刷新进程")
        refresh_process_button.clicked.connect(self.refresh_process_info)
        process_layout.addWidget(refresh_process_button)

        layout.addWidget(process_group)

    def create_log_tab(self):
        """Create log tab"""
        log_tab = QWidget()
        self.tab_widget.addTab(log_tab, "日志")

        layout = QVBoxLayout(log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        layout.addWidget(self.log_text)

        # Log controls
        log_controls = QHBoxLayout()

        clear_log_button = QPushButton("清空日志")
        clear_log_button.clicked.connect(self.clear_log)
        log_controls.addWidget(clear_log_button)

        log_controls.addStretch()

        layout.addLayout(log_controls)

    def create_about_tab(self):
        """Create about tab"""
        about_tab = QWidget()
        self.tab_widget.addTab(about_tab, "关于")

        layout = QVBoxLayout(about_tab)

        # Application info
        info_group = QGroupBox("应用程序信息")
        info_layout = QVBoxLayout(info_group)

        info_text = f"""
        <h2>Zed Editor 自动更新程序</h2>
        <p><b>版本:</b> 2.1.0</p>
        <p><b>作者:</b> Zed Update Team</p>
        <p><b>架构:</b> 现代化微服务架构</p>
        <p><b>支持:</b> Legacy + Modern 实现</p>
        <br>
        <p>自动检查、下载和安装 Zed Editor 的最新版本。</p>
        <p>支持图形界面和命令行操作，提供定时更新功能。</p>
        """

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)

        # License info
        license_group = QGroupBox("许可证")
        license_layout = QVBoxLayout(license_group)

        license_text = """
        <p>本项目采用 MIT 许可证。</p>
        <p>详见项目根目录下的 LICENSE 文件。</p>
        """

        license_label = QLabel(license_text)
        license_label.setWordWrap(True)
        license_layout.addWidget(license_label)

        layout.addWidget(license_group)

    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()

    def setup_connections(self):
        """Setup signal connections"""
        # Connect updater signals
        self.update_progress.connect(self.on_update_progress)
        self.update_completed.connect(self.on_update_completed)

        # Connect scheduler callbacks
        self.scheduler.add_update_callback(self.on_scheduler_update)

    def setup_timers(self):
        """Setup periodic timers"""
        # System info update timer
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self.refresh_system_info)
        self.system_timer.start(30000)  # Every 30 seconds

        # Log refresh timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_log)
        self.log_timer.start(5000)  # Every 5 seconds

    def load_settings(self):
        """Load settings from configuration"""
        try:
            # Apply UI settings
            minimize_to_tray = self.config.get('minimize_to_tray', True)
            start_minimized = self.config.get('start_minimized', False)

            if start_minimized:
                self.hide()
                if self.tray_icon:
                    self.tray_icon.show_message("Zed Updater", "应用程序已最小化到托盘")

            # Start scheduler if enabled
            if self.config.get('auto_check_enabled', True):
                self.scheduler.start()

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    def check_current_version(self):
        """Check and display current Zed version"""
        try:
            version = self.updater.get_current_version()
            if self.updater_gui:
                self.updater_gui.set_current_version(version or "未知")
        except Exception as e:
            self.logger.error(f"Failed to check current version: {e}")

    def check_for_updates(self):
        """Check for updates"""
        try:
            if self.updater_gui:
                self.updater_gui.check_for_updates()
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")

    def toggle_scheduler(self):
        """Toggle scheduler on/off"""
        try:
            if self.scheduler.is_running():
                self.scheduler.stop()
                self.statusBar().showMessage("定时任务已停止")
            else:
                if self.scheduler.start():
                    self.statusBar().showMessage("定时任务已启动")
                else:
                    self.statusBar().showMessage("启动定时任务失败")
        except Exception as e:
            self.logger.error(f"Failed to toggle scheduler: {e}")

    def clear_temp_files(self):
        """Clear temporary files"""
        try:
            self.updater.cleanup_temp_files()
            QMessageBox.information(self, "清理完成", "临时文件清理完成")
        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"清理临时文件时出错: {e}")

    def show_settings(self):
        """Show settings dialog"""
        if self.settings_dialog:
            self.settings_dialog.exec_()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "关于 Zed Updater",
            "Zed Editor 自动更新程序 v2.1.0\n\n"
            "自动检查、下载和安装 Zed Editor 的最新版本。\n"
            "支持图形界面和命令行操作，提供定时更新功能。"
        )

    def refresh_system_info(self):
        """Refresh system information display"""
        try:
            info = self.system_service.get_system_info()
            if info:
                info_text = "系统信息:\n"
                info_text += f"操作系统: {info.get('system', 'Unknown')} {info.get('release', '')}\n"
                info_text += f"架构: {info.get('machine', 'Unknown')}\n"
                info_text += f"Python版本: {info.get('python_version', 'Unknown')}\n"
                info_text += f"CPU核心数: {info.get('cpu_count', 'Unknown')}\n"
                info_text += f"总内存: {info.get('memory_total', 0) / (1024**3):.1f} GB\n"
                self.system_info_text.setText(info_text)
        except Exception as e:
            self.logger.error(f"Failed to refresh system info: {e}")

    def refresh_system_status(self):
        """Refresh system status display"""
        try:
            status = self.system_service.get_system_status()
            if status:
                status_text = "系统状态:\n"
                status_text += f"CPU使用率: {status.get('cpu_percent', 0):.1f}%\n"
                status_text += f"内存使用: {status.get('memory_used_gb', 0):.1f}GB / {status.get('memory_total_gb', 0):.1f}GB ({status.get('memory_percent', 0):.1f}%)\n"
                status_text += f"磁盘使用: {status.get('disk_used_gb', 0):.1f}GB / {status.get('disk_total_gb', 0):.1f}GB ({status.get('disk_percent', 0):.1f}%)\n"
                status_text += f"运行进程: {status.get('running_processes', 0)}\n"
                self.system_status_text.setText(status_text)
        except Exception as e:
            self.logger.error(f"Failed to refresh system status: {e}")

    def refresh_process_info(self):
        """Refresh process information display"""
        try:
            processes = self.system_service.find_processes_by_name('zed')
            if processes:
                process_text = "Zed相关进程:\n"
                for proc in processes[:10]:  # Limit to 10 processes
                    process_text += f"PID: {proc['pid']}, 名称: {proc['name']}\n"
                    process_text += f"  CPU: {proc['cpu_percent']:.1f}%, 内存: {proc['memory_percent']:.1f}%\n"
                self.process_text.setText(process_text)
            else:
                self.process_text.setText("未找到Zed相关进程")
        except Exception as e:
            self.logger.error(f"Failed to refresh process info: {e}")

    def refresh_log(self):
        """Refresh log display"""
        try:
            log_file = self.config.get('log_file')
            if log_file and Path(log_file).exists():
                content = EncodingUtils.read_text_file(log_file)
                if content:
                    # Show last 1000 lines
                    lines = content.split('\n')[-1000:]
                    self.log_text.setText('\n'.join(lines))
                    # Scroll to bottom
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.End)
                    self.log_text.setTextCursor(cursor)
        except Exception as e:
            self.logger.warning(f"Failed to refresh log: {e}")

    def clear_log(self):
        """Clear log display"""
        self.log_text.clear()

    # Event handlers
    def on_update_progress(self, progress: float, message: str):
        """Handle update progress"""
        if self.updater_gui:
            self.updater_gui.update_progress(progress, message)

    def on_update_completed(self, success: bool, message: str):
        """Handle update completion"""
        if self.updater_gui:
            self.updater_gui.update_completed(success, message)

        # Show notification
        if success:
            self.notification_service.show_update_completed(message)
        else:
            self.notification_service.show_update_failed(message)

    def on_scheduler_update(self, update_available: bool, result: Optional[UpdateResult]):
        """Handle scheduler update callback"""
        if update_available and result:
            self.notification_service.show_update_available(result.version or "最新版")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.config.get('minimize_to_tray', True) and self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            if self.tray_icon:
                self.tray_icon.show_message("Zed Updater", "应用程序已最小化到托盘")
            event.ignore()
        else:
            # Cleanup
            if self.scheduler.is_running():
                self.scheduler.stop()

            if self.tray_icon:
                self.tray_icon.hide()

            event.accept()