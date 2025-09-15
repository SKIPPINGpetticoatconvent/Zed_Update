#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序 - 安装配置文件
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# 读取 README.md 文件
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# 读取 requirements.txt 文件
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            requirements.append(line)

setup(
    name="zed-updater",
    version="1.0.0",
    description="Zed Editor 自动更新程序",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Zed Updater Team",
    author_email="example@example.com",
    url="https://github.com/TC999/zed-loc",
    packages=find_packages(),
    package_data={
        "updater": ["**/*"],
        "": ["*.json", "*.md", "*.txt"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "zed-updater=main:main",
        ],
        "gui_scripts": [
            "zed-updater-gui=gui_launcher:main",
        ],
    },
    python_requires=">=3.7",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
    keywords="zed, editor, updater, automatic",
    project_urls={
        "Bug Reports": "https://github.com/TC999/zed-loc/issues",
        "Source": "https://github.com/TC999/zed-loc",
    },
)
