#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for Zed Updater
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from ..utils.encoding import EncodingUtils
from ..utils.logger import get_logger


@dataclass
class ConfigData:
    """Configuration data structure"""
    # Basic settings
    zed_install_path: str = r"D:\Zed.exe"
    github_repo: str = "TC999/zed-loc"
    github_api_url: str = "https://api.github.com"

    # Update settings
    auto_check_enabled: bool = True
    check_interval_hours: int = 24
    check_on_startup: bool = True
    force_download_latest: bool = True
    auto_download: bool = True
    auto_install: bool = False
    auto_start_after_update: bool = True

    # Backup settings
    backup_enabled: bool = True
    backup_count: int = 3

    # UI settings
    minimize_to_tray: bool = True
    start_minimized: bool = False
    notification_enabled: bool = True
    language: str = "zh_CN"

    # Network settings
    download_timeout: int = 300
    retry_count: int = 3
    proxy_enabled: bool = False
    proxy_url: str = ""

    # Schedule settings
    check_time: str = "09:00"

    # Advanced settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    temp_dir: Optional[str] = None
    backup_dir: Optional[str] = None


class ConfigManager:
    """Configuration manager with validation and migration support"""

    DEFAULT_CONFIG_FILE = "config.json"

    def __init__(self, config_file: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.config_file = Path(config_file or self.DEFAULT_CONFIG_FILE)
        self._config = ConfigData()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if not self.config_file.exists():
                self.logger.info("Config file not found, using defaults")
                self._save_config()
                return

            content = EncodingUtils.read_text_file(self.config_file)
            if content is None:
                self.logger.warning("Failed to read config file, using defaults")
                return

            data = json.loads(content)

            # Migrate old config format if needed
            migrated_data = self._migrate_config(data)

            # Update config object
            for key, value in migrated_data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)

            self.logger.info("Configuration loaded successfully")

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")

    def _save_config(self) -> bool:
        """Save configuration to file"""
        try:
            config_dict = asdict(self._config)
            content = json.dumps(config_dict, indent=2, ensure_ascii=False)
            success = EncodingUtils.write_text_file(self.config_file, content)

            if success:
                self.logger.info("Configuration saved successfully")
                return True
            else:
                self.logger.error("Failed to write config file")
                return False

        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    def _migrate_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old configuration format to new format"""
        # Handle legacy config keys
        migration_map = {
            'zed_install_path': 'zed_install_path',
            'github_repo': 'github_repo',
            'backup_enabled': 'backup_enabled',
            'backup_count': 'backup_count',
            'auto_check_enabled': 'auto_check_enabled',
            'check_interval_hours': 'check_interval_hours',
            'auto_download': 'auto_download',
            'auto_install': 'auto_install',
            'auto_start_after_update': 'auto_start_after_update',
            'check_on_startup': 'check_on_startup',
            'minimize_to_tray': 'minimize_to_tray',
            'start_minimized': 'start_minimized',
            'notification_enabled': 'notification_enabled',
            'download_timeout': 'download_timeout',
            'retry_count': 'retry_count',
            'check_time': 'check_time',
            'proxy_enabled': 'proxy_enabled',
            'proxy_url': 'proxy_url',
            'language': 'language',
            'force_download_latest': 'force_download_latest'
        }

        new_config = {}
        for old_key, new_key in migration_map.items():
            if old_key in old_config:
                new_config[new_key] = old_config[old_key]

        return new_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if hasattr(self._config, key):
            return getattr(self._config, key)
        return default

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            return self._save_config()
        return False

    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        for key, value in updates.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        return self._save_config()

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        self._config = ConfigData()
        return self._save_config()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return asdict(self._config)

    def validate(self) -> Dict[str, str]:
        """Validate configuration values"""
        errors = {}

        # Validate paths
        if self._config.zed_install_path:
            zed_path = Path(self._config.zed_install_path)
            if not zed_path.exists():
                errors['zed_install_path'] = "Zed executable not found"

        # Validate intervals
        if self._config.check_interval_hours < 1:
            errors['check_interval_hours'] = "Check interval must be at least 1 hour"

        if self._config.backup_count < 1:
            errors['backup_count'] = "Backup count must be at least 1"

        # Validate time format
        if self._config.check_time:
            try:
                from datetime import datetime
                datetime.strptime(self._config.check_time, "%H:%M")
            except ValueError:
                errors['check_time'] = "Invalid time format (use HH:MM)"

        # Validate URL
        if self._config.proxy_url and not self._config.proxy_url.startswith(('http://', 'https://', 'socks5://')):
            errors['proxy_url'] = "Invalid proxy URL format"

        return errors

    def get_backup_dir(self) -> Path:
        """Get backup directory path"""
        if self._config.backup_dir:
            return Path(self._config.backup_dir)

        # Default: backups subdirectory next to Zed executable
        zed_path = Path(self._config.zed_install_path)
        return zed_path.parent / "backups"

    def get_temp_dir(self) -> Path:
        """Get temporary directory path"""
        if self._config.temp_dir:
            return Path(self._config.temp_dir)

        # Default: temp subdirectory in user home
        return Path.home() / ".zed_updater" / "temp"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        dirs_to_create = [
            self.get_backup_dir(),
            self.get_temp_dir()
        ]

        for directory in dirs_to_create:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to create directory {directory}: {e}")

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(file={self.config_file})"