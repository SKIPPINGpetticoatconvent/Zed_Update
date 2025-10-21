#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification service for Zed Updater
"""

import sys
from typing import Optional
from dataclasses import dataclass

from ..utils.logger import get_logger


@dataclass
class NotificationConfig:
    """Notification configuration"""
    enabled: bool = True
    show_tray_notifications: bool = True
    play_sounds: bool = False
    sound_file: Optional[str] = None


class NotificationService:
    """Service for handling notifications across platforms"""

    def __init__(self, config: Optional[NotificationConfig] = None):
        self.logger = get_logger(__name__)
        self.config = config or NotificationConfig()
        self._tray_icon = None

    def set_tray_icon(self, tray_icon) -> None:
        """Set the system tray icon for notifications"""
        self._tray_icon = tray_icon

    def show_notification(self, title: str, message: str, icon_type: str = "info") -> None:
        """Show a notification"""
        if not self.config.enabled:
            return

        try:
            if sys.platform == 'win32':
                self._show_windows_notification(title, message, icon_type)
            elif sys.platform == 'darwin':
                self._show_macos_notification(title, message, icon_type)
            else:
                self._show_linux_notification(title, message, icon_type)

        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

    def show_update_available(self, version: str) -> None:
        """Show update available notification"""
        title = "Zed 更新可用"
        message = f"发现新版本 {version}，是否现在更新？"
        self.show_notification(title, message, "info")

    def show_update_completed(self, version: str) -> None:
        """Show update completed notification"""
        title = "Zed 更新完成"
        message = f"Zed 已成功更新到版本 {version}"
        self.show_notification(title, message, "info")

    def show_update_failed(self, error: str) -> None:
        """Show update failed notification"""
        title = "Zed 更新失败"
        message = f"更新过程中出现错误：{error}"
        self.show_notification(title, message, "error")

    def show_backup_created(self, path: str) -> None:
        """Show backup created notification"""
        title = "Zed 备份完成"
        message = f"备份已保存到：{path}"
        self.show_notification(title, message, "info")

    def _show_windows_notification(self, title: str, message: str, icon_type: str) -> None:
        """Show notification on Windows"""
        try:
            from win10toast import ToastNotifier

            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                icon_path=None,
                duration=5,
                threaded=True
            )

        except ImportError:
            # Fallback to system tray if available
            if self._tray_icon:
                self._show_tray_notification(title, message, icon_type)

        except Exception as e:
            self.logger.warning(f"Windows notification failed: {e}")
            if self._tray_icon:
                self._show_tray_notification(title, message, icon_type)

    def _show_macos_notification(self, title: str, message: str, icon_type: str) -> None:
        """Show notification on macOS"""
        try:
            import subprocess
            import shlex

            # Use osascript for notifications
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], capture_output=True)

        except Exception as e:
            self.logger.warning(f"macOS notification failed: {e}")

    def _show_linux_notification(self, title: str, message: str, icon_type: str) -> None:
        """Show notification on Linux"""
        try:
            import subprocess

            # Try notify-send
            icon = self._get_icon_name(icon_type)
            subprocess.run([
                'notify-send',
                '--icon', icon,
                '--expire-time', '5000',
                title,
                message
            ], capture_output=True)

        except (ImportError, FileNotFoundError):
            # Fallback to system tray
            if self._tray_icon:
                self._show_tray_notification(title, message, icon_type)

        except Exception as e:
            self.logger.warning(f"Linux notification failed: {e}")
            if self._tray_icon:
                self._show_tray_notification(title, message, icon_type)

    def _show_tray_notification(self, title: str, message: str, icon_type: str) -> None:
        """Show notification via system tray icon"""
        if not self._tray_icon:
            return

        try:
            # Map icon types to standard icons
            icon_map = {
                'info': self._tray_icon.style().standardIcon(self._tray_icon.style().SP_MessageBoxInformation),
                'warning': self._tray_icon.style().standardIcon(self._tray_icon.style().SP_MessageBoxWarning),
                'error': self._tray_icon.style().standardIcon(self._tray_icon.style().SP_MessageBoxCritical),
                'success': self._tray_icon.style().standardIcon(self._tray_icon.style().SP_MessageBoxInformation)
            }

            icon = icon_map.get(icon_type, icon_map['info'])

            self._tray_icon.showMessage(title, message, icon, 5000)

        except Exception as e:
            self.logger.error(f"Tray notification failed: {e}")

    def _get_icon_name(self, icon_type: str) -> str:
        """Get icon name for Linux notifications"""
        icon_map = {
            'info': 'dialog-information',
            'warning': 'dialog-warning',
            'error': 'dialog-error',
            'success': 'dialog-information'
        }
        return icon_map.get(icon_type, 'dialog-information')

    def play_sound(self, sound_type: str = "notification") -> None:
        """Play notification sound"""
        if not self.config.play_sounds:
            return

        try:
            if sys.platform == 'win32':
                self._play_windows_sound(sound_type)
            elif sys.platform == 'darwin':
                self._play_macos_sound(sound_type)
            else:
                self._play_linux_sound(sound_type)

        except Exception as e:
            self.logger.error(f"Failed to play sound: {e}")

    def _play_windows_sound(self, sound_type: str) -> None:
        """Play sound on Windows"""
        try:
            import winsound
            winsound.MessageBeep(winsound.SMB_ICONASTERISK)
        except ImportError:
            pass

    def _play_macos_sound(self, sound_type: str) -> None:
        """Play sound on macOS"""
        try:
            import subprocess
            subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'], capture_output=True)
        except Exception:
            pass

    def _play_linux_sound(self, sound_type: str) -> None:
        """Play sound on Linux"""
        try:
            import subprocess
            # Try different sound commands
            for cmd in [['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'],
                       ['play', '-q', '/usr/share/sounds/alsa/Front_Center.wav']]:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=2)
                    break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        except Exception:
            pass