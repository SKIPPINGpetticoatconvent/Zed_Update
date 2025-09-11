#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网络重试机制功能
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock

# 设置路径
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("开始测试网络重试机制...")

try:
    from updater.updater import ZedUpdater
    from updater.config import Config
    from updater.scheduler import UpdateScheduler
    print("✅ 成功导入模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_retry_mechanism():
    """测试网络重试机制"""
    print("\n=== 网络重试机制功能测试 ===")

    import tempfile
    import threading
    from concurrent.futures import ThreadPoolExecutor

    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, 'test_config.json')

        try:
            config = Config(config_file)
            updater = ZedUpdater(config)
            scheduler = UpdateScheduler(updater, config)

            # 测试1: 基本重试功能
            print("测试1: 基本重试功能")
            with patch('updater.updater.requests.Session.get') as mock_get:
                # 模拟前两次失败，第三次成功
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers.get.return_value = '1024'
                mock_response.iter_content.return_value = [b'x' * 1024]

                mock_get.side_effect = [
                    Exception("网络超时"),
                    Exception("连接失败"),
                    mock_response
                ]

                updater.download_url = 'http://example.com/test.exe'

                success = updater.download_update() is not None
                print(f"  重试次数: {mock_get.call_count}")
                print(f"  下载成功: {success}")
                test1_passed = mock_get.call_count >= 3 and success
                print(f"  测试结果: {'✅ 通过' if test1_passed else '❌ 失败'}")

            # 测试2: 指数退避策略
            print("\n测试2: 指数退避策略")
            import time
            start_time = time.time()

            with patch('updater.updater.requests.Session.get') as mock_get:
                with patch('updater.updater.time.sleep') as mock_sleep:
                    mock_response = Mock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.headers.get.return_value = '1024'
                    mock_response.iter_content.return_value = [b'x' * 1024]

                    # 前两次失败，最后一次成功
                    mock_get.side_effect = [
                        Exception("网络错误"),
                        Exception("连接错误"),
                        mock_response
                    ]

                    updater.download_url = 'http://example.com/test.exe'
                    updater.download_update()

                    # 检查是否使用了指数退避
                    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                    if len(sleep_calls) >= 2:
                        backoff_increasing = sleep_calls[0] < sleep_calls[1] if len(sleep_calls) > 1 else True
                        print(f"  退避时间序列: {sleep_calls}")
                        print(f"  退避时间递增: {backoff_increasing}")
                        test2_passed = backoff_increasing
                    else:
                        test2_passed = False

                    print(f"  测试结果: {'✅ 通过' if test2_passed else '❌ 失败'}")

            # 测试3: 最大重试限制
            print("\n测试3: 最大重试限制")
            with patch('updater.updater.requests.Session.get') as mock_get:
                # 一直失败
                mock_get.side_effect = Exception("持久网络错误")

                updater.download_url = 'http://example.com/test.exe'
                result = updater.download_update()

                max_retries_respected = result is None and mock_get.call_count <= 3
                print(f"  请求次数: {mock_get.call_count}")
                print(f"  遵守最大重试限制: {max_retries_respected}")
                print(f"  测试结果: {'✅ 通过' if max_retries_respected else '❌ 失败'}")
                test3_passed = max_retries_respected

            # 测试4: 并发请求处理
            print("\n测试4: 并发请求处理")
            def mock_download_worker(worker_id):
                """模拟并发下载操作"""
                try:
                    # 每个worker创建自己的updater实例
                    with tempfile.TemporaryDirectory() as worker_temp:
                        worker_config = Config(os.path.join(worker_temp, f'config_{worker_id}.json'))
                        worker_updater = ZedUpdater(worker_config)

                        with patch('updater.updater.requests.Session.get') as worker_mock_get:
                            mock_response = Mock()
                            mock_response.raise_for_status.return_value = None
                            mock_response.headers.get.return_value = '1024'
                            mock_response.iter_content.return_value = [b'x' * 1024]

                            # 第一个请求失败，第二个成功
                            worker_mock_get.side_effect = [
                                Exception("并发网络冲突"),
                                mock_response
                            ]

                            worker_updater.download_url = f'http://example.com/test_{worker_id}.exe'
                            success = worker_updater.download_update()
                            return success is not None

                except Exception as e:
                    print(f"  Worker {worker_id} 错误: {e}")
                    return False

            # 启动多个并发worker
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(mock_download_worker, i) for i in range(3)]
                concurrent_results = [future.result() for future in futures]

            all_concurrent_succeeded = all(concurrent_results)
            print(f"  并发结果: {concurrent_results}")
            print(f"  全部成功: {all_concurrent_succeeded}")
            print(f"  测试结果: {'✅ 通过' if all_concurrent_succeeded else '❌ 失败'}")
            test4_passed = all_concurrent_succeeded

            # 总体结果
            all_tests_passed = test1_passed and test2_passed and test3_passed and test4_passed
            print("\n" + "="*50)
            print("网络重试机制测试总结:")
            print(f"基本重试功能: {'✅' if test1_passed else '❌'}")
            print(f"指数退避策略: {'✅' if test2_passed else '❌'}")
            print(f"最大重试限制: {'✅' if test3_passed else '❌'}")
            print(f"并发请求处理: {'✅' if test4_passed else '❌'}")
            print(f"总体结果: {'✅ 所有测试通过' if all_tests_passed else '❌ 部分测试失败'}")

            return all_tests_passed

        except Exception as e:
            print(f"❌ 网络重试机制测试失败: {e}")
            return False

if __name__ == '__main__':
    print("Zed Updater 网络重试机制验证")
    print("="*60)

    success = test_retry_mechanism()

    print("\n" + "="*60)
    if success:
        print("🎉 网络重试机制功能验证成功!")
        print("原子任务2 (实施网络请求重试机制) 已完成!")
        sys.exit(0)
    else:
        print("❌ 网络重试机制验证失败，需要进一步检查")
        sys.exit(1)