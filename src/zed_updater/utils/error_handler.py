#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error handling utilities for Zed Updater
"""

import sys
import traceback
from typing import Callable, Any, Optional
from functools import wraps

from ..utils.logger import get_logger
from ..core.exceptions import ZedUpdaterError


class ErrorHandler:
    """Centralized error handling"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def handle_error(self, error: Exception, context: str = "", show_user: bool = True) -> str:
        """
        Handle an exception and return user-friendly error message

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            show_user: Whether to show error to user (vs just log)

        Returns:
            User-friendly error message
        """
        error_msg = self._get_error_message(error)

        if context:
            full_msg = f"{context}: {error_msg}"
        else:
            full_msg = error_msg

        # Log the full error with traceback
        self.logger.error(f"Error in {context}: {error}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")

        if show_user:
            return self._format_user_message(full_msg)
        else:
            return full_msg

    def _get_error_message(self, error: Exception) -> str:
        """Get appropriate error message for different exception types"""
        from ..core.exceptions import (
            NetworkError, DownloadError, InstallationError,
            ValidationError, ConfigurationError, PermissionError,
            TimeoutError, FileOperationError
        )

        if isinstance(error, NetworkError):
            return "网络连接错误，请检查网络连接和代理设置"
        elif isinstance(error, DownloadError):
            return "下载文件时出错，请检查网络连接"
        elif isinstance(error, InstallationError):
            return "安装更新时出错，请检查文件权限"
        elif isinstance(error, ValidationError):
            return "数据验证失败，请检查配置"
        elif isinstance(error, ConfigurationError):
            return "配置错误，请检查配置文件"
        elif isinstance(error, PermissionError):
            return "权限不足，请以管理员身份运行"
        elif isinstance(error, TimeoutError):
            return "操作超时，请重试"
        elif isinstance(error, FileOperationError):
            return f"文件操作失败: {error.file_path}"
        elif isinstance(error, OSError):
            if error.errno == 1:  # Operation not permitted
                return "权限被拒绝，请检查文件权限"
            elif error.errno == 2:  # No such file or directory
                return "文件或目录不存在"
            elif error.errno == 28:  # No space left on device
                return "磁盘空间不足"
            else:
                return f"系统错误: {error.strerror}"
        else:
            return f"未知错误: {str(error)}"

    def _format_user_message(self, message: str) -> str:
        """Format message for user display"""
        return message


def error_handler(context: str = "", show_user: bool = True):
    """
    Decorator for error handling

    Args:
        context: Context description for error messages
        show_user: Whether to show errors to user
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = handler.handle_error(e, context, show_user)
                # Re-raise ZedUpdaterError types, convert others
                if isinstance(e, ZedUpdaterError):
                    raise
                else:
                    raise ZedUpdaterError(error_msg) from e
        return wrapper
    return decorator


def safe_call(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """
    Safely call a function with error handling

    Args:
        func: Function to call
        *args: Positional arguments
        default: Default return value on error
        **kwargs: Keyword arguments

    Returns:
        Function result or default value
    """
    handler = ErrorHandler()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handler.handle_error(e, f"safe_call({func.__name__})", show_user=False)
        return default


def log_exceptions(logger=None):
    """
    Decorator to log exceptions without re-raising them

    Args:
        logger: Logger to use (default: get current logger)
    """
    if logger is None:
        logger = get_logger(__name__)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                return None
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = ErrorHandler()
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        handler.handle_error(
                            e,
                            f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {current_delay}s",
                            show_user=False
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        handler.handle_error(
                            e,
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            show_user=True
                        )
                        raise

            return None  # Should not reach here
        return wrapper
    return decorator