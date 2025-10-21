#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Line Interface for Zed Updater
"""

import sys
import argparse
from pathlib import Path

from .core.config import ConfigManager
from .core.updater import ZedUpdater
from .utils.logger import setup_logging, get_logger
from .utils.encoding import EncodingUtils


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Zed Editor Auto Updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zed-updater --check              # Check for updates
  zed-updater --update             # Download and install updates
  zed-updater --version            # Show current Zed version
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
        '--log-file',
        type=str,
        help='Path to log file'
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

    # Setup encoding
    EncodingUtils.setup_utf8_environment()

    # Setup logging
    setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        use_colors=not args.quiet
    )

    logger = get_logger(__name__)

    try:
        # Handle version request
        if args.version:
            print("Zed Editor Auto Updater v2.1.0")
            return 0

        # Load configuration
        config_file = args.config or ConfigManager.DEFAULT_CONFIG_FILE
        if not Path(config_file).exists():
            config_file = None  # Use default

        config = ConfigManager(config_file)
        updater = ZedUpdater(config)

        # Handle GUI mode
        if args.gui:
            logger.info("Starting GUI mode...")
            from .gui_main import main as gui_main
            return gui_main()

        # Handle current version
        if args.current_version:
            current_version = updater.get_current_version()
            if current_version:
                print(f"Current Zed version: {current_version}")
            else:
                print("Could not determine current Zed version")
                return 1
            return 0

        # Handle check for updates
        if args.check:
            logger.info("Checking for updates...")
            release_info = updater.check_for_updates()

            if release_info:
                print(f"Update available: {release_info.version}")
                print(f"Release date: {release_info.release_date}")
                print(f"Download size: {release_info.size} bytes")
                if release_info.description:
                    print(f"Description: {release_info.description[:200]}...")
                return 0
            else:
                print("No updates available")
                return 0

        # Handle update
        if args.update:
            logger.info("Starting update process...")

            result = updater.check_and_update()

            if result.success:
                if result.version:
                    print(f"Successfully updated to version {result.version}")
                else:
                    print("Update completed successfully")
                return 0
            else:
                print(f"Update failed: {result.message}")
                if result.error_code:
                    print(f"Error code: {result.error_code}")
                return 1

        # No action specified, show help
        parser.print_help()
        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if not args.quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())