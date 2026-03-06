#!/bin/bash
# Common build script template for FFI implementations
# This script should be customized for each language implementation

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LANGUAGE_NAME="$(basename "$SCRIPT_DIR")"

echo "Building FFI implementation for: $LANGUAGE_NAME"

# Check if uv environment is active
if [[ -z "$VIRTUAL_ENV" ]] || [[ "$VIRTUAL_ENV" != *".venv"* ]]; then
    echo "WARNING: uv virtual environment is not active!"
    echo "Please activate uv environment with: uv sync && source .venv/bin/activate"
    exit 1
fi

# Language-specific build commands should be added here
# Examples:
# For C: gcc -shared -fPIC -o libfunctions.so functions.c
# For Rust: cargo build --release --lib
# For Go: go build -buildmode=c-shared -o libfunctions.so functions.go

echo "Build template - customize this script for $LANGUAGE_NAME"
echo "Add your language-specific build commands here"

# Verify shared library was created
EXPECTED_LIB="libfunctions.so"  # Adjust for platform (.dll on Windows, .dylib on macOS)
if [[ ! -f "$EXPECTED_LIB" ]]; then
    echo "ERROR: Expected shared library $EXPECTED_LIB was not created"
    exit 1
fi

echo "Build completed successfully for $LANGUAGE_NAME"