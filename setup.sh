#!/bin/bash
# setup.sh
# Single-line installer wrapper for FermVault

# 1. Define the Install Directory
INSTALL_DIR="$HOME/fermvault"

echo "========================================"
echo "   FermVault Auto-Installer"
echo "========================================"

# 2. Check/Install Git
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing..."
    sudo apt-get update && sudo apt-get install -y git
fi

# 3. Clone or Update Repo
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory exists at $INSTALL_DIR."
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" || exit 1
    git pull
else
    # Assumption: The repo name follows the same pattern as keglevel
    echo "Cloning repository to $INSTALL_DIR..."
    git clone https://github.com/keglevelmonitor/fermvault.git "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit 1
fi

# 4. Run the Main Installer
echo "Launching main installer..."
chmod +x install.sh
./install.sh
