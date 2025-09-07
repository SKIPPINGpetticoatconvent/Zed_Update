#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Updater 集成测试
验证端到端功能的完整性
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time
import subprocess

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updater.config import Config
from updater.updater import ZedUpdater
from updater.scheduler import UpdateScheduler


class TestEndToEndUpdate(unittest.TestCase):
    """端到端更新流程测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / 'config.json'
        self.backup_dir = self.temp_dir / 'backups'
        self.temp_download_dir = self.temp_dir / 'temp_downloads'

        # 创建测试配置文件
        self.config = Config(str(self.config_file))

        # 设置测试路径
        fake_zed_path = self.temp_dir / 'fake_zed.exe'
        fake_zed_path.write_bytes(b'fake zed executable')
        self.config.set_setting('zed_install_path', str(fake_zed_path))

        # 创建工作目录
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_download_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_update_cycle(self):
        """测试完整更新周期"""
        updater = ZedUpdater(self.config)

        # 模拟版本信息
        mock_version_info = {
            'version': '1.1.0',
            'download_url': 'http://example.com/fake_update.exe'
        }

        # 模拟网络请求
        with patch('updater.updater.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            # 模拟GitHub API响应
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'tag_name': 'v1.1.0',
                'assets': [{'browser_download_url': 'http://example.com/fake_update.exe'}]
            }
            mock_response.raise_for_status.return_value = None
            mock_session.get.return_value = mock_response

            # 模拟版本比较
            with patch.object(updater, 'get_current_version', return_value='1.0.0'):
                with patch.object(updater, 'compare_versions', return_value=-1):  # 当前版本 < 最新版本

                    # 测试版本检查
                    has_update = updater.has_update_available()
                    self.assertTrue(has_update, "应该检测到新版本")

                    # 模拟下载假文件
                    download_mock_response = MagicMock()
                    download_mock_response.headers.get.return_value = '1024'  # 1KB文件
                    download_mock_response.iter_content.return_value = [b'x' * 1024]
                    download_mock_response.raise_for_status.return_value = None

                    # 替换session的下载响应
                    def mock_get(url, **kwargs):
                        if 'releases' in url:
                            return mock_response
                        else:
                            return download_mock_response

                    mock_session.get.side_effect = mock_get

                    # 测试下载
                    download_path = updater.download_update()
                    self.assertIsNotNone(download_path, "下载应该成功")
                    self.assertTrue(download_path.exists(), "下载文件应该存在")

                    # 测试安装 (注意: 这是一个模拟的测试，不会实际替换系统文件)
                    with patch('updater.updater.shutil.copy2') as mock_copy:
                        with patch('updater.updater.shutil.move') as mock_move:
                            success = updater.install_update(download_path)
                            self.assertTrue(success, "安装应该成功")

    def test_scheduler_integration(self):
        """测试调度器集成"""
        updater = ZedUpdater(self.config)
        scheduler = UpdateScheduler(updater, self.config)

        # 测试调度器基本功能
        self.assertFalse(scheduler.is_scheduler_running())

        # 测试手动触发检查
        with patch.object(updater, 'get_current_version', return_value='1.0.0'):
            with patch.object(updater, 'get_latest_version_info', return_value={'version': '1.1.0'}):
                scheduler.force_check_now()
                time.sleep(0.1)  # 给线程一点时间

    def test_config_persistence(self):
        """测试配置持久化"""
        # 设置一些测试配置
        test_values = {
            'test_string': '测试字符串',
            'test_number': 42,
            'test_bool': True,
            'test_list': [1, 2, 3]
        }

        for key, value in test_values.items():
            self.config.set_setting(key, value)

        # 重新创建配置对象来模拟重新加载
        new_config = Config(str(self.config_file))

        # 验证配置被正确保存和加载
        for key, value in test_values.items():
            self.assertEqual(new_config.get_setting(key), value,
                           f"配置项 {key} 应该被正确保存和加载")


class TestErrorRecovery(unittest.TestCase):
    """错误恢复测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / 'config.json'
        self.config = Config(str(self.config_file))

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_network_failure_recovery(self):
        """测试网络失败恢复"""
        updater = ZedUpdater(self.config)

        # 模拟网络完全不可用
        with patch('updater.updater.requests.Session.get', side_effect=Exception("Network unreachable")):
            result = updater.get_latest_version_info()
            self.assertIsNone(result, "网络失败时应该返回None")

    def test_partial_config_recovery(self):
        """测试部分损坏配置文件恢复"""
        # 创建一个损坏的配置文件
        self.config_file.write_text('{invalid json content"')

        # 应该能够恢复到默认配置
        recovered_config = Config(str(self.config_file))

        # 验证所有默认配置项都存在
        for key in Config.DEFAULT_CONFIG.keys():
            value = recovered_config.get_setting(key)
            expected = Config.DEFAULT_CONFIG[key]
            self.assertEqual(value, expected, f"配置项 {key} 应该恢复为默认值")

    def test_concurrent_config_modification(self):
        """测试并发配置文件修改"""
        import threading

        errors = []
        successful_operations = []

        def modify_config(worker_id):
            """工作线程修改配置"""
            try:
                for i in range(50):  # 减少循环次数以便测试
                    self.config.set_setting(f'worker_{worker_id}_item_{i}', f'value_{i}')
                    successful_operations.append(1)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # 启动多个线程同时修改配置
        threads = []
        for i in range(3):  # 减少线程数量
            t = threading.Thread(target=modify_config, args=(i,))
            threads.append(t)
            t.start()

        # 等待线程完成
        for t in threads:
            t.join(timeout=10)  # 添加超时

        # 验证没有错误发生
        self.assertEqual(len(errors), 0, f"并发测试中发生错误: {errors}")
        self.assertGreater(len(successful_operations), 100, "应该有大量的成功操作")


class TestUnicodeCompatibility(unittest.TestCase):
    """Unicode兼容性测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / 'config.json'

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_chinese_characters_in_config(self):
        """测试配置文件中的中文字符"""
        config = Config(str(self.config_file))

        # 设置包含中文的配置
        chinese_settings = {
            '安装路径': 'C:\\程序文件\\Zed.exe',
            '用户名': '测试用户',
            '描述': '这是一个测试配置项，包含中文字符和特殊符号！@#$%^&*()'
        }

        for key, value in chinese_settings.items():
            config.set_setting(key, value)

        # 重新加载配置文件
        new_config = Config(str(self.config_file))

        # 验证中文字符被正确保存和加载
        for key, value in chinese_settings.items():
            loaded_value = new_config.get_setting(key)
            self.assertEqual(loaded_value, value, f"中文配置项 {key} 应该被正确处理")

    def test_emoji_in_config(self):
        """测试配置文件中的Emoji"""
        config = Config(str(self.config_file))

        emoji_settings = {
            '状态': '✅ 完成',
            '警告': '⚠️ 注意',
            '错误': '❌ 失败'
        }

        for key, value in emoji_settings.items():
            config.set_setting(key, value)

        # 重新加载并验证
        new_config = Config(str(self.config_file))
        for key, value in emoji_settings.items():
            loaded_value = new_config.get_setting(key)
            self.assertEqual(loaded_value, value, f"Emoji配置项 {key} 应该被正确处理")

    def test_mixed_encoding_log_files(self):
        """测试混合编码的日志文件处理"""
        # 这个测试需要GUI组件的支持，这里先占位
        pass


class TestPerformanceMonitoring(unittest.TestCase):
    """性能监控测试"""

    def test_config_operation_performance(self):
        """测试配置操作性能"""
        config = Config()

        # 批量设置大量配置项
        start_time = time.time()
        for i in range(1000):
            config.set_setting(f'perf_test_key_{i}', f'test_value_{i}')
        end_time = time.time()

        duration = end_time - start_time
        # 配置操作应该在合理时间内完成 (通常 < 1秒)
        self.assertLess(duration, 2.0, f"配置操作耗时过长: {duration:.2f}秒")

    def test_memory_usage_during_large_operations(self):
        """测试大型操作期间的内存使用"""
        # 这个测试需要外部监控工具，这里先用简单的验证
        import gc

        config = Config()
        initial_objects = len(gc.get_objects())

        # 执行大量操作
        for i in range(500):
            config.set_setting(f'mem_test_{i}', 'x' * 1000)  # 大字符串

        gc.collect()
        final_objects = len(gc.get_objects())

        # 确保没有严重的内存泄漏
        growth_ratio = final_objects / max(initial_objects, 1)
        self.assertLess(growth_ratio, 3.0, f"对象数量增长过大: {growth_ratio:.2f}x")


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    # 配置运行器
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,
        failfast=True
    )

    # 运行测试
    result = runner.run(suite)

    # 输出结果摘要
    print("\n" + "="*60)
    print("测试结果摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*60)