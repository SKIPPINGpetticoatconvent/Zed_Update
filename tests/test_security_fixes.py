#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全修复测试模块
测试安全验证和修复效果
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from updater.updater import ZedUpdater


class TestSecurityFixes(unittest.TestCase):
    """测试安全修复"""

    def setUp(self):
        """测试前准备"""
        self.config_mock = MagicMock()
        self.updater = ZedUpdater(self.config_mock)

    def test_safe_filename_normal_url(self):
        """测试正常URL的文件名生成"""
        url = "https://github.com/user/repo/releases/download/v1.0.0/zed-v1.0.0.zip"
        result = self.updater._safe_filename_from_url(url)
        self.assertTrue(result.endswith('.zip'))
        self.assertNotIn('..', result)
        self.assertNotIn('/', result)
        self.assertNotIn('\\', result)

    def test_safe_filename_path_traversal(self):
        """测试路径遍历攻击防护"""
        malicious_urls = [
            "https://example.com/../../../etc/passwd",
            "https://example.com/..\\..\\windows\\system32\\cmd.exe",
            "https://example.com/path/../../secret.txt"
        ]

        for url in malicious_urls:
            with self.subTest(url=url):
                result = self.updater._safe_filename_from_url(url)
                # 应该返回安全文件名，不包含路径遍历字符
                self.assertNotIn('..', result)
                self.assertTrue(result.startswith(('download_', 'zed_update_', 'example.com_')))

    def test_safe_filename_special_characters(self):
        """测试特殊字符处理"""
        url = "https://example.com/file:with*special<characters>.exe"
        result = self.updater._safe_filename_from_url(url)
        # 特殊字符应该被替换为下划线
        self.assertNotIn(':', result)
        self.assertNotIn('*', result)
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)

    def test_safe_filename_empty_url(self):
        """测试空URL处理"""
        result = self.updater._safe_filename_from_url("")
        self.assertTrue(result.startswith('zed_update_'))
        self.assertTrue(result.endswith('.zip'))

    def test_safe_filename_invalid_url(self):
        """测试无效URL处理"""
        invalid_urls = [
            None,
            "not-a-url",
            "http://",
            "https://"
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.updater._safe_filename_from_url(url)
                self.assertTrue(result.startswith('zed_update_'))

    def test_safe_filename_length_limit(self):
        """测试文件名长度限制"""
        long_name = "a" * 150
        url = f"https://example.com/{long_name}.zip"
        result = self.updater._safe_filename_from_url(url)
        self.assertLessEqual(len(result), 100)

    def test_safe_filename_hidden_files(self):
        """测试隐藏文件防护"""
        url = "https://example.com/.hidden_file.exe"
        result = self.updater._safe_filename_from_url(url)
        self.assertFalse(result.startswith('.'))
        self.assertNotIn('..', result)


if __name__ == '__main__':
    unittest.main()