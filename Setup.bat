@echo off
setlocal
title JobHunter Germany Setup 🇩🇪

echo =======================================================
echo          JobHunter Germany Installer 🇩🇪
echo =======================================================
echo.
echo Installing JobHunter Germany on your laptop...
echo No Python or dependencies required.
echo.

if exist "%~dp0installer\install.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1"
) else if exist "%~dp0install.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
) else (
    echo [ERROR] install.ps1 not found!
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation encountered an issue.
    pause
    exit /b 1
)
