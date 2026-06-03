@echo off
REM AgentWatch — Windows system tray app launcher
REM Double-click to start the tray app.
REM If the app hasn't been built yet, prompts you to build.

set SCRIPT_DIR=%~dp0
set APP_PATH=%SCRIPT_DIR%build\windows\AgentWatchTray\AgentWatchTray.exe

if exist "%APP_PATH%" (
    echo Launching AgentWatch Windows tray app...
    start "" "%APP_PATH%"
    echo.
    echo Look for the AgentWatch icon in your system tray ^(bottom-right^).
    echo Right-click the icon to open the menu.
    echo.
    pause
) else (
    echo ============================================
    echo   AgentWatchTray.exe not found
    echo ============================================
    echo.
    echo Please build the app first.
    echo Open PowerShell and run:
    echo.
    echo   powershell -ExecutionPolicy Bypass -File windows\build_app.ps1
    echo.
    pause
)
