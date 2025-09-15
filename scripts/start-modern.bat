@echo off
echo Starting Zed Update Manager v2.0 (PyQt5 + Go Backend)...
echo.

REM Check if Go is installed
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Go is not installed or not in PATH
    echo Please install Go from https://golang.org/dl/
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if PyQt5 is installed
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 not found, installing dependencies...
    cd /d "%~dp0..\modern\frontend"
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install PyQt5 dependencies
        echo Please run: pip install PyQt5==5.15.10
        pause
        exit /b 1
    )
)

REM Navigate to backend directory and install dependencies
echo Installing Go dependencies...
cd /d "%~dp0..\modern\backend"
go mod tidy
if %errorlevel% neq 0 (
    echo Error: Failed to install Go dependencies
    pause
    exit /b 1
)

echo.
echo Starting Go backend server...
cd /d "%~dp0..\modern\backend"
start "Zed Update Backend" cmd /k "go run main.go"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Check if backend is responding
echo Checking backend connection...
curl -f http://localhost:8080/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Backend may not be ready yet. GUI will attempt to connect...
)

echo Starting PyQt5 GUI frontend...
cd /d "%~dp0..\modern\frontend"
python main.py

echo.
echo Both applications have been started:
echo - Backend API: http://localhost:8080
echo - Frontend GUI: PyQt5 desktop application
echo.
echo To stop the applications:
echo 1. Close the GUI window
echo 2. Close the backend command window
echo.
pause
