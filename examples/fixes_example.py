#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Updater 代码修复示例
演示如何应用推荐的修复
"""

import requests
import tempfile
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Union
import threading
import time

# 示例1: 安全的文件名处理
def safe_filename_from_url(url: str) -> str:
    """从URL安全提取文件名，防止路径遍历攻击"""
    from urllib.parse import urlparse
    from pathlib import Path
    import re

    parsed = urlparse(url)
    filename = Path(parsed.path).name

    # 移除或替换危险字符
    if not filename or any(char in filename for char in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        # 生成安全的默认文件名
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"zed_update_{timestamp}.exe"

    return filename

# 示例2: 带重试机制的网络请求
def robust_http_request(url: str, max_retries: int = 3, backoff_factor: float = 2.0,
                       timeout: int = 30, **kwargs) -> Optional[requests.Response]:
    """带重试和指数退避的HTTP请求"""
    from requests.exceptions import RequestException, ConnectionError, Timeout

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response

        except (ConnectionError, Timeout, RequestException) as e:
            if attempt == max_retries - 1:
                logging.error(f"请求失败，已重试 {max_retries} 次: {e}")
                return None

            wait_time = backoff_factor ** attempt
            logging.warning(f"请求失败，将在 {wait_time:.1f} 秒后重试 ({attempt + 1}/{max_retries}): {e}")
            time.sleep(wait_time)

    return None

# 示例3: 线程安全的配置管理
class ThreadSafeConfig:
    """线程安全的配置管理器"""

    def __init__(self):
        self._config = {}
        self._lock = threading.RLock()  # 递归锁允许同一线程嵌套加锁

    def set_setting(self, key: str, value) -> None:
        """线程安全的设置配置项"""
        with self._lock:
            self._config[key] = value

    def get_setting(self, key: str, default=None):
        """线程安全的获取配置项"""
        with self._lock:
            return self._config.get(key, default)

    def update_settings(self, settings: dict) -> None:
        """线程安全的批量更新配置项"""
        with self._lock:
            self._config.update(settings)

# 示例4: 原子文件写入
def atomic_write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8-sig') -> bool:
    """原子写入文件，防止部分写入导致的数据损坏"""
    file_path = Path(file_path)

    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建临时文件
        temp_fd = None
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp',
                                               dir=file_path.parent,
                                               prefix='atomic_write_')

            # 写入临时文件
            with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)
            temp_fd = None  # 防止重复关闭

            # 原子替换原文件
            os.replace(temp_path, file_path)
            logging.info(f"成功原子写入文件: {file_path}")
            return True

        except Exception as e:
            # 清理临时文件
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except:
                    pass

            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

            logging.error(f"原子写入失败: {e}")
            raise e

    except Exception as e:
        logging.error(f"文件操作失败: {e}")
        return False

# 示例5: 编码兼容性处理
def read_file_with_fallback(file_path: Union[str, Path], fallback_encodings=None) -> Optional[str]:
    """使用多种编码尝试读取文件"""
    if fallback_encodings is None:
        fallback_encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin1']

    file_path = Path(file_path)

    for encoding in fallback_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            logging.debug(f"成功使用 {encoding} 编码读取文件: {file_path}")
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.warning(f"读取文件失败 ({encoding}): {e}")
            break

    logging.error(f"无法读取文件，所有编码都失败: {file_path}")
    return None

# 示例6: 资源限制的回调管理
class LimitedCallbackManager:
    """限制回调数量的回调管理器"""

    def __init__(self, max_callbacks: int = 50):
        self.max_callbacks = max_callbacks
        self.callbacks = []
        self._lock = threading.RLock()

    def add_callback(self, callback) -> bool:
        """添加回调函数，如果超过限制则返回False"""
        with self._lock:
            if len(self.callbacks) >= self.max_callbacks:
                logging.warning("回调函数数量已达上限，无法添加新回调")
                return False

            if callback not in self.callbacks:
                self.callbacks.append(callback)
                logging.debug(f"成功添加回调函数，现在有 {len(self.callbacks)} 个回调")
                return True
            return False

    def remove_callback(self, callback) -> bool:
        """移除回调函数"""
        with self._lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
                return True
            return False

    def notify_callbacks(self, *args, **kwargs) -> int:
        """通知所有回调函数，返回成功通知的数量"""
        with self._lock:
            success_count = 0
            for callback in self.callbacks[:]:  # 复制列表避免迭代时修改
                try:
                    callback(*args, **kwargs)
                    success_count += 1
                except Exception as e:
                    logging.error(f"回调函数执行失败: {e}")
            return success_count

# 示例7: 智能延迟调度
def smart_delayed_execution(func, delay_seconds: float, max_delay: float = 300):
    """智能延迟执行函数，根据系统负载调整延迟时间"""
    import psutil
    import os

    # 根据CPU使用率调整延迟时间
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # CPU使用率较高时增加延迟
        if cpu_percent > 80:
            adjusted_delay = min(delay_seconds * 2, max_delay)
            logging.info(f"系统负载较高，延迟从 {delay_seconds}s 增加到 {adjusted_delay}s")
            delay_seconds = adjusted_delay
        elif cpu_percent < 20:
            # 系统空闲时可以稍微减少延迟
            adjusted_delay = max(delay_seconds * 0.5, 0.1)
            delay_seconds = adjusted_delay

    except (ImportError, Exception) as e:
        logging.debug(f"无法获取系统负载信息: {e}")

    # 执行延迟
    time.sleep(delay_seconds)

    # 在线程中执行函数
    thread = threading.Thread(target=func, daemon=True)
    thread.start()
    return thread

# 示例8: 内存安全的日志读取
def read_log_file_safely(log_path: Union[str, Path], max_lines: int = 1000,
                        chunk_size: int = 8192) -> str:
    """内存安全地读取日志文件，只返回最后N行"""
    log_path = Path(log_path)

    if not log_path.exists():
        return "日志文件不存在"

    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            # 获取文件大小
            f.seek(0, 2)  # 移动到文件末尾
            file_size = f.tell()

            if file_size == 0:
                return "日志文件为空"

            # 从文件末尾开始读取
            lines = []
            buffer = ""
            position = file_size

            while len(lines) < max_lines and position > 0:
                # 每次读取一个块
                read_size = min(chunk_size, position)
                position -= read_size
                f.seek(position)

                chunk = f.read(read_size)
                buffer = chunk + buffer

                # 按行分割
                temp_lines = buffer.split('\n')

                # 如果不是最后一个块，保留不完整的行
                if position > 0:
                    buffer = temp_lines[0]
                    temp_lines = temp_lines[1:]

                # 添加完整的行
                lines.extend(temp_lines[::-1])  # 反转顺序

            # 返回最后max_lines行
            result_lines = lines[-max_lines:] if lines else ["无日志内容"]
            return '\n'.join(result_lines[::-1])  # 再次反转以恢复正确顺序

    except Exception as e:
        return f"读取日志文件失败: {e}"

# 示例9: 安全的进程终止
def safely_terminate_process(process_name: str, timeout: int = 10) -> bool:
    """安全地终止进程，支持多种终止方式"""
    try:
        import psutil
        import signal
        import subprocess

        terminated = False

        # 方法1: 使用psutil终止进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    logging.info(f"发现进程: {proc.info['pid']} - {proc.info['name']}")

                    # 尝试优雅终止
                    proc.terminate()
                    terminated = True

                    # 等待进程终止
                    try:
                        proc.wait(timeout=timeout)
                        logging.info(f"进程 {proc.info['pid']} 已终止")
                    except psutil.TimeoutExpired:
                        logging.warning(f"进程 {proc.info['pid']} 未能优雅终止，强制终止")
                        proc.kill()

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 方法2: 如果psutil不可用，使用系统命令
        if not terminated:
            try:
                if os.name == 'nt':  # Windows
                    result = subprocess.run(['taskkill', '/f', '/im', process_name],
                                          capture_output=True, timeout=timeout, check=True, text=True)
                    terminated = result.returncode == 0
                else:  # Unix-like
                    result = subprocess.run(['pkill', '-f', process_name],
                                          capture_output=True, timeout=timeout, check=False, text=True)
                    terminated = result.returncode in [0, 1]  # 0=成功, 1=未找到进程
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                terminated = False

        return terminated

    except ImportError:
        logging.warning("psutil不可用，使用基本进程终止方法")
        # 备用方法：仅使用系统命令
        try:
            subprocess.run(['taskkill', '/f', '/im', process_name],
                         capture_output=True, timeout=timeout, check=True)
            return True
        except Exception:
            return False
    except Exception as e:
        logging.error(f"终止进程时发生错误: {e}")
        return False

# 示例10: 完整的错误恢复策略
def execute_with_recovery(operation_func, recovery_funcs=None, max_attempts: int = 3):
    """执行操作并在失败时应用恢复策略"""
    from functools import wraps

    if recovery_funcs is None:
        recovery_funcs = []

    for attempt in range(max_attempts):
        try:
            return operation_func()
        except Exception as e:
            logging.warning(f"操作失败 (尝试 {attempt + 1}/{max_attempts}): {e}")

            # 应用恢复策略
            recovery_applied = False
            for recovery_func in recovery_funcs:
                try:
                    recovery_func()
                    recovery_applied = True
                    logging.info("成功应用恢复操作")
                    break
                except Exception as recovery_e:
                    logging.warning(f"恢复操作失败: {recovery_e}")

            if attempt == max_attempts - 1:
                raise e

            if recovery_applied:
                time.sleep(1)  # 短暂等待后重试

    return None

# 使用示例
if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Zed Updater 代码修复示例")

    # 示例用法
    print("\n1. 安全文件名处理:")
    urls = [
        'https://github.com/example/Zed.exe',
        'https://evil.com/../../../system32/cmd.exe',
        'https://normal.com/file?v=1'
    ]
    for url in urls:
        safe_name = safe_filename_from_url(url)
        print(f"URL: {url}")
        print(f"安全文件名: {safe_name}")
        print()

    print("2. 原子文件写入:")
    test_file = Path('test_atomic_write.txt')
    success = atomic_write_file(test_file, '这是一段测试内容，包含中文字符！')
    print(f"原子写入成功: {success}")

    if test_file.exists():
        content = read_file_with_fallback(test_file)
        print(f"读取的内容: {content}")
        test_file.unlink()  # 清理测试文件

    print("\n3. 有限回调管理器:")
    callback_manager = LimitedCallbackManager(max_callbacks=3)

    def sample_callback(message):
        print(f"收到消息: {message}")

    # 添加回调
    for i in range(5):  # 尝试添加5个，但只允许3个
        success = callback_manager.add_callback(lambda msg=f"回调{i}": sample_callback(f"消息 {msg}"))
        print(f"添加回调 {i+1}: {'成功' if success else '失败（达到上限）'}")

    # 通知所有回调
    notified_count = callback_manager.notify_callbacks("测试消息")
    print(f"成功通知 {notified_count} 个回调函数")

    print("\n修复示例完成！")