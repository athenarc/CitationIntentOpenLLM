#!/bin/bash

# Citation Intent API - Stop Script
# This script stops the running Gunicorn process

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Navigate to the API root directory (parent of scripts/)
cd "$SCRIPT_DIR/.."

LOG_DIR="./logs"
PID_FILE="$LOG_DIR/gunicorn.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "✗ PID file not found at $PID_FILE"
    echo "The server may not be running, or it wasn't started with gunicorn.sh"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping Citation Intent API (PID: $PID)..."
    kill "$PID"
    
    # Wait for process to terminate
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "✓ Server stopped successfully"
            rm -f "$PID_FILE"
            exit 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "Process still running, forcing shutdown..."
    kill -9 "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "✓ Server forcefully stopped"
else
    echo "✗ Process with PID $PID is not running"
    rm -f "$PID_FILE"
    exit 1
fi
