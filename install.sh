#!/bin/bash
# install.sh
# Installation script for FermVault application.

# Stop on any error to prevent partial installs
set -e

echo "=========================================="
echo "    FermVault Installer"
echo "=========================================="

# --- 1. Define Variables ---
# We use ${VAR:-DEFAULT} syntax. If the variable is already set (exported), 
# use it; otherwise, use the default value.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXEC="python3"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON_EXEC="$VENV_DIR/bin/python"

# Dynamic Variables (Can be overridden by setup.sh)
DATA_DIR="${DATA_DIR:-$HOME/fermvault-data}"
DESKTOP_FILENAME="${DESKTOP_FILENAME:-fermvault.desktop}"
APP_TITLE="${APP_TITLE:-Ferm Vault}"

DESKTOP_FILE_TEMPLATE="$PROJECT_DIR/fermvault.desktop"
INSTALL_LOCATION="$HOME/.local/share/applications/$DESKTOP_FILENAME"

echo "Project path:   $PROJECT_DIR"
echo "Data directory: $DATA_DIR"
echo "App Title:      $APP_TITLE"

# --- 2. Install System Dependencies (Requires Sudo) ---
echo ""
echo "--- [Step 1/5] Checking System Dependencies ---"
echo "You may be asked for your password to install system packages."

# Install Kivy Dependencies (SDL2)
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv liblgpio-dev numlockx libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# --- 3. Setup Python Environment (Clean Install) ---
echo ""
echo "--- [Step 2/5] Setting up Virtual Environment ---"

# CLEANUP: Delete existing venv to ensure a clean slate
if [ -d "$VENV_DIR" ]; then
    echo "Removing old virtual environment for a clean install..."
    rm -rf "$VENV_DIR"
fi

echo "Creating new Python virtual environment at $VENV_DIR..."
$PYTHON_EXEC -m venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    echo "[FATAL ERROR] Failed to create virtual environment."
    exit 1
fi

# --- 4. Install Python Libraries ---
echo ""
echo "--- [Step 3/5] Installing Python Libraries ---"

# Verify requirements.txt exists
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "[FATAL ERROR] requirements.txt not found in $PROJECT_DIR."
    exit 1
fi

# Install using the pip INSIDE the virtual environment
"$VENV_PYTHON_EXEC" -m pip install --upgrade pip
"$VENV_PYTHON_EXEC" -m pip install -r "$PROJECT_DIR/requirements.txt"

if [ $? -ne 0 ]; then
    echo "[FATAL ERROR] Dependency installation failed."
    exit 1
fi

# --- 5. Create User Data Directory ---
echo ""
echo "--- [Step 4/5] Configuring Data Directory ---"
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating user data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR"
    chmod 700 "$DATA_DIR"
else
    echo "Data directory already exists ($DATA_DIR). Skipping."
fi

# --- 6. Install App Icon for Taskbar (Raspberry Pi) ---
ICON_SOURCE="$PROJECT_DIR/src/assets/fermenter.png"
SYSTEM_ICON_NAME="fermvault"
if [ -f "$ICON_SOURCE" ]; then
    echo ""
    echo "Installing app icon for taskbar..."
    sudo cp "$ICON_SOURCE" "/usr/share/icons/${SYSTEM_ICON_NAME}.png"
    sudo chmod 644 "/usr/share/icons/${SYSTEM_ICON_NAME}.png"
    sudo mkdir -p /usr/share/icons/hicolor/48x48/apps
    sudo cp "$ICON_SOURCE" "/usr/share/icons/hicolor/48x48/apps/${SYSTEM_ICON_NAME}.png"
    sudo chmod 644 "/usr/share/icons/hicolor/48x48/apps/${SYSTEM_ICON_NAME}.png"
    if command -v gtk-update-icon-cache &>/dev/null; then
        sudo gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
    fi
    echo "Icon installed."
else
    echo "[WARNING] fermenter.png not found at $ICON_SOURCE - taskbar may show default icon."
fi

# --- 7. Install Desktop Shortcut ---
echo ""
echo "--- [Step 5/5] Installing Desktop Shortcut ---"

if [ -f "$DESKTOP_FILE_TEMPLATE" ]; then
    EXEC_CMD="$VENV_PYTHON_EXEC $PROJECT_DIR/src/main_kivy.py"
    
    cp "$DESKTOP_FILE_TEMPLATE" /tmp/fermvault_temp.desktop
    sed -i "s|Exec=PLACEHOLDER_EXEC_PATH|Exec=$EXEC_CMD|g" /tmp/fermvault_temp.desktop
    sed -i "s|Path=PLACEHOLDER_PATH|Path=$PROJECT_DIR/src|g" /tmp/fermvault_temp.desktop
    sed -i "s|^Name=.*|Name=$APP_TITLE|g" /tmp/fermvault_temp.desktop
    
    mkdir -p "$HOME/.local/share/applications"
    mv /tmp/fermvault_temp.desktop "$INSTALL_LOCATION"
    chmod +x "$INSTALL_LOCATION"
    echo "Shortcut installed to: $INSTALL_LOCATION"
else
    echo "[WARNING] fermvault.desktop template not found. Skipping shortcut."
fi

echo ""
echo "================================================="
echo ""
echo "Installation complete!"
echo ""
echo "At the Applications menu:"
echo "   select Other, $APP_TITLE to run the app."
echo ""
echo "================================================="
echo ""

read -p "Enter Y to launch the app, or any other key to exit: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Launching FermVault..."
    nohup "$VENV_PYTHON_EXEC" "$PROJECT_DIR/src/main_kivy.py" >/dev/null 2>&1 &
    disown
    kill -HUP $PPID
    exit 0
else
    echo "Exiting installer."
    exit 0
fi
