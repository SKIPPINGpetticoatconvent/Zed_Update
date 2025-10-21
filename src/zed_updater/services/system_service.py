#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System service for Zed Updater - handles system operations
"""

import os
import platform
import psutil
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger


class SystemService:
    """Service for system operations and information"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': os.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': self._get_disk_usage(),
                'network_interfaces': self._get_network_info(),
                'uptime': self._get_system_uptime()
            }

            return info

        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {'error': str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                'network_connections': len(psutil.net_connections()),
                'running_processes': len(list(psutil.process_iter())),
                'timestamp': psutil.time.time()
            }

            return status

        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            }
        except Exception:
            return {}

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network interface information"""
        try:
            interfaces = {}
            for name, addrs in psutil.net_if_addrs().items():
                interfaces[name] = []
                for addr in addrs:
                    if addr.family.name == 'AF_INET':
                        interfaces[name].append({
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
            return interfaces
        except Exception:
            return {}

    def _get_system_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            return psutil.time.time() - psutil.boot_time()
        except Exception:
            return 0.0

    def find_processes_by_name(self, name_pattern: str) -> list[Dict[str, Any]]:
        """Find processes by name pattern"""
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['name'] and name_pattern.lower() in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': proc.info['exe'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue

        except Exception as e:
            self.logger.error(f"Failed to find processes: {e}")

        return processes

    def terminate_process(self, pid: int, timeout: int = 10) -> bool:
        """Terminate a process by PID"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()

            # Wait for process to terminate
            try:
                proc.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                # Force kill if not terminated
                proc.kill()
                proc.wait(timeout=5)
                return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            self.logger.error(f"Failed to terminate process {pid}: {e}")
            return False

    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed process information"""
        try:
            proc = psutil.Process(pid)
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'exe': proc.exe(),
                'cwd': proc.cwd(),
                'cmdline': proc.cmdline(),
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent(),
                'memory_info': proc.memory_info()._asdict(),
                'status': proc.status(),
                'create_time': proc.create_time()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            self.logger.error(f"Failed to get process info for {pid}: {e}")
            return None

    def is_process_running(self, pid: int) -> bool:
        """Check if a process is running"""
        try:
            psutil.Process(pid)
            return True
        except psutil.NoSuchProcess:
            return False

    def get_available_space(self, path: str = ".") -> Optional[int]:
        """Get available disk space in bytes"""
        try:
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize
        except (OSError, AttributeError):
            # Windows fallback
            try:
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(path),
                    None,
                    None,
                    ctypes.pointer(free_bytes)
                )
                return free_bytes.value
            except Exception:
                return None

    def ensure_directory(self, path: str) -> bool:
        """Ensure directory exists"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()
            return {
                'path': str(path.absolute()),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': path.is_file(),
                'is_dir': path.is_dir()
            }
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {e}")
            return None