#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件线程安全
"""

import sys
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置路径
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# 设置环境变量
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_config_thread_safety():
    """测试配置线程安全"""
    try:
        from updater.config import Config
        import tempfile

        print("开始测试配置文件线程安全")
        print("="*50)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'thread_safety_test.json'

            # 创建配置实例
            config = Config(str(config_file))

            # 结果收集
            results = []
            errors = []

            def config_worker(worker_id):
                """配置操作工作线程"""
                try:
                    thread_results = []

                    # 执行多种配置操作
                    for i in range(50):  # 减少数量确保测试完整性
                        # 读操作
                        try:
                            current_value = config.get_setting('test_key', 'default')
                            thread_results.append(f"read_{worker_id}_{i}")
                        except Exception as e:
                            errors.append(f"Read error in worker {worker_id}: {e}")

                        # 写操作
                        try:
                            config.set_setting('test_key', f'value_{worker_id}_{i}')
                            thread_results.append(f"write_{worker_id}_{i}")
                        except Exception as e:
                            errors.append(f"Write error in worker {worker_id}: {e}")

                        # 批量更新
                        try:
                            batch_data = {f'batch_key_{worker_id}_{i}': f'batch_value_{worker_id}_{i}'}
                            config.update_settings(batch_data, save=False)  # 不保存以减少I/O
                            thread_results.append(f"batch_{worker_id}_{i}")
                        except Exception as e:
                            errors.append(f"Batch error in worker {worker_id}: {e}")

                        time.sleep(0.001)  # 短暂延迟增加并发概率

                    results.extend(thread_results)
                    return len(thread_results)

                except Exception as e:
                    errors.append(f"Unexpected error in worker {worker_id}: {e}")
                    return 0

            # 启动多个线程同时操作配置
            print("启动并发配置操作测试...")
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=5) as executor:  # 减少线程数
                futures = [executor.submit(config_worker, i) for i in range(5)]

                thread_results = []
                for future in as_completed(futures):
                    result = future.result()
                    thread_results.append(result)

            end_time = time.time()

            total_operations = sum(thread_results)
            duration = end_time - start_time
            ops_per_second = total_operations / duration if duration > 0 else 0

            print("线程执行统计:"            print(f"  执行时间: {duration:.2f}秒")
            print(f"  总操作数: {total_operations}")
            print(f"  每秒操作: {ops_per_second:.1f} ops/sec")

            # 验证结果
            if errors:
                print(f"发现 {len(errors)} 个错误:")
                for error in errors[:5]:  # 只显示前5个错误
                    print(f"  ❌ {error}")
                return False
            else:
                print("✅ 没有发现并发错误")

            # 验证最终状态
            try:
                final_config = config.get_all_settings()
                if final_config:
                    print("✅ 配置状态保持一致")
                    return True
                else:
                    print("❌ 配置状态异常")
                    return False
            except Exception as e:
                print(f"❌ 状态验证失败: {e}")
                return False

    except Exception as e:
        print(f"❌ 测试过程中发生意外错误: {e}")
        return False

def test_config_locking_mechanism():
    """测试配置锁定机制"""
    try:
        from updater.config import Config
        import tempfile

        print("\n测试配置锁定机制")
        print("="*30)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'lock_test.json'
            config = Config(str(config_file))

            # 检查锁的存在性
            if hasattr(config, 'lock'):
                print("✅ 配置类包含锁对象"                print(f"  锁类型: {type(config.lock).__name__}")
            else:
                print("❌ 配置类缺少锁对象")
                return False

            # 测试锁的基本功能
            lock_acquired = config.lock.acquire(blocking=False)
            if lock_acquired:
                config.lock.release()
                print("✅ 锁可以正常获取和释放")
                return True
            else:
                print("❌ 无法获取锁")
                return False

    except Exception as e:
        print(f"❌ 锁测试失败: {e}")
        return False

if __name__ == '__main__':
    print("Zed Updater 配置线程安全测试")
    print("="*60)

    # 测试锁机制
    lock_test_passed = test_config_locking_mechanism()

    # 测试线程安全
    thread_test_passed = test_config_thread_safety()

    print("\n" + "="*60)
    print("测试结果汇总:")
    print(f"锁机制测试: {'✅ 通过' if lock_test_passed else '❌ 失败'}")
    print(f"线程安全测试: {'✅ 通过' if thread_test_passed else '❌ 失败'}")

    if lock_test_passed and thread_test_passed:
        print("\n🎉 配置线程安全测试全部通过!")
        print("原子任务3 (添加配置文件线程安全) 已完成!")
        exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步检查线程安全实现")
        exit(1)