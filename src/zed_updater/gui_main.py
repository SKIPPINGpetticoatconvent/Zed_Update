#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified GUI Main entry point for Zed Updater
"""

import sys
import os

# Setup UTF-8 environment before any GUI imports
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

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit, QProgressBar, QGroupBox, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from .core.config import ConfigManager
from .core.updater import ZedUpdater
from .utils.logger import get_logger


class SimpleUpdaterGUI(QMainWindow):
    """Simplified Zed Updater GUI"""

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.updater = ZedUpdater(self.config)
        self.logger = get_logger(__name__)
        
        self.init_ui()
        self.setup_timer()
        self.load_settings()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Zed Editor 自动更新程序 v2.0")
        self.setGeometry(300, 300, 600, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Version info group
        version_group = QGroupBox("版本信息")
        version_layout = QVBoxLayout(version_group)
        
        self.current_version_label = QLabel("当前版本: 检查中...")
        self.latest_version_label = QLabel("最新版本: 检查中...")
        version_layout.addWidget(self.current_version_label)
        version_layout.addWidget(self.latest_version_label)
        
        layout.addWidget(version_group)
        
        # Control buttons group
        control_group = QGroupBox("操作")
        control_layout = QHBoxLayout(control_group)
        
        self.check_button = QPushButton("检查更新")
        self.check_button.clicked.connect(self.check_updates)
        control_layout.addWidget(self.check_button)
        
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.setEnabled(False)
        control_layout.addWidget(self.update_button)
        
        self.start_zed_button = QPushButton("启动 Zed")
        self.start_zed_button.clicked.connect(self.start_zed)
        control_layout.addWidget(self.start_zed_button)
        
        layout.addWidget(control_group)
        
        # Progress group
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Log group
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)

    def setup_timer(self):
        """Setup periodic update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_updates)
        # Auto-check every hour if enabled
        if self.config.get('auto_check_enabled'):
            self.timer.start(3600000)  # 1 hour

    def load_settings(self):
        """Load settings and display current version"""
        self.log_message("正在加载设置...")
        
        # Get current version
        current_version = self.updater.get_current_version()
        if current_version:
            self.current_version_label.setText(f"当前版本: {current_version}")
        else:
            self.current_version_label.setText("当前版本: 未知")
            
        # Auto-check on startup if enabled
        if self.config.get('check_on_startup', True):
            self.timer.singleShot(1000, self.check_updates)  # Check after 1 second

    def check_updates(self):
        """Check for updates"""
        self.log_message("正在检查更新...")
        self.check_button.setEnabled(False)
        
        # Check in a separate thread to avoid blocking UI
        QTimer.singleShot(100, self._check_updates_worker)

    def _check_updates_worker(self):
        """Worker function for checking updates"""
        try:
            release_info = self.updater.check_for_updates()
            
            if release_info:
                self.latest_version_label.setText(f"最新版本: {release_info.version}")
                self.update_button.setEnabled(True)
                self.log_message(f"发现新版本: {release_info.version}")
            else:
                self.latest_version_label.setText("最新版本: 无更新")
                self.update_button.setEnabled(False)
                self.log_message("没有可用的更新")
                
        except Exception as e:
            self.log_message(f"检查更新失败: {e}")
        finally:
            self.check_button.setEnabled(True)

    def start_update(self):
        """Start update process"""
        self.log_message("开始更新过程...")
        self.update_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start update in worker thread
        QTimer.singleShot(100, self._update_worker)

    def _update_worker(self):
        """Worker function for updating"""
        try:
            def progress_callback(progress, message):
                self.progress_bar.setValue(int(progress))
                self.progress_label.setText(message)
                if progress % 10 == 0:  # Log every 10%
                    self.log_message(message)
            
            result = self.updater.check_and_update(progress_callback)
            
            if result.success:
                self.log_message("更新成功完成!")
                self.progress_label.setText("更新完成")
                self.progress_bar.setValue(100)
            else:
                self.log_message(f"更新失败: {result.message}")
                self.progress_label.setText("更新失败")
                
        except Exception as e:
            self.log_message(f"更新过程出错: {e}")
            self.progress_label.setText("更新出错")
        finally:
            self.update_button.setEnabled(True)

    def start_zed(self):
        """Start Zed application"""
        self.log_message("启动Zed...")
        if self.updater.start_zed():
            self.log_message("Zed启动成功")
        else:
            self.log_message("Zed启动失败")

    def log_message(self, message):
        """Add message to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)


def main():
    """Main GUI entry point"""
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Zed Editor 自动更新程序")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("ZedUpdater")
        
        # Create and show main window
        window = SimpleUpdaterGUI()
        window.show()
        
        # Start application
        return app.exec_()
        
    except Exception as e:
        print(f"GUI启动错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())