#!/bin/bash
# install.sh
# Installation script for FermVault application.

# --- 1. Define Variables ---
# Get the full path to the directory this script is in (the project root)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXEC="python3" 
DESKTOP_FILE_TEMPLATE="$PROJECT_DIR/fermvault.desktop"
INSTALL_LOCATION="$HOME/.local/share/applications/fermvault.desktop"
DATA_DIR="$HOME/fermvault-data"

echo "--- FermVault Installation Script ---"
echo "Project path detected: $PROJECT_DIR"

# --- 2. Install Python Dependencies ---
# Check for python3 and requirements.txt
if command -v $PYTHON_EXEC &>/dev/null; then
    echo "Installing Python dependencies (local user install)..."
    # Use the --user flag to install packages locally, avoiding the need for sudo
    # pip is smart enough to handle missing packages or new additions.
    $PYTHON_EXEC -m pip install -r "$PROJECT_DIR/requirements.txt" --user
    
    # Check if pip installation succeeded
    if [ $? -ne 0 ]; then
        echo "[FATAL ERROR] Dependency installation failed. Check internet connection or requirements.txt."
        exit 1
    fi
else
    echo "[FATAL ERROR] Python 3 not found. Please install Python 3 and try again."
    exit 1
fi

# --- 3. Create User Data Directory (The Fix for Path Issues) ---
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating user data directory: $DATA_DIR"
    # Create the directory and set safe user permissions (rwx for owner)
    mkdir -p "$DATA_DIR"
    chmod 700 "$DATA_DIR"
else
    echo "Data directory already exists. Skipping creation."
fi

# --- 4. Install Desktop Shortcut (Creation & Copy) ---

if [ -f "$DESKTOP_FILE_TEMPLATE" ]; then
    echo "Installing application shortcut to $INSTALL_LOCATION"
    
    # 4a. Define the necessary application paths
    EXEC_PATH="$PROJECT_DIR/src/main.py"
    ICON_PATH="$PROJECT_DIR/src/assets/fermenter.png"
    
    # 4b. Use sed to replace the generic placeholders in the template with absolute paths
    # NOTE: We use '|' as the delimiter in sed since the paths contain '/'
    
    # 1. Copy the template to a temporary file
    cp "$DESKTOP_FILE_TEMPLATE" /tmp/fermvault_temp.desktop
    
    # 2. Update the Exec path (Ensures it uses the full, absolute path)
    sed -i "s|Exec=PLACEHOLDER_EXEC_PATH|Exec=/usr/bin/$PYTHON_EXEC $EXEC_PATH|g" /tmp/fermvault_temp.desktop
    
    # 3. Update the Icon path
    sed -i "s|Icon=PLACEHOLDER_ICON_PATH|Icon=$ICON_PATH|g" /tmp/fermvault_temp.desktop
    
    # 4. Copy the finalized file to the user's application menu directory
    mkdir -p "$HOME/.local/share/applications"
    mv /tmp/fermvault_temp.desktop "$INSTALL_LOCATION"
    
    # 5. Make the desktop entry executable
    chmod +x "$INSTALL_LOCATION"
    
    echo "Shortcut installed. Look for 'Fermentation Vault' in your application menu."
else
    echo "[WARNING] fermvault.desktop template not found. Skipping shortcut installation."
fi

echo "--- Installation Complete! Please restart your Raspberry Pi or log out/in to refresh the menu. ---"