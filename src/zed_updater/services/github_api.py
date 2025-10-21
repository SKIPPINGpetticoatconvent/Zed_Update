#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub API service for Zed Updater
"""

import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import requests

from ..utils.logger import get_logger


@dataclass
class ReleaseAsset:
    """Release asset information"""
    name: str
    download_url: str
    size: int
    content_type: str


@dataclass
class ReleaseInfo:
    """Release information"""
    version: str
    release_date: datetime
    download_url: str
    description: str
    size: int
    sha256: Optional[str]
    assets: List[ReleaseAsset]


class GitHubAPI:
    """GitHub API client for fetching Zed releases"""

    API_BASE = "https://api.github.com"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, repo: str = "TC999/zed-loc", api_url: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.repo = repo
        self.api_base = api_url or self.API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZedUpdater/2.1.0',
            'Accept': 'application/vnd.github.v3+json'
        })

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic"""
        url = f"{self.api_base}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=self.REQUEST_TIMEOUT)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    self.logger.warning(f"Resource not found: {url}")
                    return None
                elif response.status_code == 403:
                    self.logger.warning(f"Rate limited or forbidden: {url}")
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY * (attempt + 1))
                        continue
                    return None
                else:
                    self.logger.error(f"API request failed: {response.status_code} - {url}")
                    return None

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                else:
                    self.logger.error(f"Request failed after {self.MAX_RETRIES} attempts: {e}")
                    return None

        return None

    def get_latest_release(self) -> Optional[ReleaseInfo]:
        """Get latest release information"""
        endpoint = f"/repos/{self.repo}/releases/latest"
        data = self._make_request(endpoint)

        if not data:
            return None

        try:
            # Parse release date
            release_date = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00'))

            # Find Windows executable asset
            download_url = ""
            asset_size = 0
            assets = []

            for asset_data in data.get('assets', []):
                asset = ReleaseAsset(
                    name=asset_data['name'],
                    download_url=asset_data['browser_download_url'],
                    size=asset_data['size'],
                    content_type=asset_data.get('content_type', '')
                )
                assets.append(asset)

                # Prefer Windows executables
                if self._is_windows_executable(asset.name):
                    download_url = asset.download_url
                    asset_size = asset.size

            # Fallback to first asset if no Windows-specific found
            if not download_url and assets:
                download_url = assets[0].download_url
                asset_size = assets[0].size

            if not download_url:
                self.logger.error("No suitable download asset found")
                return None

            # Extract version from tag
            tag_name = data.get('tag_name', '')
            version = tag_name.lstrip('v') if tag_name else 'latest'

            release_info = ReleaseInfo(
                version=version,
                release_date=release_date,
                download_url=download_url,
                description=data.get('body', ''),
                size=asset_size,
                sha256=None,  # GitHub doesn't provide SHA256 in API
                assets=assets
            )

            self.logger.info(f"Retrieved latest release: {version}")
            return release_info

        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse release data: {e}")
            return None

    def get_release_by_tag(self, tag: str) -> Optional[ReleaseInfo]:
        """Get specific release by tag"""
        endpoint = f"/repos/{self.repo}/releases/tags/{tag}"
        data = self._make_request(endpoint)

        if not data:
            return None

        # Similar parsing as get_latest_release
        try:
            release_date = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00'))

            download_url = ""
            asset_size = 0
            assets = []

            for asset_data in data.get('assets', []):
                asset = ReleaseAsset(
                    name=asset_data['name'],
                    download_url=asset_data['browser_download_url'],
                    size=asset_data['size'],
                    content_type=asset_data.get('content_type', '')
                )
                assets.append(asset)

                if self._is_windows_executable(asset.name):
                    download_url = asset.download_url
                    asset_size = asset.size

            if not download_url and assets:
                download_url = assets[0].download_url
                asset_size = assets[0].size

            version = tag.lstrip('v') if tag else tag

            return ReleaseInfo(
                version=version,
                release_date=release_date,
                download_url=download_url,
                description=data.get('body', ''),
                size=asset_size,
                sha256=None,
                assets=assets
            )

        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse release data for tag {tag}: {e}")
            return None

    def get_releases(self, count: int = 10) -> List[ReleaseInfo]:
        """Get list of recent releases"""
        endpoint = f"/repos/{self.repo}/releases"
        params = {'per_page': min(count, 100)}  # GitHub API limit
        data = self._make_request(endpoint, params)

        if not data:
            return []

        releases = []
        for release_data in data:
            try:
                release_date = datetime.fromisoformat(release_data['published_at'].replace('Z', '+00:00'))

                assets = []
                for asset_data in release_data.get('assets', []):
                    asset = ReleaseAsset(
                        name=asset_data['name'],
                        download_url=asset_data['browser_download_url'],
                        size=asset_data['size'],
                        content_type=asset_data.get('content_type', '')
                    )
                    assets.append(asset)

                release_info = ReleaseInfo(
                    version=release_data.get('tag_name', '').lstrip('v'),
                    release_date=release_date,
                    download_url="",  # Will be set by caller if needed
                    description=release_data.get('body', ''),
                    size=0,  # Will be set by caller if needed
                    sha256=None,
                    assets=assets
                )

                releases.append(release_info)

            except (KeyError, ValueError) as e:
                self.logger.warning(f"Failed to parse release data: {e}")
                continue

        return releases

    def _is_windows_executable(self, filename: str) -> bool:
        """Check if filename indicates a Windows executable"""
        filename_lower = filename.lower()
        return (filename_lower.endswith('.exe') or
                filename_lower.endswith('.msi') or
                'windows' in filename_lower)

    def set_proxy(self, proxy_url: str) -> None:
        """Set proxy for requests"""
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        else:
            self.session.proxies = {}

    def verify_checksum(self, file_path: str, expected_sha256: str) -> bool:
        """Verify file checksum (if SHA256 is provided)"""
        if not expected_sha256:
            return True  # Skip verification if no hash provided

        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            calculated_hash = sha256.hexdigest()
            return calculated_hash.lower() == expected_sha256.lower()

        except Exception as e:
            self.logger.error(f"Failed to verify checksum: {e}")
            return False