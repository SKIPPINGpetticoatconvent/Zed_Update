#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified configuration management for Zed Updater
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger


@dataclass
class ConfigData:
    """Configuration data structure"""
    # Basic settings
    zed_install_path: str = r"D:\Zed.exe"
    github_repo: str = "TC999/zed-loc"

    # Update settings
    auto_check_enabled: bool = True
    check_interval_hours: int = 24
    check_on_startup: bool = True
    auto_download: bool = True
    auto_install: bool = False
    auto_start_after_update: bool = True

    # Backup settings
    backup_enabled: bool = True
    backup_count: int = 3

    # UI settings
    minimize_to_tray: bool = True
    notification_enabled: bool = True
    language: str = "zh_CN"

    # Network settings
    download_timeout: int = 300
    retry_count: int = 3
    proxy_enabled: bool = False
    proxy_url: str = ""


class ConfigManager:
    """Simplified configuration manager"""

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
                self.logger.info("配置文件不存在，使用默认设置")
                self._save_config()
                return

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update config object
            for key, value in data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)

            self.logger.info("配置文件加载成功")

        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"加载配置文件失败: {e}")
        except Exception as e:
            self.logger.error(f"未知错误: {e}")

    def _save_config(self) -> bool:
        """Save configuration to file"""
        try:
            config_dict = asdict(self._config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            self.logger.info("配置文件保存成功")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self._config, key, default)

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

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return asdict(self._config)

    def get_backup_dir(self) -> Path:
        """Get backup directory path"""
        zed_path = Path(self._config.zed_install_path)
        return zed_path.parent / "backups"

    def get_temp_dir(self) -> Path:
        """Get temporary directory path"""
        return Path.home() / ".zed_updater" / "temp"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        try:
            self.get_backup_dir().mkdir(parents=True, exist_ok=True)
            self.get_temp_dir().mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"创建目录失败: {e}")

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(file={self.config_file})"