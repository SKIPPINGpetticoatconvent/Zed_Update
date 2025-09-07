#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复GUI字体问题的补丁脚本
"""

import re

def apply_font_fix():
    """应用字体修复补丁"""

    # 输入文件
    input_file = 'updater/gui.py'
    # 输出文件
    output_file = 'updater/gui_fixed.py'

    print(f"正在修复 {input_file} 中的字体问题...")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复1: setup_fonts方法中的hasFamily调用
        old_pattern_1 = r'(\s+)if QFontDatabase\(\)\.hasFamily\(font_name\):'
        new_replacement_1 = r"""\1                    try:
\1                        # PyQt5的正确方法是families()
\1                        available_fonts = QFontDatabase().families()
\1                        if font_name in available_fonts:
\1                            font.setFamily(font_name)
\1                            break
\1                    except (AttributeError, TypeError):
\1                        # 如果方法不兼容，使用退回策略
\1                        try:
\1                            font.setFamily(font_name)
\1                            break
\1                        except Exception:
\1                            continue"""

        # 修复2: create_log_tab方法中的hasFamily调用
        old_pattern_2 = r'(\s+)if QFontDatabase\(\)\.hasFamily\(font_name\):'
        new_replacement_2 = r"""\1                try:
\1                    # 使用PyQt5兼容的families()方法
\1                    available_fonts = QFontDatabase.families()
\1                    if font_name in available_fonts:
\1                        log_font.setFamily(font_name)
\1                        break
\1                except (AttributeError, TypeError):
\1                    # 如果方法不存在，使用默认策略
\1                    try:
\1                        log_font.setFamily(font_name)
\1                        break
\1                    except Exception:
\1                        continue"""

        # 应用修复
        modified_content = re.sub(re.escape(old_pattern_1), new_replacement_1, content, flags=re.MULTILINE)
        modified_content = re.sub(re.escape(old_pattern_2), new_replacement_2, modified_content, flags=re.MULTILINE)

        # 写入修复后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        print(f"✅ 字体修复已应用到 {output_file}")
        print("⚠️  请手动将修复后的内容复制到原始文件，或直接使用修复版本")

        return True

    except Exception as e:
        print(f"❌ 字体修复失败: {e}")
        return False

def create_manual_patch():
    """创建手动的补丁文件供参考"""
    patch_content = '''
# GUI字体修复补丁 - 手动应用到 updater/gui.py

# 1. 在setup_fonts()方法的第168-172行替换：
# 原来的代码:
if QFontDatabase().hasFamily(font_name):
    font.setFamily(font_name)
    break

# 修复后的代码:
try:
    # PyQt5的正确方法是families()
    available_fonts = QFontDatabase().families()
    if font_name in available_fonts:
        font.setFamily(font_name)
        break
except (AttributeError, TypeError):
    # 如果方法不兼容，使用退回策略
    try:
        font.setFamily(font_name)
        break
    except Exception:
        continue

# 2. 在create_log_tab()方法的第559-563行替换:
# 原来的代码:
if QFontDatabase().hasFamily(font_name):
    log_font.setFamily(font_name)
    break

# 修复后的代码:
try:
    # 使用PyQt5兼容的families()方法
    available_fonts = QFontDatabase.families()
    if font_name in available_fonts:
        log_font.setFamily(font_name)
        break
except (AttributeError, TypeError):
    # 如果方法不存在，使用默认策略
    try:
        log_font.setFamily(font_name)
        break
    except Exception:
        continue
'''

    try:
        with open('gui_font_patch.txt', 'w', encoding='utf-8') as f:
            f.write(patch_content)
        print("✅ 手册补丁文件已创建: gui_font_patch.txt")
    except Exception as e:
        print(f"❌ 创建手册补丁失败: {e}")

if __name__ == '__main__':
    print("Zed Updater GUI字体错误修复工具")
    print("="*50)

    # 应用自动修复
    auto_fix_success = apply_font_fix()

    print("\n" + "="*50)
    print("修复说明:")
    print("1. 问题: PyQt5中的QFontDatabase没有hasFamily()方法")
    print("2. 解决方案: 使用families()方法检查可用字体")
    print("3. 兼容性: 包含退回策略处理版本差异")

    if auto_fix_success:
        print("✅ 自动修复成功应用")
    else:
        print("❌ 自动修复失败，请使用手册补丁")

    # 创建手册补丁
    create_manual_patch()

    print("\n🎉 字体错误修复完成!")
    print("="*50)