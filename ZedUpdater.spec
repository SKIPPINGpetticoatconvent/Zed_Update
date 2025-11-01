# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for ZedUpdater
Simplified for unified architecture
"""

import sys
from pathlib import Path

block_cipher = None

# Get project root directory
project_root = Path.cwd()

a = Analysis(
    ['src/zed_updater/gui_main.py'],  # Updated entry point
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('config.example.json', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('src/zed_updater', 'zed_updater'),  # Package data
    ],
    hiddenimports=[
        # PyQt5 core modules
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        # Windows specific modules
        'win32api',
        'win32con',
        'win32file',
        'pywintypes',
        # Core dependencies
        'psutil',
        'requests',
        # Python standard library modules
        'json',
        'logging',
        'pathlib',
        'subprocess',
        'tempfile',
        'shutil',
        'hashlib',
        'zipfile',
        'datetime',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
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
    console=False,  # No console window
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
    resources=[],
    uac_admin=False,
    uac_uiaccess=False,
)