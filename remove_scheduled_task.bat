@echo off
REM Remove Agent7 Scheduled Task

echo ========================================
echo  Remove Agent7 Scheduler Task
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

echo Stopping task...
schtasks /End /TN "Agent7Scheduler" >nul 2>&1

echo Removing task...
schtasks /Delete /TN "Agent7Scheduler" /F

if errorlevel 1 (
    echo Task was not found (may already be removed)
) else (
    echo ✅ Task removed successfully!
)

echo.
pause

