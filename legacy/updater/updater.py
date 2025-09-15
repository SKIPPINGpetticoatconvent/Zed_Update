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

        except (OSError, ValueError, TypeError) as e:
            logger.error(f"获取当前版本时出错: {type(e).__name__}: {e}")
        except ImportError as e:
            logger.error(f"缺少必需的模块: {e}")
        except Exception as e:
            logger.error(f"获取当前版本时发生意外错误: {type(e).__name__}: {e}")

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

        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"版本格式错误，无法比较: {type(e).__name__}: {e}")
            # 如果比较失败，假设需要更新
            return -1
        except Exception as e:
            logger.error(f"版本比较时发生意外错误: {type(e).__name__}: {e}")
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

    def _safe_filename_from_url(self, url: str) -> str:
        """从URL生成安全的文件名

        处理特殊字符、路径分隔符和潜在的路径遍历尝试
        """
        try:
            from urllib.parse import urlparse, unquote
            import re

            # 验证URL格式
            if not url or not isinstance(url, str):
                raise ValueError("无效的URL")

            # 解析URL并获取路径部分
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("URL格式不正确")

            path = unquote(parsed_url.path)

            # 检查路径遍历攻击
            if any(traversal in path for traversal in ['..', '../', '..\\', '\\..']):
                raise ValueError("检测到路径遍历攻击")

            # 获取基本文件名 (最后一部分)
            filename = os.path.basename(path)

            # 如果URL没有有效的文件名部分，使用域名加时间戳
            if not filename or filename == "/" or "." not in filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                domain = parsed_url.netloc.split(':')[0]  # 移除端口号
                # 清理域名中的不安全字符
                domain = re.sub(r'[^\w\-]', '_', domain)
                filename = f"{domain}_{timestamp}.zip"

            # 删除所有不安全字符，只保留字母、数字、下划线、点和连字符
            filename = re.sub(r'[^\w\-\.]', '_', filename)

            # 确保文件名不以点开头（防止隐藏文件）
            filename = filename.lstrip('.')

            # 确保文件名不包含路径分隔符
            if os.sep in filename or (os.altsep and os.altsep in filename):
                raise ValueError("文件名包含路径分隔符")

            # 如果文件名为空，使用默认名称
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"download_{timestamp}.zip"

            # 限制文件名长度
            if len(filename) > 100:
                name, ext = os.path.splitext(filename)
                filename = name[:95] + ext

            # 最终验证：确保文件名是安全的
            if not filename or '..' in filename or filename.startswith('.'):
                raise ValueError("生成的文件名不安全")

            return filename

        except (ValueError, TypeError) as e:
            logger.error(f"生成安全文件名时出错: {type(e).__name__}: {e}")
            # 出错时返回带时间戳的默认文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"zed_update_{timestamp}.zip"
        except Exception as e:
            logger.error(f"生成安全文件名时发生意外错误: {type(e).__name__}: {e}")
            # 出错时返回带时间戳的默认文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"zed_update_{timestamp}.zip"

    def download_update(self, progress_callback=None) -> Optional[Path]:
        """下载更新文件"""
        if not self.download_url:
            logger.error("没有可下载的URL")
            return None

        # 记录开始下载的详细信息
        logger.info(f"开始下载更新: URL={self.download_url}")

        try:
            # 创建临时下载目录
            temp_dir = self.config.get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 确定安全的文件名
            try:
                filename = self._safe_filename_from_url(self.download_url)
                if not filename.endswith(('.exe', '.zip')):
                    filename += '.zip'  # 默认使用zip扩展名
                logger.info(f"处理后的文件名: {filename}")
            except Exception as e:
                logger.error(f"生成文件名时出错: {e}")
                # 使用默认文件名作为备选
                import datetime
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"zed_update_{timestamp}.zip"
                logger.info(f"使用备用文件名: {filename}")

            download_path = temp_dir / filename
            logger.info(f"下载路径: {download_path}")

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
            try:
                response = self._retry_request(self.download_url, max_retries=retry_count,
                                              backoff_factor=1.5, progress_callback=progress_callback,
                                              proxies=proxies, timeout=timeout)

                if response is None:
                    logger.error("重试请求后未能获取有效响应")
                    return None

                if response.status_code != 200:
                    logger.error(f"服务器响应错误: HTTP {response.status_code}")
                    return None

                logger.info(f"请求成功: 状态码={response.status_code}")

            except Exception as e:
                logger.error(f"请求处理失败: {e}")
                return None

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            logger.info(f"文件总大小: {total_size} 字节")

            try:
                with open(download_path, 'wb') as f:
                    chunk_size = 8192
                    logger.info(f"开始写入文件，块大小: {chunk_size} 字节")
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(progress)

                                # 每10%记录一次进度
                                if int(progress) % 10 == 0 and int(progress) > 0:
                                    logger.info(f"下载进度: {int(progress)}% ({downloaded}/{total_size} 字节)")
            except Exception as e:
                logger.error(f"写入文件时出错: {e}")
                # 清理可能损坏的文件
                if download_path.exists():
                    try:
                        download_path.unlink()
                        logger.info("已删除可能损坏的下载文件")
                    except:
                        pass
                return None

            # 验证下载的文件大小
            try:
                actual_size = download_path.stat().st_size
                logger.info(f"验证文件大小: 预期={total_size}, 实际={actual_size}")

                if total_size > 0 and actual_size != total_size:
                    logger.error(f"下载文件大小不匹配，可能不完整: 预期={total_size}, 实际={actual_size}")
                    download_path.unlink()
                    return None

                # 基本文件有效性检查
                if actual_size == 0:
                    logger.error("下载的文件大小为0，文件无效")
                    download_path.unlink()
                    return None

                # 验证文件是否是有效的二进制文件
                with open(download_path, 'rb') as f:
                    magic_bytes = f.read(4)
                    # ZIP 文件头: PK\x03\x04 或 exe文件头: MZ
                    is_valid = (magic_bytes.startswith(b'PK\x03\x04') or magic_bytes.startswith(b'MZ'))
                    if not is_valid:
                        logger.error(f"下载的文件不是有效的ZIP或EXE文件 (magic bytes: {magic_bytes.hex()})")
                        download_path.unlink()
                        return None
            except Exception as e:
                logger.error(f"验证文件时出错: {e}")
                if download_path.exists():
                    try:
                        download_path.unlink()
                    except:
                        pass
                return None

            logger.info(f"下载完成并验证通过: {download_path} ({downloaded} bytes)")
            return download_path

        except requests.exceptions.ConnectTimeout as e:
            logger.error(f"连接超时: {e}")
            return None
        except requests.exceptions.ReadTimeout as e:
            logger.error(f"读取超时: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误 (可能是网络问题): {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return None
        except OSError as e:
            logger.error(f"文件系统错误: {str(e)}")
            # 记录详细错误类型
            import errno
            if hasattr(e, 'errno'):
                error_name = errno.errorcode.get(e.errno, "未知错误码")
                logger.error(f"OS错误详情: {error_name} (错误码 {e.errno})")
            return None
        except MemoryError:
            logger.error("内存不足错误")
            return None
        except Exception as e:
            logger.error(f"下载过程中发生意外错误: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
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
        if download_path is None or not download_path.exists():
            logger.error("无效的下载路径，无法安装更新")
            return False

        logger.info(f"开始安装更新: {download_path}")

        try:
            zed_path = Path(self.config.get_setting('zed_install_path'))
            logger.info(f"目标安装路径: {zed_path}")

            # 检查目标路径是否有效
            if not zed_path.parent.exists():
                logger.error(f"目标目录不存在: {zed_path.parent}")
                return False

            # 停止正在运行的Zed进程
            self._stop_zed_processes()

            # 创建备份
            backup_success = self.create_backup()
            if not backup_success:
                logger.warning("备份失败，但继续安装")

            # 等待一段时间确保进程完全停止
            time.sleep(2)

            # 如果下载的是zip文件，需要解压
            if download_path.suffix.lower() == '.zip':
                logger.info("检测到ZIP文件，开始解压")
                extracted_exe = self._extract_exe_from_zip(download_path)
                if not extracted_exe:
                    logger.error("无法从ZIP文件中提取可执行文件")
                    return False
                install_source = extracted_exe
                logger.info(f"成功解压出可执行文件: {install_source}")
            else:
                install_source = download_path
                logger.info(f"直接使用下载的可执行文件: {install_source}")

            # 验证文件是否是可执行文件
            try:
                with open(install_source, 'rb') as f:
                    header = f.read(2)
                    if header != b'MZ':  # DOS MZ头
                        logger.error(f"提取的文件不是有效的Windows可执行文件 (header: {header.hex()})")
                        return False
            except Exception as e:
                logger.error(f"验证可执行文件时出错: {e}")
                return False

            # 替换文件
            temp_old = None
            try:
                if zed_path.exists():
                    logger.info(f"目标文件已存在，准备备份: {zed_path}")
                    # 先移动到临时位置
                    temp_old = zed_path.with_suffix('.exe.old')
                    if temp_old.exists():
                        logger.info(f"删除已存在的旧备份: {temp_old}")
                        temp_old.unlink()
                    logger.info(f"将当前文件重命名为: {temp_old}")
                    zed_path.rename(temp_old)
                else:
                    logger.info(f"目标文件不存在，将直接创建: {zed_path}")

                # 复制新文件
                logger.info(f"复制新文件: {install_source} -> {zed_path}")
                shutil.copy2(install_source, zed_path)

                # 验证复制后的文件
                if not zed_path.exists():
                    logger.error("复制后的文件不存在")
                    raise Exception("文件复制失败")

                file_size = zed_path.stat().st_size
                source_size = install_source.stat().st_size
                if file_size != source_size:
                    logger.error(f"复制后的文件大小不匹配: 源={source_size}, 目标={file_size}")
                    raise Exception("文件复制不完整")

                logger.info(f"文件复制成功: 大小={file_size} 字节")
            except Exception as e:
                logger.error(f"替换文件过程中出错: {e}")
                # 尝试恢复原文件
                if temp_old and temp_old.exists() and not zed_path.exists():
                    try:
                        logger.info("尝试恢复原文件")
                        temp_old.rename(zed_path)
                    except Exception as restore_e:
                        logger.error(f"恢复原文件失败: {restore_e}")
                return False

            # 删除临时文件
            try:
                if zed_path.with_suffix('.exe.old').exists():
                    logger.info(f"删除临时备份文件: {zed_path.with_suffix('.exe.old')}")
                    zed_path.with_suffix('.exe.old').unlink()
            except Exception as e:
                logger.warning(f"清理临时文件失败 (不影响更新结果): {e}")

            # 更新配置中的版本信息
            try:
                if self.latest_version:
                    logger.info(f"更新配置中的版本信息: {self.latest_version}")
                    self.config.set_setting('current_version', self.latest_version)
                    self.config.set_setting('last_update_time', datetime.now().isoformat())
            except Exception as e:
                logger.warning(f"更新配置信息失败 (不影响更新结果): {e}")

            logger.info(f"更新安装成功: {zed_path}")
            return True

        except PermissionError as e:
            logger.error(f"安装更新时权限错误 (文件可能被占用): {e}")
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
        except OSError as e:
            logger.error(f"安装更新时系统错误: {e}")
            # 记录更详细的错误信息
            import errno
            if hasattr(e, 'errno'):
                error_name = errno.errorcode.get(e.errno, "未知错误码")
                logger.error(f"OS错误详情: {error_name} (错误码 {e.errno})")
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
        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
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
