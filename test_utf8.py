#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8编码测试脚本
用于验证项目的UTF-8兼容性和中文字符处理能力
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from updater.encoding_utils import EncodingUtils
from updater.config import Config

class UTF8Tester:
    """UTF-8编码测试器"""

    def __init__(self):
        self.test_results = []
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        full_message = f"{status} - {test_name}"
        if message:
            full_message += f": {message}"

        self.logger.info(full_message)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })

    def test_environment_setup(self):
        """测试环境设置"""
        try:
            # 测试UTF-8环境设置
            success = EncodingUtils.setup_utf8_environment()
            self.log_result("UTF-8环境设置", success)

            # 测试系统编码
            system_encoding = EncodingUtils.get_system_encoding()
            self.log_result("系统编码获取", True, f"系统编码: {system_encoding}")

            # 测试环境变量
            io_encoding = os.environ.get('PYTHONIOENCODING', '未设置')
            self.log_result("环境变量检查", True, f"PYTHONIOENCODING: {io_encoding}")

        except Exception as e:
            self.log_result("环境设置测试", False, str(e))

    def test_chinese_text_handling(self):
        """测试中文文本处理"""
        try:
            # 测试用中文文本
            test_texts = [
                "Zed编辑器自动更新程序",
                "正在检查更新...",
                "更新完成！🎉",
                "配置文件: config.json",
                "错误: 网络连接失败",
                "警告⚠️: 请先备份重要文件",
                "成功✅下载最新版本",
            ]

            for text in test_texts:
                # 测试UTF-8兼容性
                is_utf8 = EncodingUtils.is_utf8_compatible(text)
                self.log_result(f"UTF-8兼容性检查: '{text[:10]}...'", is_utf8)

                # 测试编码/解码
                try:
                    encoded = EncodingUtils.safe_encode(text)
                    decoded = EncodingUtils.safe_decode(encoded)
                    success = decoded == text
                    self.log_result(f"编码解码测试: '{text[:10]}...'", success)
                except Exception as e:
                    self.log_result(f"编码解码测试: '{text[:10]}...'", False, str(e))

                # 测试文本规范化
                try:
                    normalized = EncodingUtils.normalize_text(text)
                    success = isinstance(normalized, str)
                    self.log_result(f"文本规范化: '{text[:10]}...'", success)
                except Exception as e:
                    self.log_result(f"文本规范化: '{text[:10]}...'", False, str(e))

        except Exception as e:
            self.log_result("中文文本处理测试", False, str(e))

    def test_file_operations(self):
        """测试文件操作"""
        try:
            test_dir = Path("test_utf8_files")
            test_dir.mkdir(exist_ok=True)

            # 测试文件内容
            test_content = """# Zed编辑器配置文件
{
    "程序名称": "Zed Editor 自动更新程序",
    "版本": "1.0.0",
    "描述": "这是一个测试文件🚀",
    "支持语言": ["中文", "English", "日本語"],
    "特殊字符": "★☆♠♣♦♥→←↑↓",
    "表情符号": "😀😃😄😁😆😅🤣😂"
}
"""

            # 测试不同编码格式写入
            encodings = ['utf-8', 'utf-8-sig', 'gbk']

            for encoding in encodings:
                try:
                    test_file = test_dir / f"test_{encoding.replace('-', '_')}.json"

                    # 写入文件
                    success = EncodingUtils.write_text_file(test_file, test_content, encoding)
                    self.log_result(f"文件写入测试 ({encoding})", success)

                    if success and test_file.exists():
                        # 检测编码
                        detected_encoding = EncodingUtils.detect_file_encoding(test_file)
                        self.log_result(f"编码检测 ({encoding})", True, f"检测到: {detected_encoding}")

                        # 读取文件
                        read_content = EncodingUtils.read_text_file(test_file)
                        read_success = read_content is not None
                        self.log_result(f"文件读取测试 ({encoding})", read_success)

                        # 内容比较
                        if read_content:
                            content_match = EncodingUtils.normalize_text(read_content.strip()) == EncodingUtils.normalize_text(test_content.strip())
                            self.log_result(f"内容匹配测试 ({encoding})", content_match)

                except Exception as e:
                    self.log_result(f"文件操作测试 ({encoding})", False, str(e))

            # 清理测试文件
            try:
                import shutil
                shutil.rmtree(test_dir)
                self.log_result("测试文件清理", True)
            except Exception as e:
                self.log_result("测试文件清理", False, str(e))

        except Exception as e:
            self.log_result("文件操作测试", False, str(e))

    def test_config_file_handling(self):
        """测试配置文件处理"""
        try:
            # 创建测试配置
            test_config_data = {
                "程序设置": {
                    "程序名称": "Zed编辑器自动更新程序",
                    "版本": "1.0.0",
                    "作者": "开发者👨‍💻"
                },
                "更新设置": {
                    "自动检查": True,
                    "检查间隔": "24小时",
                    "通知消息": "发现新版本！🔔"
                },
                "界面设置": {
                    "语言": "简体中文",
                    "主题": "默认主题🎨",
                    "字体": "微软雅黑"
                }
            }

            test_config_file = Path("test_config_utf8.json")

            # 测试JSON序列化（确保中文字符正确处理）
            try:
                json_str = json.dumps(test_config_data, ensure_ascii=False, indent=4)
                success = "程序名称" in json_str and "自动检查" in json_str
                self.log_result("JSON序列化测试", success)
            except Exception as e:
                self.log_result("JSON序列化测试", False, str(e))

            # 测试配置文件写入
            try:
                success = EncodingUtils.write_text_file(
                    test_config_file,
                    json.dumps(test_config_data, ensure_ascii=False, indent=4),
                    'utf-8-sig'
                )
                self.log_result("配置文件写入", success)
            except Exception as e:
                self.log_result("配置文件写入", False, str(e))

            # 测试配置文件读取
            if test_config_file.exists():
                try:
                    content = EncodingUtils.read_text_file(test_config_file)
                    if content:
                        loaded_data = json.loads(content)
                        success = loaded_data.get("程序设置", {}).get("程序名称") == "Zed编辑器自动更新程序"
                        self.log_result("配置文件读取", success)
                    else:
                        self.log_result("配置文件读取", False, "内容为空")
                except Exception as e:
                    self.log_result("配置文件读取", False, str(e))

            # 清理测试文件
            try:
                if test_config_file.exists():
                    test_config_file.unlink()
                    self.log_result("测试配置文件清理", True)
            except Exception as e:
                self.log_result("测试配置文件清理", False, str(e))

        except Exception as e:
            self.log_result("配置文件处理测试", False, str(e))

    def test_logging_with_chinese(self):
        """测试中文日志记录"""
        try:
            # 创建测试日志文件
            test_log_file = Path("test_utf8.log")

            # 设置测试日志器
            test_logger = logging.getLogger("utf8_test")
            test_logger.setLevel(logging.INFO)

            # 添加文件处理器
            file_handler = logging.FileHandler(test_log_file, encoding='utf-8', mode='w')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            test_logger.addHandler(file_handler)

            # 测试中文日志消息
            test_messages = [
                "程序启动成功 ✅",
                "正在检查Zed更新...",
                "发现新版本: v1.0.1 🎉",
                "开始下载更新文件 📥",
                "下载进度: 50% ⏳",
                "更新安装完成 🚀",
                "程序退出 👋"
            ]

            for msg in test_messages:
                test_logger.info(msg)

            # 关闭处理器
            file_handler.close()
            test_logger.removeHandler(file_handler)

            # 验证日志文件
            if test_log_file.exists():
                content = EncodingUtils.read_text_file(test_log_file)
                if content:
                    success = all(msg in content for msg in test_messages)
                    self.log_result("中文日志记录", success)
                else:
                    self.log_result("中文日志记录", False, "无法读取日志文件")
            else:
                self.log_result("中文日志记录", False, "日志文件未创建")

            # 清理测试日志文件
            try:
                if test_log_file.exists():
                    test_log_file.unlink()
                    self.log_result("测试日志文件清理", True)
            except Exception as e:
                self.log_result("测试日志文件清理", False, str(e))

        except Exception as e:
            self.log_result("中文日志测试", False, str(e))

    def test_console_output(self):
        """测试控制台输出"""
        try:
            # 测试控制台输出中文
            test_messages = [
                "控制台输出测试开始 🚀",
                "这是一条中文消息",
                "包含特殊字符: ★☆♠♣♦♥",
                "包含表情符号: 😀😃😄😁",
                "包含数学符号: ∑∏∫∞≠≤≥",
                "控制台输出测试结束 ✅"
            ]

            success_count = 0
            for msg in test_messages:
                try:
                    print(msg)
                    success_count += 1
                except UnicodeEncodeError as e:
                    self.logger.warning(f"控制台输出失败: {msg[:20]}... - {e}")
                except Exception as e:
                    self.logger.error(f"控制台输出错误: {e}")

            success = success_count == len(test_messages)
            self.log_result("控制台中文输出", success, f"{success_count}/{len(test_messages)} 条消息输出成功")

        except Exception as e:
            self.log_result("控制台输出测试", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("=" * 60)
        self.logger.info("开始UTF-8编码兼容性测试")
        self.logger.info("=" * 60)

        # 运行各项测试
        self.test_environment_setup()
        self.test_chinese_text_handling()
        self.test_file_operations()
        self.test_config_file_handling()
        self.test_logging_with_chinese()
        self.test_console_output()

        # 统计结果
        self.print_summary()

    def print_summary(self):
        """打印测试摘要"""
        self.logger.info("=" * 60)
        self.logger.info("测试结果摘要")
        self.logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        self.logger.info(f"总测试数: {total_tests}")
        self.logger.info(f"通过: {passed_tests} ✅")
        self.logger.info(f"失败: {failed_tests} ❌")
        self.logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            self.logger.info("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    msg = f"  - {result['test']}"
                    if result['message']:
                        msg += f": {result['message']}"
                    self.logger.info(msg)

        self.logger.info("=" * 60)

        if failed_tests == 0:
            self.logger.info("🎉 所有UTF-8兼容性测试都通过了!")
        else:
            self.logger.info(f"⚠️  有 {failed_tests} 个测试失败，建议检查相关功能")

def main():
    """主函数"""
    try:
        print("Zed Editor 自动更新程序 - UTF-8编码兼容性测试")
        print("=" * 60)

        tester = UTF8Tester()
        tester.run_all_tests()

    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
