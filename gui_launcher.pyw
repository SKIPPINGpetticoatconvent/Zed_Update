#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序
功能：
1. 自动检查GitHub最新版本
2. 下载并替换Zed.exe
3. 可自定义的定时执行
4. 自动启动功能
5. 增强的异常处理和崩溃保护
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
        try:
            self.config = Config()
            self.updater = ZedUpdater(self.config)
            self.scheduler = UpdateScheduler(self.updater, self.config)
        except Exception as e:
            logger.error(f"初始化应用程序时出错: {e}")
            import traceback
            logger.error(f"初始化错误堆栈: {traceback.format_exc()}")
            self._show_error_dialog("初始化错误", f"应用程序初始化失败: {e}")
            sys.exit(1)

    def _show_error_dialog(self, title, message):
        """显示错误对话框"""
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if not QApplication.instance():
                app = QApplication([])
            QMessageBox.critical(None, title, message)
        except Exception as dialog_error:
            logger.error(f"无法显示错误对话框: {dialog_error}")

    def run_gui(self):
        """运行图形界面"""
        try:
            app = QApplication(sys.argv)

            # 设置全局异常处理
            sys.excepthook = self._global_exception_handler

            # 设置Qt应用程序的文本编码为UTF-8
            try:
                codec = QTextCodec.codecForName("UTF-8")
                QTextCodec.setCodecForLocale(codec)
            except Exception as codec_error:
                logger.warning(f"设置编码失败: {codec_error}")

            # 设置应用程序属性
            app.setApplicationName("Zed Editor 自动更新程序")
            app.setApplicationVersion("1.0.0")
            app.setOrganizationName("ZedUpdater")

            try:
                gui = UpdaterGUI(self.updater, self.scheduler, self.config)
                gui.show()
            except Exception as gui_error:
                logger.error(f"创建GUI界面失败: {gui_error}")
                import traceback
                logger.error(f"GUI创建错误堆栈: {traceback.format_exc()}")
                self._show_error_dialog("界面错误", f"无法创建应用程序界面: {gui_error}")
                return 1

            # 启动定时器检查
            try:
                if self.config.get_setting('auto_check_enabled', True):
                    self.scheduler.start()
            except Exception as scheduler_error:
                logger.error(f"启动定时器失败: {scheduler_error}")
                # 继续运行程序，不中断

            return app.exec_()
        except Exception as e:
            logger.error(f"启动GUI时发生严重错误: {e}")
            import traceback
            logger.error(f"严重错误堆栈: {traceback.format_exc()}")
            self._show_error_dialog("启动错误", f"无法启动应用程序: {e}")
            return 1

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局异常处理器"""
        # 记录未捕获的异常
        logger.error("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))

        # 显示错误对话框（如果可能）
        error_msg = f"{exc_type.__name__}: {exc_value}"
        self._show_error_dialog("程序错误", f"发生未处理的错误:\n{error_msg}")

        # 调用默认处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def run_console_update(self):
        """运行控制台更新"""
        try:
            logger.info("开始检查Zed更新...")
            try:
                update_result = self.updater.check_and_update()
                if update_result:
                    logger.info("更新完成!")
                    if self.config.get_setting('auto_start_after_update', True):
                        try:
                            self.updater.start_zed()
                        except Exception as start_error:
                            logger.error(f"启动Zed失败: {start_error}")
                else:
                    logger.info("已是最新版本或更新失败")
            except Exception as update_error:
                logger.error(f"执行更新过程中发生错误: {update_error}")
                import traceback
                logger.error(f"更新错误堆栈: {traceback.format_exc()}")
                # 在控制台模式下尝试创建一个错误日志文件
                try:
                    with open('update_error.log', 'w', encoding='utf-8') as f:
                        f.write(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"错误信息: {update_error}\n")
                        f.write(f"错误堆栈:\n{traceback.format_exc()}")
                except:
                    pass
        except Exception as e:
            logger.error(f"更新过程中发生严重错误: {e}")
            import traceback
            logger.error(f"严重错误堆栈: {traceback.format_exc()}")

def main():
    """主入口函数"""
    # 设置未处理异常的日志记录
    def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
        logger.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = log_uncaught_exceptions

    try:
        from datetime import datetime
        logger.info(f"程序启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"操作系统: {sys.platform}")

        app = ZedUpdateApp()

        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == '--update':
                # 仅执行更新
                app.run_console_update()
            elif sys.argv[1] == '--gui':
                # 运行GUI
                exit_code = app.run_gui()
                logger.info(f"GUI应用程序退出，返回码: {exit_code}")
                sys.exit(exit_code)
            elif sys.argv[1] == '--help':
                print("Zed Editor 自动更新程序")
                print("使用方法:")
                print("  python main.py          - 运行GUI界面")
                print("  python main.py --gui    - 运行GUI界面")
                print("  python main.py --update - 仅执行更新检查")
                print("  python main.py --help   - 显示帮助信息")
                return
            else:
                print(f"未知参数: {sys.argv[1]}")
                print("使用 --help 查看可用选项")
                sys.exit(1)
        else:
            # 默认运行GUI
            exit_code = app.run_gui()
            logger.info(f"GUI应用程序退出，返回码: {exit_code}")
            sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"主程序致命错误: {e}")
        import traceback
        logger.critical(f"致命错误堆栈: {traceback.format_exc()}")

        # 尝试显示错误对话框
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if not QApplication.instance():
                app = QApplication([])
            QMessageBox.critical(None, "严重错误", f"程序启动失败: {e}")
        except:
            # 如果无法显示GUI错误，尝试控制台输出
            print(f"严重错误: {e}")

        sys.exit(1)

if __name__ == "__main__":
    main()
