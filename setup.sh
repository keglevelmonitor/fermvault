#!/bin/bash
# setup.sh
# Single-line installer wrapper for FermVault

# 1. Define the Install Directories
INSTALL_DIR="$HOME/fermvault"
DATA_DIR="$HOME/fermvault-data"
WHAT_TO_INSTALL="FermVault Application and Data Directory"

echo "========================================"
echo "   FermVault Auto-Installer"
echo "========================================"

# 2. Logic to handle existing installs
if [ -d "$INSTALL_DIR" ] || [ -d "$DATA_DIR" ]; then
    echo ""
    echo "Existing installation detected:"
    [ -d "$INSTALL_DIR" ] && echo " - App Folder: $INSTALL_DIR"
    [ -d "$DATA_DIR" ]    && echo " - Data Folder: $DATA_DIR"
    echo ""
    echo "How would you like to proceed? (Case Sensitive)"
    echo "  APP  - Reinstall App only (Keeps your existing data/settings)"
    echo "  ALL  - Reinstall App AND reset data (Fresh Install)"
    echo "  EXIT - Cancel installation"
    echo ""
    read -p "Enter selection: " choice
    
    if [ "$choice" == "APP" ]; then
        WHAT_TO_INSTALL="FermVault Application"
        # Remove app dir to force a clean git clone
        if [ -d "$INSTALL_DIR" ]; then
            echo "Removing existing application..."
            rm -rf "$INSTALL_DIR"
        fi
    elif [ "$choice" == "ALL" ]; then
        WHAT_TO_INSTALL="FermVault Application and Data Directory"
        echo "Removing application and data..."
        rm -rf "$INSTALL_DIR"
        rm -rf "$DATA_DIR"
    else
        echo "Cancelled."
        exit 0
    fi
fi

# 3. Size Warning / Confirmation
echo ""
echo "------------------------------------------------------------"
echo "This script will install the $WHAT_TO_INSTALL"
echo "and will use about 20 MB of storage space on the Pi's SD card."
echo "------------------------------------------------------------"
echo ""

read -p "Press Y to proceed, or any other key to cancel: " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# 4. Check/Install Git
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing..."
    sudo apt-get update && sudo apt-get install -y git
fi

# 5. Clone Repo
# Since we deleted the directory in the logic above (if it existed), 
# we can simply clone.
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory exists (Update mode)..."
    cd "$INSTALL_DIR" || exit 1
    git pull
else
    echo "Cloning repository to $INSTALL_DIR..."
    git clone https://github.com/keglevelmonitor/fermvault.git "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit 1
fi

# 6. Run the Main Installer
echo "Launching main installer..."
chmod +x install.sh
./install.sh
