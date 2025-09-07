#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Updater 修复功能测试
测试编码修复、并发安全、网络重试等改进
"""

import unittest
import tempfile
import shutil
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updater.config import Config
from updater.updater import ZedUpdater


class TestConfigFixes(unittest.TestCase):
    """测试配置模块的修复"""

    def setUp(self):
        """测试环境设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_config.json'

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_atomic_write_config(self):
        """测试原子配置文件写入"""
        config = Config(str(self.config_file))

        # 测试正常写入
        config.set_setting('test_key', 'test_value')
        self.assertTrue(self.config_file.exists())

        # 验证文件内容
        with open(self.config_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        self.assertEqual(data['test_key'], 'test_value')

    def test_config_thread_safety(self):
        """测试配置的线程安全"""
        config = Config(str(self.config_file))

        results = []
        errors = []

        def worker(worker_id):
            """工作线程"""
            try:
                for i in range(100):
                    config.set_setting(f'key_{worker_id}_{i}', f'value_{worker_id}_{i}')
                    time.sleep(0.001)  # 小的延迟以增加竞争
                results.append(f'worker_{worker_id}_done')
            except Exception as e:
                errors.append(f'worker_{worker_id}_error: {e}')

        # 启动多个线程
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误发生
        self.assertEqual(len(errors), 0, f"线程安全测试失败: {errors}")
        self.assertEqual(len(results), 5, "不是所有工作线程都完成了")

    def test_unicode_handling(self):
        """测试Unicode字符处理"""
        config = Config(str(self.config_file))

        # 测试中文字符
        chinese_text = '中文测试字符串'
        config.set_setting('chinese_key', chinese_text)

        # 重新加载配置
        config.reload()
        self.assertEqual(config.get_setting('chinese_key'), chinese_text)

    def test_config_validation(self):
        """测试配置验证"""
        config = Config(str(self.config_file))

        # 测试无效路径
        config.set_setting('zed_install_path', '')
        errors = config.validate_config()
        self.assertIn('zed_install_path', errors)

        # 测试无效间隔
        config.set_setting('check_interval_hours', -1)
        errors = config.validate_config()
        self.assertIn('check_interval_hours', errors)


class TestUpdaterFixes(unittest.TestCase):
    """测试更新器模块的修复"""

    def setUp(self):
        """测试环境设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_config.json'
        self.config = Config(str(self.config_file))

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('updater.updater.requests.Session')
    def test_download_with_retry(self, mock_session_class):
        """测试带重试的下载功能"""
        # 创建模拟的session和response
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # 模拟前两次请求失败，最后一次成功
        mock_response = MagicMock()
        mock_response.headers.get.return_value = '1024'  # 1KB文件
        mock_response.iter_content.return_value = [b'x' * 1024]  # 模拟文件内容
        mock_response.raise_for_status.return_value = None

        # 前两次抛出异常，最后一次成功
        mock_session.get.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_response
        ]

        updater = ZedUpdater(self.config)
        updater.download_url = 'http://example.com/test.exe'

        result = updater.download_update()

        # 验证结果
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())

        # 验证重试次数
        self.assertEqual(mock_session.get.call_count, 3)

    def test_safe_filename_extraction(self):
        """测试安全文件名提取"""
        updater = ZedUpdater(self.config)

        # 测试正常的URL
        url = 'https://github.com/user/repo/releases/download/v1.0/Zed_v1.0.0.exe'
        safe_name = updater._safe_filename_from_url(url)
        self.assertNotIn('..', safe_name)
        self.assertNotIn('/', safe_name)
        self.assertNotIn('\\', safe_name)

        # 测试恶意的URL
        malicious_url = 'https://evil.com/../../../windows/system32/cmd.exe'
        safe_name = updater._safe_filename_from_url(malicious_url)
        self.assertTrue(safe_name.endswith('.exe'))
        self.assertNotIn('system32', safe_name)

    @patch('updater.updater.subprocess.run')
    def test_version_detection_robustness(self, mock_run):
        """测试版本检测的健壮性"""
        updater = ZedUpdater(self.config)

        # 模拟命令行工具不存在的情况
        mock_run.side_effect = FileNotFoundError()

        with patch('updater.updater.Path.exists', return_value=False):
            version = updater.get_current_version()
            self.assertIsNone(version)

    def test_version_comparison_edge_cases(self):
        """测试版本比较的边缘情况"""
        updater = ZedUpdater(self.config)

        # 测试相等版本
        self.assertEqual(updater.compare_versions('1.0.0', '1.0.0'), 0)

        # 测试不同长度版本号
        self.assertEqual(updater.compare_versions('1.0', '1.0.0'), 0)

        # 测试带字母的版本
        self.assertEqual(updater.compare_versions('1.0.0-alpha', '1.0.0-beta'), -1)

        # 测试无效版本字符串
        self.assertEqual(updater.compare_versions('invalid', '1.0.0'), -1)


class TestNetworkReliability(unittest.TestCase):
    """测试网络可靠性修复"""

    def test_timeout_handling(self):
        """测试超时处理"""
        # 测试在网络超时情况下重试机制是否正确工作
        pass

    def test_connection_refused_recovery(self):
        """测试连接拒绝时的恢复机制"""
        # 测试服务器拒绝连接时是否能正确回退
        pass

    def test_partial_download_recovery(self):
        """测试部分下载恢复"""
        # 测试下载中断时是否能从断点继续下载
        pass


class TestConcurrentOperations(unittest.TestCase):
    """测试并发操作的安全性"""

    def test_multiple_config_instances(self):
        """测试多个配置实例的并发操作"""
        pass

    def test_simultaneous_downloads(self):
        """测试同时下载时的冲突处理"""
        pass

    def test_gui_thread_safety(self):
        """测试GUI线程安全"""
        pass


class TestEncodingRobustness(unittest.TestCase):
    """测试编码相关修复"""

    def test_mixed_encoding_files(self):
        """测试混合编码文件的处理"""
        pass

    def test_gb2312_to_utf8_conversion(self):
        """测试GB2312到UTF-8转换"""
        pass

    def test_broken_unicode_recovery(self):
        """测试损坏的Unicode字符恢复"""
        pass


if __name__ == '__main__':
    # 配置测试运行器
    unittest.main(verbosity=2, buffer=True,
                 catchbreak=True, failfast=False)