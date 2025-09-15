#!/bin/bash

echo "========================================"
echo "    Zed Update Manager - Launcher"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    echo "Please install Python from https://python.org/downloads/"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Select implementation to run:"
echo
echo "1. Legacy Implementation (PyQt5 Standalone)"
echo "   - Original single application"
echo "   - Minimal dependencies"
echo "   - Compatible with older systems"
echo
echo "2. Modern Implementation (Go Backend + PyQt5 Frontend)"
echo "   - Microservices architecture"
echo "   - Enhanced performance"
echo "   - Real-time API communication"
echo
echo "3. Exit"
echo

while true; do
    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            echo
            echo "Starting Legacy Implementation..."
            echo "========================================"
            chmod +x "$SCRIPT_DIR/scripts/start-legacy.sh"
            "$SCRIPT_DIR/scripts/start-legacy.sh"
            break
            ;;
        2)
            echo
            echo "Starting Modern Implementation..."
            echo "========================================"

            # Check if Go is installed for modern implementation
            if ! command -v go &> /dev/null; then
                echo "Error: Go is not installed or not in PATH"
                echo "Modern implementation requires Go 1.21+"
                echo "Please install Go from https://golang.org/dl/"
                echo
                echo "Falling back to Legacy implementation..."
                chmod +x "$SCRIPT_DIR/scripts/start-legacy.sh"
                "$SCRIPT_DIR/scripts/start-legacy.sh"
            else
                chmod +x "$SCRIPT_DIR/scripts/start-modern.sh"
                "$SCRIPT_DIR/scripts/start-modern.sh"
            fi
            break
            ;;
        3)
            echo "Goodbye!"
            break
            ;;
        *)
            echo "Invalid choice. Please enter 1, 2, or 3."
            ;;
    esac
done

echo
echo "Press Enter to exit..."
read
