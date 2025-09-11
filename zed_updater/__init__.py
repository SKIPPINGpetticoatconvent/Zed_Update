#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序
一个功能完整的 Zed 编辑器自动更新工具，支持定时检查、自动下载和安装最新版本

Copyright (c) 2024
License: MIT
"""

__version__ = '1.0.0'
__author__ = 'Zed Updater Team'

# 导出主要类，便于从包直接导入
from zed_updater.core.updater import ZedUpdater
from zed_updater.core.config import Config
from zed_updater.core.scheduler import UpdateScheduler
