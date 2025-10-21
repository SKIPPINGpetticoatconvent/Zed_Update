#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor Auto Updater - Core Package

A modern, extensible auto-updater for Zed Editor with both legacy and modern
implementations supporting multiple architectures.
"""

__version__ = "2.1.0"
__author__ = "Zed Update Team"
__description__ = "Zed Editor Auto Updater with Legacy and Modern Implementations"

from .core.config import ConfigManager
from .core.updater import ZedUpdater
from .core.scheduler import UpdateScheduler
from .utils.logger import setup_logging
from .utils.encoding import EncodingUtils

__all__ = [
    'ConfigManager',
    'ZedUpdater',
    'UpdateScheduler',
    'setup_logging',
    'EncodingUtils'
]