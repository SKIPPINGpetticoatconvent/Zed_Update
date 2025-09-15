# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for ZedUpdater
Optimized for GUI-only execution without console window
"""

import sys
from pathlib import Path

block_cipher = None

# 获取项目根目录
project_root = Path.cwd()

a = Analysis(
    ['gui_launcher.pyw'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('config.example.json', '.'),
        ('main.py', '.'),
        ('updater', 'updater'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('CHANGELOG.md', '.'),
        ('QUICK_START.md', '.'),
    ],
    hiddenimports=[
        # PyQt5 core modules
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'PyQt5.Qt',
        # Windows specific modules
        'win32api',
        'win32con',
        'win32file',
        'win32gui',
        'win32process',
        'pywintypes',
        'win32com',
        'win32com.client',
        # System and utility modules
        'psutil',
        'schedule',
        'requests',
        'urllib3',
        'chardet',
        'dateutil',
        'dateutil.parser',
        'dateutil.tz',
        # Python standard library modules that might be missed
        'ctypes',
        'ctypes.wintypes',
        'threading',
        'concurrent.futures',
        'json',
        'logging',
        'pathlib',
        'subprocess',
        'tempfile',
        'zipfile',
        'shutil',
        'hashlib',
        'socket',
        'ssl',
        'certifi',
        # Encoding modules
        'encodings',
        'encodings.utf_8',
        'encodings.cp1252',
        'encodings.ascii',
        'locale',
        'codecs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'test',
        'tests',
        'unittest',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZedUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # 关键设置：禁用控制台窗口
    console=False,
    # 禁用窗口化回溯，避免错误弹窗
    disable_windowed_traceback=True,
    # Windows专用设置
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标设置（如果存在）
    icon=None,
    # 版本信息
    version_file=None,  # 可以添加版本信息文件
    # 资源文件
    resources=[],
    # UPX 压缩排除文件
    uac_admin=False,  # 不需要管理员权限
    uac_uiaccess=False,
)
