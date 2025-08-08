#!/bin/sh
# Railway startup script
# Use Railway's PORT if available, otherwise default to 8000
PORT=${PORT:-8000}
exec uvicorn main:app --host 0.0.0.0 --port $PORT