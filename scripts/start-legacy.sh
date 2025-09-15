#!/bin/bash

echo "Starting Zed Update Manager (Legacy Version)..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    echo "Please install Python from https://python.org/downloads/"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LEGACY_DIR="$SCRIPT_DIR/../legacy"

# Check if PyQt5 is installed for legacy version
echo "Checking PyQt5 installation..."
python3 -c "import PyQt5" &> /dev/null
if [ $? -ne 0 ]; then
    echo "PyQt5 not found, installing dependencies..."
    cd "$LEGACY_DIR"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install PyQt5 dependencies"
        echo "Please run: pip3 install PyQt5"
        exit 1
    fi
    echo "PyQt5 installed successfully"
fi

echo "Installing Python dependencies..."
cd "$LEGACY_DIR"
python3 -m pip install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Warning: Some Python dependencies may not have installed correctly"
fi

echo
echo "Starting Legacy Zed Update Manager..."

# Check for command line arguments
if [ "$1" = "--gui" ]; then
    python3 main.py --gui
elif [ "$1" = "--update" ]; then
    python3 main.py --update
elif [ "$1" = "--help" ]; then
    python3 main.py --help
else
    echo "Select mode:"
    echo "1. GUI Mode"
    echo "2. Console Update"
    echo "3. Help"
    echo
    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            python3 main.py --gui
            ;;
        2)
            python3 main.py --update
            ;;
        3)
            python3 main.py --help
            ;;
        *)
            echo "Invalid choice. Starting GUI mode..."
            python3 main.py --gui
            ;;
    esac
fi

echo
echo "Legacy application finished."
