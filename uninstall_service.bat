@echo off
REM Uninstall Agent7 Scheduler Windows Service

echo ========================================
echo  Agent7 Scheduler Service Removal
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

REM Check if service exists
sc query Agent7Scheduler >nul 2>&1
if errorlevel 1 (
    echo Service is not installed
    pause
    exit /b 0
)

echo Service found. Preparing to remove...
echo.

REM Stop the service if running
echo [1/2] Stopping service...
sc query Agent7Scheduler | find "RUNNING" >nul
if not errorlevel 1 (
    net stop Agent7Scheduler
    if errorlevel 1 (
        echo Warning: Could not stop service
        echo Continuing with removal...
    ) else (
        echo Service stopped
    )
) else (
    echo Service is not running
)

REM Wait a moment
timeout /t 2 /nobreak >nul

echo.
echo [2/2] Removing service...
if exist "venv" (
    call venv\Scripts\activate.bat
    python scheduler_service.py remove
) else (
    sc delete Agent7Scheduler
)

if errorlevel 1 (
    echo ERROR: Service removal failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Service removed successfully!
echo ========================================
echo.
pause


