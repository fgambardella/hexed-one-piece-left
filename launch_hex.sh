#!/bin/bash

# Configuration
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
APP_SCRIPT="hex_gui.py"

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

echo "=== Hex Solver Launcher ==="

# 1. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR" || handle_error "Failed to create virtual environment. Ensure python3-venv is installed."
else
    echo "[*] Virtual environment found."
fi

# 2. Activate virtual environment
echo "[*] Activating virtual environment..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    handle_error "Activation script not found at $VENV_DIR/bin/activate"
fi

# 3. Install requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "[*] Installing/Updating dependencies..."
    pip install -r "$REQUIREMENTS_FILE" || handle_error "Failed to install dependencies."
else
    echo "[!] Warning: $REQUIREMENTS_FILE not found. Skipping dependency installation."
fi

# 4. Run application
if [ -f "$APP_SCRIPT" ]; then
    echo "[*] Starting Application..."
    python3 "$APP_SCRIPT"
else
    handle_error "Application script $APP_SCRIPT not found."
fi

# 5. Deactivate
echo "[*] Deactivating virtual environment..."
deactivate

echo "=== Exited Cleanly ==="
