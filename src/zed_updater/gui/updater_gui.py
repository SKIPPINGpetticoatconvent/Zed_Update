#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updater GUI component for Zed Updater
"""

from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QGroupBox, QFileDialog,
    QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from ..core.config import ConfigManager
from ..core.updater import ZedUpdater, UpdateResult
from ..core.scheduler import UpdateScheduler
from ..services.github_api import ReleaseInfo
from ..utils.logger import get_logger


class UpdateWorker(QThread):
    """Worker thread for update operations"""

    progress_updated = pyqtSignal(float, str)
    update_completed = pyqtSignal(bool, str)
    version_info_received = pyqtSignal(object)  # ReleaseInfo

    def __init__(self, updater: ZedUpdater, operation: str):
        super().__init__()
        self.updater = updater
        self.operation = operation
        self.release_info = None

    def set_release_info(self, release_info: ReleaseInfo):
        """Set release info for download/install operations"""
        self.release_info = release_info

    def run(self):
        """Execute the update operation"""
        try:
            if self.operation == "check_version":
                self._check_version()
            elif self.operation == "download_update":
                self._download_update()
            elif self.operation == "install_update":
                self._install_update()
            elif self.operation == "check_and_update":
                self._check_and_update()

        except Exception as e:
            self.update_completed.emit(False, f"操作失败: {e}")

    def _check_version(self):
        """Check for version updates"""
        self.progress_updated.emit(0, "正在检查更新...")

        release_info = self.updater.get_latest_version_info()
        if release_info:
            self.version_info_received.emit(release_info)
            self.progress_updated.emit(100, "版本检查完成")
        else:
            self.update_completed.emit(False, "无法获取版本信息")

    def _download_update(self):
        """Download update"""
        if not self.release_info:
            self.update_completed.emit(False, "没有可用的更新信息")
            return

        self.progress_updated.emit(0, "开始下载更新...")

        download_path = self.updater.download_update(
            self.release_info,
            lambda progress, message: self.progress_updated.emit(progress, message)
        )

        if download_path:
            self.update_completed.emit(True, f"下载完成: {download_path.name}")
        else:
            self.update_completed.emit(False, "下载失败")

    def _install_update(self):
        """Install update"""
        if not self.release_info:
            self.update_completed.emit(False, "没有可用的更新信息")
            return

        self.progress_updated.emit(0, "开始安装更新...")

        # Assume download was done previously - need to find the file
        temp_dir = self.updater.config.get_temp_dir()
        expected_file = temp_dir / f"zed_update_{self.release_info.version}.exe"

        if not expected_file.exists():
            self.update_completed.emit(False, "未找到下载的文件")
            return

        result = self.updater.install_update(expected_file)

        if result.success:
            self.progress_updated.emit(100, "安装完成")
            self.update_completed.emit(True, result.message)
        else:
            self.update_completed.emit(False, result.message)

    def _check_and_update(self):
        """Check for updates and perform installation"""
        self.progress_updated.emit(0, "正在检查更新...")

        result = self.updater.check_and_update(
            lambda progress, message: self.progress_updated.emit(progress, message)
        )

        self.update_completed.emit(result.success, result.message)


class UpdaterGUI(QWidget):
    """Main updater GUI component"""

    def __init__(self, config: ConfigManager, updater: ZedUpdater, scheduler: UpdateScheduler):
        super().__init__()

        self.config = config
        self.updater = updater
        self.scheduler = scheduler
        self.logger = get_logger(__name__)

        # State
        self.current_version = "未知"
        self.latest_version = "未知"
        self.current_release_info = None
        self.update_worker = None

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Version info group
        version_group = QGroupBox("版本信息")
        version_layout = QGridLayout(version_group)

        version_layout.addWidget(QLabel("当前版本:"), 0, 0)
        self.current_version_label = QLabel(self.current_version)
        version_layout.addWidget(self.current_version_label, 0, 1)

        version_layout.addWidget(QLabel("最新版本:"), 1, 0)
        self.latest_version_label = QLabel(self.latest_version)
        version_layout.addWidget(self.latest_version_label, 1, 1)

        version_layout.addWidget(QLabel("状态:"), 2, 0)
        self.status_label = QLabel("就绪")
        version_layout.addWidget(self.status_label, 2, 1)

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
        progress_group = QGroupBox("操作进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)
        self.progress_group = progress_group
        self.progress_group.hide()

        # Release notes group
        notes_group = QGroupBox("更新说明")
        notes_layout = QVBoxLayout(notes_group)

        self.release_notes = QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setMaximumHeight(150)
        notes_layout.addWidget(self.release_notes)

        layout.addWidget(notes_group)

        # Scheduler status group
        scheduler_group = QGroupBox("定时任务状态")
        scheduler_layout = QGridLayout(scheduler_group)

        scheduler_layout.addWidget(QLabel("状态:"), 0, 0)
        self.scheduler_status_label = QLabel("未启动")
        scheduler_layout.addWidget(self.scheduler_status_label, 0, 1)

        scheduler_layout.addWidget(QLabel("下次运行:"), 1, 0)
        self.next_run_label = QLabel("未设置")
        scheduler_layout.addWidget(self.next_run_label, 1, 1)

        self.toggle_scheduler_button = QPushButton("启动定时任务")
        self.toggle_scheduler_button.clicked.connect(self.toggle_scheduler)
        scheduler_layout.addWidget(self.toggle_scheduler_button, 2, 0, 1, 2)

        layout.addWidget(scheduler_group)

        # Update status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_scheduler_status)
        self.status_timer.start(5000)  # Update every 5 seconds

    def setup_connections(self):
        """Setup signal connections"""
        pass  # Connections will be established when worker is created

    def set_current_version(self, version: str):
        """Set the current version display"""
        self.current_version = version
        self.current_version_label.setText(version)

    def check_for_updates(self):
        """Check for updates"""
        if self.update_worker and self.update_worker.isRunning():
            QMessageBox.warning(self, "操作进行中", "请等待当前操作完成")
            return

        self.status_label.setText("正在检查更新...")
        self.check_updates_button.setEnabled(False)

        self.update_worker = UpdateWorker(self.updater, "check_version")
        self.update_worker.progress_updated.connect(self.on_progress_updated)
        self.update_worker.version_info_received.connect(self.on_version_info_received)
        self.update_worker.update_completed.connect(self.on_update_completed)
        self.update_worker.start()

    def download_update(self):
        """Download the available update"""
        if not self.current_release_info:
            QMessageBox.warning(self, "没有更新", "请先检查更新")
            return

        if self.update_worker and self.update_worker.isRunning():
            QMessageBox.warning(self, "操作进行中", "请等待当前操作完成")
            return

        self.progress_group.show()
        self.download_button.setEnabled(False)

        self.update_worker = UpdateWorker(self.updater, "download_update")
        self.update_worker.set_release_info(self.current_release_info)
        self.update_worker.progress_updated.connect(self.on_progress_updated)
        self.update_worker.update_completed.connect(self.on_update_completed)
        self.update_worker.start()

    def install_update(self):
        """Install the downloaded update"""
        if not self.current_release_info:
            QMessageBox.warning(self, "没有更新", "请先检查更新")
            return

        if self.update_worker and self.update_worker.isRunning():
            QMessageBox.warning(self, "操作进行中", "请等待当前操作完成")
            return

        reply = QMessageBox.question(
            self, "确认安装",
            "确定要安装更新吗？这将关闭当前的Zed进程。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.progress_group.show()
        self.install_button.setEnabled(False)

        self.update_worker = UpdateWorker(self.updater, "install_update")
        self.update_worker.set_release_info(self.current_release_info)
        self.update_worker.progress_updated.connect(self.on_progress_updated)
        self.update_worker.update_completed.connect(self.on_update_completed)
        self.update_worker.start()

    def start_zed(self):
        """Start Zed application"""
        zed_path = self.config.get('zed_install_path')

        if not zed_path or not Path(zed_path).exists():
            QMessageBox.warning(self, "文件不存在", f"Zed可执行文件不存在: {zed_path}")
            return

        try:
            success = self.updater.start_zed()
            if success:
                QMessageBox.information(self, "启动成功", "Zed已启动")
            else:
                QMessageBox.critical(self, "启动失败", "无法启动Zed")
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动Zed时出错: {e}")

    def toggle_scheduler(self):
        """Toggle scheduler on/off"""
        try:
            if self.scheduler.is_running():
                self.scheduler.stop()
                self.toggle_scheduler_button.setText("启动定时任务")
                self.scheduler_status_label.setText("已停止")
            else:
                if self.scheduler.start():
                    self.toggle_scheduler_button.setText("停止定时任务")
                    self.scheduler_status_label.setText("运行中")
                    self.update_scheduler_status()
                else:
                    QMessageBox.warning(self, "启动失败", "无法启动定时任务")
        except Exception as e:
            QMessageBox.critical(self, "操作失败", f"切换定时任务状态时出错: {e}")

    def update_scheduler_status(self):
        """Update scheduler status display"""
        try:
            status = self.scheduler.get_status()

            if status.is_running:
                self.scheduler_status_label.setText("运行中")
                self.toggle_scheduler_button.setText("停止定时任务")

                if status.next_run_time:
                    self.next_run_label.setText(
                        status.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                else:
                    self.next_run_label.setText("未设置")
            else:
                self.scheduler_status_label.setText("已停止")
                self.toggle_scheduler_button.setText("启动定时任务")
                self.next_run_label.setText("未设置")

        except Exception as e:
            self.logger.error(f"Failed to update scheduler status: {e}")

    # Event handlers
    def on_progress_updated(self, progress: float, message: str):
        """Handle progress updates"""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
        self.status_label.setText(message)

    def on_version_info_received(self, release_info: ReleaseInfo):
        """Handle version information received"""
        self.current_release_info = release_info
        self.latest_version = release_info.version
        self.latest_version_label.setText(self.latest_version)

        # Update release notes
        self.release_notes.setText(release_info.description or "没有更新说明")

        # Enable download button
        self.download_button.setEnabled(True)

        # Check if update is needed
        current = self.updater.get_current_version()
        if self.updater._is_newer_version(current, release_info.version):
            self.status_label.setText("发现新版本")
            QMessageBox.information(self, "发现更新", f"发现新版本 {release_info.version}")
        else:
            self.status_label.setText("已是最新版本")

    def on_update_completed(self, success: bool, message: str):
        """Handle update operation completion"""
        self.progress_group.hide()
        self.status_label.setText("完成" if success else "失败")

        # Re-enable buttons
        self.check_updates_button.setEnabled(True)

        if "下载" in message.lower():
            self.download_button.setEnabled(True)
            self.install_button.setEnabled(True)
        elif "安装" in message.lower():
            # Update current version display
            if success:
                self.set_current_version(self.latest_version)
                # Auto-start if configured
                if self.config.get('auto_start_after_update'):
                    QTimer.singleShot(1000, self.start_zed)

        # Show result message
        if success:
            QMessageBox.information(self, "操作成功", message)
        else:
            QMessageBox.warning(self, "操作失败", message)

        # Clean up worker
        if self.update_worker:
            self.update_worker.quit()
            self.update_worker.wait()
            self.update_worker = None

    def update_progress(self, progress: float, message: str):
        """Update progress display (called from main window)"""
        self.on_progress_updated(progress, message)

    def update_completed(self, success: bool, message: str):
        """Handle update completion (called from main window)"""
        self.on_update_completed(success, message)

    def closeEvent(self, event):
        """Handle widget close event"""
        if self.update_worker and self.update_worker.isRunning():
            self.update_worker.quit()
            self.update_worker.wait()
        event.accept()