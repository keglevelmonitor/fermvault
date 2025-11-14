#!/bin/bash
# update.sh
# Handles post-pull dependency updates for FermVault.

# --- 1. Define Variables ---
# Get the full path to the directory this script is in (the project root)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXEC="python3"

echo "--- FermVault Update Script ---"
echo "Starting dependency refresh in $PROJECT_DIR"

# --- 2. Check for Git Sanity (Optional, but good defense against user error) ---
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "[ERROR] This directory does not appear to be a Git repository."
    echo "Please ensure you run 'git clone' first."
    exit 1
fi

# --- 3. Run Dependency Installation ---
# This is crucial for catching new libraries added in the update.
if command -v $PYTHON_EXEC &>/dev/null; then
    echo "Checking for new Python dependencies..."
    # Re-run pip install with --user to install new dependencies locally.
    # pip is smart enough not to reinstall existing packages.
    $PYTHON_EXEC -m pip install -r "$PROJECT_DIR/requirements.txt" --user
else
    echo "[ERROR] Python 3 not found. Cannot update dependencies."
    exit 1
fi

echo "--- Dependency Update Complete ---"
echo "If you ran this script manually, please restart the FermVault application."