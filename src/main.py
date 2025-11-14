"""
Fermentation Vault App
main.py
"""
import tkinter as tk
import time
import os
import sys
import threading

# --- FIX: Ensure all classes used later are imported here ---
print("[DEBUG] Main: Importing SettingsManager...")
from settings_manager import SettingsManager
print("[DEBUG] Main: Importing TemperatureController...")
from temperature_controller import TemperatureController
print("[DEBUG] Main: Importing UIManager...")
from ui_manager import UIManager
print("[DEBUG] Main: Importing NotificationManager...")
from notification_manager import NotificationManager
print("[DEBUG] Main: Importing RelayControl...")
from relay_control import RelayControl
print("[DEBUG] Main: Importing APIManager...")
from api_manager import APIManager 
print("[DEBUG] Main: Importing FGCalculator...")
from fg_calculator import FGCalculator
print("[DEBUG] Main: All imports complete.")
# -------------------------------------------------------------

# --- FIX: CORRECT BCM PINS CORRESPONDING TO BOARD 37, 38, 40 ---
RELAY_PINS = {
    "Heat": 26, # Was 17 (Board Pin 37)
    "Cool": 20, # Was 27 (Board Pin 38)
    "Fan": 21,  # Was 22 (Board Pin 40)
}
# -----------------------------------------------------------------

# Get the base application directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- App Initialization ---
print("[DEBUG] Main: Step 1 - Initializing SettingsManager...")
settings = SettingsManager()

# --- NEW: Force Control Mode to Ambient on every launch ---
settings.set("control_mode", "Ambient Hold")
# --- END NEW ---

# --- MODIFICATION: Check shutdown status ---
if not settings.get_last_shutdown_status():
    print("[WARNING] Main: Previous shutdown was uncontrolled.")
    # You can add any cleanup logic here
else:
    print("[DEBUG] Main: Previous shutdown was controlled.")
# --- END MODIFICATION ---

print("[DEBUG] Main: Step 2 - Initializing Tkinter root...")
root = tk.Tk()
root.withdraw() 
print("[DEBUG] Main: Step 3 - Initializing APIManager...")

# 1. Load Dynamic API Manager (Early initialization needed for other steps)
api_manager = APIManager(settings)
api_manager.discover_services(BASE_DIR)
print("[DEBUG] Main: Step 4 - Initializing NotificationManager...")

# 2. Create the NotificationManager instance FIRST (pass None for UI temporarily)
notification_manager = NotificationManager(settings, ui_manager=None) 
print("[DEBUG] Main: Step 5 - Initializing Control Components (RelayControl)...")

# 3. Initialize Control Components (Independent of the UI)
relay_control = RelayControl(settings, RELAY_PINS)
print("[DEBUG] Main: Step 6 - Initializing Control Components (TempController)...")
temp_controller = TemperatureController(settings, relay_control)
print("[DEBUG] Main: Step 7 - Initializing FGCalculator...")

# 3.5. Initialize FG Calculator (New Step)
fg_calculator = FGCalculator(settings, api_manager)

# --- CRITICAL FIX: Ensure root is visible and ready BEFORE UI is built ---
print("[DEBUG] Main: Step 8 - Deiconifying root...")
root.deiconify()
print("[DEBUG] Main: Step 9 - Initializing UIManager...")

# 4. Initialize UI (UIManager) (MOVED HERE)
ui = UIManager(root, settings, temp_controller, api_manager, notification_manager, "Fermentation Vault v1.0", fg_calculator) 
print("[DEBUG] Main: Step 10 - Finalizing Circular References...")

# 5. Finalize Circular References (MOVED HERE)
notification_manager.ui = ui # Back-link the UI reference
temp_controller.notification_manager = notification_manager
relay_control.set_logger(ui.log_system_message) # Inject the logger
print("[DEBUG] Main: Step 11 - Starting Services...")

# --- Start Services and Main Loop ---
# temp_controller.start_monitoring()

def shutdown_application():
    # ... (shutdown function body) ...
    # --- MODIFICATION: Changed log message ---
    print(f"[SHUTDOWN] Controlled shutdown initiated...")
    # --- END MODIFICATION ---
    
    if notification_manager:
        notification_manager.stop_scheduler()

    if temp_controller:
        temp_controller.stop_monitoring()
        
    if relay_control:
        relay_control.turn_off_all_relays()

    settings.set_controlled_shutdown(True)
    time.sleep(0.5)

    root.quit()
    root.destroy()
    print("[SHUTDOWN] Application closed.")
# Bind shutdown function to window close event
root.protocol("WM_DELETE_WINDOW", shutdown_application)

print("[DEBUG] Main: Step 12 - Starting mainloop()...")
# Start Tkinter event loop
root.mainloop()
