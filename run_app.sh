#!/usr/bin/env bash
# JobHunter Germany - Unix/Linux/macOS Launcher

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "         JobHunter Germany Launcher 🇩🇪"
echo "======================================================="

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Check dependencies
if ! python3 -c "import jobspy, pywebview, pandas, openpyxl, requests, bs4" >/dev/null 2>&1; then
    echo "[*] Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

echo "[*] Launching JobHunter Germany..."
python3 main.py "$@"
