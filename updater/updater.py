#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed编辑器更新模块
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

logger = logging.getLogger(__name__)

class ZedUpdater:
    """Zed编辑器更新器"""

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
        """从GitHub获取最新版本信息

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

            # 提取版本号
            tag_name = release_info.get('tag_name', '')
            if tag_name.startswith('v'):
                version = tag_name[1:]  # 移除'v'前缀
            else:
                version = tag_name

            self.latest_version = version

            # 查找Windows版本的下载链接
            assets = release_info.get('assets', [])
            download_url = None

            # 寻找Windows版本 (通常包含win、windows或.exe)
            for asset in assets:
                asset_name = asset.get('name', '').lower()
                if any(keyword in asset_name for keyword in ['win', 'windows', '.exe']):
                    download_url = asset.get('browser_download_url')
                    break

            if not download_url and assets:
                # 如果没找到明确的Windows版本，使用第一个资源
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
        """比较版本号

        Args:
            current: 当前版本
            latest: 最新版本

        Returns:
            -1: current < latest
             0: current = latest
             1: current > latest
        """
        try:
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
        """检查是否有可用更新

        Returns:
            bool: 是否有更新可用
        """
        current = self.get_current_version()
        latest_info = self.get_latest_version_info()

        if not current or not latest_info:
            return False

        latest = latest_info['version']

        # 更新最后检查时间
        self.config.set_setting('last_check_time', datetime.now().isoformat())

        return self.compare_versions(current, latest) < 0

    def download_update(self, progress_callback=None) -> Optional[Path]:
        """下载更新文件

        Args:
            progress_callback: 进度回调函数

        Returns:
            下载文件的路径，失败时返回None
        """
        if not self.download_url:
            logger.error("没有可下载的URL")
            return None

        try:
            # 创建临时下载目录
            temp_dir = self.config.get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 确定文件名
            filename = self.download_url.split('/')[-1]
            if not filename.endswith(('.exe', '.zip')):
                filename += '.exe'

            download_path = temp_dir / filename

            # 设置代理
            proxies = None
            if self.config.get_setting('use_proxy'):
                proxy_url = self.config.get_setting('proxy_url')
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}

            timeout = self.config.get_setting('download_timeout', 300)

            logger.info(f"开始下载: {self.download_url}")

            response = self.session.get(self.download_url,
                                      stream=True,
                                      timeout=timeout,
                                      proxies=proxies)
            response.raise_for_status()

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

            logger.info(f"下载完成: {download_path}")
            return download_path

        except Exception as e:
            logger.error(f"下载失败: {e}")
            return None

    def create_backup(self) -> bool:
        """创建当前版本的备份

        Returns:
            bool: 是否备份成功
        """
        try:
            if not self.config.get_setting('backup_enabled'):
                return True

            zed_path = Path(self.config.get_setting('zed_install_path'))
            if not zed_path.exists():
                logger.warning("Zed.exe不存在，无需备份")
                return True

            backup_dir = self.config.get_backup_dir()
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_version = self.current_version or 'unknown'
            backup_name = f"Zed_v{current_version}_{timestamp}.exe"
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
        """清理旧备份文件"""
        try:
            backup_dir = self.config.get_backup_dir()
            if not backup_dir.exists():
                return

            backup_count = self.config.get_setting('backup_count', 3)
            if backup_count <= 0:
                return

            # 获取所有备份文件并按修改时间排序
            backup_files = []
            for file in backup_dir.glob('Zed_v*.exe'):
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
        """安装更新

        Args:
            download_path: 下载文件的路径

        Returns:
            bool: 是否安装成功
        """
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
        """从zip文件中提取exe文件

        Args:
            zip_path: zip文件路径

        Returns:
            提取的exe文件路径
        """
        try:
            temp_dir = self.config.get_temp_dir() / 'extracted'
            temp_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找exe文件
                exe_files = [name for name in zip_ref.namelist()
                           if name.lower().endswith('.exe') and 'zed' in name.lower()]

                if not exe_files:
                    logger.error("zip文件中没有找到Zed.exe")
                    return None

                # 提取第一个找到的exe文件
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
        """检查并执行更新

        Args:
            progress_callback: 进度回调函数

        Returns:
            bool: 是否有更新并成功安装
        """
        try:
            logger.info("检查更新...")

            if not self.has_update_available():
                logger.info("已是最新版本")
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
