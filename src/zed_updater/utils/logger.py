#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger utility for Zed Updater with UTF-8 support and structured logging
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


class UTF8Formatter(logging.Formatter):
    """Custom formatter with UTF-8 and color support"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def __init__(self, use_colors: bool = True, include_timestamp: bool = True):
        super().__init__()
        self.use_colors = use_colors and self._supports_color()
        self.include_timestamp = include_timestamp

    def _supports_color(self) -> bool:
        """Check if terminal supports colors"""
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                return kernel32.GetConsoleMode(kernel32.GetStdHandle(-11)) != 0
            except:
                return False
        else:
            return sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with UTF-8 and optional colors"""
        # Create base format
        if self.include_timestamp:
            base_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        else:
            base_format = '%(levelname)s - %(name)s - %(message)s'

        # Apply color if supported
        if self.use_colors and record.levelname in self.COLORS:
            colored_format = f"{self.COLORS[record.levelname]}{base_format}{self.COLORS['RESET']}"
            formatter = logging.Formatter(colored_format, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            formatter = logging.Formatter(base_format, datefmt='%Y-%m-%d %H:%M:%S')

        return formatter.format(record)


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True
) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size
        backup_count: Number of backup files to keep
        use_colors: Whether to use colored output

    Returns:
        Root logger instance
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Create formatter
    formatter = UTF8Formatter(use_colors=use_colors)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_formatter = UTF8Formatter(use_colors=False)  # No colors in file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls

    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}")
                raise
        return wrapper
    return decorator