#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings dialog for Zed Updater
"""

from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QFileDialog, QGroupBox, QScrollArea, QWidget, QMessageBox,
    QTimeEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTime

from ..core.config import ConfigManager
from ..utils.logger import get_logger


class SettingsDialog(QDialog):
    """Settings dialog for configuring Zed Updater"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)

        self.config = config
        self.logger = get_logger(__name__)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("设置 - Zed Editor 自动更新程序")
        self.setModal(True)
        self.resize(600, 500)

        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
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
        self.github_repo_edit.setPlaceholderText("owner/repo")
        basic_layout.addWidget(self.github_repo_edit, 1, 1, 1, 2)

        layout.addWidget(basic_group)

        # Update settings group
        update_group = QGroupBox("更新设置")
        update_layout = QGridLayout(update_group)

        self.auto_check_enabled = QCheckBox("启用自动检查更新")
        update_layout.addWidget(self.auto_check_enabled, 0, 0, 1, 2)

        update_layout.addWidget(QLabel("检查间隔(小时):"), 1, 0)
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 168)  # 1 hour to 1 week
        update_layout.addWidget(self.check_interval_spin, 1, 1)

        update_layout.addWidget(QLabel("检查时间:"), 2, 0)
        self.check_time_edit = QTimeEdit()
        self.check_time_edit.setTime(QTime.fromString("09:00", "hh:mm"))
        update_layout.addWidget(self.check_time_edit, 2, 1)

        self.check_on_startup = QCheckBox("启动时检查更新")
        update_layout.addWidget(self.check_on_startup, 3, 0, 1, 2)

        self.force_download_latest = QCheckBox("强制下载最新版本")
        update_layout.addWidget(self.force_download_latest, 4, 0, 1, 2)

        layout.addWidget(update_group)

        # Download/Install settings group
        action_group = QGroupBox("下载和安装设置")
        action_layout = QGridLayout(action_group)

        self.auto_download = QCheckBox("自动下载更新")
        action_layout.addWidget(self.auto_download, 0, 0, 1, 2)

        self.auto_install = QCheckBox("自动安装更新")
        action_layout.addWidget(self.auto_install, 1, 0, 1, 2)

        self.auto_start_after_update = QCheckBox("更新后自动启动Zed")
        action_layout.addWidget(self.auto_start_after_update, 2, 0, 1, 2)

        action_layout.addWidget(QLabel("下载超时(秒):"), 3, 0)
        self.download_timeout_spin = QSpinBox()
        self.download_timeout_spin.setRange(30, 3600)
        update_layout.addWidget(self.download_timeout_spin, 3, 1)

        action_layout.addWidget(QLabel("重试次数:"), 4, 0)
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        action_layout.addWidget(self.retry_count_spin, 4, 1)

        layout.addWidget(action_group)

        # Backup settings group
        backup_group = QGroupBox("备份设置")
        backup_layout = QGridLayout(backup_group)

        self.backup_enabled = QCheckBox("启用自动备份")
        backup_layout.addWidget(self.backup_enabled, 0, 0, 1, 2)

        backup_layout.addWidget(QLabel("保留备份数:"), 1, 0)
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        backup_layout.addWidget(self.backup_count_spin, 1, 1)

        layout.addWidget(backup_group)

        # Network settings group
        network_group = QGroupBox("网络设置")
        network_layout = QGridLayout(network_group)

        self.proxy_enabled = QCheckBox("启用代理")
        network_layout.addWidget(self.proxy_enabled, 0, 0, 1, 2)

        network_layout.addWidget(QLabel("代理URL:"), 1, 0)
        self.proxy_url_edit = QLineEdit()
        self.proxy_url_edit.setPlaceholderText("http://proxy.example.com:8080")
        network_layout.addWidget(self.proxy_url_edit, 1, 1)

        layout.addWidget(network_group)

        # UI settings group
        ui_group = QGroupBox("界面设置")
        ui_layout = QGridLayout(ui_group)

        self.minimize_to_tray = QCheckBox("最小化到系统托盘")
        ui_layout.addWidget(self.minimize_to_tray, 0, 0, 1, 2)

        self.start_minimized = QCheckBox("启动时最小化")
        ui_layout.addWidget(self.start_minimized, 1, 0, 1, 2)

        self.notification_enabled = QCheckBox("启用通知")
        ui_layout.addWidget(self.notification_enabled, 2, 0, 1, 2)

        ui_layout.addWidget(QLabel("语言:"), 3, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        ui_layout.addWidget(self.language_combo, 3, 1)

        layout.addWidget(ui_group)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)

        main_layout.addWidget(button_box)

    def load_settings(self):
        """Load settings from configuration"""
        try:
            # Basic settings
            self.zed_path_edit.setText(self.config.get('zed_install_path', ''))
            self.github_repo_edit.setText(self.config.get('github_repo', ''))

            # Update settings
            self.auto_check_enabled.setChecked(self.config.get('auto_check_enabled', True))
            self.check_interval_spin.setValue(self.config.get('check_interval_hours', 24))
            check_time = self.config.get('check_time', '09:00')
            self.check_time_edit.setTime(QTime.fromString(check_time, "hh:mm"))
            self.check_on_startup.setChecked(self.config.get('check_on_startup', True))
            self.force_download_latest.setChecked(self.config.get('force_download_latest', True))

            # Action settings
            self.auto_download.setChecked(self.config.get('auto_download', True))
            self.auto_install.setChecked(self.config.get('auto_install', False))
            self.auto_start_after_update.setChecked(self.config.get('auto_start_after_update', True))
            self.download_timeout_spin.setValue(self.config.get('download_timeout', 300))
            self.retry_count_spin.setValue(self.config.get('retry_count', 3))

            # Backup settings
            self.backup_enabled.setChecked(self.config.get('backup_enabled', True))
            self.backup_count_spin.setValue(self.config.get('backup_count', 3))

            # Network settings
            self.proxy_enabled.setChecked(self.config.get('proxy_enabled', False))
            self.proxy_url_edit.setText(self.config.get('proxy_url', ''))

            # UI settings
            self.minimize_to_tray.setChecked(self.config.get('minimize_to_tray', True))
            self.start_minimized.setChecked(self.config.get('start_minimized', False))
            self.notification_enabled.setChecked(self.config.get('notification_enabled', True))
            self.language_combo.setCurrentText(self.config.get('language', 'zh_CN'))

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            QMessageBox.warning(self, "加载失败", f"加载设置时出错: {e}")

    def save_settings(self) -> bool:
        """Save settings to configuration"""
        try:
            updates = {}

            # Basic settings
            updates['zed_install_path'] = self.zed_path_edit.text()
            updates['github_repo'] = self.github_repo_edit.text()

            # Update settings
            updates['auto_check_enabled'] = self.auto_check_enabled.isChecked()
            updates['check_interval_hours'] = self.check_interval_spin.value()
            check_time = self.check_time_edit.time().toString("hh:mm")
            updates['check_time'] = check_time
            updates['check_on_startup'] = self.check_on_startup.isChecked()
            updates['force_download_latest'] = self.force_download_latest.isChecked()

            # Action settings
            updates['auto_download'] = self.auto_download.isChecked()
            updates['auto_install'] = self.auto_install.isChecked()
            updates['auto_start_after_update'] = self.auto_start_after_update.isChecked()
            updates['download_timeout'] = self.download_timeout_spin.value()
            updates['retry_count'] = self.retry_count_spin.value()

            # Backup settings
            updates['backup_enabled'] = self.backup_enabled.isChecked()
            updates['backup_count'] = self.backup_count_spin.value()

            # Network settings
            updates['proxy_enabled'] = self.proxy_enabled.isChecked()
            updates['proxy_url'] = self.proxy_url_edit.text()

            # UI settings
            updates['minimize_to_tray'] = self.minimize_to_tray.isChecked()
            updates['start_minimized'] = self.start_minimized.isChecked()
            updates['notification_enabled'] = self.notification_enabled.isChecked()
            updates['language'] = self.language_combo.currentText()

            # Save to config
            success = self.config.update(updates)

            if success:
                # Validate configuration
                errors = self.config.validate()
                if errors:
                    error_msg = "配置验证失败:\n" + "\n".join(f"- {k}: {v}" for k, v in errors.items())
                    QMessageBox.warning(self, "配置警告", error_msg)

                self.logger.info("Settings saved successfully")
                return True
            else:
                QMessageBox.critical(self, "保存失败", "无法保存设置")
                return False

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {e}")
            return False

    def browse_zed_path(self):
        """Browse for Zed executable path"""
        current_path = self.zed_path_edit.text()
        if not current_path:
            current_path = "C:\\"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Zed.exe", current_path, "Executable files (*.exe)"
        )

        if file_path:
            self.zed_path_edit.setText(file_path)

    def apply_settings(self):
        """Apply settings without closing dialog"""
        if self.save_settings():
            QMessageBox.information(self, "应用成功", "设置已应用")

    def accept(self):
        """Accept dialog and save settings"""
        if self.save_settings():
            super().accept()
        # Don't close if save failed