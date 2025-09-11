#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台工具模块
提供系统平台相关的功能和操作
"""

import os
import sys
import logging
import subprocess
import platform
import winreg
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

def is_windows() -> bool:
    """
    检查当前系统是否为Windows

    Returns:
        bool: 是否为Windows系统
    """
    return sys.platform == 'win32'

def is_admin() -> bool:
    """
    检查当前程序是否以管理员权限运行

    Returns:
        bool: 是否具有管理员权限
    """
    if not is_windows():
        return False

    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"检查管理员权限时出错: {e}")
        return False

def get_system_info() -> dict:
    """
    获取系统信息

    Returns:
        dict: 包含系统信息的字典
    """
    info = {
        'os_name': platform.system(),
        'os_version': platform.version(),
        'os_release': platform.release(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }

    if is_windows():
        try:
            import wmi
            c = wmi.WMI()
            for os in c.Win32_OperatingSystem():
                info['windows_edition'] = os.Caption
                info['windows_build'] = os.BuildNumber
                info['last_boot'] = os.LastBootUpTime
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"获取Windows系统信息时出错: {e}")

    return info

def kill_process(process_name: str) -> bool:
    """
    强制结束指定名称的进程

    Args:
        process_name: 进程名称，例如"zed.exe"

    Returns:
        bool: 是否成功结束进程
    """
    try:
        if is_windows():
            # Windows平台使用taskkill命令
            subprocess.run(
                ['taskkill', '/F', '/IM', process_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        else:
            # 在其他平台上，这个函数不应该被调用
            logger.warning("kill_process函数目前仅支持Windows平台")
            return False
    except Exception as e:
        logger.error(f"结束进程 {process_name} 时出错: {e}")
        return False

def is_process_running(process_name: str) -> bool:
    """
    检查指定名称的进程是否在运行

    Args:
        process_name: 进程名称，例如"zed.exe"

    Returns:
        bool: 进程是否在运行
    """
    try:
        if is_windows():
            # Windows平台使用tasklist命令
            result = subprocess.run(
                ['tasklist', '/NH', '/FI', f'IMAGENAME eq {process_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return process_name.lower() in result.stdout.lower()
        else:
            # 在其他平台上，这个函数不应该被调用
            logger.warning("is_process_running函数目前仅支持Windows平台")
            return False
    except Exception as e:
        logger.error(f"检查进程 {process_name} 是否运行时出错: {e}")
        return False

def set_autostart(enable: bool, app_name: str = "ZedUpdater", executable_path: Optional[str] = None) -> bool:
    """
    设置或取消程序开机自启动

    Args:
        enable: 是否启用开机自启动
        app_name: 应用程序名称，用于注册表键
        executable_path: 可执行文件路径，如果为None则使用当前脚本路径

    Returns:
        bool: 操作是否成功
    """
    if not is_windows():
        logger.warning("设置开机自启动功能目前仅支持Windows平台")
        return False

    try:
        # 如果未指定可执行文件路径，使用当前脚本路径
        if executable_path is None:
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的环境
                executable_path = sys.executable
            else:
                # 常规Python脚本环境
                script_path = os.path.abspath(sys.argv[0])
                executable_path = f'"{sys.executable}" "{script_path}"'

        # 打开注册表键
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enable:
            # 设置开机自启动
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
            logger.info(f"已设置开机自启动: {executable_path}")
        else:
            # 取消开机自启动
            try:
                winreg.DeleteValue(key, app_name)
                logger.info("已取消开机自启动")
            except FileNotFoundError:
                # 如果键不存在，忽略错误
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"设置开机自启动时出错: {e}")
        return False

def get_autostart_status(app_name: str = "ZedUpdater") -> bool:
    """
    获取程序是否设置了开机自启动

    Args:
        app_name: 应用程序名称，用于注册表键

    Returns:
        bool: 是否已设置开机自启动
    """
    if not is_windows():
        return False

    try:
        # 打开注册表键
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_QUERY_VALUE
        )

        # 查询键值
        try:
            winreg.QueryValueEx(key, app_name)
            result = True
        except FileNotFoundError:
            result = False

        winreg.CloseKey(key)
        return result
    except Exception as e:
        logger.error(f"检查开机自启动状态时出错: {e}")
        return False

def get_windows_version() -> Tuple[int, int, int]:
    """
    获取Windows版本号

    Returns:
        Tuple[int, int, int]: (主版本号, 次版本号, 构建号)
    """
    if not is_windows():
        return (0, 0, 0)

    try:
        version = platform.version().split('.')
        return (
            int(version[0]) if len(version) > 0 else 0,
            int(version[1]) if len(version) > 1 else 0,
            int(version[2]) if len(version) > 2 else 0
        )
    except Exception as e:
        logger.error(f"获取Windows版本号时出错: {e}")
        return (0, 0, 0)

def get_windows_exe_info(exe_path: str) -> dict:
    """
    获取Windows可执行文件信息

    Args:
        exe_path: 可执行文件路径

    Returns:
        dict: 包含文件信息的字典
    """
    if not is_windows():
        return {}

    try:
        import win32api
        info = win32api.GetFileVersionInfo(exe_path, '\\')
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"

        # 获取字符串信息
        string_file_info = {}
        try:
            # 查找第一个语言和代码页
            lang, codepage = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')[0]
            string_info_path = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\'

            # 获取各种字符串信息
            for info_name in ['FileDescription', 'FileVersion', 'InternalName', 'LegalCopyright',
                            'OriginalFilename', 'ProductName', 'ProductVersion', 'CompanyName']:
                try:
                    string_file_info[info_name] = win32api.GetFileVersionInfo(exe_path, string_info_path + info_name)
                except:
                    pass
        except:
            pass

        return {
            'version': version,
            'version_tuple': (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls)),
            'string_info': string_file_info
        }
    except ImportError:
        logger.warning("无法导入win32api模块，无法获取EXE文件版本信息")
        return {}
    except Exception as e:
        logger.error(f"获取EXE文件信息时出错: {e}")
        return {}

def create_shortcut(target_path: str, shortcut_path: str, description: str = "",
                  arguments: str = "", working_dir: Optional[str] = None, icon_path: Optional[str] = None) -> bool:
    """
    创建Windows快捷方式

    Args:
        target_path: 目标文件路径
        shortcut_path: 快捷方式保存路径，需要包含.lnk扩展名
        description: 快捷方式描述
        arguments: 命令行参数
        working_dir: 工作目录，如果为None则使用目标文件所在目录
        icon_path: 图标路径，如果为None则使用目标文件图标

    Returns:
        bool: 是否成功创建快捷方式
    """
    if not is_windows():
        logger.warning("创建快捷方式功能目前仅支持Windows平台")
        return False

    try:
        import pythoncom
        from win32com.client import Dispatch

        if working_dir is None:
            working_dir = str(Path(target_path).parent)

        if not shortcut_path.endswith('.lnk'):
            shortcut_path += '.lnk'

        # 创建快捷方式
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.Arguments = arguments
        shortcut.Description = description
        shortcut.WorkingDirectory = working_dir

        if icon_path:
            shortcut.IconLocation = icon_path

        shortcut.save()
        logger.info(f"成功创建快捷方式: {shortcut_path}")
        return True
    except ImportError:
        logger.warning("无法导入必要模块，无法创建快捷方式")
        return False
    except Exception as e:
        logger.error(f"创建快捷方式时出错: {e}")
        return False
