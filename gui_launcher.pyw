#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor GUI 启动器 - 无控制台窗口版本
这个文件专门用于启动GUI界面，不会显示控制台窗口
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置UTF-8编码环境
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    """启动程序，支持命令行参数"""
    try:
        # 导入主程序模块
        from main import ZedUpdateApp

        # 创建应用实例
        app = ZedUpdateApp()

        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == '--update':
                # 仅执行更新
                app.run_console_update()
                return
            elif sys.argv[1] == '--help':
                print("Zed Editor 自动更新程序")
                print("使用方法:")
                print("  gui_launcher.pyw          - 运行GUI界面")
                print("  gui_launcher.pyw --gui    - 运行GUI界面")
                print("  gui_launcher.pyw --update - 仅执行更新检查")
                print("  gui_launcher.pyw --help   - 显示帮助信息")
                return

        # 默认启动GUI界面
        sys.exit(app.run_gui())

    except ImportError as e:
        # 如果导入失败，显示错误对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "导入错误",
                f"无法导入必要的模块: {e}\n\n请确保所有依赖项已正确安装。"
            )
            sys.exit(1)
        except:
            # 如果连PyQt5都没有，就退出
            sys.exit(1)

    except Exception as e:
        # 其他错误也显示对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "启动错误",
                f"程序启动时发生错误: {e}"
            )
            sys.exit(1)
        except:
            sys.exit(1)

if __name__ == "__main__":
    main()
