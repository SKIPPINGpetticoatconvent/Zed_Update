#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责管理Zed更新程序的所有配置项
"""

import json
import os
import sys
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, List

from zed_updater.utils.encoding import ensure_utf8, read_file_with_encoding, write_file_with_encoding

logger = logging.getLogger(__name__)

class Config:
    """配置管理类，负责处理程序配置的加载、保存和访问"""

    DEFAULT_CONFIG = {
        # 基本设置
        'zed_install_path': r'D:\Zed.exe',
        'backup_enabled': True,
        'backup_count': 3,

        # GitHub设置
        'github_repo': 'TC999/zed-loc',
        'github_api_url': 'https://api.github.com/repos/TC999/zed-loc/releases/latest',
        'download_timeout': 300,
        'retry_count': 3,

        # 自动更新设置
        'auto_check_enabled': True,
        'check_interval_hours': 24,
        'check_on_startup': True,
        'auto_download': True,
        'auto_install': False,  # 需要用户确认
        'force_download_latest': True,  # 强制下载最新版本，不进行版本检查

        # 启动设置
        'auto_start_after_update': True,
        'start_minimized': False,

        # 通知设置
        'show_notifications': True,
        'notify_on_update_available': True,
        'notify_on_update_complete': True,

        # 定时任务设置
        'scheduled_update_enabled': False,
        'scheduled_time': '02:00',  # 24小时格式
        'scheduled_days': [0, 1, 2, 3, 4, 5, 6],  # 0=周一, 6=周日

        # 高级设置
        'use_proxy': False,
        'proxy_url': '',
        'verify_signature': True,
        'log_level': 'INFO',

        # 界面设置
        'window_width': 600,
        'window_height': 500,
        'minimize_to_tray': True,
        'start_with_system': False,

        # 版本信息
        'current_version': '',
        'last_check_time': '',
        'last_update_time': ''
    }

    def __init__(self, config_file: str = 'config.json'):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        self.lock = threading.RLock()  # 添加线程锁保护配置操作
        self.load_config()

    def load_config(self) -> None:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                content = read_file_with_encoding(self.config_file)
                loaded_config = json.loads(content)

                # 合并配置，保留默认值
                with self.lock:
                    self.config.update(loaded_config)

                logger.info(f"配置已从 {self.config_file} 加载")
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.save_config()  # 保存默认配置
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            logger.info("使用默认配置")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")

    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 使用线程锁保护写入操作
            with self.lock:
                config_json = json.dumps(self.config, indent=4, ensure_ascii=False)

            # 使用UTF-8编码保存
            success = write_file_with_encoding(self.config_file, config_json, encoding='utf-8-sig')

            if success:
                logger.info(f"配置已保存到 {self.config_file}")
            else:
                logger.error("保存配置文件失败")

            return success
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置项键名
            default: 默认值

        Returns:
            配置项值
        """
        with self.lock:
            return self.config.get(key, default)

    def set_setting(self, key: str, value: Any, save: bool = True) -> None:
        """设置配置项

        Args:
            key: 配置项键名
            value: 配置项值
            save: 是否立即保存到文件
        """
        with self.lock:
            self.config[key] = value

        if save:
            self.save_config()

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置项

        Returns:
            所有配置项的字典
        """
        with self.lock:
            return self.config.copy()

    def update_settings(self, settings: Dict[str, Any], save: bool = True) -> None:
        """批量更新配置项

        Args:
            settings: 要更新的配置项字典
            save: 是否立即保存到文件
        """
        with self.lock:
            self.config.update(settings)

        if save:
            self.save_config()

    def reset_to_default(self, keys: Optional[List[str]] = None) -> None:
        """重置配置项为默认值

        Args:
            keys: 要重置的配置项键名列表，None表示重置所有
        """
        with self.lock:
            if keys is None:
                self.config = self.DEFAULT_CONFIG.copy()
            else:
                for key in keys:
                    if key in self.DEFAULT_CONFIG:
                        self.config[key] = self.DEFAULT_CONFIG[key]

        self.save_config()

    def validate_config(self) -> Dict[str, str]:
        """验证配置有效性

        Returns:
            错误信息字典，键为配置项名，值为错误信息
        """
        errors = {}

        # 验证Zed安装路径
        zed_path = self.get_setting('zed_install_path')
        if not zed_path or not isinstance(zed_path, str):
            errors['zed_install_path'] = 'Zed安装路径不能为空'
        elif not Path(zed_path).parent.exists():
            errors['zed_install_path'] = 'Zed安装路径的父目录不存在'

        # 验证检查间隔
        interval = self.get_setting('check_interval_hours')
        if not isinstance(interval, (int, float)) or interval <= 0:
            errors['check_interval_hours'] = '检查间隔必须为正数'

        # 验证重试次数
        retry_count = self.get_setting('retry_count')
        if not isinstance(retry_count, int) or retry_count < 0:
            errors['retry_count'] = '重试次数必须为非负整数'

        # 验证超时时间
        timeout = self.get_setting('download_timeout')
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors['download_timeout'] = '下载超时时间必须为正数'

        # 验证备份数量
        backup_count = self.get_setting('backup_count')
        if not isinstance(backup_count, int) or backup_count < 0:
            errors['backup_count'] = '备份数量必须为非负整数'

        # 验证定时时间格式
        scheduled_time = self.get_setting('scheduled_time')
        if scheduled_time:
            try:
                hour, minute = scheduled_time.split(':')
                hour, minute = int(hour), int(minute)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError()
            except (ValueError, AttributeError):
                errors['scheduled_time'] = '定时时间格式错误，应为 HH:MM 格式'

        # 验证定时天数
        scheduled_days = self.get_setting('scheduled_days')
        if not isinstance(scheduled_days, list) or not all(isinstance(d, int) and 0 <= d <= 6 for d in scheduled_days):
            errors['scheduled_days'] = '定时天数设置错误'

        # 验证代理URL
        if self.get_setting('use_proxy'):
            proxy_url = self.get_setting('proxy_url')
            if not proxy_url or not isinstance(proxy_url, str):
                errors['proxy_url'] = '启用代理时必须设置代理URL'

        return errors

    def get_backup_dir(self) -> Path:
        """获取备份目录路径

        Returns:
            备份目录路径
        """
        zed_path = Path(self.get_setting('zed_install_path'))
        return zed_path.parent / 'zed_backups'

    def get_temp_dir(self) -> Path:
        """获取临时下载目录路径

        Returns:
            临时目录路径
        """
        # 使用当前目录下的temp_downloads子目录
        temp_dir = Path.cwd() / 'temp_downloads'
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def is_first_run(self) -> bool:
        """检查是否为首次运行

        Returns:
            bool: 是否为首次运行
        """
        return not self.config_file.exists()

    def export_config(self, export_path: Path) -> bool:
        """导出配置到指定文件

        Args:
            export_path: 导出文件路径

        Returns:
            bool: 是否导出成功
        """
        try:
            with self.lock:
                config_json = json.dumps(self.config, indent=4, ensure_ascii=False)

            return write_file_with_encoding(export_path, config_json, encoding='utf-8-sig')
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False

    def import_config(self, import_path: Path) -> bool:
        """从指定文件导入配置

        Args:
            import_path: 导入文件路径

        Returns:
            bool: 是否导入成功
        """
        try:
            if not import_path.exists():
                logger.error(f"导入配置文件不存在: {import_path}")
                return False

            content = read_file_with_encoding(import_path)
            imported_config = json.loads(content)

            # 验证导入的配置是否包含必要的字段
            if not isinstance(imported_config, dict):
                logger.error("导入的配置不是有效的JSON对象")
                return False

            # 合并配置，保留默认值
            with self.lock:
                # 先创建一个新的配置字典
                new_config = self.DEFAULT_CONFIG.copy()
                # 用导入的配置更新默认配置
                new_config.update(imported_config)
                # 更新当前配置
                self.config = new_config

            # 保存导入的配置
            return self.save_config()
        except json.JSONDecodeError as e:
            logger.error(f"导入配置文件JSON格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
