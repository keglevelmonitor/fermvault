💻 Fermentation Vault Project

This project requires special hardware and must be wired carefully according to the wiring diagram. 

## ⚙️ Hardware Requirements

For the complete list of required hardware, part numbers, and purchasing links, please see the detailed hardware list:

➡️ **[View Detailed Hardware List](assets/hardware.md)**

## ⚡ Wiring Diagram

Here is the required wiring setup. Follow this diagram carefully.
![Wiring Diagram for FermVault](assets/wiring.gif)

To install the FermVault App on your Raspberry Pi:

Open **Terminal** and run these three commands one-after-another:
    (explanations in parenthesis)

git clone https://github.com/keglevelmonitor/fermvault.git
    (clones the repository)

cd ~/fermvault
    (navigates to the project folder)

./install.sh
    (installs the dependencies and app launcher on your RPi)


That's it! You will now find "Fermentation Vault" in your application menu under, "Other". 
You can use the "Check for Updates" action inside the app to install future updates.

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


