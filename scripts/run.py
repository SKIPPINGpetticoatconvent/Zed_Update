#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序启动脚本
负责启动应用程序
"""

import os
import sys
import logging
from pathlib import Path

# 添加父目录到模块搜索路径
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from zed_updater.__main__ import main

if __name__ == "__main__":
    # 设置当前工作目录为项目根目录
    os.chdir(parent_dir)

    # 启动应用程序
    main()
