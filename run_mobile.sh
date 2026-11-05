#!/usr/bin/env bash
# JobHunter Germany - Mobile Testing Launcher (via SSH)
# Starts local backend server and exposes temporary secure HTTPS tunnel for mobile browser testing.

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT=5892

echo "======================================================="
echo "   JobHunter Germany - Mobile Testing Mode 📱🇩🇪     "
echo "======================================================="

# Ensure virtual environment is activated
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start python backend server in background
python3 main.py --host 0.0.0.0 --port $PORT &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "[*] Shutting down JobHunter mobile server..."
    kill $SERVER_PID 2>/dev/null || true
    kill $TUNNEL_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

sleep 2

echo "[*] Local server is running on port $PORT."
echo "[*] Opening secure mobile tunnel (localhost.run)..."
echo "-------------------------------------------------------"
echo "Tap the HTTPS link below on your phone to open the UI:"
echo "-------------------------------------------------------"

# Launch tunnel and stream output to display the public HTTPS link
ssh -o StrictHostKeyChecking=no -R 80:localhost:$PORT nokey@localhost.run &
TUNNEL_PID=$!

wait $SERVER_PID
