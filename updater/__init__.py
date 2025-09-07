#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序 - updater模块

这个模块包含了Zed编辑器自动更新的核心功能：
- 配置管理 (config.py)
- 更新逻辑 (updater.py)
- 定时调度 (scheduler.py)
- 图形界面 (gui.py)
"""

__version__ = "1.0.0"
__author__ = "ZedUpdater"
__description__ = "Zed Editor 自动更新程序"

# 导入主要类以便外部使用
from .config import Config
from .updater import ZedUpdater
from .scheduler import UpdateScheduler
from .encoding_utils import EncodingUtils

# 初始化UTF-8环境
try:
    EncodingUtils.setup_utf8_environment()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"初始化UTF-8环境失败: {e}")

__all__ = [
    'Config',
    'ZedUpdater',
    'UpdateScheduler',
    'EncodingUtils'
]
