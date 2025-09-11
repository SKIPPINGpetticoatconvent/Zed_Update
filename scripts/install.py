#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序安装脚本
负责安装和配置应用程序
"""

import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
import json
import ctypes
import winreg
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 添加父目录到模块搜索路径
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def request_admin():
    """请求管理员权限重新启动脚本"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

def find_zed_executable():
    """尝试自动查找Zed可执行文件"""
    # 常见的Zed安装路径
    common_paths = [
        Path(os.environ.get('LOCALAPPDATA', '')) / "Programs" / "Zed" / "Zed.exe",
        Path(os.environ.get('PROGRAMFILES', '')) / "Zed" / "Zed.exe",
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / "Zed" / "Zed.exe",
        Path("C:/Program Files") / "Zed" / "Zed.exe",
        Path("C:/Program Files (x86)") / "Zed" / "Zed.exe",
        Path("D:/Program Files") / "Zed" / "Zed.exe",
        Path("D:/Zed.exe"),
        Path("C:/Zed.exe"),
    ]

    # 搜索注册表
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Zed.exe")
        value, _ = winreg.QueryValueEx(key, "")
        if value:
            common_paths.insert(0, Path(value))
        winreg.CloseKey(key)
    except:
        pass

    # 搜索桌面快捷方式
    desktop = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
    for item in desktop.glob("*Zed*.lnk"):
        try:
            from win32com.client import Dispatch
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(item))
            target = shortcut.Targetpath
            if target and "zed" in target.lower():
                common_paths.insert(0, Path(target))
        except:
            pass

    # 检查每个路径
    for path in common_paths:
        if path.exists() and path.is_file():
            return str(path)

    return None

def create_config_file(zed_path, auto_start=True):
    """创建默认配置文件"""
    config_path = Path(parent_dir) / "config.json"

    config = {
        # 基本设置
        'zed_install_path': str(zed_path),
        'backup_enabled': True,
        'backup_count': 3,

        # GitHub设置
        'github_repo': 'TC999/zed-loc',
        'github_api_url': 'https://api.github.com/repos/TC999/zed-loc/releases/latest',
        'download_timeout': 300,
        'retry_count': 3,

        # 自动更新设置
        'auto_check_enabled': True,
        'check_interval_hours': 24,
        'check_on_startup': True,
        'auto_download': True,
        'auto_install': False,
        'force_download_latest': True,

        # 启动设置
        'auto_start_after_update': True,
        'start_minimized': False,

        # 通知设置
        'show_notifications': True,
        'notify_on_update_available': True,
        'notify_on_update_complete': True,

        # 定时任务设置
        'scheduled_update_enabled': False,
        'scheduled_time': '02:00',
        'scheduled_days': [0, 1, 2, 3, 4, 5, 6],

        # 高级设置
        'use_proxy': False,
        'proxy_url': '',
        'verify_signature': True,
        'log_level': 'INFO',

        # 界面设置
        'window_width': 600,
        'window_height': 500,
        'minimize_to_tray': True,
        'start_with_system': auto_start,
    }

    with open(config_path, 'w', encoding='utf-8-sig') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    logger.info(f"已创建配置文件: {config_path}")
    return config_path

def create_shortcuts(auto_start=True):
    """创建桌面和开始菜单快捷方式"""
    try:
        import pythoncom
        from win32com.client import Dispatch

        # 获取路径
        app_path = Path(parent_dir)
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包时
            target_path = sys.executable
        else:
            # 普通 Python 脚本
            target_path = str(app_path / "scripts" / "run.py")

        # 创建桌面快捷方式
        desktop_path = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))
        desktop_shortcut = desktop_path / "Zed自动更新.lnk"

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(desktop_shortcut))
        shortcut.Targetpath = sys.executable if getattr(sys, 'frozen', False) else sys.executable
        shortcut.Arguments = "" if getattr(sys, 'frozen', False) else f'"{target_path}"'
        shortcut.WorkingDirectory = str(app_path)
        shortcut.Description = "Zed编辑器自动更新程序"
        shortcut.IconLocation = str(app_path / "resources" / "icons" / "app.ico")
        shortcut.save()

        logger.info(f"已创建桌面快捷方式: {desktop_shortcut}")

        # 创建开始菜单快捷方式
        start_menu_path = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Zed自动更新"
        start_menu_path.mkdir(parents=True, exist_ok=True)
        start_menu_shortcut = start_menu_path / "Zed自动更新.lnk"

        shortcut = shell.CreateShortCut(str(start_menu_shortcut))
        shortcut.Targetpath = sys.executable if getattr(sys, 'frozen', False) else sys.executable
        shortcut.Arguments = "" if getattr(sys, 'frozen', False) else f'"{target_path}"'
        shortcut.WorkingDirectory = str(app_path)
        shortcut.Description = "Zed编辑器自动更新程序"
        shortcut.IconLocation = str(app_path / "resources" / "icons" / "app.ico")
        shortcut.save()

        logger.info(f"已创建开始菜单快捷方式: {start_menu_shortcut}")

        # 设置开机自启动
        if auto_start:
            startup_path = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup_shortcut = startup_path / "Zed自动更新.lnk"

            shortcut = shell.CreateShortCut(str(startup_shortcut))
            shortcut.Targetpath = sys.executable if getattr(sys, 'frozen', False) else sys.executable
            shortcut.Arguments = "--gui" if getattr(sys, 'frozen', False) else f'"{target_path}" --gui'
            shortcut.WorkingDirectory = str(app_path)
            shortcut.Description = "Zed编辑器自动更新程序"
            shortcut.IconLocation = str(app_path / "resources" / "icons" / "app.ico")
            shortcut.save()

            logger.info(f"已设置开机自启动: {startup_shortcut}")

        return True
    except Exception as e:
        logger.error(f"创建快捷方式失败: {e}")
        return False

def set_registry_autostart(auto_start=True):
    """设置注册表自启动项"""
    try:
        app_path = Path(parent_dir)
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包时
            target_path = f'"{sys.executable}" --gui'
        else:
            # 普通 Python 脚本
            script_path = str(app_path / "scripts" / "run.py")
            target_path = f'"{sys.executable}" "{script_path}" --gui'

        # 打开注册表键
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if auto_start:
            # 设置开机自启动
            winreg.SetValueEx(key, "ZedUpdater", 0, winreg.REG_SZ, target_path)
            logger.info(f"已设置注册表开机自启动")
        else:
            # 尝试删除自启动项
            try:
                winreg.DeleteValue(key, "ZedUpdater")
                logger.info("已移除注册表开机自启动项")
            except:
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"设置注册表自启动失败: {e}")
        return False

def create_temp_dirs():
    """创建临时目录"""
    try:
        temp_dir = Path(parent_dir) / "temp_downloads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"已创建临时下载目录: {temp_dir}")
        return True
    except Exception as e:
        logger.error(f"创建临时目录失败: {e}")
        return False

def install_requirements():
    """安装Python依赖"""
    if getattr(sys, 'frozen', False):
        logger.info("已打包为可执行文件，无需安装依赖")
        return True

    try:
        requirements_file = Path(parent_dir) / "requirements.txt"
        if not requirements_file.exists():
            logger.error(f"依赖文件不存在: {requirements_file}")
            return False

        logger.info("正在安装Python依赖...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        logger.info("依赖安装完成")
        return True
    except Exception as e:
        logger.error(f"安装依赖失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Zed Editor 自动更新程序安装脚本")
    parser.add_argument("--no-admin", action="store_true", help="不请求管理员权限")
    parser.add_argument("--no-autostart", action="store_true", help="不设置开机自启动")
    parser.add_argument("--zed-path", type=str, help="手动指定Zed可执行文件路径")
    args = parser.parse_args()

    print("=" * 60)
    print("     Zed Editor 自动更新程序安装向导")
    print("=" * 60)
    print("这个向导将帮助您安装和配置Zed编辑器自动更新程序。")
    print()

    # 1. 检查管理员权限
    if not args.no_admin and not is_admin():
        print("需要管理员权限来完成安装。正在请求提升权限...")
        request_admin()

    # 2. 查找Zed可执行文件
    zed_path = args.zed_path
    if not zed_path:
        print("正在查找Zed编辑器可执行文件...")
        zed_path = find_zed_executable()

    if not zed_path:
        print("\nZed编辑器未找到。请手动指定Zed.exe的路径:")
        user_input = input("> ").strip()
        if user_input and Path(user_input).exists():
            zed_path = user_input
        else:
            print("无效的路径，安装中止")
            return False

    print(f"找到Zed编辑器: {zed_path}")

    # 3. 询问是否开机自启动
    auto_start = not args.no_autostart
    if not args.no_autostart:
        print("\n是否设置开机自启动? (Y/n)")
        user_input = input("> ").strip().lower()
        auto_start = user_input != "n"

    print(f"{'启用' if auto_start else '禁用'}开机自启动")

    # 4. 创建配置文件
    print("\n正在创建配置文件...")
    config_path = create_config_file(zed_path, auto_start)

    # 5. 安装依赖
    print("\n正在安装依赖...")
    install_requirements()

    # 6. 创建临时目录
    print("\n正在创建临时目录...")
    create_temp_dirs()

    # 7. 创建快捷方式
    print("\n正在创建快捷方式...")
    create_shortcuts(auto_start)

    # 8. 设置注册表自启动
    print("\n正在设置注册表...")
    set_registry_autostart(auto_start)

    print("\n" + "=" * 60)
    print("     安装完成!")
    print("=" * 60)
    print(f"Zed编辑器路径: {zed_path}")
    print(f"配置文件: {config_path}")
    print(f"开机自启动: {'启用' if auto_start else '禁用'}")
    print()
    print("您可以通过以下方式启动Zed自动更新程序:")
    print("1. 双击桌面快捷方式")
    print("2. 通过开始菜单启动")
    print(f"3. 运行脚本: {parent_dir}/scripts/run.py")
    print()
    print("是否立即启动Zed自动更新程序? (Y/n)")
    user_input = input("> ").strip().lower()

    if user_input != "n":
        print("\n正在启动Zed自动更新程序...")
        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, "--gui"], cwd=parent_dir)
            else:
                run_script = Path(parent_dir) / "scripts" / "run.py"
                subprocess.Popen([sys.executable, str(run_script), "--gui"], cwd=parent_dir)
            print("启动成功!")
        except Exception as e:
            print(f"启动失败: {e}")

    return True

if __name__ == "__main__":
    main()
