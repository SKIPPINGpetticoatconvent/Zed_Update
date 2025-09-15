#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时调度模块
负责管理Zed更新的定时任务
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
import logging
import schedule

logger = logging.getLogger(__name__)

class UpdateScheduler:
    """更新调度器"""

    def __init__(self, updater, config):
        """初始化调度器

        Args:
            updater: 更新器实例
            config: 配置管理器实例
        """
        self.updater = updater
        self.config = config
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.update_callbacks = []

    def add_update_callback(self, callback: Callable):
        """添加更新回调函数

        Args:
            callback: 当有更新时调用的回调函数
        """
        self.update_callbacks.append(callback)

    def remove_update_callback(self, callback: Callable):
        """移除更新回调函数

        Args:
            callback: 要移除的回调函数
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

    def _notify_callbacks(self, update_available: bool, version_info: dict = None):
        """通知所有回调函数

        Args:
            update_available: 是否有可用更新
            version_info: 版本信息字典
        """
        for callback in self.update_callbacks:
            try:
                callback(update_available, version_info)
            except Exception as e:
                logger.error(f"调用更新回调函数时出错: {e}")

    def _check_for_updates(self):
        """检查更新的内部方法"""
        try:
            logger.info("定时检查更新...")

            # 获取当前版本和最新版本信息
            current_version = self.updater.get_current_version()
            latest_info = self.updater.get_latest_version_info()

            if not latest_info:
                logger.warning("无法获取最新版本信息")
                return

            latest_version = latest_info['version']

            # 比较版本
            if current_version and self.updater.compare_versions(current_version, latest_version) < 0:
                logger.info(f"发现新版本: {latest_version} (当前: {current_version})")

                # 通知回调函数
                self._notify_callbacks(True, latest_info)

                # 如果启用了自动下载，则开始下载
                if self.config.get_setting('auto_download', True):
                    self._auto_update(latest_info)

            else:
                logger.info("已是最新版本")
                self._notify_callbacks(False, latest_info)

        except Exception as e:
            logger.error(f"检查更新时出错: {e}")

    def _auto_update(self, version_info: dict):
        """自动更新处理

        Args:
            version_info: 版本信息
        """
        try:
            # 如果启用了自动安装，则直接更新
            if self.config.get_setting('auto_install', False):
                logger.info("开始自动更新...")

                def progress_callback(progress, message=""):
                    logger.info(f"更新进度: {progress:.1f}% - {message}")

                success = self.updater.check_and_update(progress_callback)

                if success:
                    logger.info("自动更新成功")

                    # 如果设置了更新后自动启动，则启动Zed
                    if self.config.get_setting('auto_start_after_update', True):
                        self.updater.start_zed()
                else:
                    logger.error("自动更新失败")
            else:
                logger.info("自动安装未启用，仅下载更新文件")
                download_path = self.updater.download_update()
                if download_path:
                    logger.info(f"更新文件已下载到: {download_path}")

        except Exception as e:
            logger.error(f"自动更新过程中出错: {e}")

    def setup_schedule(self):
        """设置调度任务"""
        try:
            schedule.clear()  # 清除现有任务

            # 检查间隔调度
            if self.config.get_setting('auto_check_enabled', True):
                interval_hours = self.config.get_setting('check_interval_hours', 24)
                schedule.every(interval_hours).hours.do(self._check_for_updates)
                logger.info(f"设置间隔检查: 每 {interval_hours} 小时")

            # 定时调度
            if self.config.get_setting('scheduled_update_enabled', False):
                scheduled_time = self.config.get_setting('scheduled_time', '02:00')
                scheduled_days = self.config.get_setting('scheduled_days', [0, 1, 2, 3, 4, 5, 6])

                # 根据选择的天数设置任务
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday',
                           'friday', 'saturday', 'sunday']

                for day_index in scheduled_days:
                    if 0 <= day_index <= 6:
                        day_name = day_names[day_index]
                        getattr(schedule.every(), day_name).at(scheduled_time).do(self._check_for_updates)
                        logger.info(f"设置定时检查: 每周{day_name} {scheduled_time}")

            # 启动时检查
            if self.config.get_setting('check_on_startup', True):
                # 延迟5秒后执行启动检查，避免启动时的资源竞争
                def delayed_startup_check():
                    time.sleep(5)
                    self._check_for_updates()

                threading.Thread(target=delayed_startup_check, daemon=True).start()
                logger.info("设置启动时检查")

        except Exception as e:
            logger.error(f"设置调度任务时出错: {e}")

    def _scheduler_worker(self):
        """调度器工作线程"""
        logger.info("调度器线程已启动")

        while not self.stop_event.is_set():
            try:
                schedule.run_pending()
                # 优化检查间隔，减少CPU使用
                time.sleep(60)  # 每60秒检查一次，提高性能

            except Exception as e:
                logger.error(f"调度器线程执行时出错: {type(e).__name__}: {e}")
                time.sleep(120)  # 出错后等待更长时间

        logger.info("调度器线程已停止")

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return

        try:
            # 设置调度任务
            self.setup_schedule()

            # 启动调度器线程
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            self.scheduler_thread.start()

            self.is_running = True
            logger.info("调度器已启动")

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            self.is_running = False

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return

        try:
            # 停止调度器线程
            self.stop_event.set()

            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)

            # 清除所有调度任务
            schedule.clear()

            self.is_running = False
            logger.info("调度器已停止")

        except Exception as e:
            logger.error(f"停止调度器时出错: {e}")

    def restart(self):
        """重启调度器"""
        logger.info("重启调度器...")
        self.stop()
        time.sleep(1)
        self.start()

    def is_scheduler_running(self) -> bool:
        """检查调度器是否在运行

        Returns:
            bool: 调度器是否在运行
        """
        return self.is_running

    def get_next_run_time(self) -> Optional[datetime]:
        """获取下次运行时间

        Returns:
            下次运行时间，如果没有设置任务则返回None
        """
        try:
            jobs = schedule.jobs
            if not jobs:
                return None

            # 找到最近的下次运行时间
            next_run_times = [job.next_run for job in jobs if job.next_run]
            if next_run_times:
                return min(next_run_times)

        except Exception as e:
            logger.error(f"获取下次运行时间时出错: {e}")

        return None

    def get_schedule_status(self) -> dict:
        """获取调度状态信息

        Returns:
            包含调度状态信息的字典
        """
        try:
            jobs = schedule.jobs
            next_run = self.get_next_run_time()

            return {
                'is_running': self.is_running,
                'jobs_count': len(jobs),
                'next_run_time': next_run.isoformat() if next_run else None,
                'last_check_time': self.config.get_setting('last_check_time'),
                'last_update_time': self.config.get_setting('last_update_time'),
                'auto_check_enabled': self.config.get_setting('auto_check_enabled', True),
                'scheduled_update_enabled': self.config.get_setting('scheduled_update_enabled', False),
                'check_interval_hours': self.config.get_setting('check_interval_hours', 24)
            }

        except Exception as e:
            logger.error(f"获取调度状态时出错: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }

    def force_check_now(self):
        """立即执行一次更新检查"""
        logger.info("手动触发更新检查")
        threading.Thread(target=self._check_for_updates, daemon=True).start()

    def update_schedule_config(self):
        """更新调度配置（当配置发生变化时调用）"""
        if self.is_running:
            logger.info("配置已更改，重新设置调度任务")
            self.setup_schedule()
