#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本获取修复的脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from updater.config import Config
from updater.updater import ZedUpdater

def test_version_fix():
    """测试版本获取修复"""
    try:
        # 初始化配置
        config = Config()

        # 创建设置为默认或设置配置中已有的
        zed_path = config.get_setting('zed_install_path', 'D:\\Zed.exe')
        print(f"配置中的Zed路径: {zed_path}")

        from pathlib import Path
        if not Path(zed_path).exists():
            print(f"警告: Zed.exe不存在于 {zed_path}")
            return

        # 初始化更新器
        updater = ZedUpdater(config)

        # 测试版本获取
        print("正在获取当前版本...")
        version = updater.get_current_version()

        if version:
            print(f"成功获取版本: {version}")
        else:
            print("无法获取版本，但没有抛出异常（这可能是正常的）")

        print("测试完成")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_version_fix()