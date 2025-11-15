💻 INSTALLATION

To install FermVault on your Raspberry Pi, open Terminal and follow these instructions to run the three commands.

NOTES ARE IN ALL CAPS! DO NOT TYPE NOTES!

OPEN TERMINAL AND AT THE DEFAULT PROMPT ENTER THESE COMMANDS:

TO CLONE THE REPOSITORY:

git clone https://github.com/keglevelmonitor/fermvault.git

TO NAVIGATE TO THE PROJECT FOLDER:

cd ~/fermvault

TO INSTALL THE APP ON YOUR PI:

./install.sh


That's it! You will now find "Fermentation Vault" in your application menu under, "Other". 
You can use the "Check for Updates" action inside the app to check for and install future updates.

REFERENCE file structure:
```
~/fermvault/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── install.sh
├── update.sh
├── fermvault.desktop
│
├── src/
│   ├── main.py
│   ├── api_manager.py
│   ├── brewersfriend.api.py
│   ├── fg_calculator.py
│   ├── messages.py
│   ├── notification_manager.py
│   ├── popup_manager.py
│   ├── relay_control.py
│   ├── settings_manager.py
│   ├── temperature_controller.py
│   ├── ui_manager.py
│   ├── ui_manager_base.py
│   │
│   └── assets/
│        ├── help.txt
│        ├── changelog.txt
│        ├── wiring.gif
│        ├── support.gif
│        └── fermenter.png
│            
fermvault-data/
    ├── fermentation_data.json
    ├── fermvault_settings.json
    └── pid_tuning_log.csv
```


