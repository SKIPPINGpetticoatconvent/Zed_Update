#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Main entry point for Zed Updater
"""

import sys
import os

# Setup UTF-8 environment before any GUI imports
if sys.platform == 'win32':
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTextCodec

from .core.config import ConfigManager
from .core.updater import ZedUpdater
from .core.scheduler import UpdateScheduler
from .gui.main_window import MainWindow
from .utils.logger import setup_logging, get_logger
from .utils.encoding import EncodingUtils


def main():
    """Main GUI entry point"""
    # Setup encoding
    EncodingUtils.setup_utf8_environment()

    # Setup logging
    setup_logging(use_colors=False)  # Disable colors in GUI mode
    logger = get_logger(__name__)

    try:
        # Create Qt application
        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("Zed Editor 自动更新程序")
        app.setApplicationVersion("2.1.0")
        app.setOrganizationName("ZedUpdater")

        # Setup UTF-8 codec
        try:
            codec = QTextCodec.codecForName("UTF-8")
            if codec:
                QTextCodec.setCodecForLocale(codec)
        except Exception as e:
            logger.warning(f"Failed to set UTF-8 codec: {e}")

        # Initialize components
        config = ConfigManager()
        updater = ZedUpdater(config)
        scheduler = UpdateScheduler(updater, config)

        # Create main window
        window = MainWindow(config, updater, scheduler)

        # Show window (unless configured to start minimized)
        if not config.get('start_minimized', False):
            window.show()

        # Start application
        logger.info("Starting Zed Updater GUI")
        return app.exec_()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"GUI application error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())