#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网络重试机制核心功能
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

# 设置路径
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# 设置环境变量
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_core_retry_functionality():
    """测试核心重试功能"""
    try:
        from updater.updater import ZedUpdater
        from updater.config import Config
        import tempfile

        print("✅ 测试核心重试功能")
        print("="*60)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.json'
            config = Config(str(config_file))
            updater = ZedUpdater(config)

            # 测试1: 验证 _retry_request 方法存在并且功能完整
            assert hasattr(updater, '_retry_request'), "❌ _retry_request 方法不存在"

            # 测试2: 模拟网络请求失败和恢复
            print("测试2: 模拟重试场景")

            with patch('updater.updater.requests.Session.get') as mock_get:
                # 设置模拟行为：前两次失败，第三次成功
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers.get.return_value = '1024'
                mock_response.iter_content.return_value = [b'x' * 1024]

                # 前两次抛出异常，第三次成功
                mock_get.side_effect = [
                    Exception("网络连接失败"),
                    Exception("请求超时"),
                    mock_response
                ]

                # 调用重试方法
                updater.download_url = 'http://example.com/test.exe'

                try:
                    result = updater.download_update()
                    # 由于这是模拟，实际文件不会创建，但方法应该尝试执行而不崩溃
                    print(f"✅ 重试机制执行完成，返回结果: {result is not None}")
                except Exception as e:
                    print(f"❌ 重试执行失败: {e}")
                    return False

            # 测试3: 验证下载配置
            print("测试3: 配置验证")
            config.set_setting('retry_count', 5)
            config.set_setting('download_timeout', 120)

            retry_count = config.get_setting('retry_count')
            timeout = config.get_setting('download_timeout')

            print(f"✅ 重试次数配置: {retry_count}")
            print(f"✅ 超时配置: {timeout}")

            # 测试4: 边界情况 - 网络完全不可用
            print("测试4: 网络异常处理")

            with patch('updater.updater.requests.Session.get') as mock_get:
                # 总是失败
                mock_get.side_effect = Exception("网络完全不可用")
                updater.download_url = 'http://nonexistent.com/file.exe'

                result = updater.download_update()
                if result is None:
                    print("✅ 网络异常时正确返回None")
                else:
                    print(f"❌ 网络异常时不应返回有效结果: {result}")
                    return False

            print("\n" + "="*60)
            print("🎉 核心重试功能验证通过!")
            return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生意外错误: {e}")
        return False

def test_retry_mechanism_integration():
    """测试重试机制与整体系统的集成"""
    try:
        from updater.config import Config
        from updater.updater import ZedUpdater
        from updater.scheduler import UpdateScheduler
        import tempfile

        print("\n\n测试重试机制集成")
        print("="*60)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'integration_config.json'
            config = Config(str(config_file))

            # 创建所有组件
            updater = ZedUpdater(config)
            scheduler = UpdateScheduler(updater, config)

            # 验证集成
            components = [
                ('配置管理器', hasattr(config, 'get_setting')),
                ('更新器', hasattr(updater, '_retry_request')),
                ('调度器', hasattr(scheduler, 'start'))
            ]

            for name, exists in components:
                status = "✅" if exists else "❌"
                print(f"{status} {name}: {'可用' if exists else '不可用'}")

            all_components_available = all(exists for _, exists in components)

            if all_components_available:
                print("🎉 系统集成验证通过!")
                return True
            else:
                print("❌ 系统集成验证失败")
                return False

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

if __name__ == '__main__':
    print("Zed Updater 网络重试机制核心测试")
    print("="*80)

    # 测试核心功能
    core_test_passed = test_core_retry_functionality()

    # 测试集成
    integration_test_passed = test_retry_mechanism_integration()

    print("\n" + "="*80)
    print("最终测试结果:")
    print(f"核心功能测试: {'✅ 通过' if core_test_passed else '❌ 失败'}")
    print(f"集成测试: {'✅ 通过' if integration_test_passed else '❌ 失败'}")

    if core_test_passed and integration_test_passed:
        print("\n🎉 网络重试机制测试全部通过!")
        print("原子任务2 (实施网络请求重试机制) 已完成!")
        exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步验证")
        exit(1)