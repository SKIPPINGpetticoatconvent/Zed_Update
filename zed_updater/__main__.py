#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序主入口
负责处理命令行参数和启动应用
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 设置默认编码为UTF-8
import locale
import codecs

# 添加父目录到模块搜索路径，确保可以导入主包
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from zed_updater.core.updater import ZedUpdater
from zed_updater.core.config import Config
from zed_updater.core.scheduler import UpdateScheduler
from zed_updater.utils.encoding import setup_encoding

# 隐藏控制台窗口（仅在GUI模式下）
def hide_console():
    """隐藏控制台窗口"""
    if sys.platform == 'win32':
        try:
            import ctypes
            import ctypes.wintypes

            # 获取控制台窗口句柄
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32

            # 获取当前控制台窗口
            console_window = kernel32.GetConsoleWindow()

            if console_window:
                # SW_HIDE = 0, 隐藏窗口
                user32.ShowWindow(console_window, 0)
        except Exception as e:
            # 如果隐藏失败，记录但不影响程序运行
            pass

# 设置日志
def setup_logging():
    """设置日志系统"""
    log_file = 'zed_updater.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
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

    return logging.getLogger(__name__)

def run_gui(config, updater, scheduler):
    """运行图形界面"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTextCodec
    from zed_updater.ui.gui import UpdaterGUI

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

    gui = UpdaterGUI(updater, scheduler, config)
    gui.show()

    # 启动定时器检查
    if config.get_setting('auto_check_enabled', True):
        scheduler.start()

    return app.exec_()

def run_console_update(updater, config, logger):
    """运行控制台更新"""
    try:
        logger.info("开始检查Zed更新...")
        if updater.check_and_update():
            logger.info("更新完成!")
            if config.get_setting('auto_start_after_update', True):
                updater.start_zed()
        else:
            logger.info("已是最新版本或更新失败")
    except Exception as e:
        logger.error(f"更新过程中发生错误: {e}")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Zed Editor 自动更新程序')
    parser.add_argument('--update', action='store_true', help='仅执行更新检查')
    parser.add_argument('--gui', action='store_true', help='运行图形界面')
    parser.add_argument('--config', type=str, default='config.json', help='指定配置文件路径')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='日志级别')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    return parser.parse_args()

def main():
    """主入口函数"""
    # 解析命令行参数
    args = parse_arguments()

    # 设置编码环境
    setup_encoding()

    # 设置日志
    logger = setup_logging()

    # 创建应用核心组件
    config = Config(args.config)
    updater = ZedUpdater(config)
    scheduler = UpdateScheduler(updater, config)

    # 根据命令行参数决定运行模式
    if args.update:
        # 仅执行更新
        run_console_update(updater, config, logger)
    elif args.gui or len(sys.argv) <= 1:  # 默认运行GUI
        # 隐藏控制台窗口并运行GUI
        hide_console()
        sys.exit(run_gui(config, updater, scheduler))
    else:
        # 显示帮助信息
        print("Zed Editor 自动更新程序")
        print("使用方法:")
        print("  python -m zed_updater          - 运行GUI界面")
        print("  python -m zed_updater --gui    - 运行GUI界面")
        print("  python -m zed_updater --update - 仅执行更新检查")
        print("  python -m zed_updater --help   - 显示帮助信息")

if __name__ == "__main__":
    main()
