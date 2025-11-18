## 💻 FermVault Project

The **FermVault app** monitors the temperature of a fermenting product (beer, wine, mead, etc.) inside a refrigerator or freezer. The app turns the refrigerator/freezer on or off, and optionally a heater on or off, to maintain a consistent fermentation temperature. The temperature of the fermenting product can be used as the control-to point. PID regulation ensures accurate temperature control with very little or no overshoot or undershoot of the setpoint temperature. Robust email notifications allow flexible remote monitoring. A "command" mail integration allows remote email control of the FermVault system.

Currently tested only on the Raspberry Pi 3B running Trixie and Bookworm. Should work with RPi4 running the same OS's but not yet tested.

Please **donate $$** if you use the app. See "Support the app" under the Settings & Info menu.

There is also a **KegLevel Monitor** project in the repository. The KegLevel Monitor allows homebrewers to monitor and track the level of beer in their kegs. Up to 10 kegs are supported. Robust email notifications allow flexible remote monitoring.

🔗 [KegLevel Project](https://github.com/keglevelmonitor/keglevel)

## To Install the FermVault App

Open **Terminal** and run these three commands one-after-another to clone the repository, navigate to the project folder, and install the dependencies and app launcher on your RPi::

```bash
git clone https://github.com/keglevelmonitor/fermvault.git
```

```bash
cd ~/fermvault
```

```bash
./install.sh
```

That's it! You will now find "Fermentation Vault" in your application menu under **Other**. You can use the "Check for Updates" action inside the app to install future updates.

## 🔗 Detailed installation instructions

Refer to the detailed installation instructions for specific hardware requirements and a complete wiring & hookup instructions:

👉 (placeholder for installation instructions)

## ⚙️ Summary hardware requirements

Required
👉 (placeholder for summary hardware requirements) 

## ⚙️ Hardware Requirements

For the complete list of required hardware, part numbers, and purchasing links, please see the detailed hardware list:

➡️ **[View Detailed Hardware List](assets/hardware.md)**

## ⚡ Quick Wiring Diagram

Here is a quick wiring diagram showing the logical connections of the system's components:
![Wiring Diagram for FermVault](src/assets/wiring.gif)

## ⚙️ For reference

Installed file structure:
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
├── venv/
│   ├── (installed dependencies)
│   ├── rpi-lgpio
│   ├── requests
│   ├── pytz
│
~/fermvault-data/
    ├── fermentation_data.json
    ├── fermvault_settings.json
    └── pid_tuning_log.csv
    
System-level dependencies
(installed via apt outside venv)
- python3-tk
- python3-dev
- swig
```


