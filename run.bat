@echo off
:: 设置UTF-8编码支持
chcp 65001 >nul 2>&1
title Zed Editor 自动更新程序

:: 设置环境变量确保UTF-8编码
set PYTHONIOENCODING=utf-8

:: 设置工作目录到批处理文件所在目录
cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误: 未找到Python环境
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 显示菜单
echo.
echo ================================
echo   Zed Editor 自动更新程序
echo ================================
echo.
echo 请选择运行模式:
echo.
echo [1] 启动图形界面 (无控制台窗口)
echo [2] 仅检查并更新
echo [3] 安装程序和依赖
echo [4] 卸载程序
echo [5] 查看帮助
echo [0] 退出
echo.

:menu
set /p choice="请输入选项 (0-5): "

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto update
if "%choice%"=="3" goto install
if "%choice%"=="4" goto uninstall
if "%choice%"=="5" goto help
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择
goto menu

:gui
echo.
echo 正在启动图形界面...
set PYTHONIOENCODING=utf-8
if exist "gui_launcher.pyw" (
    pythonw gui_launcher.pyw
) else if exist "main.pyw" (
    pythonw main.pyw
) else (
    pythonw main.py --gui
)
goto end

:update
echo.
echo 正在检查并更新Zed...
set PYTHONIOENCODING=utf-8
python main.py --update
goto end

:install
echo.
echo 正在运行安装程序...
set PYTHONIOENCODING=utf-8
python install.py
goto end

:uninstall
echo.
echo 正在运行卸载程序...
set PYTHONIOENCODING=utf-8
python uninstall.py
goto end

:help
echo.
echo 使用说明:
echo.
echo 1. 图形界面模式 - 提供完整的配置和管理界面 (无控制台窗口)
echo 2. 命令行更新 - 仅执行检查和更新操作
echo 3. 安装程序 - 首次使用时运行，安装依赖和配置
echo 4. 卸载程序 - 完全移除程序和配置文件
echo 5. 查看帮助 - 显示此帮助信息
echo.
echo 配置文件: config.json
echo 日志文件: zed_updater.log
echo 项目地址: https://github.com/TC999/zed-loc
echo.
pause
goto menu

:exit
echo 再见！
exit /b 0

:end
echo.
pause
