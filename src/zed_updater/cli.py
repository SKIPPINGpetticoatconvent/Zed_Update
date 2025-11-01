#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Command Line Interface for Zed Updater
"""

import sys
import argparse
from pathlib import Path

from .core.config import ConfigManager
from .core.updater import ZedUpdater
from .utils.logger import setup_logging, get_logger


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Zed Editor Auto Updater v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zed-updater --check              # Check for updates
  zed-updater --update             # Download and install updates
  zed-updater --current-version    # Show current Zed version
  zed-updater --config PATH        # Use custom config file
  zed-updater --gui                # Start GUI mode
        """
    )

    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Show Zed Updater version'
    )

    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='Check for Zed updates'
    )

    parser.add_argument(
        '--update', '-u',
        action='store_true',
        help='Download and install Zed updates'
    )

    parser.add_argument(
        '--current-version',
        action='store_true',
        help='Show current Zed version'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level'
    )

    parser.add_argument(
        '--gui', '-g',
        action='store_true',
        help='Start GUI mode'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (less output)'
    )

    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(
        level=args.log_level,
        use_colors=not args.quiet
    )

    logger = get_logger(__name__)

    try:
        # Handle version request
        if args.version:
            print("Zed Editor Auto Updater v2.0")
            return 0

        # Load configuration
        config_file = args.config
        config = ConfigManager(config_file)
        
        # Ensure required directories exist
        config.ensure_directories()
        
        updater = ZedUpdater(config)

        # Handle GUI mode
        if args.gui:
            logger.info("启动GUI模式...")
            try:
                from .gui_main import main as gui_main
                return gui_main()
            except ImportError as e:
                print(f"无法启动GUI: {e}")
                return 1

        # Handle current version
        if args.current_version:
            current_version = updater.get_current_version()
            if current_version:
                print(f"当前Zed版本: {current_version}")
            else:
                print("无法确定当前Zed版本")
                return 1
            return 0

        # Handle check for updates
        if args.check:
            logger.info("检查更新中...")
            release_info = updater.check_for_updates()

            if release_info:
                print(f"发现可用更新: {release_info.version}")
                print(f"发布日期: {release_info.release_date}")
                print(f"下载大小: {release_info.size} 字节")
                if release_info.description:
                    print(f"描述: {release_info.description[:200]}...")
                return 0
            else:
                print("没有可用的更新")
                return 0

        # Handle update
        if args.update:
            logger.info("开始更新过程...")

            def progress_callback(progress, message):
                if not args.quiet:
                    print(f"\r{message}", end='', flush=True)

            result = updater.check_and_update(progress_callback)

            if not args.quiet:
                print()  # New line after progress

            if result.success:
                if result.version:
                    print(f"成功更新到版本 {result.version}")
                else:
                    print("更新成功完成")
                return 0
            else:
                print(f"更新失败: {result.message}")
                if result.error_code:
                    print(f"错误代码: {result.error_code}")
                return 1

        # No action specified, show help
        parser.print_help()
        return 0

    except KeyboardInterrupt:
        logger.info("用户取消了操作")
        return 130
    except Exception as e:
        logger.error(f"意外错误: {e}")
        if not args.quiet:
            print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())