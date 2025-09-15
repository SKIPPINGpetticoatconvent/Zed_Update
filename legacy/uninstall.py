#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序 - 卸载脚本
用于完全卸载程序和清理相关文件
"""

import os
import sys
import shutil
import winreg
from pathlib import Path
import json

class ZedUpdaterUninstaller:
    """Zed更新程序卸载器"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.install_dir = self.script_dir
        self.config_file = self.install_dir / 'config.json'

    def remove_startup_entry(self):
        """移除开机自启动项"""
        print("移除开机自启动项...")

        try:
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "ZedUpdater"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0,
                               winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, app_name)
                    print("✅ 开机自启动项已移除")
                except FileNotFoundError:
                    print("ℹ️  开机自启动项不存在")

            return True

        except Exception as e:
            print(f"❌ 移除开机自启动项失败: {e}")
            return False

    def remove_shortcuts(self):
        """移除桌面快捷方式"""
        print("移除桌面快捷方式...")

        try:
            desktop = Path.home() / 'Desktop'
            shortcut_names = [
                'Zed自动更新程序.lnk',
                'ZedUpdater.lnk',
                'Zed Editor Updater.lnk'
            ]

            removed_count = 0
            for shortcut_name in shortcut_names:
                shortcut_path = desktop / shortcut_name
                if shortcut_path.exists():
                    shortcut_path.unlink()
                    print(f"✅ 已删除快捷方式: {shortcut_name}")
                    removed_count += 1

            if removed_count == 0:
                print("ℹ️  没有找到快捷方式")

            return True

        except Exception as e:
            print(f"❌ 移除快捷方式失败: {e}")
            return False

    def stop_running_processes(self):
        """停止正在运行的程序进程"""
        print("停止正在运行的程序...")

        try:
            import psutil

            current_pid = os.getpid()
            stopped_count = 0

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 跳过当前卸载进程
                    if proc.info['pid'] == current_pid:
                        continue

                    cmdline = proc.info.get('cmdline', [])
                    if not cmdline:
                        continue

                    # 检查是否是我们的程序
                    cmdline_str = ' '.join(cmdline).lower()
                    if ('python' in cmdline_str and
                        ('main.py' in cmdline_str or 'zedupdater' in cmdline_str)):

                        print(f"停止进程: PID {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=5)
                        stopped_count += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass

            if stopped_count > 0:
                print(f"✅ 已停止 {stopped_count} 个进程")
            else:
                print("ℹ️  没有找到运行中的程序进程")

            return True

        except ImportError:
            print("⚠️  无法检查运行进程 (缺少psutil模块)")
            return True
        except Exception as e:
            print(f"❌ 停止进程失败: {e}")
            return False

    def backup_user_data(self):
        """备份用户数据"""
        print("备份用户数据...")

        try:
            # 询问是否备份配置和日志
            while True:
                choice = input("是否备份配置文件和日志? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是']:
                    create_backup = True
                    break
                elif choice in ['n', 'no', '否']:
                    create_backup = False
                    break
                else:
                    print("请输入 y 或 n")

            if not create_backup:
                print("⏭️  跳过数据备份")
                return True

            # 创建备份目录
            backup_dir = Path.home() / 'Desktop' / 'ZedUpdater_Backup'
            backup_dir.mkdir(exist_ok=True)

            # 备份配置文件
            if self.config_file.exists():
                shutil.copy2(self.config_file, backup_dir / 'config.json')
                print(f"✅ 配置文件已备份到: {backup_dir}")

            # 备份日志文件
            log_file = self.install_dir / 'zed_updater.log'
            if log_file.exists():
                shutil.copy2(log_file, backup_dir / 'zed_updater.log')
                print(f"✅ 日志文件已备份到: {backup_dir}")

            # 备份Zed备份文件夹（如果存在）
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    zed_path = config.get('zed_install_path', '')
                    if zed_path:
                        zed_backup_dir = Path(zed_path).parent / 'zed_backups'
                        if zed_backup_dir.exists():
                            backup_zed_dir = backup_dir / 'zed_backups'
                            shutil.copytree(zed_backup_dir, backup_zed_dir, dirs_exist_ok=True)
                            print(f"✅ Zed备份文件已备份到: {backup_zed_dir}")

            print(f"📁 所有备份文件位于: {backup_dir}")
            return True

        except Exception as e:
            print(f"❌ 备份用户数据失败: {e}")
            return False

    def clean_zed_backups(self):
        """清理Zed备份文件"""
        print("清理Zed备份文件...")

        try:
            if not self.config_file.exists():
                print("ℹ️  配置文件不存在，跳过Zed备份清理")
                return True

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            zed_path = config.get('zed_install_path', '')
            if not zed_path:
                print("ℹ️  未配置Zed路径，跳过备份清理")
                return True

            backup_dir = Path(zed_path).parent / 'zed_backups'
            if backup_dir.exists():
                # 询问是否删除Zed备份
                while True:
                    print(f"找到Zed备份目录: {backup_dir}")
                    choice = input("是否删除Zed备份文件? (y/n): ").lower().strip()
                    if choice in ['y', 'yes', '是']:
                        shutil.rmtree(backup_dir)
                        print("✅ Zed备份文件已删除")
                        break
                    elif choice in ['n', 'no', '否']:
                        print("⏭️  保留Zed备份文件")
                        break
                    else:
                        print("请输入 y 或 n")
            else:
                print("ℹ️  没有找到Zed备份文件")

            return True

        except Exception as e:
            print(f"❌ 清理Zed备份失败: {e}")
            return False

    def remove_program_files(self):
        """移除程序文件"""
        print("移除程序文件...")

        try:
            # 要删除的文件和目录列表
            items_to_remove = [
                'main.py',
                'updater',
                'requirements.txt',
                'install.py',
                'config.json',
                'zed_updater.log',
                'ZedUpdater.bat',
                'ZedUpdate.bat',
                'ZedUpdateSilent.bat',
                'temp_downloads',
                '__pycache__'
            ]

            removed_count = 0
            for item_name in items_to_remove:
                item_path = self.install_dir / item_name
                if item_path.exists():
                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                        print(f"✅ 已删除目录: {item_name}")
                    else:
                        item_path.unlink()
                        print(f"✅ 已删除文件: {item_name}")
                    removed_count += 1

            print(f"✅ 共删除 {removed_count} 个项目")

            # 检查是否还有其他文件
            remaining_files = list(self.install_dir.glob('*'))
            if remaining_files:
                print(f"\n剩余文件:")
                for file in remaining_files:
                    if file.name not in ['uninstall.py']:  # 排除卸载脚本本身
                        print(f"  - {file.name}")

                while True:
                    choice = input("\n是否删除所有剩余文件? (y/n): ").lower().strip()
                    if choice in ['y', 'yes', '是']:
                        for file in remaining_files:
                            if file.name != 'uninstall.py':
                                try:
                                    if file.is_dir():
                                        shutil.rmtree(file)
                                    else:
                                        file.unlink()
                                    print(f"✅ 已删除: {file.name}")
                                except Exception as e:
                                    print(f"❌ 删除 {file.name} 失败: {e}")
                        break
                    elif choice in ['n', 'no', '否']:
                        print("⏭️  保留剩余文件")
                        break
                    else:
                        print("请输入 y 或 n")

            return True

        except Exception as e:
            print(f"❌ 移除程序文件失败: {e}")
            return False

    def clean_temp_files(self):
        """清理临时文件"""
        print("清理临时文件...")

        try:
            # 清理系统临时目录中的相关文件
            import tempfile
            temp_dir = Path(tempfile.gettempdir())

            cleaned_count = 0
            for pattern in ['zed_updater_*', 'ZedUpdater_*']:
                for temp_file in temp_dir.glob(pattern):
                    try:
                        if temp_file.is_dir():
                            shutil.rmtree(temp_file)
                        else:
                            temp_file.unlink()
                        cleaned_count += 1
                    except Exception:
                        pass

            if cleaned_count > 0:
                print(f"✅ 清理了 {cleaned_count} 个临时文件")
            else:
                print("ℹ️  没有找到临时文件")

            return True

        except Exception as e:
            print(f"❌ 清理临时文件失败: {e}")
            return False

    def run(self):
        """运行卸载程序"""
        print("=" * 50)
        print("Zed Editor 自动更新程序 - 卸载向导")
        print("=" * 50)

        # 确认卸载
        print("⚠️  警告: 这将完全卸载Zed自动更新程序及其所有组件")
        print("包括配置文件、日志文件和备份文件")

        while True:
            choice = input("\n确定要继续卸载吗? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                break
            elif choice in ['n', 'no', '否']:
                print("卸载已取消")
                return True
            else:
                print("请输入 y 或 n")

        steps = [
            ("停止正在运行的程序", self.stop_running_processes),
            ("备份用户数据", self.backup_user_data),
            ("移除开机自启动项", self.remove_startup_entry),
            ("移除桌面快捷方式", self.remove_shortcuts),
            ("清理Zed备份文件", self.clean_zed_backups),
            ("清理临时文件", self.clean_temp_files),
            ("移除程序文件", self.remove_program_files)
        ]

        failed_steps = []

        for step_name, step_func in steps:
            print(f"\n{'=' * 20} {step_name} {'=' * 20}")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except KeyboardInterrupt:
                print("\n\n卸载被用户中断")
                return False
            except Exception as e:
                print(f"❌ {step_name} 执行失败: {e}")
                failed_steps.append(step_name)

        print("\n" + "=" * 50)
        print("卸载完成!")
        print("=" * 50)

        if failed_steps:
            print(f"⚠️  以下步骤执行失败: {', '.join(failed_steps)}")
            print("可能需要手动清理这些项目")
        else:
            print("✅ 卸载成功完成!")

        print("\n卸载说明:")
        print("- 程序文件已删除")
        print("- 开机自启动项已移除")
        print("- 桌面快捷方式已删除")
        print("- 如果创建了备份，文件位于桌面的 'ZedUpdater_Backup' 文件夹")

        # 询问是否删除安装目录
        if self.install_dir.exists() and any(self.install_dir.iterdir()):
            try:
                choice = input(f"\n是否删除安装目录 {self.install_dir}? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是']:
                    # 移动卸载脚本到临时位置
                    import tempfile
                    temp_uninstall = Path(tempfile.gettempdir()) / 'zed_uninstall_final.py'
                    shutil.copy2(__file__, temp_uninstall)

                    print("正在删除安装目录...")
                    print(f"注意: 卸载脚本已复制到 {temp_uninstall}")

                    input("按Enter键完成最终清理...")

                    # 创建最终清理脚本
                    final_script = f'''
import os
import shutil
import time
from pathlib import Path

# 等待主程序退出
time.sleep(2)

try:
    install_dir = Path(r"{self.install_dir}")
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print(f"✅ 已删除安装目录: {{install_dir}}")
    else:
        print("ℹ️  安装目录已不存在")

    # 删除自己
    os.unlink(__file__)
    print("✅ 卸载完全完成!")

except Exception as e:
    print(f"❌ 最终清理失败: {{e}}")
    print("请手动删除安装目录")

input("按Enter键退出...")
'''

                    with open(temp_uninstall, 'w', encoding='utf-8') as f:
                        f.write(final_script)

                    # 启动最终清理脚本
                    import subprocess
                    subprocess.Popen([sys.executable, str(temp_uninstall)])
                    return True

            except KeyboardInterrupt:
                pass

        print("\n感谢使用 Zed Editor 自动更新程序!")
        input("按Enter键退出...")
        return len(failed_steps) == 0

def main():
    """主函数"""
    uninstaller = ZedUpdaterUninstaller()
    success = uninstaller.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
