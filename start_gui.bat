@echo off
REM Zed Editor GUI 启动器 - 无控制台窗口版本
REM 使用 pythonw 命令启动GUI界面，不显示控制台窗口

cd /d "%~dp0"

REM 检查是否存在 .pyw 文件，优先使用
if exist "gui_launcher.pyw" (
    pythonw gui_launcher.pyw
) else if exist "main.pyw" (
    pythonw main.pyw
) else (
    REM 如果没有 .pyw 文件，使用 pythonw 运行 .py 文件
    pythonw main.py --gui
)

REM 如果上述命令失败，尝试使用普通的 python 命令
if errorlevel 1 (
    if exist "gui_launcher.py" (
        python gui_launcher.py
    ) else (
        python main.py --gui
    )
)
