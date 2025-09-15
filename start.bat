@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Zed Update Manager - Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
)

echo Select implementation to run:
echo.
echo 1. Legacy Implementation (PyQt5 Standalone)
echo    - Original single application
echo    - Minimal dependencies
echo    - Compatible with older systems
echo.
echo 2. Modern Implementation (Go Backend + PyQt5 Frontend)
echo    - Microservices architecture
echo    - Enhanced performance
echo    - Real-time API communication
echo.
echo 3. Exit
echo.

:SELECT_OPTION
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto LEGACY
if "%choice%"=="2" goto MODERN
if "%choice%"=="3" goto EXIT
echo Invalid choice. Please enter 1, 2, or 3.
goto SELECT_OPTION

:LEGACY
echo.
echo Starting Legacy Implementation...
echo ========================================
call "%~dp0scripts\start-legacy.bat"
goto END

:MODERN
echo.
echo Starting Modern Implementation...
echo ========================================
REM Check if Go is installed for modern implementation
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Go is not installed or not in PATH
    echo Modern implementation requires Go 1.21+
    echo Please install Go from https://golang.org/dl/
    echo.
    echo Falling back to Legacy implementation...
    call "%~dp0scripts\start-legacy.bat"
    goto END
)
call "%~dp0scripts\start-modern.bat"
goto END

:EXIT
echo Goodbye!
goto END

:END
echo.
echo Press any key to exit...
pause >nul
