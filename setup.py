#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Zed Updater
"""

from setuptools import setup, find_packages

# Read requirements
def read_requirements(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Zed Editor Auto Updater"

setup(
    name="zed-updater",
    version="2.1.0",
    description="Zed Editor Auto Updater - Modern implementation with GUI and CLI support",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Zed Update Team",
    author_email="team@zed-updater.dev",
    url="https://github.com/TC999/zed-update",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0',
        ],
        'build': [
            'pyinstaller>=5.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'zed-updater=zed_updater.cli:main',
        ],
        'gui_scripts': [
            'zed-updater-gui=zed_updater.gui_main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: System :: Software Distribution",
    ],
    python_requires=">=3.9",
    keywords="zed editor updater auto-update gui automation",
    project_urls={
        "Homepage": "https://github.com/TC999/zed-update",
        "Repository": "https://github.com/TC999/zed-update",
        "Issues": "https://github.com/TC999/zed-update/issues",
        "Changelog": "https://github.com/TC999/zed-update/blob/main/CHANGELOG.md",
    },
)