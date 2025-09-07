#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形界面模块
提供用户友好的GUI界面管理Zed更新设置
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QTextEdit, QProgressBar, QTabWidget, QGroupBox,
    QFileDialog, QMessageBox, QSystemTrayIcon, QMenu, QAction,
    QTimeEdit, QListWidget, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QTime, QTextCodec
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QFontDatabase
import logging
import locale
import os

# UTF-8兼容性设置
if sys.platform == 'win32':
    # 确保Windows下的GUI文本显示使用UTF-8编码
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass

    # 设置环境变量确保UTF-8编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class UpdateWorker(QThread):
    """更新工作线程"""

    progress_updated = pyqtSignal(float, str)
    update_completed = pyqtSignal(bool, str)

    def __init__(self, updater):
        super().__init__()
        self.updater = updater

    def run(self):
        """执行更新"""
        try:
            def progress_callback(progress, message=""):
                self.progress_updated.emit(progress, message)

            success = self.updater.check_and_update(progress_callback)

            if success:
                self.update_completed.emit(True, "更新完成！")
            else:
                self.update_completed.emit(False, "没有可用更新或更新失败")

        except Exception as e:
            self.update_completed.emit(False, f"更新失败: {str(e)}")

class VersionCheckWorker(QThread):
    """版本检查工作线程"""

    version_checked = pyqtSignal(bool, dict)

    def __init__(self, updater):
        super().__init__()
        self.updater = updater

    def run(self):
        """检查版本"""
        try:
            current_version = self.updater.get_current_version()
            latest_info = self.updater.get_latest_version_info()

            if latest_info and current_version:
                has_update = self.updater.compare_versions(current_version, latest_info['version']) < 0
                version_data = {
                    'current': current_version,
                    'latest': latest_info['version'],
                    'download_url': latest_info.get('download_url'),
                    'release_notes': latest_info.get('body', '')
                }
                self.version_checked.emit(has_update, version_data)
            else:
                self.version_checked.emit(False, {
                    'current': current_version or '未知',
                    'latest': '无法获取',
                    'download_url': '',
                    'release_notes': ''
                })

        except Exception as e:
            logger.error(f"版本检查失败: {e}")
            self.version_checked.emit(False, {'error': str(e)})

class UpdaterGUI(QMainWindow):
    """主GUI窗口"""

    def __init__(self, updater, scheduler, config):
        super().__init__()
        self.updater = updater
        self.scheduler = scheduler
        self.config = config

        # 工作线程
        self.update_worker = None
        self.version_check_worker = None

        # 系统托盘
        self.tray_icon = None

        # 定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 每5秒更新一次状态

        self.init_ui()
        self.setup_tray_icon()
        self.load_settings()

        # 添加调度器回调
        self.scheduler.add_update_callback(self.on_update_available)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Zed Editor 自动更新程序")
        self.setGeometry(100, 100, 700, 600)

        # 设置应用程序字体，确保中文显示正常
        self.setup_fonts()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(self.tab_widget)

        # 创建各个选项卡
        self.create_main_tab()
        self.create_settings_tab()
        self.create_schedule_tab()
        self.create_advanced_tab()
        self.create_log_tab()

        # 状态栏
        self.statusBar().showMessage("就绪")

    def setup_fonts(self):
        """设置应用程序字体，确保UTF-8字符显示正常"""
        try:
            # 获取系统默认字体
            font = QFont()

            # Windows系统字体设置
            if sys.platform == 'win32':
                # 优先使用支持中文的字体
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
                for font_name in chinese_fonts:
                    try:
                        # PyQt5的正确方法是families()
                        available_fonts = QFontDatabase().families()
                        if font_name in available_fonts:
                            font.setFamily(font_name)
                            break
                    except (AttributeError, TypeError):
                        # 如果方法不兼容，使用退回策略
                        try:
                            font.setFamily(font_name)
                            break
                        except Exception:
                            continue
                else:
                    # 如果没有找到中文字体，使用系统默认
                    font.setFamily("Arial")

            # 设置字体大小
            font.setPointSize(9)
            font.setStyleHint(QFont.SansSerif)

            # 应用到整个应用程序
            QApplication.instance().setFont(font)

            # 设置文本编码
            try:
                codec = QTextCodec.codecForName("UTF-8")
                if codec:
                    QTextCodec.setCodecForLocale(codec)
            except:
                pass

            logger.info(f"字体设置完成: {font.family()}")

        except Exception as e:
            logger.warning(f"字体设置失败: {e}")

    def create_main_tab(self):
        """创建主界面选项卡"""
        main_tab = QWidget()
        self.tab_widget.addTab(main_tab, "主界面")

        layout = QVBoxLayout(main_tab)

        # 版本信息组
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

        # 操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout(button_group)

        self.check_button = QPushButton("检查更新")
        self.check_button.clicked.connect(self.check_for_updates)
        button_layout.addWidget(self.check_button)

        self.update_button = QPushButton("立即更新")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.setEnabled(False)
        button_layout.addWidget(self.update_button)

        self.start_zed_button = QPushButton("启动 Zed")
        self.start_zed_button.clicked.connect(self.start_zed)
        button_layout.addWidget(self.start_zed_button)

        layout.addWidget(button_group)

        # 进度条
        self.progress_group = QGroupBox("更新进度")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(self.progress_group)
        self.progress_group.hide()

        # 发布说明
        notes_group = QGroupBox("发布说明")
        notes_layout = QVBoxLayout(notes_group)

        self.release_notes = QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setMaximumHeight(200)
        notes_layout.addWidget(self.release_notes)

        layout.addWidget(notes_group)

        # 调度状态
        scheduler_group = QGroupBox("定时任务状态")
        scheduler_layout = QGridLayout(scheduler_group)

        scheduler_layout.addWidget(QLabel("状态:"), 0, 0)
        self.scheduler_status_label = QLabel("已停止")
        scheduler_layout.addWidget(self.scheduler_status_label, 0, 1)

        scheduler_layout.addWidget(QLabel("下次运行:"), 1, 0)
        self.next_run_label = QLabel("未设置")
        scheduler_layout.addWidget(self.next_run_label, 1, 1)

        self.toggle_scheduler_button = QPushButton("启动调度")
        self.toggle_scheduler_button.clicked.connect(self.toggle_scheduler)
        scheduler_layout.addWidget(self.toggle_scheduler_button, 2, 0, 1, 2)

        layout.addWidget(scheduler_group)

        layout.addStretch()

    def create_settings_tab(self):
        """创建设置选项卡"""
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "基本设置")

        scroll_area = QVBoxLayout(settings_tab)

        # Zed安装路径
        path_group = QGroupBox("Zed安装路径")
        path_layout = QHBoxLayout(path_group)

        self.zed_path_edit = QLineEdit()
        path_layout.addWidget(self.zed_path_edit)

        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_zed_path)
        path_layout.addWidget(browse_button)

        scroll_area.addWidget(path_group)

        # 自动更新设置
        auto_group = QGroupBox("自动更新设置")
        auto_layout = QGridLayout(auto_group)

        self.auto_check_cb = QCheckBox("启用自动检查")
        auto_layout.addWidget(self.auto_check_cb, 0, 0, 1, 2)

        auto_layout.addWidget(QLabel("检查间隔(小时):"), 1, 0)
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setMinimum(1)
        self.check_interval_spin.setMaximum(168)  # 一周
        auto_layout.addWidget(self.check_interval_spin, 1, 1)

        self.startup_check_cb = QCheckBox("启动时检查更新")
        auto_layout.addWidget(self.startup_check_cb, 2, 0, 1, 2)

        self.auto_download_cb = QCheckBox("自动下载更新")
        auto_layout.addWidget(self.auto_download_cb, 3, 0, 1, 2)

        self.auto_install_cb = QCheckBox("自动安装更新(需谨慎)")
        auto_layout.addWidget(self.auto_install_cb, 4, 0, 1, 2)

        self.auto_start_cb = QCheckBox("更新后自动启动Zed")
        auto_layout.addWidget(self.auto_start_cb, 5, 0, 1, 2)

        scroll_area.addWidget(auto_group)

        # 备份设置
        backup_group = QGroupBox("备份设置")
        backup_layout = QGridLayout(backup_group)

        self.backup_enabled_cb = QCheckBox("启用备份")
        backup_layout.addWidget(self.backup_enabled_cb, 0, 0, 1, 2)

        backup_layout.addWidget(QLabel("保留备份数量:"), 1, 0)
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setMinimum(0)
        self.backup_count_spin.setMaximum(10)
        backup_layout.addWidget(self.backup_count_spin, 1, 1)

        scroll_area.addWidget(backup_group)

        # 通知设置
        notify_group = QGroupBox("通知设置")
        notify_layout = QGridLayout(notify_group)

        self.show_notifications_cb = QCheckBox("显示通知")
        notify_layout.addWidget(self.show_notifications_cb, 0, 0, 1, 2)

        self.notify_update_available_cb = QCheckBox("有更新时通知")
        notify_layout.addWidget(self.notify_update_available_cb, 1, 0, 1, 2)

        self.notify_update_complete_cb = QCheckBox("更新完成时通知")
        notify_layout.addWidget(self.notify_update_complete_cb, 2, 0, 1, 2)

        scroll_area.addWidget(notify_group)

        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QGridLayout(ui_group)

        self.minimize_to_tray_cb = QCheckBox("最小化到托盘")
        ui_layout.addWidget(self.minimize_to_tray_cb, 0, 0, 1, 2)

        self.start_with_system_cb = QCheckBox("开机自启动")
        ui_layout.addWidget(self.start_with_system_cb, 1, 0, 1, 2)

        scroll_area.addWidget(ui_group)

        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        scroll_area.addWidget(save_button)

        scroll_area.addStretch()

    def create_schedule_tab(self):
        """创建定时任务选项卡"""
        schedule_tab = QWidget()
        self.tab_widget.addTab(schedule_tab, "定时设置")

        layout = QVBoxLayout(schedule_tab)

        # 定时任务设置
        schedule_group = QGroupBox("定时任务设置")
        schedule_layout = QGridLayout(schedule_group)

        self.scheduled_update_cb = QCheckBox("启用定时更新")
        schedule_layout.addWidget(self.scheduled_update_cb, 0, 0, 1, 2)

        schedule_layout.addWidget(QLabel("执行时间:"), 1, 0)
        self.scheduled_time_edit = QTimeEdit()
        self.scheduled_time_edit.setTime(QTime(2, 0))  # 默认凌晨2点
        schedule_layout.addWidget(self.scheduled_time_edit, 1, 1)

        schedule_layout.addWidget(QLabel("执行天数:"), 2, 0)

        # 星期选择
        days_widget = QWidget()
        days_layout = QHBoxLayout(days_widget)

        self.day_checkboxes = []
        day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for i, day_name in enumerate(day_names):
            cb = QCheckBox(day_name)
            if i < 5:  # 默认选中工作日
                cb.setChecked(True)
            self.day_checkboxes.append(cb)
            days_layout.addWidget(cb)

        schedule_layout.addWidget(days_widget, 3, 0, 1, 2)

        layout.addWidget(schedule_group)

        # 任务状态
        status_group = QGroupBox("任务状态")
        status_layout = QGridLayout(status_group)

        status_layout.addWidget(QLabel("调度器状态:"), 0, 0)
        self.scheduler_running_label = QLabel("未知")
        status_layout.addWidget(self.scheduler_running_label, 0, 1)

        status_layout.addWidget(QLabel("任务数量:"), 1, 0)
        self.jobs_count_label = QLabel("0")
        status_layout.addWidget(self.jobs_count_label, 1, 1)

        status_layout.addWidget(QLabel("下次执行:"), 2, 0)
        self.next_execution_label = QLabel("未设置")
        status_layout.addWidget(self.next_execution_label, 2, 1)

        layout.addWidget(status_group)

        # 控制按钮
        control_layout = QHBoxLayout()

        self.start_scheduler_button = QPushButton("启动调度器")
        self.start_scheduler_button.clicked.connect(self.start_scheduler)
        control_layout.addWidget(self.start_scheduler_button)

        self.stop_scheduler_button = QPushButton("停止调度器")
        self.stop_scheduler_button.clicked.connect(self.stop_scheduler)
        control_layout.addWidget(self.stop_scheduler_button)

        self.restart_scheduler_button = QPushButton("重启调度器")
        self.restart_scheduler_button.clicked.connect(self.restart_scheduler)
        control_layout.addWidget(self.restart_scheduler_button)

        layout.addLayout(control_layout)

        # 保存定时设置按钮
        save_schedule_button = QPushButton("保存定时设置")
        save_schedule_button.clicked.connect(self.save_schedule_settings)
        layout.addWidget(save_schedule_button)

        layout.addStretch()

    def create_advanced_tab(self):
        """创建高级设置选项卡"""
        advanced_tab = QWidget()
        self.tab_widget.addTab(advanced_tab, "高级设置")

        layout = QVBoxLayout(advanced_tab)

        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QGridLayout(network_group)

        network_layout.addWidget(QLabel("下载超时(秒):"), 0, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(30)
        self.timeout_spin.setMaximum(600)
        network_layout.addWidget(self.timeout_spin, 0, 1)

        network_layout.addWidget(QLabel("重试次数:"), 1, 0)
        self.retry_spin = QSpinBox()
        self.retry_spin.setMinimum(0)
        self.retry_spin.setMaximum(10)
        network_layout.addWidget(self.retry_spin, 1, 1)

        self.use_proxy_cb = QCheckBox("使用代理")
        network_layout.addWidget(self.use_proxy_cb, 2, 0, 1, 2)

        network_layout.addWidget(QLabel("代理地址:"), 3, 0)
        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("http://proxy.example.com:8080")
        network_layout.addWidget(self.proxy_edit, 3, 1)

        layout.addWidget(network_group)

        # GitHub设置
        github_group = QGroupBox("GitHub设置")
        github_layout = QGridLayout(github_group)

        github_layout.addWidget(QLabel("仓库:"), 0, 0)
        self.github_repo_edit = QLineEdit()
        github_layout.addWidget(self.github_repo_edit, 0, 1)

        github_layout.addWidget(QLabel("API地址:"), 1, 0)
        self.github_api_edit = QLineEdit()
        github_layout.addWidget(self.github_api_edit, 1, 1)

        layout.addWidget(github_group)

        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QGridLayout(log_group)

        log_layout.addWidget(QLabel("日志级别:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        log_layout.addWidget(self.log_level_combo, 0, 1)

        layout.addWidget(log_group)

        # 清理按钮
        cleanup_group = QGroupBox("清理")
        cleanup_layout = QHBoxLayout(cleanup_group)

        clear_temp_button = QPushButton("清理临时文件")
        clear_temp_button.clicked.connect(self.clear_temp_files)
        cleanup_layout.addWidget(clear_temp_button)

        clear_backups_button = QPushButton("清理备份文件")
        clear_backups_button.clicked.connect(self.clear_backups)
        cleanup_layout.addWidget(clear_backups_button)

        reset_config_button = QPushButton("重置配置")
        reset_config_button.clicked.connect(self.reset_config)
        cleanup_layout.addWidget(reset_config_button)

        layout.addWidget(cleanup_group)

        # 保存高级设置按钮
        save_advanced_button = QPushButton("保存高级设置")
        save_advanced_button.clicked.connect(self.save_advanced_settings)
        layout.addWidget(save_advanced_button)

        layout.addStretch()

    def create_log_tab(self):
        """创建日志选项卡"""
        log_tab = QWidget()
        self.tab_widget.addTab(log_tab, "日志")

        layout = QVBoxLayout(log_tab)

        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)

        # 设置等宽字体，确保中文字符正常显示
        log_font = QFont()
        if sys.platform == 'win32':
            # Windows下优先使用支持中文的等宽字体
            monospace_fonts = ['Consolas', 'Courier New', 'SimSun', 'Microsoft YaHei']
            for font_name in monospace_fonts:
                try:
                    # 使用PyQt5兼容的families()方法
                    available_fonts = QFontDatabase.families()
                    if font_name in available_fonts:
                        log_font.setFamily(font_name)
                        break
                except (AttributeError, TypeError):
                    # 如果方法不存在，使用默认策略
                    try:
                        log_font.setFamily(font_name)
                        break
                    except Exception:
                        continue
        else:
            log_font.setFamily("monospace")

        log_font.setPointSize(9)
        log_font.setFixedPitch(True)
        self.log_display.setFont(log_font)

        layout.addWidget(self.log_display)

        # 日志控制
        log_control_layout = QHBoxLayout()

        clear_log_button = QPushButton("清空日志")
        clear_log_button.clicked.connect(self.clear_log_display)
        log_control_layout.addWidget(clear_log_button)

        refresh_log_button = QPushButton("刷新日志")
        refresh_log_button.clicked.connect(self.refresh_log_display)
        log_control_layout.addWidget(refresh_log_button)

        save_log_button = QPushButton("保存日志")
        save_log_button.clicked.connect(self.save_log)
        log_control_layout.addWidget(save_log_button)

        log_control_layout.addStretch()

        layout.addLayout(log_control_layout)

        # 定时刷新日志
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_log_display)
        self.log_timer.start(5000)  # 每5秒刷新一次

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)

                # 使用默认图标或自定义图标
                icon = self.style().standardIcon(self.style().SP_ComputerIcon)
                self.tray_icon.setIcon(icon)

                # 创建托盘菜单
                tray_menu = QMenu()

                show_action = QAction("显示主窗口", self)
                show_action.triggered.connect(self.show_window)
                tray_menu.addAction(show_action)

                check_action = QAction("检查更新", self)
                check_action.triggered.connect(self.check_for_updates)
                tray_menu.addAction(check_action)

                tray_menu.addSeparator()

                quit_action = QAction("退出", self)
                quit_action.triggered.connect(self.quit_app)
                tray_menu.addAction(quit_action)

                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.tray_icon_activated)

                self.tray_icon.show()

        except Exception as e:
            logger.error(f"设置系统托盘失败: {e}")

    def tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.config.get_setting('minimize_to_tray', True) and self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
            if self.config.get_setting('show_notifications', True):
                self.tray_icon.showMessage(
                    "Zed Updater",
                    "应用程序已最小化到托盘",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            event.accept()

    def quit_app(self):
        """退出应用程序"""
        self.scheduler.stop()
        QApplication.quit()

    def load_settings(self):
        """加载设置到界面"""
        try:
            # 基本设置
            self.zed_path_edit.setText(self.config.get_setting('zed_install_path', ''))
            self.auto_check_cb.setChecked(self.config.get_setting('auto_check_enabled', True))
            self.check_interval_spin.setValue(self.config.get_setting('check_interval_hours', 24))
            self.startup_check_cb.setChecked(self.config.get_setting('check_on_startup', True))
            self.auto_download_cb.setChecked(self.config.get_setting('auto_download', True))
            self.auto_install_cb.setChecked(self.config.get_setting('auto_install', False))
            self.auto_start_cb.setChecked(self.config.get_setting('auto_start_after_update', True))

            # 备份设置
            self.backup_enabled_cb.setChecked(self.config.get_setting('backup_enabled', True))
            self.backup_count_spin.setValue(self.config.get_setting('backup_count', 3))

            # 通知设置
            self.show_notifications_cb.setChecked(self.config.get_setting('show_notifications', True))
            self.notify_update_available_cb.setChecked(self.config.get_setting('notify_on_update_available', True))
            self.notify_update_complete_cb.setChecked(self.config.get_setting('notify_on_update_complete', True))

            # 界面设置
            self.minimize_to_tray_cb.setChecked(self.config.get_setting('minimize_to_tray', True))
            self.start_with_system_cb.setChecked(self.config.get_setting('start_with_system', False))

            # 定时设置
            self.scheduled_update_cb.setChecked(self.config.get_setting('scheduled_update_enabled', False))
            scheduled_time = self.config.get_setting('scheduled_time', '02:00')
            hour, minute = scheduled_time.split(':')
            self.scheduled_time_edit.setTime(QTime(int(hour), int(minute)))

            scheduled_days = self.config.get_setting('scheduled_days', [0, 1, 2, 3, 4])
            for i, cb in enumerate(self.day_checkboxes):
                cb.setChecked(i in scheduled_days)

            # 高级设置
            self.timeout_spin.setValue(self.config.get_setting('download_timeout', 300))
            self.retry_spin.setValue(self.config.get_setting('retry_count', 3))
            self.use_proxy_cb.setChecked(self.config.get_setting('use_proxy', False))
            self.proxy_edit.setText(self.config.get_setting('proxy_url', ''))
            self.github_repo_edit.setText(self.config.get_setting('github_repo', 'zed-industries/zed'))
            self.github_api_edit.setText(self.config.get_setting('github_api_url', ''))

            log_level = self.config.get_setting('log_level', 'INFO')
            index = self.log_level_combo.findText(log_level)
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)

            # 初始检查更新
            self.check_for_updates()

        except Exception as e:
            logger.error(f"加载设置失败: {e}")

    def save_settings(self):
        """保存基本设置"""
        try:
            settings = {
                'zed_install_path': self.zed_path_edit.text(),
                'auto_check_enabled': self.auto_check_cb.isChecked(),
                'check_interval_hours': self.check_interval_spin.value(),
                'check_on_startup': self.startup_check_cb.isChecked(),
                'auto_download': self.auto_download_cb.isChecked(),
                'auto_install': self.auto_install_cb.isChecked(),
                'auto_start_after_update': self.auto_start_cb.isChecked(),
                'backup_enabled': self.backup_enabled_cb.isChecked(),
                'backup_count': self.backup_count_spin.value(),
                'show_notifications': self.show_notifications_cb.isChecked(),
                'notify_on_update_available': self.notify_update_available_cb.isChecked(),
                'notify_on_update_complete': self.notify_update_complete_cb.isChecked(),
                'minimize_to_tray': self.minimize_to_tray_cb.isChecked(),
                'start_with_system': self.start_with_system_cb.isChecked()
            }

            self.config.update_settings(settings)

            # 验证配置
            errors = self.config.validate_config()
            if errors:
                error_msg = "配置验证失败:\n" + "\n".join([f"- {key}: {msg}" for key, msg in errors.items()])
                QMessageBox.warning(self, "配置错误", error_msg)
            else:
                QMessageBox.information(self, "保存成功", "设置已保存")
                # 重启调度器应用新设置
                if self.scheduler.is_scheduler_running():
                    self.scheduler.update_schedule_config()

        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {str(e)}")

    def save_schedule_settings(self):
        """保存定时设置"""
        try:
            scheduled_time = self.scheduled_time_edit.time().toString("hh:mm")
            scheduled_days = [i for i, cb in enumerate(self.day_checkboxes) if cb.isChecked()]

            settings = {
                'scheduled_update_enabled': self.scheduled_update_cb.isChecked(),
                'scheduled_time': scheduled_time,
                'scheduled_days': scheduled_days
            }

            self.config.update_settings(settings)
            QMessageBox.information(self, "保存成功", "定时设置已保存")

            # 重启调度器应用新设置
            if self.scheduler.is_scheduler_running():
                self.scheduler.update_schedule_config()

        except Exception as e:
            logger.error(f"保存定时设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存定时设置时出错: {str(e)}")

    def save_advanced_settings(self):
        """保存高级设置"""
        try:
            settings = {
                'download_timeout': self.timeout_spin.value(),
                'retry_count': self.retry_spin.value(),
                'use_proxy': self.use_proxy_cb.isChecked(),
                'proxy_url': self.proxy_edit.text(),
                'github_repo': self.github_repo_edit.text(),
                'github_api_url': self.github_api_edit.text(),
                'log_level': self.log_level_combo.currentText()
            }

            self.config.update_settings(settings)
            QMessageBox.information(self, "保存成功", "高级设置已保存")

        except Exception as e:
            logger.error(f"保存高级设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存高级设置时出错: {str(e)}")

    def browse_zed_path(self):
        """浏览Zed安装路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Zed.exe", "", "可执行文件 (*.exe)"
        )
        if file_path:
            self.zed_path_edit.setText(file_path)

    def check_for_updates(self):
        """检查更新"""
        try:
            self.check_button.setEnabled(False)
            self.check_button.setText("检查中...")

            # 启动版本检查线程
            self.version_check_worker = VersionCheckWorker(self.updater)
            self.version_check_worker.version_checked.connect(self.on_version_checked)
            self.version_check_worker.start()

        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            self.check_button.setEnabled(True)
            self.check_button.setText("检查更新")

    def on_version_checked(self, has_update, version_data):
        """版本检查完成回调"""
        try:
            self.check_button.setEnabled(True)
            self.check_button.setText("检查更新")

            if 'error' in version_data:
                self.current_version_label.setText("检查失败")
                self.latest_version_label.setText("检查失败")
                QMessageBox.warning(self, "检查失败", f"检查更新时出错: {version_data['error']}")
                return

            self.current_version_label.setText(version_data.get('current', '未知'))
            self.latest_version_label.setText(version_data.get('latest', '未知'))

            # 更新发布说明
            release_notes = version_data.get('release_notes', '')
            if release_notes:
                self.release_notes.setText(release_notes)
            else:
                self.release_notes.setText("暂无发布说明")

            # 更新最后检查时间
            self.last_check_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            if has_update:
                self.update_button.setEnabled(True)
                if self.config.get_setting('show_notifications', True):
                    if self.tray_icon:
                        self.tray_icon.showMessage(
                            "Zed更新可用",
                            f"发现新版本: {version_data['latest']}",
                            QSystemTrayIcon.Information,
                            5000
                        )
                QMessageBox.information(
                    self, "更新可用",
                    f"发现新版本: {version_data['latest']}\n当前版本: {version_data['current']}"
                )
            else:
                self.update_button.setEnabled(False)
                QMessageBox.information(self, "无更新", "您已使用最新版本")

        except Exception as e:
            logger.error(f"处理版本检查结果失败: {e}")

    def start_update(self):
        """开始更新"""
        try:
            # 显示进度组
            self.progress_group.show()
            self.progress_bar.setValue(0)
            self.progress_label.setText("准备更新...")

            # 禁用按钮
            self.update_button.setEnabled(False)
            self.check_button.setEnabled(False)

            # 启动更新线程
            self.update_worker = UpdateWorker(self.updater)
            self.update_worker.progress_updated.connect(self.on_update_progress)
            self.update_worker.update_completed.connect(self.on_update_completed)
            self.update_worker.start()

        except Exception as e:
            logger.error(f"启动更新失败: {e}")
            QMessageBox.critical(self, "更新失败", f"启动更新时出错: {str(e)}")

    def on_update_progress(self, progress, message):
        """更新进度回调"""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)

    def on_update_completed(self, success, message):
        """更新完成回调"""
        try:
            # 隐藏进度组
            self.progress_group.hide()

            # 恢复按钮状态
            self.update_button.setEnabled(False)
            self.check_button.setEnabled(True)

            if success:
                if self.config.get_setting('show_notifications', True):
                    if self.tray_icon:
                        self.tray_icon.showMessage(
                            "Zed更新完成",
                            "更新已成功安装",
                            QSystemTrayIcon.Information,
                            5000
                        )

                # 询问是否启动Zed
                reply = QMessageBox.question(
                    self, "更新完成",
                    f"{message}\n是否现在启动Zed?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.start_zed()

                # 重新检查版本
                self.check_for_updates()
            else:
                QMessageBox.warning(self, "更新失败", message)

        except Exception as e:
            logger.error(f"处理更新完成事件失败: {e}")

    def start_zed(self):
        """启动Zed"""
        try:
            if self.updater.start_zed():
                self.statusBar().showMessage("Zed已启动", 3000)
            else:
                QMessageBox.warning(self, "启动失败", "无法启动Zed，请检查安装路径")

        except Exception as e:
            logger.error(f"启动Zed失败: {e}")
            QMessageBox.critical(self, "启动失败", f"启动Zed时出错: {str(e)}")

    def toggle_scheduler(self):
        """切换调度器状态"""
        if self.scheduler.is_scheduler_running():
            self.stop_scheduler()
        else:
            self.start_scheduler()

    def start_scheduler(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            self.toggle_scheduler_button.setText("停止调度")
            self.statusBar().showMessage("调度器已启动", 3000)

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            QMessageBox.critical(self, "启动失败", f"启动调度器时出错: {str(e)}")

    def stop_scheduler(self):
        """停止调度器"""
        try:
            self.scheduler.stop()
            self.toggle_scheduler_button.setText("启动调度")
            self.statusBar().showMessage("调度器已停止", 3000)

        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            QMessageBox.critical(self, "停止失败", f"停止调度器时出错: {str(e)}")

    def restart_scheduler(self):
        """重启调度器"""
        try:
            self.scheduler.restart()
            self.statusBar().showMessage("调度器已重启", 3000)

        except Exception as e:
            logger.error(f"重启调度器失败: {e}")
            QMessageBox.critical(self, "重启失败", f"重启调度器时出错: {str(e)}")

    def update_status(self):
        """更新状态显示"""
        try:
            # 更新调度器状态
            if self.scheduler.is_scheduler_running():
                self.scheduler_status_label.setText("运行中")
                self.toggle_scheduler_button.setText("停止调度")
                self.scheduler_running_label.setText("运行中")

                # 获取下次运行时间
                next_run = self.scheduler.get_next_run_time()
                if next_run:
                    next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                    self.next_run_label.setText(next_run_str)
                    self.next_execution_label.setText(next_run_str)
                else:
                    self.next_run_label.setText("未设置")
                    self.next_execution_label.setText("未设置")
            else:
                self.scheduler_status_label.setText("已停止")
                self.toggle_scheduler_button.setText("启动调度")
                self.scheduler_running_label.setText("已停止")
                self.next_run_label.setText("未启动")
                self.next_execution_label.setText("未启动")

            # 更新任务数量
            status = self.scheduler.get_schedule_status()
            self.jobs_count_label.setText(str(status.get('jobs_count', 0)))

            # 更新最后检查时间
            last_check = self.config.get_setting('last_check_time')
            if last_check:
                try:
                    dt = datetime.fromisoformat(last_check)
                    self.last_check_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
                except:
                    pass

        except Exception as e:
            logger.error(f"更新状态显示失败: {e}")

    def on_update_available(self, update_available, version_info):
        """更新可用回调"""
        if update_available and self.config.get_setting('notify_on_update_available', True):
            if self.tray_icon and self.config.get_setting('show_notifications', True):
                self.tray_icon.showMessage(
                    "Zed更新可用",
                    f"发现新版本: {version_info.get('version', '未知')}",
                    QSystemTrayIcon.Information,
                    10000
                )

    def clear_temp_files(self):
        """清理临时文件"""
        try:
            self.updater.cleanup_temp_files()
            QMessageBox.information(self, "清理完成", "临时文件已清理")

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            QMessageBox.critical(self, "清理失败", f"清理临时文件时出错: {str(e)}")

    def clear_backups(self):
        """清理备份文件"""
        try:
            backup_dir = self.config.get_backup_dir()
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
                QMessageBox.information(self, "清理完成", "备份文件已清理")
            else:
                QMessageBox.information(self, "无需清理", "没有找到备份文件")

        except Exception as e:
            logger.error(f"清理备份文件失败: {e}")
            QMessageBox.critical(self, "清理失败", f"清理备份文件时出错: {str(e)}")

    def reset_config(self):
        """重置配置"""
        try:
            reply = QMessageBox.question(
                self, "确认重置",
                "确定要重置所有配置到默认值吗？这将清除所有自定义设置。",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.config.reset_to_default()
                self.load_settings()
                QMessageBox.information(self, "重置完成", "配置已重置为默认值")

        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            QMessageBox.critical(self, "重置失败", f"重置配置时出错: {str(e)}")

    def refresh_log_display(self):
        """刷新日志显示"""
        try:
            log_file = Path('zed_updater.log')
            if log_file.exists():
                # 尝试多种编码格式读取日志文件
                encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', locale.getpreferredencoding()]
                content = None

                for encoding in encodings:
                    try:
                        with open(log_file, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        break

                if content is None:
                    # 如果所有编码都失败，使用二进制模式读取并处理错误字符
                    with open(log_file, 'rb') as f:
                        raw_content = f.read()
                        content = raw_content.decode('utf-8', errors='replace')

                if content:
                    # 只显示最后1000行
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        lines = lines[-1000:]
                        content = '\n'.join(lines)

                    self.log_display.setText(content)
                    # 滚动到底部
                    self.log_display.moveCursor(self.log_display.textCursor().End)

        except Exception as e:
            logger.error(f"刷新日志失败: {e}")

    def clear_log_display(self):
        """清空日志显示"""
        self.log_display.clear()

    def save_log(self):
        """保存日志到文件"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存日志", f"zed_updater_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt)"
            )

            if file_path:
                # 使用UTF-8 BOM格式保存，确保Windows记事本能正确显示中文
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(self.log_display.toPlainText())
                QMessageBox.information(self, "保存成功", f"日志已保存到: {file_path}")

        except Exception as e:
            logger.error(f"保存日志失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存日志时出错: {str(e)}")
