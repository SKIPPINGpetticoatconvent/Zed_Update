#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core updater functionality for Zed Editor
"""

import os
import shutil
import hashlib
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

import requests
import psutil

from .config import ConfigManager
from ..services.github_api import GitHubAPI, ReleaseInfo
from ..utils.logger import get_logger
from ..utils.encoding import EncodingUtils


@dataclass
class UpdateResult:
    """Update operation result"""
    success: bool
    message: str
    version: Optional[str] = None
    error_code: Optional[str] = None


class ZedUpdater:
    """Core Zed updater with improved error handling and progress tracking"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = get_logger(__name__)
        self.github_api = GitHubAPI(
            repo=config.get('github_repo'),
            api_url=config.get('github_api_url')
        )

        # Setup proxy if configured
        if config.get('proxy_enabled') and config.get('proxy_url'):
            self.github_api.set_proxy(config.get('proxy_url'))

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
            return self.github_api.get_latest_release()
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
        temp_dir = self.config.get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)

        download_path = temp_dir / f"zed_update_{release_info.version}.exe"

        try:
            self.logger.info(f"Downloading from: {release_info.download_url}")

            # Setup request with timeout and retries
            timeout = self.config.get('download_timeout', 300)
            retry_count = self.config.get('retry_count', 3)

            for attempt in range(retry_count):
                try:
                    response = requests.get(
                        release_info.download_url,
                        stream=True,
                        timeout=timeout
                    )
                    response.raise_for_status()

                    # Get total size
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
                                    progress_callback(progress, f"Downloading... {progress:.1f}%")

                    # Verify download integrity
                    if release_info.sha256:
                        if not self.github_api.verify_checksum(str(download_path), release_info.sha256):
                            self.logger.error("Download checksum verification failed")
                            if attempt < retry_count - 1:
                                continue
                            return None

                    self.logger.info(f"Download completed: {download_path}")
                    return download_path

                except requests.exceptions.RequestException as e:
                    self.logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"Download failed after {retry_count} attempts")
                        return None

        except Exception as e:
            self.logger.error(f"Download error: {e}")
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
        """Stop all running Zed processes"""
        try:
            zed_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'zed' in proc.info['name'].lower():
                        if proc.info['exe'] and Path(proc.info['exe']).name.lower().startswith('zed'):
                            zed_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            for proc in zed_processes:
                try:
                    self.logger.info(f"Stopping Zed process: {proc.pid}")
                    proc.terminate()

                    # Wait for process to terminate
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        proc.kill()  # Force kill if not terminated

                except Exception as e:
                    self.logger.warning(f"Failed to stop process {proc.pid}: {e}")

        except Exception as e:
            self.logger.warning(f"Error stopping Zed processes: {e}")

    def _extract_version_from_file(self, file_path: Path) -> Optional[str]:
        """Extract version from installed file"""
        try:
            # Simple version extraction - could be enhanced
            return "installed"
        except Exception:
            return None

    def check_and_update(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> UpdateResult:
        """Check for updates and perform installation if available"""
        try:
            # Check for updates
            release_info = self.check_for_updates()
            if not release_info:
                return UpdateResult(
                    success=True,
                    message="No updates available"
                )

            # Download update
            if progress_callback:
                progress_callback(0, "Downloading update...")

            download_path = self.download_update(release_info, progress_callback)
            if not download_path:
                return UpdateResult(
                    success=False,
                    message="Download failed",
                    error_code="DOWNLOAD_FAILED"
                )

            # Install update
            if progress_callback:
                progress_callback(100, "Installing update...")

            install_result = self.install_update(download_path)

            # Auto-start if configured and installation successful
            if (install_result.success and
                self.config.get('auto_start_after_update')):
                self.start_zed()

            return install_result

        except Exception as e:
            error_msg = f"Update check/install failed: {e}"
            self.logger.error(error_msg)
            return UpdateResult(
                success=False,
                message=error_msg,
                error_code="UPDATE_FAILED"
            )

    def start_zed(self) -> bool:
        """Start Zed application"""
        zed_path = self.config.get('zed_install_path')

        if not zed_path or not Path(zed_path).exists():
            self.logger.error(f"Zed executable not found: {zed_path}")
            return False

        try:
            self.logger.info(f"Starting Zed: {zed_path}")
            subprocess.Popen([zed_path], shell=False)
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Zed: {e}")
            return False

    def cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        try:
            temp_dir = self.config.get_temp_dir()
            if temp_dir.exists():
                # Remove old temp files (older than 1 day)
                import time
                current_time = time.time()
                max_age = 24 * 60 * 60  # 1 day

                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        if current_time - file_path.stat().st_mtime > max_age:
                            try:
                                file_path.unlink()
                                self.logger.debug(f"Cleaned temp file: {file_path}")
                            except Exception as e:
                                self.logger.warning(f"Failed to clean temp file {file_path}: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")