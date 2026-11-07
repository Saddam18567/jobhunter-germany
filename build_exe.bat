@echo off
chcp 65001 >nul 2>&1
setlocal
title Build JobHunter Germany Executable [DE]

echo =======================================================
echo     Packaging JobHunter Germany into Windows .exe [DE]
echo =======================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    pause
    exit /b 1
)

REM Use existing .venv if available
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo [*] Installing dependencies and PyInstaller...
pip install -r requirements.txt pyinstaller

echo [*] Running build script...
python build_exe.py

echo.
echo =======================================================
echo If the build succeeded, your app is in:
echo   dist\JobHunterGermany\JobHunterGermany.exe
echo =======================================================
pause
