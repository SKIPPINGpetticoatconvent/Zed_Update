@echo off
chcp 65001 >nul
cd /d "D:\Vs\Zed_Update"
"C:\Users\ANGOM\scoop\apps\python\current\python.exe" main.py --update >nul 2>&1
