@echo off
REM Agent7 Launcher Script
REM Starts the Agent7 web UI and scheduler service

echo ========================================
echo        Agent7 Launcher
echo ========================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo.
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo.
    echo [2/5] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo.
echo [4/5] Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully

REM Check if scheduler service is running
echo.
echo [5/5] Checking scheduler service...
sc query Agent7Scheduler >nul 2>&1
if errorlevel 1 (
    echo Scheduler service not installed
    echo You can install it later with: install_service.bat
) else (
    sc query Agent7Scheduler | find "RUNNING" >nul
    if errorlevel 1 (
        echo Scheduler service is installed but not running
        echo Starting service...
        net start Agent7Scheduler >nul 2>&1
        if errorlevel 1 (
            echo Could not start service automatically
            echo You can start it manually with: net start Agent7Scheduler
        ) else (
            echo Scheduler service started
        )
    ) else (
        echo Scheduler service is running
    )
)

echo.
echo ========================================
echo Starting Agent7 Web Server...
echo ========================================
echo.
echo Web UI will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the web server
python web_server.py

REM If we get here, the server stopped
echo.
echo Agent7 web server stopped
pause


