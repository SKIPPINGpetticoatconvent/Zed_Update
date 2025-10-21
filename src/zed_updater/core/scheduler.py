#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update scheduler for Zed Updater
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from .config import ConfigManager
from .updater import ZedUpdater, UpdateResult
from ..utils.logger import get_logger


@dataclass
class ScheduleStatus:
    """Scheduler status information"""
    is_running: bool
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    last_result: Optional[UpdateResult]


class UpdateScheduler:
    """Scheduler for automatic Zed updates"""

    def __init__(self, updater: ZedUpdater, config: ConfigManager):
        self.updater = updater
        self.config = config
        self.logger = get_logger(__name__)

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_callbacks: list[Callable[[bool, UpdateResult], None]] = []

        self._status = ScheduleStatus(
            is_running=False,
            next_run_time=None,
            last_run_time=None,
            last_result=None
        )

    def add_update_callback(self, callback: Callable[[bool, UpdateResult], None]) -> None:
        """Add callback for update events"""
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)

    def remove_update_callback(self, callback: Callable[[bool, UpdateResult], None]) -> None:
        """Remove update callback"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    def _notify_callbacks(self, update_available: bool, result: Optional[UpdateResult] = None) -> None:
        """Notify all registered callbacks"""
        for callback in self._update_callbacks:
            try:
                callback(update_available, result)
            except Exception as e:
                self.logger.error(f"Update callback failed: {e}")

    def start(self) -> bool:
        """Start the scheduler"""
        if self._thread and self._thread.is_alive():
            self.logger.warning("Scheduler is already running")
            return False

        if not self.config.get('auto_check_enabled'):
            self.logger.info("Auto-check is disabled, not starting scheduler")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

        self._status.is_running = True
        self._update_next_run_time()

        self.logger.info("Update scheduler started")
        return True

    def stop(self) -> bool:
        """Stop the scheduler"""
        if not self._thread or not self._thread.is_alive():
            self.logger.warning("Scheduler is not running")
            return False

        self._stop_event.set()
        self._thread.join(timeout=5)

        self._status.is_running = False
        self._status.next_run_time = None

        self.logger.info("Update scheduler stopped")
        return True

    def restart(self) -> bool:
        """Restart the scheduler"""
        self.stop()
        return self.start()

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._status.is_running and self._thread and self._thread.is_alive()

    def force_check_now(self) -> UpdateResult:
        """Force an immediate update check"""
        self.logger.info("Forced update check initiated")

        try:
            result = self.updater.check_and_update()
            self._status.last_run_time = datetime.now()
            self._status.last_result = result

            # Notify callbacks
            update_available = result.success and result.version is not None
            self._notify_callbacks(update_available, result)

            return result

        except Exception as e:
            error_result = UpdateResult(
                success=False,
                message=f"Scheduled check failed: {e}",
                error_code="SCHEDULE_FAILED"
            )
            self._status.last_result = error_result
            self._notify_callbacks(False, error_result)
            return error_result

    def get_status(self) -> ScheduleStatus:
        """Get current scheduler status"""
        return self._status

    def update_schedule_config(self) -> None:
        """Update schedule configuration"""
        if self.is_running():
            self._update_next_run_time()

    def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        self.logger.debug("Scheduler loop started")

        while not self._stop_event.is_set():
            try:
                # Calculate next run time
                self._update_next_run_time()

                if self._status.next_run_time:
                    # Wait until next run time
                    while (not self._stop_event.is_set() and
                           datetime.now() < self._status.next_run_time):
                        # Sleep in small intervals to allow for quick shutdown
                        self._stop_event.wait(60)  # Check every minute

                    if self._stop_event.is_set():
                        break

                    # Time to run the check
                    self.logger.info("Scheduled update check starting")
                    self.force_check_now()

                    # Add small delay before next iteration
                    time.sleep(1)

                else:
                    # No schedule configured, wait a bit and check again
                    self._stop_event.wait(300)  # Wait 5 minutes

            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                # Wait before retrying
                self._stop_event.wait(60)

        self.logger.debug("Scheduler loop ended")

    def _update_next_run_time(self) -> None:
        """Update the next scheduled run time"""
        try:
            if not self.config.get('auto_check_enabled'):
                self._status.next_run_time = None
                return

            interval_hours = self.config.get('check_interval_hours', 24)
            check_time = self.config.get('check_time')

            now = datetime.now()

            if check_time:
                # Use specific time each day
                try:
                    hour, minute = map(int, check_time.split(':'))
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # If the time has passed today, schedule for tomorrow
                    if next_run <= now:
                        next_run += timedelta(days=1)

                except ValueError:
                    # Invalid time format, fall back to interval
                    next_run = now + timedelta(hours=interval_hours)
            else:
                # Use interval from now
                next_run = now + timedelta(hours=interval_hours)

            self._status.next_run_time = next_run
            self.logger.debug(f"Next scheduled run: {next_run}")

        except Exception as e:
            self.logger.error(f"Failed to calculate next run time: {e}")
            self._status.next_run_time = None

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        return self._status.next_run_time

    def get_last_run_time(self) -> Optional[datetime]:
        """Get the last run time"""
        return self._status.last_run_time

    def get_last_result(self) -> Optional[UpdateResult]:
        """Get the last update result"""
        return self._status.last_result