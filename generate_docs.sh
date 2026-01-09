#!/bin/bash
# Script to generate documentation for the project

DOCS_DIR="docs"
HEXED_DOC_FILE="$DOCS_DIR/hexed_gui.html"
PARTICLE_DOC_FILE="$DOCS_DIR/particle.html"

# Create docs directory if it doesn't exist
if [ ! -d "$DOCS_DIR" ]; then
    echo "Creating docs directory..."
    mkdir -p "$DOCS_DIR"
fi

echo "Generating documentation for hexed_gui.py..."

# Use pydoc to generate HTML documentation
./venv/bin/python3 -m pydoc -w hexed_gui

# Move the generated file to docs directory
if [ -f "hexed_gui.html" ]; then
    mv hexed_gui.html "$HEXED_DOC_FILE"
    echo "Documentation generated successfully: $HEXED_DOC_FILE"
else
    echo "Error: Failed to generate documentation for hexed_gui.py"
    exit 1
fi

echo "Generating documentation for particle.py..."

# Generate documentation for particle module
./venv/bin/python3 -m pydoc -w particle

# Move the generated file to docs directory
if [ -f "particle.html" ]; then
    mv particle.html "$PARTICLE_DOC_FILE"
    echo "Documentation generated successfully: $PARTICLE_DOC_FILE"
else
    echo "Error: Failed to generate documentation for particle.py"
    exit 1
fi

echo "All documentation generated successfully in $DOCS_DIR/ directory!"
