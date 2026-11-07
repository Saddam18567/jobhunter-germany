@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title JobHunter Germany [DE]

echo =======================================================
echo          JobHunter Germany Launcher [DE]
echo =======================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check or create virtual environment
if not exist ".venv" (
    echo [*] Creating local Python virtual environment (.venv)...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import jobspy, pywebview, pandas, openpyxl, requests, bs4" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing required libraries (one-time setup)...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

echo [*] Starting JobHunter Germany desktop app...
start "" pythonw main.py

if %errorlevel% neq 0 (
    REM Fallback to standard python if pythonw has any restriction
    python main.py
)
