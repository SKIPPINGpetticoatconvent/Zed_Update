#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本检查验证脚本
用于验证程序是否正确使用 TC999/zed-loc GitHub releases 进行版本检查
"""

import json
import requests
import sys
import os
from pathlib import Path

def verify_config():
    """验证配置文件是否正确设置"""
    print("🔍 检查配置文件...")

    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ config.json 不存在")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        github_repo = config.get('github_repo', '')
        github_api_url = config.get('github_api_url', '')

        print(f"   GitHub 仓库: {github_repo}")
        print(f"   API 地址: {github_api_url}")

        if github_repo == 'TC999/zed-loc':
            print("✅ GitHub 仓库配置正确")
        else:
            print("❌ GitHub 仓库配置错误，应该是 'TC999/zed-loc'")
            return False

        if github_api_url == 'https://api.github.com/repos/TC999/zed-loc/releases/latest':
            print("✅ API 地址配置正确")
        else:
            print("❌ API 地址配置错误")
            return False

        return True

    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False

def test_github_api():
    """测试 GitHub API 是否可访问"""
    print("\n🌐 测试 GitHub API 连接...")

    api_url = 'https://api.github.com/repos/TC999/zed-loc/releases/latest'

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        release_info = response.json()

        tag_name = release_info.get('tag_name', '')
        published_at = release_info.get('published_at', '')
        assets = release_info.get('assets', [])

        print(f"✅ API 连接成功")
        print(f"   最新版本标签: {tag_name}")
        print(f"   发布时间: {published_at}")
        print(f"   资源文件数量: {len(assets)}")

        # 显示资源文件
        if assets:
            print("   可用资源文件:")
            for asset in assets[:3]:  # 只显示前3个
                name = asset.get('name', '')
                size = asset.get('size', 0)
                print(f"     - {name} ({size} bytes)")

        return True, tag_name

    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求失败: {e}")
        return False, None
    except Exception as e:
        print(f"❌ 解析 API 响应失败: {e}")
        return False, None

def verify_updater_logic():
    """验证更新器逻辑是否正确"""
    print("\n🔧 验证更新器逻辑...")

    try:
        # 导入更新器模块
        sys.path.insert(0, str(Path.cwd()))
        from updater.config import Config
        from updater.updater import ZedUpdater

        # 创建配置和更新器实例
        config = Config()
        updater = ZedUpdater(config)

        # 检查配置
        repo = config.get_setting('github_repo')
        api_url = config.get_setting('github_api_url')

        print(f"   更新器使用的仓库: {repo}")
        print(f"   更新器使用的 API: {api_url}")

        if repo == 'TC999/zed-loc' and 'TC999/zed-loc' in api_url:
            print("✅ 更新器配置正确")

            # 尝试获取版本信息
            print("   正在获取最新版本信息...")
            version_info = updater.get_latest_version_info()

            if version_info:
                print(f"✅ 版本信息获取成功")
                print(f"   版本: {version_info.get('version', '未知')}")
                print(f"   标签: {version_info.get('tag_name', '未知')}")
                download_url = version_info.get('download_url', '')
                if download_url:
                    print(f"   下载链接: {download_url[:50]}...")
                return True
            else:
                print("❌ 无法获取版本信息")
                return False
        else:
            print("❌ 更新器配置错误")
            return False

    except ImportError as e:
        print(f"❌ 导入更新器模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证更新器逻辑失败: {e}")
        return False

def check_version_format(tag_name):
    """检查版本格式"""
    print(f"\n📅 分析版本格式: {tag_name}")

    if not tag_name:
        print("❌ 版本标签为空")
        return False

    # 检查是否为日期格式 (YYYYMMDD)
    if len(tag_name) == 8 and tag_name.isdigit():
        year = tag_name[:4]
        month = tag_name[4:6]
        day = tag_name[6:8]
        print(f"✅ 日期格式版本: {year}-{month}-{day}")
        return True

    # 检查是否为传统版本格式 (v1.2.3)
    if tag_name.startswith('v') and '.' in tag_name:
        version = tag_name[1:]
        print(f"✅ 传统版本格式: {version}")
        return True

    # 其他格式
    print(f"✅ 其他格式版本: {tag_name}")
    return True

def main():
    """主函数"""
    print("🚀 Zed Editor 版本检查验证工具")
    print("=" * 50)

    success_count = 0
    total_tests = 4

    # 1. 验证配置文件
    if verify_config():
        success_count += 1

    # 2. 测试 GitHub API
    api_success, tag_name = test_github_api()
    if api_success:
        success_count += 1

    # 3. 检查版本格式
    if tag_name and check_version_format(tag_name):
        success_count += 1

    # 4. 验证更新器逻辑
    if verify_updater_logic():
        success_count += 1

    # 总结
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {success_count}/{total_tests} 项测试通过")

    if success_count == total_tests:
        print("🎉 所有测试通过！程序已正确配置为使用 TC999/zed-loc GitHub releases 进行版本检查。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置或网络连接。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程中发生意外错误: {e}")
        sys.exit(1)
