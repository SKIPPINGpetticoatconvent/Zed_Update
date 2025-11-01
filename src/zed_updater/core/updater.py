#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Zed Editor updater - Unified architecture
"""

import os
import shutil
import hashlib
import tempfile
import subprocess
import time
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import requests
import psutil
from .config import ConfigManager
from ..utils.logger import get_logger


@dataclass
class UpdateResult:
    """Update operation result"""
    success: bool
    message: str
    version: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ReleaseInfo:
    """Release information"""
    version: str
    release_date: datetime
    download_url: str
    description: str
    size: int
    sha256: Optional[str] = None


class ZedUpdater:
    """Simplified and unified Zed updater"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZedUpdater/2.0',
            'Accept': 'application/vnd.github.v3+json'
        })

        # Setup proxy if configured
        if config.get('proxy_enabled') and config.get('proxy_url'):
            proxy_url = config.get('proxy_url')
            self.session.proxies = {'http': proxy_url, 'https': proxy_url}

    def get_current_version(self) -> Optional[str]:
        """Get currently installed Zed version"""
        zed_path = self.config.get('zed_install_path')
        if not zed_path or not Path(zed_path).exists():
            self.logger.warning(f"Zed executable not found: {zed_path}")
            return None

        try:
            # Try to get version info from file properties (Windows)
            import win32api
            import win32con

            info = win32api.GetFileVersionInfo(zed_path, "\\")
            version = "%d.%d.%d.%d" % (
                win32api.HIWORD(info['FileVersionMS']),
                win32api.LOWORD(info['FileVersionMS']),
                win32api.HIWORD(info['FileVersionLS']),
                win32api.LOWORD(info['FileVersionLS'])
            )
            return version

        except ImportError:
            # Fallback: try to run Zed with --version
            try:
                result = subprocess.run(
                    [zed_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Parse version from output
                    output = result.stdout.strip()
                    # Extract version number (simple heuristic)
                    import re
                    match = re.search(r'(\d+\.\d+\.\d+)', output)
                    if match:
                        return match.group(1)

            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

        except Exception as e:
            self.logger.warning(f"Failed to get Zed version: {e}")

        # Return unknown if we can't determine version
        return "unknown"

    def get_latest_version_info(self) -> Optional[ReleaseInfo]:
        """Get latest version information from GitHub"""
        try:
            repo = self.config.get('github_repo', 'TC999/zed-loc')
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract version from tag
            tag_name = data.get('tag_name', '')
            version = tag_name.lstrip('v') if tag_name else 'latest'
            
            # Find download URL (prefer Windows executables)
            download_url = ""
            for asset in data.get('assets', []):
                name = asset.get('name', '').lower()
                if 'windows' in name or 'win' in name or name.endswith('.exe'):
                    download_url = asset.get('browser_download_url', '')
                    break
            
            # Fallback to first asset
            if not download_url and data.get('assets'):
                download_url = data['assets'][0].get('browser_download_url', '')
            
            if not download_url:
                self.logger.error("No suitable download asset found")
                return None
            
            release_info = ReleaseInfo(
                version=version,
                release_date=datetime.fromisoformat(data['published_at'].replace('Z', '+00:00')),
                download_url=download_url,
                description=data.get('body', ''),
                size=sum(asset.get('size', 0) for asset in data.get('assets', [])),
                sha256=None
            )
            
            self.logger.info(f"Found latest version: {version}")
            return release_info
            
        except Exception as e:
            self.logger.error(f"Failed to get latest version info: {e}")
            return None

    def check_for_updates(self) -> Optional[ReleaseInfo]:
        """Check if updates are available"""
        current_version = self.get_current_version()
        latest_info = self.get_latest_version_info()

        if not latest_info:
            return None

        self.logger.info(f"Current version: {current_version}")
        self.logger.info(f"Latest version: {latest_info.version}")

        # For date-based versions or when forced, always consider as update available
        if (self.config.get('force_download_latest') or
            self._is_newer_version(current_version, latest_info.version)):
            return latest_info

        return None

    def _is_newer_version(self, current: str, latest: str) -> bool:
        """Compare version strings"""
        if not current or current == "unknown":
            return True

        try:
            # Handle date-based versions (e.g., "2024-01-15")
            from datetime import datetime
            try:
                current_date = datetime.strptime(current, "%Y-%m-%d")
                latest_date = datetime.strptime(latest, "%Y-%m-%d")
                return latest_date > current_date
            except ValueError:
                pass

            # Handle semantic versions
            import re
            current_parts = re.findall(r'\d+', current)
            latest_parts = re.findall(r'\d+', latest)

            if not current_parts or not latest_parts:
                return True  # Assume newer if can't parse

            # Compare version parts
            for c, l in zip(current_parts, latest_parts):
                if int(l) > int(c):
                    return True
                elif int(l) < int(c):
                    return False

            # If all parts equal, check if latest has more parts
            return len(latest_parts) > len(current_parts)

        except Exception as e:
            self.logger.warning(f"Version comparison failed: {e}")
            return True  # Assume update available on error

    def download_update(
        self,
        release_info: ReleaseInfo,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[Path]:
        """Download update file"""
        try:
            temp_dir = self.config.get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            download_path = temp_dir / f"zed_update_{release_info.version}.exe"
            
            self.logger.info(f"Downloading from: {release_info.download_url}")
            
            timeout = self.config.get('download_timeout', 300)
            retry_count = self.config.get('retry_count', 3)
            
            for attempt in range(retry_count):
                try:
                    response = self.session.get(release_info.download_url, stream=True, timeout=timeout)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Report progress
                                if progress_callback and total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    progress_callback(progress, f"下载中... {progress:.1f}%")
                    
                    self.logger.info(f"下载完成: {download_path}")
                    return download_path
                    
                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"下载尝试 {attempt + 1} 失败: {e}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        self.logger.error(f"下载失败，已重试 {retry_count} 次")
                        return None

        except Exception as e:
            self.logger.error(f"下载错误: {e}")
            return None

    def create_backup(self) -> Optional[Path]:
        """Create backup of current Zed installation"""
        if not self.config.get('backup_enabled'):
            return None

        zed_path = Path(self.config.get('zed_install_path'))
        if not zed_path.exists():
            self.logger.warning("Zed executable not found, skipping backup")
            return None

        try:
            backup_dir = self.config.get_backup_dir()
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Clean old backups
            self._cleanup_old_backups()

            # Create backup filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"zed_backup_{timestamp}.exe"

            # Copy file
            shutil.copy2(zed_path, backup_path)
            self.logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self) -> None:
        """Clean up old backup files"""
        try:
            backup_dir = self.config.get_backup_dir()
            if not backup_dir.exists():
                return

            backup_count = self.config.get('backup_count', 3)
            backup_files = list(backup_dir.glob("zed_backup_*.exe"))

            if len(backup_files) > backup_count:
                # Sort by modification time (oldest first)
                backup_files.sort(key=lambda x: x.stat().st_mtime)

                # Remove oldest files
                files_to_remove = backup_files[:-backup_count]
                for old_file in files_to_remove:
                    try:
                        old_file.unlink()
                        self.logger.debug(f"Removed old backup: {old_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove old backup {old_file}: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup backups: {e}")

    def install_update(self, download_path: Path) -> UpdateResult:
        """Install downloaded update"""
        zed_path = Path(self.config.get('zed_install_path'))

        try:
            # Stop Zed processes
            self._stop_zed_processes()

            # Create backup first
            backup_path = self.create_backup()
            if backup_path:
                self.logger.info(f"Backup created before installation: {backup_path}")

            # Install new version
            self.logger.info(f"Installing update from {download_path} to {zed_path}")

            # For safety, create a temporary backup of current file
            temp_backup = zed_path.with_suffix('.tmp')
            if zed_path.exists():
                shutil.move(zed_path, temp_backup)

            try:
                # Move new file to installation location
                shutil.move(download_path, zed_path)

                # Set executable permissions (in case)
                os.chmod(zed_path, 0o755)

                # Remove temporary backup
                if temp_backup.exists():
                    temp_backup.unlink()

                self.logger.info("Update installation completed successfully")
                return UpdateResult(
                    success=True,
                    message="Update installed successfully",
                    version=self._extract_version_from_file(zed_path)
                )

            except Exception as install_error:
                # Restore from temporary backup
                if temp_backup.exists():
                    try:
                        shutil.move(temp_backup, zed_path)
                        self.logger.info("Restored from backup after installation failure")
                    except Exception as restore_error:
                        self.logger.error(f"Failed to restore backup: {restore_error}")

                raise install_error

        except Exception as e:
            error_msg = f"Installation failed: {e}"
            self.logger.error(error_msg)
            return UpdateResult(
                success=False,
                message=error_msg,
                error_code="INSTALL_FAILED"
            )

    def _stop_zed_processes(self) -> None:
        """停止所有Zed进程"""
        try:
            zed_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if (proc.info['name'] and 'zed' in proc.info['name'].lower() and
                        proc.info['exe'] and Path(proc.info['exe']).name.lower().startswith('zed')):
                        zed_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            for proc in zed_processes:
                try:
                    self.logger.info(f"停止Zed进程: {proc.pid}")
                    proc.terminate()
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    proc.kill()  # 强制终止
                except Exception as e:
                    self.logger.warning(f"停止进程 {proc.pid} 失败: {e}")

        except Exception as e:
            self.logger.warning(f"停止Zed进程时出错: {e}")

    def check_and_update(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> UpdateResult:
        """检查更新并执行安装"""
        try:
            # 检查更新
            release_info = self.check_for_updates()
            if not release_info:
                return UpdateResult(
                    success=True,
                    message="没有可用的更新"
                )

            # 下载更新
            if progress_callback:
                progress_callback(0, "开始下载更新...")

            download_path = self.download_update(release_info, progress_callback)
            if not download_path:
                return UpdateResult(
                    success=False,
                    message="下载失败",
                    error_code="DOWNLOAD_FAILED"
                )

            # 安装更新
            if progress_callback:
                progress_callback(80, "正在安装更新...")

            install_result = self.install_update(download_path)

            # 如果配置了自动启动且安装成功
            if (install_result.success and
                self.config.get('auto_start_after_update')):
                self.start_zed()

            return install_result

        except Exception as e:
            error_msg = f"更新检查/安装失败: {e}"
            self.logger.error(error_msg)
            return UpdateResult(
                success=False,
                message=error_msg,
                error_code="UPDATE_FAILED"
            )

    def start_zed(self) -> bool:
        """启动Zed应用程序"""
        zed_path = self.config.get('zed_install_path', 'D:\\Zed.exe')

        if not zed_path or not Path(zed_path).exists():
            self.logger.error(f"Zed可执行文件不存在: {zed_path}")
            return False

        try:
            self.logger.info(f"启动Zed: {zed_path}")
            subprocess.Popen([zed_path])
            return True
        except Exception as e:
            self.logger.error(f"启动Zed失败: {e}")
            return False

    def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        try:
            temp_dir = self.config.get_temp_dir()
            if temp_dir.exists():
                # 删除1天前的临时文件
                current_time = time.time()
                max_age = 24 * 60 * 60  # 1天

                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        if current_time - file_path.stat().st_mtime > max_age:
                            try:
                                file_path.unlink()
                                self.logger.debug(f"清理临时文件: {file_path}")
                            except Exception as e:
                                self.logger.warning(f"清理临时文件失败: {file_path}")

        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")