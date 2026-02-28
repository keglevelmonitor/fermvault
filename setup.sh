#!/bin/bash
# setup.sh
# Single-line installer wrapper for FermVault

# 1. Define the Install Directories
INSTALL_DIR="$HOME/fermvault"

# --- CRITICAL FIX: Export variables so install.sh can see them ---
export DATA_DIR="$HOME/fermvault-data"
export DESKTOP_FILENAME="fermvault.desktop"
export APP_TITLE="FermVault"
# ---------------------------------------------------------------

WHAT_TO_INSTALL="FermVault Application and Data Directory"
CLEANUP_MODE="NONE"

echo "========================================"
echo "    FermVault Auto-Installer"
echo "========================================"

# 2. Logic to handle existing installs
if [ -d "$INSTALL_DIR" ] || [ -d "$DATA_DIR" ]; then
    while true; do
        echo ""
        echo "Existing installation detected:"
        [ -d "$INSTALL_DIR" ] && echo " - App Folder: $INSTALL_DIR"
        [ -d "$DATA_DIR" ]    && echo " - Data Folder: $DATA_DIR"
        echo ""
        echo "How would you like to proceed? (Case Sensitive)"
        echo "  APP       - Reinstall App only (Keeps your existing data/settings)"
        echo "  ALL       - Reinstall App AND reset data (Fresh Install)"
        echo "  UNINSTALL - Uninstall the app and the data directory"
        echo "  EXIT      - Cancel installation"
        echo ""
        read -p "Enter selection: " choice
        
        if [ "$choice" == "APP" ]; then
            WHAT_TO_INSTALL="FermVault Application"
            CLEANUP_MODE="APP"
            break
        elif [ "$choice" == "ALL" ]; then
            WHAT_TO_INSTALL="FermVault Application and Data Directory"
            CLEANUP_MODE="ALL"
            break
        elif [ "$choice" == "UNINSTALL" ]; then
            echo "------------------------------------------"
            echo "YOU ARE ABOUT TO DELETE:"
            echo "The FermVault application AND all user data/settings."
            echo "------------------------------------------"
            echo ""
            read -p "Type YES to UNINSTALL the app and the user data folder, or any other key to return to the menu: " confirm
            
            if [ "$confirm" == "YES" ]; then
                echo ""
                echo "Removing files..."
                
                # 1. Remove Desktop Shortcut
                DESKTOP_FILE="$HOME/.local/share/applications/$DESKTOP_FILENAME"
                if [ -f "$DESKTOP_FILE" ]; then
                    rm "$DESKTOP_FILE"
                    echo " - Removed desktop shortcut"
                fi
                
                # 2. Remove App Directory
                if [ -d "$INSTALL_DIR" ]; then
                    rm -rf "$INSTALL_DIR"
                    echo " - Removed application directory: $INSTALL_DIR"
                fi
                
                # 3. Remove Data Directory
                if [ -d "$DATA_DIR" ]; then
                    rm -rf "$DATA_DIR"
                    echo " - Removed data directory: $DATA_DIR"
                fi
                
                echo ""
                echo "=========================================="
                echo "   Uninstallation Complete"
                echo "=========================================="
                exit 0
            else
                echo ""
                echo "Uninstallation aborted. Returning to main menu..."
                # Loop naturally continues back to the prompt
            fi
        elif [ "$choice" == "EXIT" ]; then
            echo "Cancelled."
            exit 0
        else
            echo "Invalid selection. Please enter APP, ALL, UNINSTALL, or EXIT."
            # Loop naturally continues back to the prompt
        fi
    done
fi

# 3. Size Warning / Confirmation
echo ""
echo "------------------------------------------------------------"
echo "This script will install the $WHAT_TO_INSTALL"
echo "and will use about 20 MB of storage space on the Pi's SD card."
echo ""
echo "Basic installed file structure:"
echo ""
echo "  $INSTALL_DIR/"
echo "  |-- utility files..."
echo "  |-- src/"
echo "  |   |-- application files..."
echo "  |   |-- assets/"
echo "  |       |-- supporting files..."
echo "  |-- venv/"
echo "  |   |-- python3 & dependencies"
echo "  $DATA_DIR/"
echo "  |-- user data..."
echo ""
echo "------------------------------------------------------------"
echo ""

read -p "Press Y to proceed, or any other key to cancel: " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# 4. Perform Cleanup (Delayed until AFTER confirmation)
if [ "$CLEANUP_MODE" == "APP" ]; then
    echo "Removing existing application..."
    rm -rf "$INSTALL_DIR"
elif [ "$CLEANUP_MODE" == "ALL" ]; then
    echo "Removing application and data..."
    rm -rf "$INSTALL_DIR"
    rm -rf "$DATA_DIR"
fi

# 5. Check/Install Git
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing..."
    sudo apt-get update && sudo apt-get install -y git
fi

# 6. Clone Repo
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

# 7. Run the Main Installer
echo "Launching main installer..."
chmod +x install.sh

# The exported variables (DATA_DIR, DESKTOP_FILENAME) will now be passed automatically
./install.sh
