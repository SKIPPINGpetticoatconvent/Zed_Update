#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System tray icon component for Zed Updater
"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

from ..utils.logger import get_logger


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu"""

    show_window_requested = pyqtSignal()
    check_updates_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)

        self.init_tray_icon()
        self.create_context_menu()

    def init_tray_icon(self):
        """Initialize the system tray icon"""
        try:
            # Try to set a proper icon (you may want to add actual icon files)
            self.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

            # Set tooltip
            self.setToolTip("Zed Editor 自动更新程序")

            self.logger.debug("System tray icon initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize tray icon: {e}")

    def create_context_menu(self):
        """Create the context menu for the tray icon"""
        try:
            tray_menu = QMenu()

            # Show window action
            show_action = QAction("显示窗口(&S)", self)
            show_action.triggered.connect(self.show_window_requested.emit)
            tray_menu.addAction(show_action)

            # Check updates action
            check_action = QAction("检查更新(&C)", self)
            check_action.triggered.connect(self.check_updates_requested.emit)
            tray_menu.addAction(check_action)

            tray_menu.addSeparator()

            # Quit action
            quit_action = QAction("退出(&X)", self)
            quit_action.triggered.connect(self.quit_requested.emit)
            tray_menu.addAction(quit_action)

            self.setContextMenu(tray_menu)
            self.logger.debug("Tray context menu created")

        except Exception as e:
            self.logger.error(f"Failed to create tray menu: {e}")

    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, timeout=5000):
        """Show a tray notification message"""
        try:
            self.showMessage(title, message, icon, timeout)
        except Exception as e:
            self.logger.error(f"Failed to show tray message: {e}")

    def show_update_available(self, version: str):
        """Show update available notification"""
        self.show_message(
            "Zed 更新可用",
            f"发现新版本 {version}",
            QSystemTrayIcon.Information
        )

    def show_update_completed(self, version: str):
        """Show update completed notification"""
        self.show_message(
            "Zed 更新完成",
            f"已成功更新到版本 {version}",
            QSystemTrayIcon.Information
        )

    def show_update_failed(self, error: str):
        """Show update failed notification"""
        self.show_message(
            "Zed 更新失败",
            f"更新失败: {error}",
            QSystemTrayIcon.Critical
        )

    def show_backup_completed(self, path: str):
        """Show backup completed notification"""
        self.show_message(
            "Zed 备份完成",
            "备份已保存",
            QSystemTrayIcon.Information
        )