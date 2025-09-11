#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数包初始化模块
包含各种辅助工具和实用函数
"""

# 导出模块和功能
from zed_updater.utils.encoding import setup_encoding, ensure_utf8
from zed_updater.utils.version import compare_versions, parse_version
from zed_updater.utils.network import download_file, get_json, setup_proxy

__all__ = [
    'setup_encoding',
    'ensure_utf8',
    'compare_versions',
    'parse_version',
    'download_file',
    'get_json',
    'setup_proxy'
]
