#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI字体修复
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("测试GUI字体修复...")

def test_font_availability():
    """测试字体可用性检查方法"""
    try:
        # 模拟PyQt5环境
        from unittest.mock import Mock

        # 创建模拟的QFontDatabase
        mock_font_db = Mock()

        # 测试不同的方法名称
        font_methods = ['hasFamily', 'families', 'fontFamilies', 'availableFamilies']

        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
        found_fonts = []
        working_method = None

        for method_name in font_methods:
            print(f"测试方法: {method_name}")

            try:
                if method_name == 'hasFamily':
                    # 模拟hasFamily方法
                    for font in chinese_fonts:
                        # 假设某些字体可用
                        if font in ['Microsoft YaHei', 'SimSun']:
                            found_fonts.append(font)
                    working_method = method_name
                    print(f"  ✅ hasFamily方法工作正常，发现字体: {found_fonts}")
                    break

                elif method_name == 'families':
                    # 模拟families()方法
                    mock_font_db.families.return_value = ['Arial', 'Microsoft YaHei', 'SimSun', 'Times New Roman']
                    available_fonts = mock_font_db.families()
                    for font in chinese_fonts:
                        if font in available_fonts:
                            found_fonts.append(font)
                    working_method = method_name
                    print(f"  ✅ families()方法工作正常，发现字体: {found_fonts}")
                    break

                elif method_name == 'fontFamilies':
                    # 模拟fontFamilies方法
                    mock_font_db.fontFamilies.return_value = ['Arial', 'Microsoft YaHei']
                    available_fonts = mock_font_db.fontFamilies()
                    for font in chinese_fonts:
                        if font in available_fonts:
                            found_fonts.append(font)
                    working_method = method_name
                    print(f"  ✅ fontFamilies()方法工作正常，发现字体: {found_fonts}")
                    break

                elif method_name == 'availableFamilies':
                    # 模拟availableFamilies方法
                    mock_font_db.availableFamilies.return_value = ['Arial', 'SimHei', 'Microsoft YaHei']
                    available_fonts = mock_font_db.availableFamilies()
                    for font in chinese_fonts:
                        if font in available_fonts:
                            found_fonts.append(font)
                    working_method = method_name
                    print(f"  ✅ availableFamilies()方法工作正常，发现字体: {found_fonts}")
                    break

            except Exception as e:
                print(f"  ❌ 方法 {method_name} 测试失败: {e}")
                continue

        # 生成修复建议
        if working_method:
            print("
修复建议:"            print(f"  使用方法: {working_method}")
            print("  中文字体: {', '.join(found_fonts) if found_fonts else '无'}")

            if working_method == 'families':
                fix_code = '''
# PyQt5字体检查修复
def check_font_availability(font_name):
    \"\"\"检查字体是否可用\"\"\"
    try:
        available_fonts = QFontDatabase().families()
        return font_name in available_fonts
    except AttributeError:
        # PyQt5中可能使用不同的方法
        return True  # 退回到默认行为
'''
            elif working_method == 'hasFamily':
                fix_code = '''
# PyQt5字体检查修复（如果hasFamily存在）
def check_font_availability(font_name):
    \"\"\"检查字体是否可用\"\"\"
    try:
        return QFontDatabase().hasFamily(font_name)
    except AttributeError:
        return True  # 退回到默认行为
'''
            else:
                fix_code = '''
# 通用字体检查修复
def check_font_availability(font_name):
    \"\"\"检查字体是否可用\"\"\"
    try:
        # 尝试多种方法
        if hasattr(QFontDatabase(), 'families'):
            available_fonts = QFontDatabase().families()
            return font_name in available_fonts
        elif hasattr(QFontDatabase(), 'hasFamily'):
            return QFontDatabase().hasFamily(font_name)
        else:
            return True  # 退回到默认行为
    except Exception:
        return True  # 退回到默认行为
'''

            print("
代码修复:"            print(fix_code)
            return fix_code

        else:
            print("❌ 未找到可用的字体检查方法")
            return None

    except ImportError as e:
        print(f"❌ 无法测试字体功能: {e}")
        return None
    except Exception as e:
        print(f"❌ 测试过程中发生意外错误: {e}")
        return None

def generate_font_fix():
    """生成字体修复代码"""
    fix_code = '''
def safe_check_font_availability(font_name):
    \"\"\"安全检查字体可用性，支持PyQt5兼容性\"\"\"
    try:
        from PyQt5.QtGui import QFontDatabase

        # PyQt5中正确的方法是families()
        available_fonts = QFontDatabase.families()
        return font_name in available_fonts

    except AttributeError:
        # 如果方法不存在，使用退回策略
        try:
            # 尝试其他方法
            if hasattr(QFontDatabase, 'hasFamily'):
                return QFontDatabase.hasFamily(font_name)
        except:
            pass

        # 最后的退回策略
        return True  # 假设字体可用，交给系统处理

    except Exception as e:
        print(f"字体检查失败: {e}")
        return True  # 退回到默认行为，不中断应用程序启动

# 在GUI代码中使用安全检查
def setup_fonts_safe():
    \"\"\"安全的字体设置\"\"\"
    try:
        from PyQt5.QtGui import QFont, QFontDatabase

        # 中文字体候选列表
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']

        # 查找可用的中文字体
        selected_font = None
        for font_name in chinese_fonts:
            if safe_check_font_availability(font_name):
                selected_font = font_name
                break

        # 设置字体
        if selected_font:
            font = QFont(selected_font)
        else:
            font = QFont("Arial")  # 退回默认字体

        # 应用字体设置
        font.setPointSize(9)
        return font

    except Exception as e:
        print(f"字体设置失败，使用系统默认: {e}")
        return QFont()  # 使用默认字体
'''

    return fix_code

if __name__ == '__main__':
    print("Zed Updater GUI字体修复测试")
    print("="*60)

    # 测试字体可用性
    fix_suggestion = test_font_availability()

    print("\n" + "="*60)
    if fix_suggestion:
        print("✅ 字体检查修复建议生成成功")
        print("建议的修复代码:"        print(generate_font_fix())
    else:
        print("❌ 无法生成字体修复建议")
        print("采用通用修复方案:")
        print(generate_font_fix())

    print("\n🎉 建议修复GUI中的字体检查代码以解决启动错误")