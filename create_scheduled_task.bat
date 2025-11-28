@echo off
REM Create Windows Scheduled Task instead of Windows Service
REM This is more reliable and easier to configure

echo ========================================
echo  Agent7 Scheduler - Task Scheduler
echo ========================================
echo.
echo This will create a Windows Scheduled Task that:
echo - Runs at system startup
echo - Runs in the background
echo - Restarts if it fails
echo - Doesn't require complicated service setup
echo.

REM Check for administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: This script requires Administrator privileges
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/3] Removing existing task (if any)...
schtasks /Delete /TN "Agent7Scheduler" /F >nul 2>&1
echo Done

echo.
echo [2/3] Creating scheduled task...

REM Get full path to Python in venv
set PYTHON_PATH=%CD%\venv\Scripts\python.exe
set SCRIPT_PATH=%CD%\scheduler_service.py
set WORKING_DIR=%CD%

echo Python: %PYTHON_PATH%
echo Script: %SCRIPT_PATH%
echo Working Directory: %WORKING_DIR%

REM Create the scheduled task
schtasks /Create /TN "Agent7Scheduler" /TR "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" debug" /SC ONSTART /RU SYSTEM /RL HIGHEST /F

if errorlevel 1 (
    echo ERROR: Failed to create scheduled task
    pause
    exit /b 1
)

echo.
echo [3/3] Starting the task...
schtasks /Run /TN "Agent7Scheduler"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Scheduler Task Created Successfully!
echo ========================================
echo.
echo The scheduler will:
echo - Start automatically when Windows boots
echo - Run in the background
echo - Check for scheduled tasks every 30 seconds
echo.
echo To check status:
echo   schtasks /Query /TN "Agent7Scheduler"
echo.
echo To stop:
echo   schtasks /End /TN "Agent7Scheduler"
echo.
echo To remove:
echo   schtasks /Delete /TN "Agent7Scheduler" /F
echo.
echo Log file location:
echo   %WORKING_DIR%\scheduler_debug.log
echo.

timeout /t 2 /nobreak >nul

echo Checking if task is running...
schtasks /Query /TN "Agent7Scheduler" /FO LIST | findstr /C:"Status"

echo.
echo Checking log file...
if exist "scheduler_debug.log" (
    echo.
    echo === Recent Log Entries ===
    powershell -Command "Get-Content scheduler_debug.log -Tail 10"
    echo === End of Log ===
) else (
    echo Waiting for log file to be created...
    timeout /t 5 /nobreak >nul
    if exist "scheduler_debug.log" (
        echo.
        echo === Log File ===
        type scheduler_debug.log
    ) else (
        echo Log file not created yet. Task may still be starting.
    )
)

echo.
pause

