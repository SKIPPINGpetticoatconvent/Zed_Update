#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络工具模块
提供网络请求、下载和代理设置等功能
"""

import os
import sys
import time
import requests
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional, Callable, Union, Tuple, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def setup_proxy(proxy_url: Optional[str] = None):
    """
    设置HTTP/HTTPS代理

    Args:
        proxy_url: 代理URL，格式为 "http://host:port" 或 "https://host:port"
                   如果为None，则使用环境变量中的代理设置

    Returns:
        Dict: 包含代理设置的字典，可直接用于requests库
    """
    proxies = {}

    if proxy_url:
        # 使用指定的代理
        if proxy_url.startswith(('http://', 'https://')):
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        else:
            # 添加协议前缀
            proxies = {
                'http': f"http://{proxy_url}",
                'https': f"https://{proxy_url}"
            }
        logger.info(f"已设置代理: {proxy_url}")
    else:
        # 从环境变量获取代理设置
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy

        if proxies:
            logger.info(f"使用环境变量中的代理设置: {proxies}")

    return proxies

def get_json(url: str,
             headers: Optional[Dict] = None,
             proxies: Optional[Dict] = None,
             timeout: int = 30,
             retry_count: int = 3) -> Optional[Dict]:
    """
    发送GET请求并返回JSON响应

    Args:
        url: 请求URL
        headers: 请求头
        proxies: 代理设置
        timeout: 超时时间(秒)
        retry_count: 重试次数

    Returns:
        成功返回JSON数据字典，失败返回None
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }

    for attempt in range(retry_count + 1):
        try:
            logger.debug(f"GET请求: {url} (尝试 {attempt+1}/{retry_count+1})")
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=timeout,
                verify=True
            )

            response.raise_for_status()  # 抛出HTTP错误

            # 尝试解析JSON
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败 ({e.__class__.__name__}): {e}")
            if attempt < retry_count:
                wait_time = 2 ** attempt  # 指数退避策略
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"请求失败，已达到最大重试次数: {url}")
                return None

        except ValueError as e:
            logger.error(f"JSON解析失败: {e}")
            return None

    return None

def download_file(url: str,
                  output_path: Optional[Union[str, Path]] = None,
                  progress_callback: Optional[Callable[[float, str], None]] = None,
                  proxies: Optional[Dict] = None,
                  timeout: int = 300,
                  retry_count: int = 3,
                  chunk_size: int = 8192) -> Optional[Path]:
    """
    下载文件并显示进度

    Args:
        url: 下载URL
        output_path: 输出文件路径，如果为None则使用临时文件
        progress_callback: 进度回调函数，接收参数(progress_percentage, status_message)
        proxies: 代理设置
        timeout: 超时时间(秒)
        retry_count: 重试次数
        chunk_size: 每次读取的块大小(字节)

    Returns:
        成功返回下载文件的Path对象，失败返回None
    """
    # 如果没有指定输出路径，创建临时文件
    if output_path is None:
        temp_dir = Path(tempfile.gettempdir()) / "zed_updater_downloads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 从URL中提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"download_{int(time.time())}.tmp"

        output_path = temp_dir / filename

    # 确保output_path是Path对象
    if isinstance(output_path, str):
        output_path = Path(output_path)

    # 创建目录
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    for attempt in range(retry_count + 1):
        try:
            # 开始下载
            if progress_callback:
                progress_callback(0, f"开始下载 (尝试 {attempt+1}/{retry_count+1})")

            # 创建临时下载文件
            temp_file = output_path.with_suffix('.downloading')

            with requests.get(url, headers=headers, proxies=proxies, stream=True, timeout=timeout) as response:
                response.raise_for_status()

                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0))

                # 已下载大小
                downloaded_size = 0

                # 最后一次进度更新时间
                last_update_time = time.time()

                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 更新进度
                            current_time = time.time()
                            if current_time - last_update_time > 0.5 or downloaded_size == total_size:  # 每0.5秒更新一次
                                if total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    speed = downloaded_size / (current_time - last_update_time + 0.1)

                                    if progress_callback:
                                        status = f"已下载: {downloaded_size/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB ({speed/1024/1024:.1f}MB/s)"
                                        progress_callback(progress, status)

                                    last_update_time = current_time

            # 下载完成，重命名文件
            if temp_file.exists():
                if output_path.exists():
                    output_path.unlink()
                temp_file.rename(output_path)

                if progress_callback:
                    progress_callback(100, f"下载完成: {output_path.name}")

                logger.info(f"文件下载成功: {output_path}")
                return output_path

        except requests.exceptions.RequestException as e:
            logger.warning(f"下载失败 ({e.__class__.__name__}): {e}")

            # 清理临时文件
            if 'temp_file' in locals() and temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass

            if attempt < retry_count:
                wait_time = 2 ** attempt  # 指数退避策略
                if progress_callback:
                    progress_callback(0, f"下载失败，{wait_time}秒后重试...")
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"下载失败，已达到最大重试次数: {url}")
                if progress_callback:
                    progress_callback(0, "下载失败，请检查网络连接")
                return None

        except Exception as e:
            logger.error(f"下载过程中发生错误: {e}")
            if progress_callback:
                progress_callback(0, f"下载出错: {str(e)}")

            # 清理临时文件
            if 'temp_file' in locals() and temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass

            return None

    return None

def check_internet_connection(test_url: str = "https://www.baidu.com", timeout: int = 5) -> bool:
    """
    检查网络连接状态

    Args:
        test_url: 用于测试的URL
        timeout: 超时时间(秒)

    Returns:
        有网络连接返回True，否则返回False
    """
    try:
        requests.get(test_url, timeout=timeout)
        return True
    except requests.exceptions.RequestException:
        return False

def get_file_size(url: str, proxies: Optional[Dict] = None, timeout: int = 10) -> Optional[int]:
    """
    获取远程文件大小

    Args:
        url: 文件URL
        proxies: 代理设置
        timeout: 超时时间(秒)

    Returns:
        文件大小(字节)，如果无法获取则返回None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        response = requests.head(url, headers=headers, proxies=proxies, timeout=timeout)
        response.raise_for_status()

        content_length = response.headers.get('content-length')
        if content_length:
            return int(content_length)

    except (requests.exceptions.RequestException, ValueError) as e:
        logger.warning(f"获取文件大小失败: {e}")

    return None
