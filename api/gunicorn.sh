#!/bin/bash

# Citation Intent API - Production Deployment Script
# This script starts the FastAPI application using Gunicorn with optimized settings

set -e

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
APP_MODULE="main:app"

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

# Start the application
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

if [ $? -eq 0 ]; then
    echo "✓ Citation Intent API started successfully!"
    echo ""
    echo "PID file: $LOG_DIR/gunicorn.pid"
    echo "Access log: $ACCESS_LOG"
    echo "Error log: $ERROR_LOG"
    echo ""
    echo "API available at: http://$HOST:$PORT"
    echo "API docs available at: http://$HOST:$PORT/docs"
    echo ""
    echo "To stop the server, run: kill \$(cat $LOG_DIR/gunicorn.pid)"
else
    echo "✗ Failed to start Citation Intent API"
    exit 1
fi
