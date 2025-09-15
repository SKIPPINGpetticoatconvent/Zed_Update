@echo off
echo Starting Zed Update Manager (Legacy Version)...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if PyQt5 is installed for legacy version
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 not found, installing dependencies...
    cd /d "%~dp0..\legacy"
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install PyQt5 dependencies
        echo Please run: pip install PyQt5
        pause
        exit /b 1
    )
)

echo Installing Python dependencies...
cd /d "%~dp0..\legacy"
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Some Python dependencies may not have installed correctly
)

echo.
echo Starting Legacy Zed Update Manager...

REM Check for command line arguments
if "%1"=="--gui" (
    python main.py --gui
) else if "%1"=="--update" (
    python main.py --update
) else if "%1"=="--help" (
    python main.py --help
) else (
    echo Select mode:
    echo 1. GUI Mode
    echo 2. Console Update
    echo 3. Help
    echo.
    set /p choice="Enter your choice (1-3): "

    if "%choice%"=="1" (
        python main.py --gui
    ) else if "%choice%"=="2" (
        python main.py --update
    ) else if "%choice%"=="3" (
        python main.py --help
    ) else (
        echo Invalid choice. Starting GUI mode...
        python main.py --gui
    )
)

echo.
echo Legacy application finished.
pause
