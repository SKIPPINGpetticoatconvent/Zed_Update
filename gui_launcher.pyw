#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序
功能：
1. 自动检查GitHub最新版本
2. 下载并替换Zed.exe
3. 可自定义的定时执行
4. 自动启动功能
"""

import sys
import os
import json
import logging
from pathlib import Path

# 设置默认编码为UTF-8
import locale
import codecs

# 确保标准输出使用UTF-8编码
if sys.platform == 'win32':
    # Windows系统UTF-8兼容性设置
    try:
        # 尝试设置控制台代码页为UTF-8
        os.system('chcp 65001 > nul')
    except:
        pass

    # 设置环境变量确保UTF-8编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # 重新配置标准输出流
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QTextCodec
from updater.gui import UpdaterGUI
from updater.scheduler import UpdateScheduler
from updater.updater import ZedUpdater
from updater.config import Config

# 设置日志，确保UTF-8编码
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zed_updater.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 确保日志处理器使用UTF-8编码
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        if hasattr(handler.stream, 'reconfigure'):
            try:
                handler.stream.reconfigure(encoding='utf-8')
            except:
                pass

logger = logging.getLogger(__name__)

class ZedUpdateApp:
    def __init__(self):
        self.config = Config()
        self.updater = ZedUpdater(self.config)
        self.scheduler = UpdateScheduler(self.updater, self.config)

    def run_gui(self):
        """运行图形界面"""
        app = QApplication(sys.argv)

        # 设置Qt应用程序的文本编码为UTF-8
        try:
            codec = QTextCodec.codecForName("UTF-8")
            QTextCodec.setCodecForLocale(codec)
        except:
            pass

        # 设置应用程序属性
        app.setApplicationName("Zed Editor 自动更新程序")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("ZedUpdater")

        gui = UpdaterGUI(self.updater, self.scheduler, self.config)
        gui.show()

        # 启动定时器检查
        if self.config.get_setting('auto_check_enabled', True):
            self.scheduler.start()

        return app.exec_()

    def run_console_update(self):
        """运行控制台更新"""
        try:
            logger.info("开始检查Zed更新...")
            if self.updater.check_and_update():
                logger.info("更新完成!")
                if self.config.get_setting('auto_start_after_update', True):
                    self.updater.start_zed()
            else:
                logger.info("已是最新版本或更新失败")
        except Exception as e:
            logger.error(f"更新过程中发生错误: {e}")

def main():
    """主入口函数"""
    app = ZedUpdateApp()

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--update':
            # 仅执行更新
            app.run_console_update()
        elif sys.argv[1] == '--gui':
            # 运行GUI
            sys.exit(app.run_gui())
        elif sys.argv[1] == '--help':
            print("Zed Editor 自动更新程序")
            print("使用方法:")
            print("  python main.py          - 运行GUI界面")
            print("  python main.py --gui    - 运行GUI界面")
            print("  python main.py --update - 仅执行更新检查")
            print("  python main.py --help   - 显示帮助信息")
            return
    else:
        # 默认运行GUI
        sys.exit(app.run_gui())

if __name__ == "__main__":
    main()