@echo off
chcp 65001 >nul
cd /d "D:\Vs\Zed_Update"
"D:\Vs\Zed_Update\.venv\Scripts\python.exe" main.py --gui
pause
