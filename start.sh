#!/bin/sh
# Railway startup script
# Debug: Print environment variables
echo "DEBUG: PORT environment variable is: $PORT"
echo "DEBUG: All environment variables:"
env | grep -E "(PORT|RAILWAY)" || echo "No PORT/RAILWAY vars found"

# Use Railway's PORT if available, otherwise default to 8000
PORT=${PORT:-8000}
echo "DEBUG: Using PORT: $PORT"

exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1