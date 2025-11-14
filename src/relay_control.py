# relay_control.py

import threading
import time
from datetime import datetime
import os
import sys
import RPi.GPIO as GPIO # Import the real RPi.GPIO library directly

# --- GPIO SETUP ---
# Set BCM mode globally ONCE at import time
GPIO.setmode(GPIO.BCM) 

# Define Relay States (RELAY_OFF = HIGH, RELAY_ON = LOW)
RELAY_OFF = GPIO.HIGH
RELAY_ON = GPIO.LOW
# --- END GPIO SETUP ---


class RelayControl:
    
    def __init__(self, settings_manager, relay_pins):
        self.settings = settings_manager
        self.pins = relay_pins
        self.gpio = GPIO # Use the real GPIO library
        
        self.last_cool_change = time.time()
        self.cool_start_time = None
        self.cool_disabled_until = 0.0
        
        self.logger = None 
        
        self.current_restriction_key = "dwell"
        
        # --- NEW: Set initial Dwell Message on Startup ---
        try:
            DWELL_TIME_S = self.settings.get_all_compressor_protection_settings()["cooling_dwell_time_s"]
            dwell_end_time = datetime.fromtimestamp(self.last_cool_change + DWELL_TIME_S)
            
            # Set the initial default message (Demand is OFF at startup)
            startup_msg = f"Demand OFF; DWELL until {dwell_end_time.strftime('%H:%M:%S')}"
            self.settings.set("cool_restriction_status", startup_msg)
        except Exception as e:
            print(f"[ERROR] RelayControl init failed to set startup dwell message: {e}")
        # --- END NEW ---
        
        self._setup_gpio()

    def set_logger(self, logger_callable):
        """Assigns the UI's logging function to this class."""
        self.logger = logger_callable
        
        if self.logger:
            # Removed the initial logging of the Dwell Time, as it's not a true restriction yet.
            pass

    def _setup_gpio(self):
        # Removed IS_HARDWARE_AVAILABLE check
        self.gpio.setwarnings(False)
        # self.gpio.setmode(self.gpio.BCM) # Mode is set at import

        for pin in self.pins.values():
            try:
                pin_int = int(pin)
            except ValueError:
                print(f"[ERROR] GPIO: Skipping pin {pin} as it's not a valid number.")
                continue

            self.gpio.setup(pin_int, self.gpio.OUT)
            self.gpio.output(pin_int, RELAY_OFF) # Ensure all are OFF initially

    def _is_cooling_on(self):
        # Removed IS_HARDWARE_AVAILABLE check
        return self.gpio.input(self.pins["Cool"]) == RELAY_ON

    def _is_heating_on(self):
        # Removed IS_HARDWARE_AVAILABLE check
        return self.gpio.input(self.pins["Heat"]) == RELAY_ON

    # --- RELAY CONTROL AND PROTECTION ENFORCEMENT ---

    def set_desired_states(self, desired_heat, desired_cool, control_mode):
        """
        Receives simple ON/OFF commands and executes them after enforcing constraints.
        
        --- FIX: Returns the final, enforced state of the relays ---
        """
        current_time = time.time()
        
        # --- MODIFICATION START ---
        # 1. State/Status Initialization
        is_currently_on = self._is_cooling_on()
        final_cool_state = desired_cool # Start with the initial intent
        
        # The status message that goes to the NEW Cooling Message Area
        restriction_message = "" 
        
        # Get protection settings
        cool_settings = self.settings.get_all_compressor_protection_settings()
        DWELL_TIME_S = cool_settings["cooling_dwell_time_s"]
        MAX_RUNTIME_S = cool_settings["max_cool_runtime_s"]
        FAIL_SAFE_SHUTDOWN_S = cool_settings["fail_safe_shutdown_time_s"]
        
        # 2. Cooling Protection Checks (Priority Order)
        
        # A. Check Fail-Safe Shutdown Time (Is compressor currently locked out?)
        if current_time < self.cool_disabled_until:
            minutes_remaining = max(1, int((self.cool_disabled_until - current_time) / 60))
            restriction_message = f"FAIL-SAFE active until {datetime.fromtimestamp(self.cool_disabled_until).strftime('%H:%M:%S')}"
            
            # CRITICAL: Log this restriction to the SYSTEM MESSAGES area
            self._log_restriction_change(
                key="fail_safe",
                message=f"Cooling restricted by Fail-Safe for {minutes_remaining} min."
            )
            final_cool_state = False # Enforce OFF

        # B. Check Max Run Time (and activate Fail-Safe if exceeded)
        elif final_cool_state and self.cool_start_time and (current_time - self.cool_start_time) >= MAX_RUNTIME_S:
            self.cool_disabled_until = current_time + FAIL_SAFE_SHUTDOWN_S
            
            restriction_message = f"FAIL-SAFE active until {datetime.fromtimestamp(self.cool_disabled_until).strftime('%H:%M:%S')}"
            final_cool_state = False # Enforce OFF
            self.cool_start_time = None 
            
            # CRITICAL: Log this restriction to the SYSTEM MESSAGES area
            self._log_restriction_change(
                key="fail_safe_triggered",
                message=f"Cooling ran for max time. Fail-Safe enabled until {datetime.fromtimestamp(self.cool_disabled_until).strftime('%H:%M:%S')}."
            )
        
        # C. Check Dwell Time (Persistent Check)
        else:
            dwell_remaining = (self.last_cool_change + DWELL_TIME_S) - current_time
            
            if dwell_remaining > 0:
                # Dwell is ACTIVE.
                # Determine what the controller *wants* to do.
                demand_status = "ON" if desired_cool else "OFF"
                restriction_message = f"Demand {demand_status}; DWELL until {datetime.fromtimestamp(current_time + dwell_remaining).strftime('%H:%M:%S')}"
                
                # Force the final state to match the *actual* current state
                final_cool_state = is_currently_on 
            
            else:
                # Dwell is NOT active. A state change is allowed.
                if final_cool_state != is_currently_on:
                    # A change is happening, so reset the dwell timer
                    self.last_cool_change = current_time
                    
                    # Update cool_start_time
                    if final_cool_state: 
                        self.cool_start_time = current_time 
                    else: 
                        self.cool_start_time = None
                
                # We must ensure we reset the restriction key if it was fail-safe
                self.current_restriction_key = "none"

        # --- 3. Apply Final States to Relays ---
        final_heat_state = desired_heat and not final_cool_state 
        
        # Removed IS_HARDWARE_AVAILABLE check
        self.gpio.output(self.pins["Heat"], RELAY_ON if final_heat_state else RELAY_OFF)
        self.gpio.output(self.pins["Cool"], RELAY_ON if final_cool_state else RELAY_OFF)
            
        # --- 4. Update SettingsManager with simplified state and new restriction message ---
        
        # Simple Relay State (for the main indicator)
        self.settings.set("heat_state", "HEATING" if final_heat_state else "Heating OFF")
        self.settings.set("cool_state", "COOLING" if final_cool_state else "Cooling OFF") 
        
        # Restriction Status (for the new secondary indicator)
        self.settings.set("cool_restriction_status", restriction_message) 
        
        # --- MODIFICATION END ---
        
        return final_heat_state, final_cool_state

    # --- FAN CONTROL ---
    def turn_on_fan(self):
        fan_mode = self.settings.get("fan_control_mode", "Auto") 
        if fan_mode in ["Auto", "ON"]:
            # Removed IS_HARDWARE_AVAILABLE check
            self.gpio.output(self.pins["Fan"], RELAY_ON)
            self.settings.set("fan_state", "Fan ON")

    def turn_off_fan(self):
        # Removed IS_HARDWARE_AVAILABLE check
        self.gpio.output(self.pins["Fan"], RELAY_OFF)
        self.settings.set("fan_state", "Fan OFF")

    def turn_off_all_relays(self, skip_fan=False):
        # Removed IS_HARDWARE_AVAILABLE check
        self.gpio.output(self.pins["Heat"], RELAY_OFF)
        self.gpio.output(self.pins["Cool"], RELAY_OFF)
        if not skip_fan: self.gpio.output(self.pins["Fan"], RELAY_OFF)
        
        # --- MODIFICATION START ---
        self.settings.set("heat_state", "Heating OFF")
        self.settings.set("cool_state", "Cooling OFF")
        # --- MODIFICATION END ---
        if not skip_fan: self.settings.set("fan_state", "Fan OFF")

    # --- UI UPDATE HELPERS ---
    
    def _log_restriction_change(self, key, message):
        """Logs a change in restriction state *only if* the state is new and the message is NOT DWELL."""
        
        # If the message contains "Dwell", return immediately (User Request)
        if "Dwell" in message:
            return

        # Handle Fail-Safe logging (key should be "fail_safe" or "fail_safe_triggered")
        if "fail_safe" in key:
            if self.current_restriction_key != key:
                self.current_restriction_key = key
                if self.logger and message:
                    self.logger(message)
                return
        
        # Reset the key if a normal cooling cycle started after a Fail-Safe
        if key == "dwell_started": # This key is used in old versions but ensures reset
            self.current_restriction_key = "dwell" 
        
        # If we reach here, it's either an ignored message or a repeat log.
        return
        
    def update_ui_data(self, beer_temp, amb_temp, amb_min, amb_max, current_mode, ramp_target, ambient_target):
        """Updates UI's display variables in SettingsManager with calculated and actual values."""
        
        # --- DEBUG PRINT ---
        # print(f"[DEBUG] RC: Received Actuals: {beer_temp} ({type(beer_temp)}), Setpoint Min: {amb_min}")
        # -------------------

        # 1. ACTUAL TEMPS
        # beer_temp/amb_temp are passed as float or the string "--.-"
        self.settings.set("beer_temp_actual", beer_temp)
        self.settings.set("amb_temp_actual", amb_temp)
             
        # 2. SETPOINTS (Numeric values)
        self.settings.set("amb_min_setpoint", amb_min)
        self.settings.set("amb_max_setpoint", amb_max)
        self.settings.set("amb_target_setpoint", ambient_target) # <-- NEW LINE
        
        # 3. BEER SETPOINT (Dynamic based on mode)
        beer_target = 0.0
        if current_mode == "Ramp-Up":
             beer_target = ramp_target
        elif current_mode == "Beer Hold":
             beer_target = self.settings.get("beer_hold_f") 
        elif current_mode == "Fast Crash":
             beer_target = self.settings.get("fast_crash_hold_f")
        else: # Ambient Hold or initial state
             beer_target = self.settings.get("beer_hold_f") 
             
        # Use the actual calculated target if available, otherwise the primary hold setting
        self.settings.set("beer_setpoint_current", beer_target)
