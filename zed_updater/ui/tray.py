#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘模块
提供系统托盘图标和菜单功能
"""

import sys
import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject, Qt

from zed_updater.constants import APP_NAME, ICON_PATH, TRAY_MENU_ITEMS

logger = logging.getLogger(__name__)

class SystemTrayIcon(QSystemTrayIcon):
    """系统托盘图标类，提供托盘图标和右键菜单功能"""

    # 定义信号
    show_main_window = pyqtSignal()
    check_for_updates = pyqtSignal()
    start_update = pyqtSignal()
    start_zed = pyqtSignal()
    quit_application = pyqtSignal()

    def __init__(self, icon_path=None, parent=None):
        """初始化系统托盘图标

        Args:
            icon_path: 图标文件路径，如果为None则使用默认图标
            parent: 父窗口
        """
        # 加载图标
        if icon_path is None:
            try:
                icon = QIcon(str(ICON_PATH))
            except Exception as e:
                logger.warning(f"无法加载系统托盘图标: {e}")
                icon = QIcon()
        else:
            icon = QIcon(str(icon_path))

        super().__init__(icon, parent)

        # 设置工具提示
        self.setToolTip(APP_NAME)

        # 创建托盘菜单
        self.setup_menu()

        # 连接激活信号
        self.activated.connect(self.on_tray_icon_activated)

    def setup_menu(self):
        """设置托盘菜单"""
        # 创建菜单
        self.tray_menu = QMenu()

        # 添加菜单项
        self.show_action = QAction("显示主界面", self)
        self.check_action = QAction("检查更新", self)
        self.update_action = QAction("立即更新", self)
        self.start_zed_action = QAction("启动Zed", self)
        self.quit_action = QAction("退出", self)

        # 连接信号
        self.show_action.triggered.connect(self.show_main_window.emit)
        self.check_action.triggered.connect(self.check_for_updates.emit)
        self.update_action.triggered.connect(self.start_update.emit)
        self.start_zed_action.triggered.connect(self.start_zed.emit)
        self.quit_action.triggered.connect(self.quit_application.emit)

        # 添加到菜单
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.check_action)
        self.tray_menu.addAction(self.update_action)
        self.tray_menu.addAction(self.start_zed_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)

        # 设置为托盘菜单
        self.setContextMenu(self.tray_menu)

        logger.debug("系统托盘菜单已设置")

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件

        Args:
            reason: 激活原因
        """
        # 双击或点击时显示主窗口
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_main_window.emit()
            logger.debug("系统托盘图标被点击，显示主窗口")

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, timeout=5000):
        """显示托盘通知消息

        Args:
            title: 通知标题
            message: 通知内容
            icon: 通知图标类型
            timeout: 显示时间（毫秒）
        """
        try:
            self.showMessage(title, message, icon, timeout)
            logger.debug(f"显示系统通知: {title} - {message}")
        except Exception as e:
            logger.error(f"显示系统通知失败: {e}")

    def update_status(self, status_text):
        """更新托盘图标提示文本

        Args:
            status_text: 状态文本
        """
        self.setToolTip(f"{APP_NAME} - {status_text}")
        logger.debug(f"更新托盘状态: {status_text}")

    def set_update_available(self, available=True):
        """设置更新可用状态

        Args:
            available: 是否有更新可用
        """
        if available:
            self.update_action.setText("立即更新 (有新版本)")
            # 可以添加图标指示有更新
            # self.update_action.setIcon(QIcon("path/to/update_icon.png"))
        else:
            self.update_action.setText("立即更新")

def is_system_tray_available():
    """检查系统是否支持系统托盘

    Returns:
        bool: 是否支持系统托盘
    """
    return QSystemTrayIcon.isSystemTrayAvailable()
