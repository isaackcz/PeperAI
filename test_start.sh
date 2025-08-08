#!/bin/sh
# Test Railway startup script
PORT=${PORT:-8000}
exec uvicorn test_railway:app --host 0.0.0.0 --port $PORT