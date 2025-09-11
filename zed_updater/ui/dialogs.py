#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框模块
提供各种应用对话框
"""

import logging
import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QCheckBox, QTabWidget, QWidget,
    QFormLayout, QSpinBox, QLineEdit, QMessageBox, QFileDialog,
    QDialogButtonBox, QComboBox, QGroupBox, QGridLayout, QTimeEdit
)
from PyQt5.QtCore import Qt, QTime, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

from zed_updater.constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION, APP_WEBSITE

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    """关于对话框，显示应用程序信息"""

    def __init__(self, parent=None):
        """初始化关于对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("关于 " + APP_NAME)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()

        # 应用标题
        title_label = QLabel(APP_NAME)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本信息
        version_label = QLabel(f"版本: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 作者信息
        author_label = QLabel(f"作者: {APP_AUTHOR}")
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        # 应用描述
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 添加分隔
        layout.addSpacing(10)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        layout.addSpacing(10)

        # 功能简介
        features_label = QLabel("主要功能:")
        features_font = features_label.font()
        features_font.setBold(True)
        features_label.setFont(features_font)
        layout.addWidget(features_label)

        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setHtml("""
        <ul>
            <li>自动检查 Zed 编辑器的最新版本</li>
            <li>智能下载适合系统的安装包</li>
            <li>安全更新，自动备份旧版本</li>
            <li>支持定时检查和更新</li>
            <li>系统托盘集成，后台运行</li>
            <li>开机自启动支持</li>
        </ul>
        """)
        features_text.setMaximumHeight(120)
        layout.addWidget(features_text)

        # 网站链接
        website_button = QPushButton("访问官方网站")
        website_button.clicked.connect(lambda: webbrowser.open(APP_WEBSITE))
        layout.addWidget(website_button)

        # 底部按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


class SettingsDialog(QDialog):
    """设置对话框，用于配置应用参数"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, config, parent=None):
        """初始化设置对话框

        Args:
            config: 配置管理器实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.config = config
        self.settings = config.get_all_settings()

        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 基本设置标签
        self.basic_tab = QWidget()
        self.setup_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本设置")

        # 计划任务标签
        self.schedule_tab = QWidget()
        self.setup_schedule_tab()
        self.tab_widget.addTab(self.schedule_tab, "计划任务")

        # 高级设置标签
        self.advanced_tab = QWidget()
        self.setup_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级设置")

        layout.addWidget(self.tab_widget)

        # 底部按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def setup_basic_tab(self):
        """设置基本标签页"""
        layout = QVBoxLayout()

        # Zed安装路径
        path_group = QGroupBox("Zed安装路径")
        path_layout = QHBoxLayout()

        self.zed_path_edit = QLineEdit()
        self.zed_path_edit.setReadOnly(True)

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_zed_path)

        path_layout.addWidget(self.zed_path_edit)
        path_layout.addWidget(browse_button)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 自动更新选项
        update_group = QGroupBox("自动更新选项")
        update_layout = QVBoxLayout()

        self.auto_check_cb = QCheckBox("启用自动检查更新")
        self.check_startup_cb = QCheckBox("启动时检查更新")
        self.auto_download_cb = QCheckBox("发现更新时自动下载")
        self.auto_install_cb = QCheckBox("下载完成后自动安装 (谨慎使用)")
        self.force_download_cb = QCheckBox("总是下载最新版本 (不检查版本号)")

        check_interval_layout = QHBoxLayout()
        check_interval_layout.addWidget(QLabel("检查间隔:"))
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setMinimum(1)
        self.check_interval_spin.setMaximum(168)  # 一周
        self.check_interval_spin.setSuffix(" 小时")
        check_interval_layout.addWidget(self.check_interval_spin)
        check_interval_layout.addStretch()

        update_layout.addWidget(self.auto_check_cb)
        update_layout.addWidget(self.check_startup_cb)
        update_layout.addLayout(check_interval_layout)
        update_layout.addWidget(self.auto_download_cb)
        update_layout.addWidget(self.auto_install_cb)
        update_layout.addWidget(self.force_download_cb)

        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # 启动选项
        startup_group = QGroupBox("启动选项")
        startup_layout = QVBoxLayout()

        self.start_with_system_cb = QCheckBox("开机自动启动")
        self.start_minimized_cb = QCheckBox("启动时最小化到系统托盘")
        self.minimize_to_tray_cb = QCheckBox("关闭窗口时最小化到系统托盘")
        self.auto_start_after_update_cb = QCheckBox("更新完成后自动启动Zed")

        startup_layout.addWidget(self.start_with_system_cb)
        startup_layout.addWidget(self.start_minimized_cb)
        startup_layout.addWidget(self.minimize_to_tray_cb)
        startup_layout.addWidget(self.auto_start_after_update_cb)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()
        self.basic_tab.setLayout(layout)

    def setup_schedule_tab(self):
        """设置计划任务标签页"""
        layout = QVBoxLayout()

        # 定时更新选项
        schedule_group = QGroupBox("定时更新")
        schedule_layout = QVBoxLayout()

        self.scheduled_update_cb = QCheckBox("启用定时更新")

        # 执行时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("执行时间:"))
        self.scheduled_time_edit = QTimeEdit()
        self.scheduled_time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.scheduled_time_edit)
        time_layout.addStretch()

        # 执行天数
        days_group = QGroupBox("执行天数")
        days_layout = QGridLayout()

        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(days):
            cb = QCheckBox(day)
            self.day_checkboxes.append(cb)
            days_layout.addWidget(cb, i // 4, i % 4)

        days_group.setLayout(days_layout)

        schedule_layout.addWidget(self.scheduled_update_cb)
        schedule_layout.addLayout(time_layout)
        schedule_layout.addWidget(days_group)

        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        # 通知选项
        notification_group = QGroupBox("通知选项")
        notification_layout = QVBoxLayout()

        self.show_notifications_cb = QCheckBox("显示系统通知")
        self.notify_on_update_available_cb = QCheckBox("有可用更新时通知")
        self.notify_on_update_complete_cb = QCheckBox("更新完成时通知")

        notification_layout.addWidget(self.show_notifications_cb)
        notification_layout.addWidget(self.notify_on_update_available_cb)
        notification_layout.addWidget(self.notify_on_update_complete_cb)

        notification_group.setLayout(notification_layout)
        layout.addWidget(notification_group)

        layout.addStretch()
        self.schedule_tab.setLayout(layout)

    def setup_advanced_tab(self):
        """设置高级标签页"""
        layout = QVBoxLayout()

        # 备份选项
        backup_group = QGroupBox("备份选项")
        backup_layout = QHBoxLayout()

        self.backup_enabled_cb = QCheckBox("启用备份")
        backup_layout.addWidget(self.backup_enabled_cb)

        backup_layout.addWidget(QLabel("保留备份数量:"))
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setMinimum(1)
        self.backup_count_spin.setMaximum(10)
        backup_layout.addWidget(self.backup_count_spin)
        backup_layout.addStretch()

        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # 代理设置
        proxy_group = QGroupBox("网络代理")
        proxy_layout = QVBoxLayout()

        self.use_proxy_cb = QCheckBox("使用代理")

        proxy_url_layout = QHBoxLayout()
        proxy_url_layout.addWidget(QLabel("代理URL:"))
        self.proxy_url_edit = QLineEdit()
        self.proxy_url_edit.setPlaceholderText("例如: http://127.0.0.1:7890")
        proxy_url_layout.addWidget(self.proxy_url_edit)

        proxy_layout.addWidget(self.use_proxy_cb)
        proxy_layout.addLayout(proxy_url_layout)

        proxy_group.setLayout(proxy_layout)
        layout.addWidget(proxy_group)

        # GitHub设置
        github_group = QGroupBox("GitHub设置")
        github_layout = QFormLayout()

        self.github_repo_edit = QLineEdit()
        self.github_api_url_edit = QLineEdit()

        github_layout.addRow("仓库:", self.github_repo_edit)
        github_layout.addRow("API URL:", self.github_api_url_edit)

        github_group.setLayout(github_layout)
        layout.addWidget(github_group)

        # 超时和重试设置
        timeout_group = QGroupBox("超时和重试")
        timeout_layout = QFormLayout()

        self.download_timeout_spin = QSpinBox()
        self.download_timeout_spin.setMinimum(30)
        self.download_timeout_spin.setMaximum(900)
        self.download_timeout_spin.setSuffix(" 秒")

        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setMinimum(0)
        self.retry_count_spin.setMaximum(10)
        self.retry_count_spin.setSuffix(" 次")

        timeout_layout.addRow("下载超时:", self.download_timeout_spin)
        timeout_layout.addRow("重试次数:", self.retry_count_spin)

        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)

        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QHBoxLayout()

        log_layout.addWidget(QLabel("日志级别:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addWidget(self.log_level_combo)
        log_layout.addStretch()

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # 重置按钮
        reset_button = QPushButton("重置为默认设置")
        reset_button.clicked.connect(self.reset_settings)
        layout.addWidget(reset_button)

        layout.addStretch()
        self.advanced_tab.setLayout(layout)

    def load_settings(self):
        """从配置加载设置"""
        # 基本设置
        self.zed_path_edit.setText(self.settings.get('zed_install_path', ''))
        self.auto_check_cb.setChecked(self.settings.get('auto_check_enabled', True))
        self.check_startup_cb.setChecked(self.settings.get('check_on_startup', True))
        self.check_interval_spin.setValue(self.settings.get('check_interval_hours', 24))
        self.auto_download_cb.setChecked(self.settings.get('auto_download', True))
        self.auto_install_cb.setChecked(self.settings.get('auto_install', False))
        self.force_download_cb.setChecked(self.settings.get('force_download_latest', True))

        # 启动选项
        self.start_with_system_cb.setChecked(self.settings.get('start_with_system', False))
        self.start_minimized_cb.setChecked(self.settings.get('start_minimized', False))
        self.minimize_to_tray_cb.setChecked(self.settings.get('minimize_to_tray', True))
        self.auto_start_after_update_cb.setChecked(self.settings.get('auto_start_after_update', True))

        # 计划任务
        self.scheduled_update_cb.setChecked(self.settings.get('scheduled_update_enabled', False))

        scheduled_time = self.settings.get('scheduled_time', '02:00')
        try:
            hour, minute = map(int, scheduled_time.split(':'))
            self.scheduled_time_edit.setTime(QTime(hour, minute))
        except:
            self.scheduled_time_edit.setTime(QTime(2, 0))

        scheduled_days = self.settings.get('scheduled_days', [0, 1, 2, 3, 4, 5, 6])
        for i, cb in enumerate(self.day_checkboxes):
            cb.setChecked(i in scheduled_days)

        # 通知选项
        self.show_notifications_cb.setChecked(self.settings.get('show_notifications', True))
        self.notify_on_update_available_cb.setChecked(self.settings.get('notify_on_update_available', True))
        self.notify_on_update_complete_cb.setChecked(self.settings.get('notify_on_update_complete', True))

        # 高级设置
        self.backup_enabled_cb.setChecked(self.settings.get('backup_enabled', True))
        self.backup_count_spin.setValue(self.settings.get('backup_count', 3))

        self.use_proxy_cb.setChecked(self.settings.get('use_proxy', False))
        self.proxy_url_edit.setText(self.settings.get('proxy_url', ''))
        self.proxy_url_edit.setEnabled(self.settings.get('use_proxy', False))

        self.github_repo_edit.setText(self.settings.get('github_repo', 'TC999/zed-loc'))
        self.github_api_url_edit.setText(self.settings.get('github_api_url', 'https://api.github.com/repos/TC999/zed-loc/releases/latest'))

        self.download_timeout_spin.setValue(self.settings.get('download_timeout', 300))
        self.retry_count_spin.setValue(self.settings.get('retry_count', 3))

        log_level = self.settings.get('log_level', 'INFO')
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)

        # 连接信号
        self.use_proxy_cb.toggled.connect(self.proxy_url_edit.setEnabled)

    def save_settings(self):
        """保存设置"""
        # 更新设置字典
        # 基本设置
        self.settings['zed_install_path'] = self.zed_path_edit.text()
        self.settings['auto_check_enabled'] = self.auto_check_cb.isChecked()
        self.settings['check_on_startup'] = self.check_startup_cb.isChecked()
        self.settings['check_interval_hours'] = self.check_interval_spin.value()
        self.settings['auto_download'] = self.auto_download_cb.isChecked()
        self.settings['auto_install'] = self.auto_install_cb.isChecked()
        self.settings['force_download_latest'] = self.force_download_cb.isChecked()

        # 启动选项
        self.settings['start_with_system'] = self.start_with_system_cb.isChecked()
        self.settings['start_minimized'] = self.start_minimized_cb.isChecked()
        self.settings['minimize_to_tray'] = self.minimize_to_tray_cb.isChecked()
        self.settings['auto_start_after_update'] = self.auto_start_after_update_cb.isChecked()

        # 计划任务
        self.settings['scheduled_update_enabled'] = self.scheduled_update_cb.isChecked()
        self.settings['scheduled_time'] = self.scheduled_time_edit.time().toString('HH:mm')

        # 获取选中的执行天数
        scheduled_days = []
        for i, cb in enumerate(self.day_checkboxes):
            if cb.isChecked():
                scheduled_days.append(i)
        self.settings['scheduled_days'] = scheduled_days

        # 通知选项
        self.settings['show_notifications'] = self.show_notifications_cb.isChecked()
        self.settings['notify_on_update_available'] = self.notify_on_update_available_cb.isChecked()
        self.settings['notify_on_update_complete'] = self.notify_on_update_complete_cb.isChecked()

        # 高级设置
        self.settings['backup_enabled'] = self.backup_enabled_cb.isChecked()
        self.settings['backup_count'] = self.backup_count_spin.value()

        self.settings['use_proxy'] = self.use_proxy_cb.isChecked()
        self.settings['proxy_url'] = self.proxy_url_edit.text()

        self.settings['github_repo'] = self.github_repo_edit.text()
        self.settings['github_api_url'] = self.github_api_url_edit.text()

        self.settings['download_timeout'] = self.download_timeout_spin.value()
        self.settings['retry_count'] = self.retry_count_spin.value()

        self.settings['log_level'] = self.log_level_combo.currentText()

        # 发送设置更改信号
        self.settings_changed.emit(self.settings)

        # 接受对话框
        self.accept()

    def browse_zed_path(self):
        """浏览Zed安装路径"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Zed可执行文件",
            self.zed_path_edit.text(),
            "Executable Files (*.exe);;All Files (*)",
            options=options
        )

        if file_path:
            self.zed_path_edit.setText(file_path)

    def reset_settings(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            "重置设置",
            "确定要将所有设置重置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 重置为默认设置
            self.settings = self.config.DEFAULT_CONFIG.copy()
            self.load_settings()


class UpdateProgressDialog(QDialog):
    """更新进度对话框，显示下载和安装进度"""

    def __init__(self, parent=None):
        """初始化更新进度对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("更新进度")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()

        # 状态标签
        self.status_label = QLabel("准备更新...")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 详细状态
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

        # 按钮
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        self.background_button = QPushButton("后台运行")
        self.background_button.clicked.connect(self.hide)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.background_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_progress(self, progress, message=""):
        """更新进度

        Args:
            progress: 进度百分比(0-100)
            message: 进度消息
        """
        self.progress_bar.setValue(int(progress))
        if message:
            self.detail_label.setText(message)

    def set_status(self, status):
        """设置状态文本

        Args:
            status: 状态文本
        """
        self.status_label.setText(status)

    def enable_cancel(self, enable):
        """启用或禁用取消按钮

        Args:
            enable: 是否启用
        """
        self.cancel_button.setEnabled(enable)


class LogViewerDialog(QDialog):
    """日志查看器对话框"""

    def __init__(self, log_file_path, parent=None):
        """初始化日志查看器

        Args:
            log_file_path: 日志文件路径
            parent: 父窗口
        """
        super().__init__(parent)
        self.log_file_path = log_file_path
        self.setWindowTitle("日志查看器")
        self.resize(700, 500)
        self.setup_ui()
        self.load_log()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        font = QFont("Courier New", 9)
        self.log_text.setFont(font)
        layout.addWidget(self.log_text)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.load_log)

        self.clear_button = QPushButton("清空日志")
        self.clear_button.clicked.connect(self.clear_log)

        self.save_button = QPushButton("保存日志")
        self.save_button.clicked.connect(self.save_log)

        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_log(self):
        """加载日志文件"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            self.log_text.setPlainText(log_content)
            # 滚动到底部
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            self.log_text.setTextCursor(cursor)
        except Exception as e:
            self.log_text.setPlainText(f"无法读取日志文件: {e}")

    def clear_log(self):
        """清空日志文件"""
        reply = QMessageBox.question(
            self,
            "清空日志",
            "确定要清空日志文件吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"日志已于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 清空\n")
                self.load_log()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清空日志文件失败: {e}")

    def save_log(self):
        """保存日志到指定文件"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存日志文件",
            f"zed_updater_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
            options=options
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", f"日志已保存到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存日志文件失败: {e}")
