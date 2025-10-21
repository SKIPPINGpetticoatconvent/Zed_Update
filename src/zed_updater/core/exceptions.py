#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom exceptions for Zed Updater
"""


class ZedUpdaterError(Exception):
    """Base exception for Zed Updater"""
    pass


class ConfigurationError(ZedUpdaterError):
    """Configuration related errors"""
    pass


class NetworkError(ZedUpdaterError):
    """Network and API related errors"""
    pass


class DownloadError(ZedUpdaterError):
    """Download related errors"""
    pass


class InstallationError(ZedUpdaterError):
    """Installation related errors"""
    pass


class ValidationError(ZedUpdaterError):
    """Validation related errors"""
    pass


class GitHubAPIError(NetworkError):
    """GitHub API specific errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class ChecksumError(ValidationError):
    """Checksum validation errors"""
    def __init__(self, expected: str, actual: str, file_path: str):
        self.expected = expected
        self.actual = actual
        self.file_path = file_path
        super().__init__(f"Checksum mismatch for {file_path}: expected {expected}, got {actual}")


class ProcessError(ZedUpdaterError):
    """Process management errors"""
    def __init__(self, pid: int, operation: str, message: str = None):
        self.pid = pid
        self.operation = operation
        super().__init__(message or f"Failed to {operation} process {pid}")


class PermissionError(ZedUpdaterError):
    """Permission related errors"""
    pass


class TimeoutError(ZedUpdaterError):
    """Timeout related errors"""
    pass


class FileOperationError(ZedUpdaterError):
    """File operation errors"""
    def __init__(self, file_path: str, operation: str, message: str = None):
        self.file_path = file_path
        self.operation = operation
        super().__init__(message or f"Failed to {operation} file: {file_path}")


class SchedulerError(ZedUpdaterError):
    """Scheduler related errors"""
    pass