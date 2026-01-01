#!/bin/bash
# Script to generate documentation for the project

DOC_FILE="hex_gui.html"

echo "Generating documentation for hex_gui.py..."

# Use pydoc to generate HTML documentation
./venv/bin/python3 -m pydoc -w hex_gui

if [ -f "$DOC_FILE" ]; then
    echo "Documentation generated successfully: $DOC_FILE"
else
    echo "Error: Failed to generate documentation."
    exit 1
fi
