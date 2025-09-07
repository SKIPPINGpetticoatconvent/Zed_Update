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

__all__ = [
    'Config',
    'ZedUpdater',
    'UpdateScheduler'
]
