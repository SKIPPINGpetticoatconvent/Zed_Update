#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量定义模块
定义应用程序中使用的所有常量
"""

import os
import sys
from pathlib import Path

# 应用信息
APP_NAME = "Zed Editor 自动更新程序"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Zed Updater Team"
APP_DESCRIPTION = "一个功能完整的 Zed 编辑器自动更新工具"
APP_WEBSITE = "https://github.com/TC999/zed-loc"

# 文件路径
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # 普通Python环境
    APP_DIR = Path(os.path.abspath(os.path.dirname(__file__))).parent

CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "zed_updater.log"
TEMP_DIR = APP_DIR / "temp_downloads"
BACKUP_DIR_NAME = "zed_backups"

# GitHub相关
DEFAULT_GITHUB_REPO = "TC999/zed-loc"
DEFAULT_GITHUB_API = "https://api.github.com/repos/TC999/zed-loc/releases/latest"
USER_AGENT = f"ZedUpdater/{APP_VERSION}"

# UI设置
DEFAULT_WINDOW_WIDTH = 600
DEFAULT_WINDOW_HEIGHT = 500
MIN_WINDOW_WIDTH = 500
MIN_WINDOW_HEIGHT = 400

# 图标路径
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境
    ICON_PATH = APP_DIR / "resources" / "icons" / "app.ico"
else:
    # 普通Python环境
    ICON_PATH = APP_DIR / "resources" / "icons" / "app.ico"

# 时间设置
DEFAULT_CHECK_INTERVAL_HOURS = 24
DEFAULT_SCHEDULED_TIME = "02:00"  # 24小时格式
DEFAULT_SCHEDULED_DAYS = [0, 1, 2, 3, 4, 5, 6]  # 0=周一, 6=周日

# 网络设置
DEFAULT_TIMEOUT = 300  # 秒
DEFAULT_RETRY_COUNT = 3
CHUNK_SIZE = 8192  # 字节

# 日志设置
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}
DEFAULT_LOG_LEVEL = "INFO"

# 其他设置
DEFAULT_BACKUP_COUNT = 3
MAX_BACKUP_COUNT = 10

# 系统托盘菜单项
TRAY_MENU_ITEMS = [
    "显示主界面",
    "检查更新",
    "立即更新",
    "启动Zed",
    "退出"
]

# 错误信息
ERROR_MESSAGES = {
    "no_internet": "无法连接到网络，请检查网络连接",
    "github_api_error": "无法访问GitHub API，请检查网络连接或代理设置",
    "download_failed": "下载更新失败，请检查网络连接",
    "installation_failed": "安装更新失败，请尝试手动安装",
    "invalid_config": "配置文件无效，已重置为默认配置",
    "permission_denied": "权限不足，无法完成操作",
    "file_not_found": "找不到指定的文件",
    "invalid_path": "无效的文件路径",
    "unknown_error": "发生未知错误"
}

# 成功信息
SUCCESS_MESSAGES = {
    "update_available": "发现新版本！",
    "update_not_available": "已是最新版本",
    "download_complete": "更新下载完成",
    "installation_complete": "更新安装完成",
    "config_saved": "配置已保存",
    "scheduler_started": "定时任务已启动",
    "scheduler_stopped": "定时任务已停止"
}

# 版本相关
VERSION_REGEX = r"v?(\d+\.\d+\.\d+)"
