@echo off
REM Install Agent7 Scheduler as Windows Service

echo ========================================
echo  Agent7 Scheduler Service Installation
echo ========================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script requires Administrator privileges
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get the directory where this script is located
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Checking virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo.
echo [2/3] Installing dependencies...
pip install -q pywin32 schedule python-dateutil
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Installing Windows service...
python scheduler_service.py install
if errorlevel 1 (
    echo ERROR: Service installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Service installed successfully!
echo ========================================
echo.
echo Service name: Agent7Scheduler
echo.
echo To start the service:
echo   net start Agent7Scheduler
echo.
echo To configure the service to start automatically:
echo   sc config Agent7Scheduler start= auto
echo.
echo Would you like to start the service now? (Y/N)
set /p START_NOW=

if /i "%START_NOW%"=="Y" (
    echo.
    echo Starting service...
    net start Agent7Scheduler
    if errorlevel 1 (
        echo Failed to start service
        echo You can start it manually with: net start Agent7Scheduler
    ) else (
        echo Service started successfully!
    )
)

echo.
pause


