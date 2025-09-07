#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed编辑器更新模块 - 支持日期发行版版本管理
负责检查版本、下载和安装更新
"""

import os
import sys
import json
import shutil
import hashlib
import requests
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import logging
import time
import tempfile
import zipfile
import locale

# UTF-8兼容性设置
if sys.platform == 'win32':
    # 确保Windows下的文件操作使用UTF-8编码
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

class ZedUpdater:
    """Zed编辑器更新器 - 支持日期格式发行版"""

    def __init__(self, config):
        """初始化更新器

        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.session = requests.Session()
        self.current_version = None
        self.latest_version = None
        self.download_url = None

        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'ZedUpdater/1.0.0',
            'Accept': 'application/vnd.github.v3+json'
        })

    def get_current_version(self) -> Optional[str]:
        """获取当前安装的Zed版本

        Returns:
            当前版本号，如果无法获取则返回None
        """
        try:
            zed_path = self.config.get_setting('zed_install_path')
            if not Path(zed_path).exists():
                logger.warning(f"Zed.exe不存在: {zed_path}")
                return None

            # 尝试通过命令行获取版本
            try:
                result = subprocess.run([zed_path, '--version'],
                                      capture_output=True,
                                      text=True,
                                      timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.strip().split('\n')[0]
                    # 提取版本号 (假设格式为 "Zed v0.x.x")
                    if 'v' in version_line:
                        version = version_line.split('v')[1].split()[0]
                        self.current_version = version
                        return version
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                logger.warning(f"无法通过命令行获取版本: {e}")

            # 如果命令行方式失败，尝试从文件属性获取
            import win32api
            try:
                info = win32api.GetFileVersionInfo(zed_path, "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}"
                if version != "0.0.0":
                    self.current_version = version
                    return version
            except Exception as e:
                # 处理文件被锁定或其他访问问题
                import pywintypes
                if isinstance(e, pywintypes.error) and e.winerror == 5:  # ERROR_ACCESS_DENIED
                    logger.warning(f"文件被锁定，版本获取失败: {zed_path} 被其他进程占用")
                else:
                    logger.warning(f"无法从文件属性获取版本: {e}")

            # 从配置中获取上次记录的版本
            saved_version = self.config.get_setting('current_version')
            if saved_version:
                self.current_version = saved_version
                return saved_version

        except Exception as e:
            logger.error(f"获取当前版本时出错: {e}")

        return None

    def get_latest_version_info(self) -> Optional[Dict[str, Any]]:
        """从GitHub获取最新版本信息 - 支持日期发行版

        Returns:
            包含版本信息的字典，失败时返回None
        """
        try:
            url = self.config.get_setting('github_api_url')
            timeout = self.config.get_setting('download_timeout', 30)

            # 设置代理
            proxies = None
            if self.config.get_setting('use_proxy'):
                proxy_url = self.config.get_setting('proxy_url')
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}

            response = self.session.get(url, timeout=timeout, proxies=proxies)
            response.raise_for_status()

            release_info = response.json()

            # 提取版本号 - 支持日期格式和传统版本格式
            tag_name = release_info.get('tag_name', '')

            # 对于TC999/zed-loc仓库，tag_name通常是日期格式
            # 对于官方仓库，tag_name通常是v0.x.x格式
            if tag_name.startswith('v'):
                version = tag_name[1:]  # 移除'v'前缀 (传统格式)
            else:
                version = tag_name      # 日期格式或其他格式

            self.latest_version = version

            # 查找Windows版本的下载链接
            assets = release_info.get('assets', [])
            download_url = None

            # 寻找Windows版本 (通常包含win、windows或.zip)
            for asset in assets:
                asset_name = asset.get('name', '').lower()
                if any(keyword in asset_name for keyword in ['win', 'windows', 'zip', 'exe']):
                    if 'windows' in asset_name or 'win' in asset_name:
                        download_url = asset.get('browser_download_url')
                        break

            # 如果没找到特定Windows版本，尝试寻找.zip文件
            if not download_url:
                for asset in assets:
                    asset_name = asset.get('name', '').lower()
                    if 'zip' in asset_name:
                        download_url = asset.get('browser_download_url')
                        break

            if not download_url and assets:
                # 如果还是没找到，使用第一个资源
                download_url = assets[0].get('browser_download_url')

            self.download_url = download_url

            return {
                'version': version,
                'tag_name': tag_name,
                'download_url': download_url,
                'published_at': release_info.get('published_at'),
                'body': release_info.get('body', ''),
                'prerelease': release_info.get('prerelease', False)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"获取最新版本信息失败: {e}")
        except Exception as e:
            logger.error(f"解析版本信息时出错: {e}")

        return None

    def compare_versions(self, current: str, latest: str) -> int:
        """比较版本号 - 支持日期和传统版本格式

        Args:
            current: 当前版本
            latest: 最新版本

        Returns:
            -1: current < latest
             0: current = latest
             1: current > latest
        """
        try:
            # 如果是日期格式，直接按字符串比较 (最新的日期较大)
            if current.isdigit() and latest.isdigit():
                if len(current) == 8 and len(latest) == 8:  # YYYYMMDD 格式
                    if current < latest:
                        return -1
                    elif current > latest:
                        return 1
                    else:
                        return 0

            # 如果其中一个是日期格式，另一个是传统格式
            # 假设日期格式总是更新 (因为是新发行版本)
            if current.isdigit() != latest.isdigit():
                # 如果current是日期格式，latest不是，那么latest更新
                # 如果current不是日期格式，latest是，那么latest更新
                return -1

            # 传统版本比较逻辑
            def parse_version(version):
                # 移除非数字字符，只保留数字和点
                import re
                clean_version = re.sub(r'[^\d.]', '', version)
                parts = clean_version.split('.')
                # 确保至少有3个部分，不足的补0
                while len(parts) < 3:
                    parts.append('0')
                return [int(p) for p in parts[:3]]

            current_parts = parse_version(current)
            latest_parts = parse_version(latest)

            for c, l in zip(current_parts, latest_parts):
                if c < l:
                    return -1
                elif c > l:
                    return 1

            return 0

        except Exception as e:
            logger.error(f"版本比较出错: {e}")
            # 如果比较失败，假设需要更新
            return -1

    def has_update_available(self) -> bool:
        """检查是否有可用更新 - 适用于日期发行版

        Returns:
            bool: 是否有更新可用
        """
        current = self.get_current_version()
        latest_info = self.get_latest_version_info()

        if not latest_info:
            return False

        latest = latest_info['version']

        # 对于日期格式，新的日期总是代表更新版本
        if not current:
            return True

        # 更新最后检查时间
        self.config.set_setting('last_check_time', datetime.now().isoformat())

        if current == latest:
            return False
        elif current.isdigit() and latest.isdigit() and len(current) == 8 and len(latest) == 8:
            # 日期格式比较
            return current < latest
        else:
            # 其他情况使用版本比较
            return self.compare_versions(current, latest) < 0

    def _safe_filename_from_url(self, url: str) -> str:
        """从URL安全提取文件名"""
        from urllib.parse import urlparse
        from pathlib import Path

        parsed = urlparse(url)
        filename = Path(parsed.path).name

        # 验证文件名安全，移除路径遍历字符
        if not filename or any(invalid in filename for invalid in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            # 生成安全文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"zed_update_{timestamp}.zip"

        return filename

    def _retry_request(self, url: str, max_retries: int = 3, backoff_factor: float = 2.0,
                      progress_callback=None, proxies=None, timeout: int = 300):
        """带重试机制的HTTP请求"""
        for attempt in range(max_retries):
            try:
                logger.info(f"下载尝试 {attempt + 1}/{max_retries}: {url}")

                response = self.session.get(url, stream=True, timeout=timeout, proxies=proxies)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"所有重试都失败: {e}")
                    raise

                wait_time = backoff_factor ** attempt
                logger.warning(f"请求失败，重试 {attempt + 1}/{max_retries}，等待 {wait_time:.1f}s: {e}")
                time.sleep(wait_time)

    def download_update(self, progress_callback=None) -> Optional[Path]:
        """下载更新文件"""
        if not self.download_url:
            logger.error("没有可下载的URL")
            return None

        try:
            # 创建临时下载目录
            temp_dir = self.config.get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 确定安全的文件名
            filename = self._safe_filename_from_url(self.download_url)
            if not filename.endswith(('.exe', '.zip')):
                filename += '.zip'  # 默认使用zip扩展名

            download_path = temp_dir / filename

            # 设置代理
            proxies = None
            if self.config.get_setting('use_proxy'):
                proxy_url = self.config.get_setting('proxy_url')
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}

            timeout = self.config.get_setting('download_timeout', 300)
            retry_count = self.config.get_setting('retry_count', 3)

            logger.info(f"开始下载: {self.download_url}")

            # 使用重试机制获取响应
            response = self._retry_request(self.download_url, max_retries=retry_count,
                                          backoff_factor=1.5, progress_callback=progress_callback,
                                          proxies=proxies, timeout=timeout)

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)

            # 验证下载的文件大小
            if total_size > 0 and download_path.stat().st_size != total_size:
                logger.error("下载文件大小不匹配，可能不完整")
                download_path.unlink()
                return None

            logger.info(f"下载完成: {download_path} ({downloaded} bytes)")
            return download_path

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return None
        except OSError as e:
            logger.error(f"文件系统错误: {e}")
            return None
        except Exception as e:
            logger.error(f"下载过程中发生意外错误: {e}")
            return None

    def create_backup(self) -> bool:
        """创建当前版本的备份"""
        try:
            if not self.config.get_setting('backup_enabled'):
                return True

            zed_path = Path(self.config.get_setting('zed_install_path'))
            if not zed_path.exists():
                logger.warning("Zed.exe不存在，无需备份")
                return True

            backup_dir = self.config.get_backup_dir()
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名 - 支持日期和版本格式
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_version = self.current_version or 'unknown'
            if current_version.isdigit():
                backup_name = f"Zed_{current_version}_{timestamp}.exe"  # 日期格式
            else:
                backup_name = f"Zed_v{current_version}_{timestamp}.exe"  # 版本格式

            backup_path = backup_dir / backup_name

            # 复制文件
            shutil.copy2(zed_path, backup_path)
            logger.info(f"备份创建成功: {backup_path}")

            # 清理旧备份
            self._cleanup_old_backups()

            return True

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False

    def _cleanup_old_backups(self):
        """清理旧备份文件 - 支持日期和版本格式"""
        try:
            backup_dir = self.config.get_backup_dir()
            if not backup_dir.exists():
                return

            backup_count = self.config.get_setting('backup_count', 3)
            if backup_count <= 0:
                return

            # 获取所有备份文件并按修改时间排序
            backup_files = []
            for file in backup_dir.glob('Zed_*.exe'):
                backup_files.append((file.stat().st_mtime, file))

            backup_files.sort(key=lambda x: x[0], reverse=True)

            # 删除多余的备份文件
            for _, backup_file in backup_files[backup_count:]:
                try:
                    backup_file.unlink()
                    logger.info(f"删除旧备份: {backup_file}")
                except Exception as e:
                    logger.warning(f"删除备份文件失败: {e}")

        except Exception as e:
            logger.error(f"清理备份文件时出错: {e}")

    def install_update(self, download_path: Path) -> bool:
        """安装更新"""
        try:
            zed_path = Path(self.config.get_setting('zed_install_path'))

            # 停止正在运行的Zed进程
            self._stop_zed_processes()

            # 创建备份
            if not self.create_backup():
                logger.warning("备份失败，但继续安装")

            # 等待一段时间确保进程完全停止
            time.sleep(2)

            # 如果下载的是zip文件，需要解压
            if download_path.suffix.lower() == '.zip':
                extracted_exe = self._extract_exe_from_zip(download_path)
                if not extracted_exe:
                    return False
                install_source = extracted_exe
            else:
                install_source = download_path

            # 替换文件
            if zed_path.exists():
                # 先移动到临时位置
                temp_old = zed_path.with_suffix('.exe.old')
                if temp_old.exists():
                    temp_old.unlink()
                zed_path.rename(temp_old)

            # 复制新文件
            shutil.copy2(install_source, zed_path)

            # 删除临时文件
            if zed_path.with_suffix('.exe.old').exists():
                zed_path.with_suffix('.exe.old').unlink()

            # 更新配置中的版本信息
            if self.latest_version:
                self.config.set_setting('current_version', self.latest_version)
                self.config.set_setting('last_update_time', datetime.now().isoformat())

            logger.info(f"更新安装成功: {zed_path}")
            return True

        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            # 尝试恢复
            try:
                temp_old = Path(self.config.get_setting('zed_install_path')).with_suffix('.exe.old')
                if temp_old.exists():
                    zed_path = Path(self.config.get_setting('zed_install_path'))
                    if zed_path.exists():
                        zed_path.unlink()
                    temp_old.rename(zed_path)
                    logger.info("已恢复原文件")
            except Exception as restore_e:
                logger.error(f"恢复原文件失败: {restore_e}")

            return False

    def _extract_exe_from_zip(self, zip_path: Path) -> Optional[Path]:
        """从zip文件中提取exe文件"""
        try:
            temp_dir = self.config.get_temp_dir() / 'extracted'
            temp_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找exe文件 - 优先查找zed-release/zed.exe
                exe_files = [name for name in zip_ref.namelist()
                           if name.lower().endswith('.exe')]

                if not exe_files:
                    logger.error("zip文件中没有找到exe文件")
                    return None

                # 优先选择包含zed的exe文件
                zed_files = [f for f in exe_files if 'zed' in f.lower()]
                if zed_files:
                    exe_name = zed_files[0]
                else:
                    exe_name = exe_files[0]

                zip_ref.extract(exe_name, temp_dir)

                extracted_path = temp_dir / exe_name
                return extracted_path

        except Exception as e:
            logger.error(f"解压zip文件失败: {e}")
            return None

    def _stop_zed_processes(self):
        """停止所有Zed进程"""
        try:
            import psutil

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'zed' in proc.info['name'].lower():
                        logger.info(f"终止Zed进程: {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass

        except ImportError:
            # 如果psutil不可用，使用系统命令
            try:
                subprocess.run(['taskkill', '/f', '/im', 'zed.exe'],
                             capture_output=True, timeout=10)
            except Exception as e:
                logger.warning(f"无法停止Zed进程: {e}")

    def start_zed(self) -> bool:
        """启动Zed编辑器

        Returns:
            bool: 是否启动成功
        """
        try:
            zed_path = self.config.get_setting('zed_install_path')
            if not Path(zed_path).exists():
                logger.error(f"Zed.exe不存在: {zed_path}")
                return False

            # 启动Zed
            subprocess.Popen([zed_path],
                           cwd=Path(zed_path).parent,
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

            logger.info("Zed已启动")
            return True

        except Exception as e:
            logger.error(f"启动Zed失败: {e}")
            return False

    def check_and_update(self, progress_callback=None) -> bool:
        """检查并执行更新 - 对于日期发行版，总是下载最新版本

        Args:
            progress_callback: 进度回调函数

        Returns:
            bool: 是否有更新并成功安装
        """
        try:
            logger.info("检查更新...")

            latest_info = self.get_latest_version_info()
            if not latest_info:
                logger.error("无法获取最新版本信息")
                return False

            logger.info(f"发现新版本: {self.latest_version}")

            # 下载更新
            if progress_callback:
                progress_callback(0, "开始下载...")

            download_path = self.download_update(
                lambda p: progress_callback(p * 0.8, "下载中...") if progress_callback else None
            )

            if not download_path:
                logger.error("下载失败")
                return False

            # 安装更新
            if progress_callback:
                progress_callback(80, "安装中...")

            success = self.install_update(download_path)

            if success:
                if progress_callback:
                    progress_callback(100, "更新完成")
                logger.info("更新完成")

                # 清理下载文件
                try:
                    if download_path.exists():
                        download_path.unlink()
                except Exception as e:
                    logger.warning(f"清理下载文件失败: {e}")

            return success

        except Exception as e:
            logger.error(f"更新过程中出错: {e}")
            if progress_callback:
                progress_callback(-1, f"更新失败: {str(e)}")
            return False

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dir = self.config.get_temp_dir()
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")