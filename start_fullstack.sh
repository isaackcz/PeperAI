#!/bin/bash

# Railway Fullstack Startup Script
# This script starts both the frontend (nginx) and backend (FastAPI) services

set -e

# Get the port from environment variable, default to 8080
PORT=${PORT:-8080}
BACKEND_PORT=8081

echo "DEBUG: PORT environment variable is: $PORT"
echo "DEBUG: Backend will run on port: $BACKEND_PORT"
echo "DEBUG: Nginx will serve frontend on port: $PORT"

# Print all environment variables for debugging
echo "DEBUG: All environment variables:"
env | sort

echo "DEBUG: Starting nginx..."
# Start nginx in the background
nginx -g "daemon off;" &
NGINX_PID=$!

echo "DEBUG: Starting backend API server on port $BACKEND_PORT..."
# Start the backend API server on internal port
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

echo "DEBUG: Both services started successfully"
echo "DEBUG: Nginx PID: $NGINX_PID"
echo "DEBUG: Backend PID: $BACKEND_PID"

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $NGINX_PID $BACKEND_PID 2>/dev/null || true
    wait $NGINX_PID $BACKEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals to ensure clean shutdown
trap shutdown SIGTERM SIGINT

# Wait for both processes
wait $NGINX_PID $BACKEND_PID