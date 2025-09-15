#!/bin/bash

echo "Starting Zed Update Manager v2.0 (PyQt5 + Go Backend)..."
echo

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Error: Go is not installed or not in PATH"
    echo "Please install Go from https://golang.org/dl/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    echo "Please install Python from https://python.org/downloads/"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
MODERN_DIR="$SCRIPT_DIR/../modern"

# Check if PyQt5 is installed
echo "Checking PyQt5 installation..."
python3 -c "import PyQt5" &> /dev/null
if [ $? -ne 0 ]; then
    echo "PyQt5 not found, installing dependencies..."
    cd "$MODERN_DIR/frontend"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install PyQt5 dependencies"
        echo "Please run: pip3 install PyQt5==5.15.10"
        exit 1
    fi
    echo "PyQt5 installed successfully"
fi

# Navigate to backend directory and install dependencies
echo "Installing Go dependencies..."
cd "$MODERN_DIR/backend"
go mod tidy
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Go dependencies"
    exit 1
fi

echo
echo "Starting Go backend server..."
cd "$MODERN_DIR/backend"

# Start backend in background
go run main.go &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend failed to start"
    exit 1
fi

# Check if backend is responding
echo "Checking backend connection..."
if command -v curl &> /dev/null; then
    curl -f http://localhost:8080/api/v1/health &> /dev/null
    if [ $? -ne 0 ]; then
        echo "Warning: Backend may not be ready yet. GUI will attempt to connect..."
    else
        echo "Backend connection successful"
    fi
else
    echo "curl not available, skipping connection check"
fi

echo "Starting PyQt5 GUI frontend..."
cd "$MODERN_DIR/frontend"

# Start frontend
python3 main.py &
FRONTEND_PID=$!

echo
echo "Both applications have been started:"
echo "- Backend API: http://localhost:8080"
echo "- Frontend GUI: PyQt5 desktop application"
echo "- Backend PID: $BACKEND_PID"
echo "- Frontend PID: $FRONTEND_PID"
echo

# Function to cleanup processes on exit
cleanup() {
    echo
    echo "Shutting down applications..."
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "Backend stopped"
    fi
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "Frontend stopped"
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

echo "Press Ctrl+C to stop both applications"
echo

# Wait for frontend to finish
wait $FRONTEND_PID

# Cleanup backend when frontend closes
cleanup
