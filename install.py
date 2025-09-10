#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zed Editor 自动更新程序 - 安装脚本
用于安装依赖、配置环境和创建快捷方式
"""

import os
import sys
import subprocess
import shutil
import winreg
from pathlib import Path
import json
import locale

# UTF-8兼容性设置
if sys.platform == 'win32':
    # 设置控制台代码页为UTF-8
    try:
        os.system('chcp 65001 > nul')
    except:
        pass

    # 设置环境变量确保UTF-8编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # 重新配置标准输出流
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

    # 设置本地化
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass

class ZedUpdaterInstaller:
    """Zed更新程序安装器"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.install_dir = self.script_dir
        self.python_exe = sys.executable
        self.main_script = self.install_dir / 'main.py'

    def check_python_version(self):
        """检查Python版本"""
        print("检查Python版本...")
        if sys.version_info < (3, 7):
            print("❌ 错误: 需要Python 3.7或更高版本")
            print(f"当前版本: Python {sys.version}")
            return False

        print(f"✅ Python版本检查通过: {sys.version}")
        return True

    def install_dependencies(self):
        """安装Python依赖"""
        print("\n安装Python依赖包...")

        requirements_file = self.install_dir / 'requirements.txt'
        if not requirements_file.exists():
            print("❌ 找不到requirements.txt文件")
            return False

        try:
            # 升级pip
            print("升级pip...")
            subprocess.run([self.python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'],
                         check=True, capture_output=True)

            # 安装依赖
            print("安装依赖包...")
            result = subprocess.run([
                self.python_exe, '-m', 'pip', 'install',
                '-r', str(requirements_file)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ 依赖包安装成功")
                return True
            else:
                print("❌ 依赖包安装失败:")
                print(result.stderr)
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ 安装依赖时出错: {e}")
            return False
        except Exception as e:
            print(f"❌ 安装过程中出现异常: {e}")
            return False

    def create_batch_files(self):
        """创建批处理文件"""
        print("\n创建启动脚本...")

        try:
            # 创建GUI启动脚本
            gui_batch = self.install_dir / 'ZedUpdater.bat'
            gui_content = f'''@echo off
chcp 65001 >nul
cd /d "{self.install_dir}"
"{self.python_exe}" main.py --gui
pause
'''
            with open(gui_batch, 'w', encoding='utf-8-sig') as f:
                f.write(gui_content)
            print(f"✅ GUI启动脚本已创建: {gui_batch}")

            # 创建命令行更新脚本
            update_batch = self.install_dir / 'ZedUpdate.bat'
            update_content = f'''@echo off
chcp 65001 >nul
cd /d "{self.install_dir}"
"{self.python_exe}" main.py --update
pause
'''
            with open(update_batch, 'w', encoding='utf-8-sig') as f:
                f.write(update_content)
            print(f"✅ 更新脚本已创建: {update_batch}")

            # 创建静默更新脚本（用于计划任务）
            silent_batch = self.install_dir / 'ZedUpdateSilent.bat'
            silent_content = f'''@echo off
chcp 65001 >nul
cd /d "{self.install_dir}"
"{self.python_exe}" main.py --update >nul 2>&1
'''
            with open(silent_batch, 'w', encoding='utf-8-sig') as f:
                f.write(silent_content)
            print(f"✅ 静默更新脚本已创建: {silent_batch}")

            return True

        except Exception as e:
            print(f"❌ 创建批处理文件失败: {e}")
            return False

    def create_shortcuts(self):
        """创建桌面快捷方式"""
        print("\n创建桌面快捷方式...")

        try:
            import win32com.client

            desktop = Path.home() / 'Desktop'
            shell = win32com.client.Dispatch("WScript.Shell")

            # 创建GUI快捷方式
            shortcut_path = desktop / 'Zed自动更新程序.lnk'
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(self.install_dir / 'ZedUpdater.bat')
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.Description = 'Zed Editor 自动更新程序'
            shortcut.save()

            print(f"✅ 桌面快捷方式已创建: {shortcut_path}")
            return True

        except ImportError:
            print("⚠️  无法创建快捷方式 (缺少win32com模块)")
            return False
        except Exception as e:
            print(f"❌ 创建快捷方式失败: {e}")
            return False

    def setup_startup(self):
        """设置开机自启动"""
        print("\n配置开机自启动...")

        try:
            # 询问用户是否需要开机自启动
            while True:
                choice = input("是否设置开机自启动? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是']:
                    enable_startup = True
                    break
                elif choice in ['n', 'no', '否']:
                    enable_startup = False
                    break
                else:
                    print("请输入 y 或 n")

            if not enable_startup:
                print("⏭️  跳过开机自启动设置")
                return True

            # 注册表路径
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "ZedUpdater"
            app_command = f'"{self.python_exe}" "{self.main_script}" --gui'

            # 写入注册表
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0,
                               winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_command)

            print("✅ 开机自启动已设置")
            return True

        except Exception as e:
            print(f"❌ 设置开机自启动失败: {e}")
            return False

    def create_default_config(self):
        """创建默认配置文件"""
        print("\n创建默认配置文件...")

        try:
            config_file = self.install_dir / 'config.json'

            # 询问Zed安装路径
            print("请设置Zed.exe的安装路径:")
            print("1. 自动检测")
            print("2. 手动输入")

            while True:
                choice = input("请选择 (1/2): ").strip()
                if choice == '1':
                    # 尝试自动检测Zed路径
                    zed_path = self.detect_zed_path()
                    if zed_path:
                        print(f"检测到Zed路径: {zed_path}")
                        confirm = input("使用此路径? (y/n): ").lower().strip()
                        if confirm in ['y', 'yes', '是']:
                            break

                    print("自动检测失败或用户拒绝，请手动输入")
                    zed_path = input("请输入Zed.exe的完整路径: ").strip()
                    break

                elif choice == '2':
                    zed_path = input("请输入Zed.exe的完整路径: ").strip()
                    break
                else:
                    print("请输入 1 或 2")

            # 验证路径
            if not Path(zed_path).exists():
                print(f"⚠️  警告: 路径不存在: {zed_path}")
                print("可以稍后在配置中修改")

            # 创建配置
            config = {
                'zed_install_path': zed_path,
                'auto_check_enabled': True,
                'check_interval_hours': 24,
                'check_on_startup': True,
                'auto_download': True,
                'auto_install': False,
                'auto_start_after_update': True,
                'backup_enabled': True,
                'backup_count': 3,
                'show_notifications': True,
                'minimize_to_tray': True,
                'github_repo': 'TC999/zed-loc',
                'github_api_url': 'https://api.github.com/repos/TC999/zed-loc/releases/latest',
                'download_timeout': 300,
                'retry_count': 3
            }

            with open(config_file, 'w', encoding='utf-8-sig') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            print(f"✅ 默认配置文件已创建: {config_file}")
            return True

        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
            return False

    def detect_zed_path(self):
        """自动检测Zed安装路径"""
        try:
            # 常见安装位置
            possible_paths = [
                Path.home() / 'AppData' / 'Local' / 'Zed' / 'Zed.exe',
                Path('C:') / 'Program Files' / 'Zed' / 'Zed.exe',
                Path('C:') / 'Program Files (x86)' / 'Zed' / 'Zed.exe',
                Path('D:') / 'Zed.exe',
                Path('C:') / 'Zed.exe'
            ]

            for path in possible_paths:
                if path.exists():
                    return str(path)

            # 在PATH环境变量中查找
            for path_dir in os.environ.get('PATH', '').split(os.pathsep):
                zed_exe = Path(path_dir) / 'zed.exe'
                if zed_exe.exists():
                    return str(zed_exe)

            return None

        except Exception:
            return None

    def test_installation(self):
        """测试安装"""
        print("\n测试安装...")

        try:
            # 测试主模块导入
            result = subprocess.run([
                self.python_exe, '-c',
                'import updater; print("✅ 模块导入成功")'
            ], cwd=self.install_dir, capture_output=True, text=True, timeout=10,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})

            if result.returncode == 0:
                print("✅ 安装测试通过")
                return True
            else:
                print("❌ 安装测试失败:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("❌ 安装测试超时")
            return False
        except Exception as e:
            print(f"❌ 测试安装时出错: {e}")
            return False

    def run(self):
        """运行安装程序"""
        print("=" * 50)
        print("Zed Editor 自动更新程序 - 安装向导")
        print("=" * 50)

        steps = [
            ("检查Python版本", self.check_python_version),
            ("安装Python依赖", self.install_dependencies),
            ("创建启动脚本", self.create_batch_files),
            ("创建桌面快捷方式", self.create_shortcuts),
            ("配置开机自启动", self.setup_startup),
            ("创建默认配置", self.create_default_config),
            ("测试安装", self.test_installation)
        ]

        failed_steps = []

        for step_name, step_func in steps:
            print(f"\n{'=' * 20} {step_name} {'=' * 20}")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except KeyboardInterrupt:
                print("\n\n安装被用户中断")
                return False
            except Exception as e:
                print(f"❌ {step_name} 执行失败: {e}")
                failed_steps.append(step_name)

        print("\n" + "=" * 50)
        print("安装完成!")
        print("=" * 50)

        if failed_steps:
            print(f"⚠️  以下步骤执行失败: {', '.join(failed_steps)}")
            print("程序仍可以使用，但某些功能可能受限")
        else:
            print("✅ 所有安装步骤都成功完成!")

        print(f"\n程序安装目录: {self.install_dir}")
        print(f"配置文件: {self.install_dir / 'config.json'}")
        print(f"日志文件: {self.install_dir / 'zed_updater.log'}")

        print("\n启动方式:")
        print(f"1. 双击桌面快捷方式 'Zed自动更新程序'")
        print(f"2. 运行 {self.install_dir / 'ZedUpdater.bat'}")
        print(f"3. 命令行: python {self.main_script} --gui")

        print("\n命令行更新:")
        print(f"运行 {self.install_dir / 'ZedUpdate.bat'} 或")
        print(f"命令行: python {self.main_script} --update")

        # 询问是否立即启动
        try:
            choice = input("\n是否现在启动程序? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                print("启动程序...")
                subprocess.Popen([self.python_exe, str(self.main_script), '--gui'],
                               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        except KeyboardInterrupt:
            pass

        input("\n按Enter键退出...")
        return len(failed_steps) == 0

def main():
    """主函数"""
    installer = ZedUpdaterInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
