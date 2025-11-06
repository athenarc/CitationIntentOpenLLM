#!/bin/bash

# Citation Intent API - Production Deployment Script
# This script starts the FastAPI application using Gunicorn with optimized settings

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Navigate to the API root directory (parent of scripts/)
cd "$SCRIPT_DIR/.."

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading configuration from .env file..."
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "Warning: .env file not found, using default values"
fi

# Configuration
WORKERS=${WORKERS:-4}
WORKER_CLASS="uvicorn.workers.UvicornWorker"
HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-8000}
BIND_ADDRESS="$HOST:$PORT"
APP_MODULE="src.main:app"

# Log files
LOG_DIR="./logs"
ACCESS_LOG="$LOG_DIR/access.log"
ERROR_LOG="$LOG_DIR/error.log"
LOG_LEVEL=${LOG_LEVEL:-info}

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "Citation Intent Classification API"
echo "=========================================="
echo "Workers: $WORKERS"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Log Level: $LOG_LEVEL"
echo "=========================================="

# Pre-flight checks
echo "Running pre-flight checks..."

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✗ Error: Port $PORT is already in use"
    echo "  Current process using port $PORT:"
    lsof -Pi :$PORT -sTCP:LISTEN
    echo ""
    echo "  To kill the existing process, run:"
    echo "  kill \$(lsof -t -i:$PORT)"
    exit 1
fi

# Check if Python can import the app module
echo "Validating app module..."
if ! python -c "from src.main import app; print('✓ Module import successful')" 2>"$LOG_DIR/import_error.log"; then
    echo "✗ Error: Failed to import app module"
    echo "  Details in: $LOG_DIR/import_error.log"
    echo ""
    cat "$LOG_DIR/import_error.log"
    exit 1
fi

# Start the application
echo "Starting Gunicorn..."
gunicorn \
  --workers "$WORKERS" \
  --worker-class "$WORKER_CLASS" \
  --bind "$BIND_ADDRESS" \
  --daemon \
  --access-logfile "$ACCESS_LOG" \
  --error-logfile "$ERROR_LOG" \
  --log-level "$LOG_LEVEL" \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 300 \
  --keep-alive 2 \
  --pid "$LOG_DIR/gunicorn.pid" \
  "$APP_MODULE"

if [ $? -ne 0 ]; then
    echo "✗ Failed to start Citation Intent API"
    echo "  Check error log for details: $ERROR_LOG"
    if [ -f "$ERROR_LOG" ]; then
        echo ""
        echo "Last 20 lines of error log:"
        tail -20 "$ERROR_LOG"
    fi
    exit 1
fi

# Wait a moment and verify the process is running
sleep 2

if [ -f "$LOG_DIR/gunicorn.pid" ]; then
    PID=$(cat "$LOG_DIR/gunicorn.pid")
    if ps -p $PID > /dev/null 2>&1; then
        # Verify the API is responding
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health | grep -q "200"; then
            echo "✓ Citation Intent API started successfully!"
            echo ""
            echo "PID: $PID (saved in $LOG_DIR/gunicorn.pid)"
            echo "Access log: $ACCESS_LOG"
            echo "Error log: $ERROR_LOG"
            echo ""
            echo "API available at: http://$HOST:$PORT"
            echo "API docs available at: http://$HOST:$PORT/docs"
            echo ""
            echo "To stop the server, run: bash scripts/stop.sh"
        else
            echo "⚠ Warning: Server started but health check failed"
            echo "  The API may still be initializing or there may be a configuration issue"
            echo "  Check logs: tail -f $ERROR_LOG"
        fi
    else
        echo "✗ Process started but died immediately"
        echo "  Check error log: $ERROR_LOG"
        if [ -f "$ERROR_LOG" ]; then
            echo ""
            echo "Last 20 lines of error log:"
            tail -20 "$ERROR_LOG"
        fi
        exit 1
    fi
else
    echo "✗ PID file not created - startup failed"
    echo "  Check error log: $ERROR_LOG"
    if [ -f "$ERROR_LOG" ]; then
        echo ""
        echo "Last 20 lines of error log:"
        tail -20 "$ERROR_LOG"
    fi
    exit 1
fi
