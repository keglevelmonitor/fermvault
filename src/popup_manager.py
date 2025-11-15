"""
Fermentation Vault App
popup_manager.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import math
import os
import sys
from datetime import datetime
import re
import webbrowser
import tkinter.font as tkfont
import tkinter.scrolledtext as scrolledtext

# --- Constants for Conversion (Placeholder) ---
MINUTES_TO_SECONDS = 60
HOURS_TO_SECONDS = 3600
# --- End Constants ---

class PopupManager:
    
# List of popups matching the 'Settings & Info' menu
    # --- MODIFICATION: Renamed "API Settings", added "PID & Tuning", added "Support" ---
    POPUP_LIST = [
        "Temperature Setpoints", "PID & Tuning", "Notification Settings", "API & FG Settings", 
        "Brew Sessions", "System Settings", "Wiring Diagram", "Help", "About",
        "Support this Project"
    ]
    # --- END MODIFICATION ---
    
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.root = ui_instance.root
        self.settings_manager = ui_instance.settings_manager
        self.temp_controller = ui_instance.temp_controller
        self.api_manager = ui_instance.api_manager
        self.notification_manager = ui_instance.notification_manager
        
        # Expose the popup list to the UIBase for the menu creation
        self.ui.popup_list = self.POPUP_LIST
        
        # --- NEW: EULA/Support Popup Variables ---
        self.eula_agreement_var = tk.IntVar(value=0) # 0=unset, 1=agree, 2=disagree
        self.show_eula_checkbox_var = tk.BooleanVar()
        self.support_qr_image = None # To hold the PhotoImage reference
        # --- END NEW ---
        
        # --- NEW: Wiring Diagram Variable ---
        self.wiring_diagram_image = None
        # --- END NEW ---
        
        # --- Internal StringVars for Popups ---
        # Control Mode
        self.amb_hold_var = tk.StringVar()
        self.beer_hold_var = tk.StringVar()
        self.ramp_hold_var = tk.StringVar()
        self.ramp_duration_var = tk.StringVar()
        self.crash_hold_var = tk.StringVar()
        self.control_units_var = tk.StringVar()
        
        # API Settings
        self.api_key_var = tk.StringVar()
        self.api_freq_min_var = tk.StringVar()
        self.fg_check_freq_h_var = tk.StringVar()
        self.fg_tolerance_var = tk.StringVar()
        self.fg_window_size_var = tk.StringVar()
        self.fg_max_outliers_var = tk.StringVar()
        
        # --- NEW: Added for API logging toggle ---
        self.api_logging_var = tk.BooleanVar()
        # --- END NEW ---
        
        # Compressor Protection (Minutes conversion required for saving)
        self.dwell_time_min_var = tk.StringVar()
        self.max_run_time_min_var = tk.StringVar()
        self.fail_safe_shutdown_min_var = tk.StringVar()

        # System Settings (Sensor Assignment)
        self.beer_sensor_var = tk.StringVar()
        self.ambient_sensor_var = tk.StringVar()
        
        # --- MODIFICATION: Added var for PID logging ---
        self.pid_logging_var = tk.BooleanVar()
        # --- END MODIFICATION ---
        
        # --- NEW: PID & Tuning Variables ---
        self.pid_kp_var = tk.StringVar()
        self.pid_ki_var = tk.StringVar()
        self.pid_kd_var = tk.StringVar()
        self.pid_idle_zone_var = tk.StringVar()
        self.ambient_deadband_var = tk.StringVar()
        self.beer_pid_envelope_width_var = tk.StringVar()
        self.ramp_pre_ramp_tolerance_var = tk.StringVar()
        self.ramp_thermo_deadband_var = tk.StringVar()
        self.ramp_pid_landing_zone_var = tk.StringVar()
        self.crash_pid_envelope_width_var = tk.StringVar()
        # --- END NEW ---
        
        # Notification Settings (simplified)
        self.notif_type_var = tk.StringVar() # Notification Method (Email/Text)
        self.notif_freq_h_var = tk.StringVar()
        
        self.notif_content_type_var = tk.StringVar() # Notification Type (Status/FG)
        self.notif_content_options = ["None", "Status", "Final Gravity", "Both"]

        # --- Brew Session Variables (Max 10 inputs) ---
        self.brew_session_vars = [tk.StringVar() for _ in range(10)]
        
        # Status Request Settings (IMAP/SMTP)
        self.req_sender_var = tk.StringVar()
        self.req_rpi_email_var = tk.StringVar()
        self.req_rpi_password_var = tk.StringVar()
        self.req_imap_server_var = tk.StringVar()
        self.req_imap_port_var = tk.StringVar()
        self.req_smtp_server_var = tk.StringVar()
        self.req_smtp_port_var = tk.StringVar()
        
        # --- ADDED FOR SMS POPUP ---
        self.sms_number_var = tk.StringVar()
        self.sms_carrier_gateway_var = tk.StringVar()
        
        # --- MODIFICATION: Split into separate vars ---
        self.push_enable_var = tk.BooleanVar()
        self.req_enable_var = tk.BooleanVar()
        self.push_recipient_var = tk.StringVar()
        # self.req_sender_var is already defined
        # --- END MODIFICATION ---

    def _center_popup(self, popup, popup_width, popup_height):
        """
        Calculates and sets the geometry to center a popup over the main window.
        This function forces the root window to update its geometry first
        and then reveals the popup.
        """
        try:
            # Ensure dimensions are integers
            popup_width = int(popup_width)
            popup_height = int(popup_height)
            
            # --- THIS IS THE FIX ---
            # Force tkinter to process all pending events, including geometry
            # This is stronger than update_idletasks() and ensures
            # the winfo_ commands return the correct, final values.
            self.root.update()
            # --- END FIX ---

            # Get main window's position and size (now reliable)
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_width = self.root.winfo_width()
            root_height = self.root.winfo_height()
            
            # Check for default/un-placed window (e.g., < 100px wide)
            # If so, fall back to screen centering
            if root_width < 100 or root_height < 100:
                print("[_center_popup] Main window not placed, falling back to screen center.")
                root_x = 0
                root_y = 0
                root_width = self.root.winfo_screenwidth()
                root_height = self.root.winfo_screenheight()

            # Calculate center position
            center_x = root_x + (root_width // 2) - (popup_width // 2)
            center_y = root_y + (root_height // 2) - (popup_height // 2)
            
            # Set the geometry
            popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
            
            # --- MODIFICATION: Reveal the popup ---
            popup.deiconify()
            # --- END MODIFICATION ---
        
        except Exception as e:
            # Fallback in case anything fails
            print(f"[ERROR] Failed to center popup: {e}. Using fallback geometry.")
            popup.geometry(f"{popup_width}x{popup_height}+100+100")
            # --- MODIFICATION: Reveal the popup ---
            popup.deiconify()
            # --- END MODIFICATION ---
    
    def _to_float_or_error(self, var_str, is_temp=False):
        """
        Safely converts input string to float. If conversion fails or string is empty, 
        it raises ValueError.
        """
        temp_str = var_str.strip()
        if not temp_str:
            raise ValueError(f"Input cannot be empty.")
            
        # The tkinter input boxes should NOT contain " F" or " C" due to the new layout, 
        # so we revert to strict number conversion.
        try:
            value = float(temp_str)
        except ValueError:
            # This will catch cases where the user enters text or leaves the field partially filled.
            raise ValueError(f"'{temp_str}' is not a valid number.")

        if is_temp:
             is_input_f = self.control_units_var.get() == "F"
             if not is_input_f:
                 # Convert C input to F control unit
                 return (value * 9/5) + 32
        return value

    def _to_int_or_error(self, var_str):
        """
        Safely converts input string to integer. If conversion fails, string is empty,
        or contains a significant decimal part, it raises ValueError.
        We allow integers written as '587' or '587.0' but reject '587.5'.
        """
        temp_str = var_str.strip()
        if not temp_str:
            raise ValueError("Input cannot be empty.")
            
        try:
            value = float(temp_str)
            # Check if the float value is numerically an integer (i.e., difference is zero)
            if value != int(value):
                 raise ValueError("Input must be a whole number (no decimals allowed).")
            
            return int(value)
        except ValueError as e:
            # Catch errors from float() or the custom check above
            raise ValueError(f"'{temp_str}' is not a valid whole number: {e}")
            
    def _open_popup_by_name(self, name):
        # --- MODIFICATION: Reset the menu variable (REMOVED) ---
        # self.ui.settings_menu_var.set("Select...")
        # --- END MODIFICATION ---

        if name == "Temperature Setpoints": self._open_control_mode_settings_popup()
        elif name == "PID & Tuning": self._open_pid_tuning_popup() # <-- NEW
        elif name == "Notification Settings": self._open_notification_settings_popup()
        # --- MODIFICATION: Renamed "API Settings" ---
        elif name == "API & FG Settings": self._open_api_settings_popup()
        # --- END MODIFICATION ---
        elif name == "Brew Sessions": self._open_brew_sessions_popup()
        elif name == "System Settings": self._open_system_settings_popup()
        # --- MODIFICATION: Call new function ---
        elif name == "Wiring Diagram": self._open_wiring_diagram_popup()
        # --- END MODIFICATION ---
        elif name == "Help": self._open_help_popup()
        elif name == "About": self._open_about_popup()
        # --- NEW: Handle Support popup ---
        elif name == "Support this Project": 
            self._open_support_popup(is_launch=False)
        # --- END NEW ---
        else: self.ui.log_system_message(f"Error: Popup '{name}' not implemented.")
        
    # --- CONTROL MODE SETTINGS ---
    def _open_control_mode_settings_popup(self):
        popup = tk.Toplevel(self.root)
        # popup.withdraw() <-- REMOVED FROM HERE
        popup.title("Temperature Setpoints")
        popup.transient(self.root); popup.grab_set()
        
        c_settings = self.settings_manager.get_all_control_settings()
        
        # Convert control unit (F) values back to display units (F or C)
        is_display_f = c_settings['temp_units'] == "F"
        def to_display(temp_f):
            return temp_f if is_display_f else (temp_f - 32) * 5/9

        self.amb_hold_var.set(f"{to_display(c_settings['ambient_hold_f']):.1f}")
        self.beer_hold_var.set(f"{to_display(c_settings['beer_hold_f']):.1f}")
        self.ramp_hold_var.set(f"{to_display(c_settings['ramp_up_hold_f']):.1f}")
        self.ramp_duration_var.set(f"{c_settings['ramp_up_duration_hours']:.1f}")
        self.crash_hold_var.set(f"{to_display(c_settings['fast_crash_hold_f']):.1f}")
        self.control_units_var.set(c_settings['temp_units'])
        
        # --- MODIFICATION: Store the current unit state for the handler ---
        self.popup_display_units = c_settings['temp_units']
        # --- END MODIFICATION ---

        # Build UI
        form_frame = ttk.Frame(popup, padding="15"); 
        form_frame.pack(fill="both", expand=True)
        
        ROW_PADDING = 8
        LABEL_WIDTH = 20
        INPUT_WIDTH = 6

        def add_row(parent, label_text, var, unit_var=None, unit_text=None, is_dropdown=False, options=None):
            row = tk.Frame(parent)
            row.pack(fill='x', pady=(ROW_PADDING, 0))
            
            ttk.Label(row, text=label_text, width=LABEL_WIDTH, anchor='w').pack(side='left')
            
            widget = None # Define widget
            if is_dropdown:
                widget = ttk.Combobox(row, textvariable=var, values=options, state="readonly", width=INPUT_WIDTH)
            else:
                widget = ttk.Entry(row, textvariable=var, width=INPUT_WIDTH)
            widget.pack(side='left', padx=(5, 5))
            
            if unit_var:
                 ttk.Label(row, textvariable=unit_var).pack(side='left')
            elif unit_text:
                 ttk.Label(row, text=unit_text).pack(side='left')
                 
            return widget # Return the widget for binding


        # Units Selector
        units_dropdown = add_row(form_frame, "Temperature Units:", self.control_units_var, is_dropdown=True, options=["F", "C"])
        
        # --- MODIFICATION: Add the trace to the variable for dynamic updates ---
        self.control_units_var.trace_add("write", self._on_units_changed)
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Update popup labels to shorter names ---
        # Ambient Hold
        add_row(form_frame, "Ambient Temp:", self.amb_hold_var, unit_var=self.control_units_var)

        # Beer Hold
        add_row(form_frame, "Beer Temp:", self.beer_hold_var, unit_var=self.control_units_var)

        # Ramp-Up Hold
        add_row(form_frame, "Ramp Temp:", self.ramp_hold_var, unit_var=self.control_units_var)
        
        # Ramp-Up Duration
        add_row(form_frame, "Ramp Duration:", self.ramp_duration_var, unit_text="hours")

        # Fast Crash Hold
        add_row(form_frame, "Crash Temp:", self.crash_hold_var, unit_var=self.control_units_var)
        # --- END MODIFICATION ---
        
        # Buttons
        btns_frame = ttk.Frame(popup, padding="10"); 
        btns_frame.pack(fill="x", side="bottom")
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_control_mode_settings(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # --- THIS IS THE FIX (Part 1) ---
        # 1. Calculate the required size (while window is still visible)
        popup.update_idletasks()
        
        popup_width = 380
        popup_height = popup.winfo_height()
        
        # 2. Hide the popup *after* getting its size
        popup.withdraw()
        # --- END FIX (Part 1) ---
        
        # --- THIS IS THE FIX (Part 2) ---
        # 3. Center and reveal (the helper function now just centers and reveals)
        self._center_popup(popup, popup_width, popup_height)
        # --- END FIX (Part 2) ---

    def _save_control_mode_settings(self, popup):
        try:
            # 1. Retrieve CURRENT (OLD) settings from disk
            old_settings = self.settings_manager.get_all_control_settings()
            
            # All calls to _to_float_or_error are guaranteed to return a float or raise ValueError.
            new_settings = {
                "temp_units": self.control_units_var.get(),
                "ambient_hold_f": self._to_float_or_error(self.amb_hold_var.get(), is_temp=True),
                "beer_hold_f": self._to_float_or_error(self.beer_hold_var.get(), is_temp=True),
                "ramp_up_hold_f": self._to_float_or_error(self.ramp_hold_var.get(), is_temp=True),
                "ramp_up_duration_hours": self._to_float_or_error(self.ramp_duration_var.get(), is_temp=False),
                "fast_crash_hold_f": self._to_float_or_error(self.crash_hold_var.get(), is_temp=True),
            }
            
            # --- Validation Logic (retained from previous fix) ---
            numeric_temps = [v for k, v in new_settings.items() if k != 'temp_units' and 'temp' in k and 'hold' in k]
            if any(v < -100.0 or v > 300.0 for v in numeric_temps):
                 messagebox.showerror("Input Error", "Temperatures seem unrealistic (-100 to 300 F/C).", parent=popup); return
            if new_settings['ramp_up_duration_hours'] <= 0.0 and self.settings_manager.get("control_mode") == "Ramp-Up":
                 messagebox.showerror("Input Error", "Ramp-Up Duration must be positive when Ramp-Up mode is selected.", parent=popup); return
            
            # Save the new settings to disk
            self.settings_manager.save_control_settings(new_settings)
            
            # --- NEW FIX: Generate descriptive log message showing only changes ---
            display_unit = new_settings['temp_units']
            log_parts = []
            
            def log_convert(temp_f):
                # Utility to convert F value to the chosen unit for the log message
                if display_unit == "F":
                    return f"{temp_f:.1f}"
                else:
                    return f"{((temp_f - 32) * 5/9):.1f}"

            # --- MODIFICATION: Use shorter names to match UI ---
            if new_settings["ambient_hold_f"] != old_settings["ambient_hold_f"]:
                 log_parts.append(f"Ambient Temp changed to {log_convert(new_settings['ambient_hold_f'])} {display_unit}.")
                 
            if new_settings["beer_hold_f"] != old_settings["beer_hold_f"]:
                 log_parts.append(f"Beer Temp changed to {log_convert(new_settings['beer_hold_f'])} {display_unit}.")
                 
            if new_settings["ramp_up_hold_f"] != old_settings["ramp_up_hold_f"]:
                 log_parts.append(f"Ramp Temp changed to {log_convert(new_settings['ramp_up_hold_f'])} {display_unit}.")

            if new_settings["ramp_up_duration_hours"] != old_settings["ramp_up_duration_hours"]:
                 log_parts.append(f"Ramp Duration changed to {new_settings['ramp_up_duration_hours']:.1f} hours.")
                 
            if new_settings["fast_crash_hold_f"] != old_settings["fast_crash_hold_f"]:
                 log_parts.append(f"Crash Temp changed to {log_convert(new_settings['fast_crash_hold_f'])} {display_unit}.")
            # --- END MODIFICATION ---
            
            # If the units themselves changed (string comparison)
            if new_settings["temp_units"] != old_settings["temp_units"]:
                 log_parts.append(f"Units changed to {new_settings['temp_units']}.")

            # --- MODIFICATION: Use new title in log message ---
            if log_parts:
                message = "Temperature Setpoints saved. " + " ".join(log_parts)
            else:
                message = "Temperature Setpoints saved. (No changes detected.)"
            # --- END MODIFICATION ---

            self.ui.log_system_message(message)
            # ------------------------------------------------------------------
            
            # Always trigger UI refresh after saving setpoints
            if hasattr(self, 'refresh_setpoint_display'):
                self.ui.refresh_setpoint_display() 
            
            popup.destroy()
            self.root.update() # <-- FIX: Force UI loop to run
            
        except ValueError as e:
            # This block now correctly catches all invalid numeric input errors
            messagebox.showerror("Input Error", f"Please enter valid numbers for all fields. ({e})", parent=popup)
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=popup)
             
    def _on_units_changed(self, *args):
        """Called when the F/C combobox is changed in the setpoints popup."""
        try:
            new_unit = self.control_units_var.get()
            # popup_display_units was set when the popup was opened
            old_unit = self.popup_display_units
            
            if new_unit == old_unit:
                return # No change

            vars_to_convert = [
                self.amb_hold_var,
                self.beer_hold_var,
                self.ramp_hold_var,
                self.crash_hold_var
            ]

            for var in vars_to_convert:
                try:
                    current_val = float(var.get())
                    if new_unit == 'F':
                        # Convert C to F
                        new_val = (current_val * 9/5) + 32
                    else:
                        # Convert F to C
                        new_val = (current_val - 32) * 5/9
                    
                    var.set(f"{new_val:.1f}")
                except ValueError:
                    # Ignore if the field has invalid text (e.g., "--" or "abc")
                    pass
            
            # Update the state for the next conversion
            self.popup_display_units = new_unit
            
        except Exception as e:
            print(f"Error converting units: {e}")

    # --- NOTIFICATION SETTINGS (Push & Request) ---
    def _open_notification_settings_popup(self):
        # NOTE: Using the combined SMTP configuration for simplicity
        
        popup = tk.Toplevel(self.root)
        # popup.withdraw() <-- REMOVED FROM HERE
        popup.title("Notification Settings"); popup.transient(self.root); popup.grab_set()
        
        push_settings = self.settings_manager.get_all_smtp_settings()
        req_settings = self.settings_manager.get_all_status_request_settings()
        
        # --- Load Vars from settings ---
        
        # --- MODIFICATION: Load Push Notification vars ---
        freq_h = self.settings_manager.get("frequency_hours", 24)
        if freq_h == 0 or freq_h == "None":
            self.push_enable_var.set(False)
            self.notif_freq_h_var.set("Every 24 hours") # Default to 24
        else:
            self.push_enable_var.set(True)
            self.notif_freq_h_var.set(f"Every {freq_h} hours")
        
        self.push_recipient_var.set(push_settings.get("email_recipient", ""))
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Load Email Control vars ---
        self.req_enable_var.set(req_settings.get("enable_status_request", False))
        self.req_sender_var.set(req_settings.get("authorized_sender", ""))
        # --- END MODIFICATION ---
        
        # RPi Email Configuration
        self.req_rpi_email_var.set(push_settings.get("server_email", ""))
        self.req_rpi_password_var.set(push_settings.get("server_password", ""))
        self.req_imap_server_var.set(req_settings.get("imap_server", ""))
        self.req_imap_port_var.set(str(req_settings.get("imap_port", 993)))
        self.req_smtp_server_var.set(push_settings.get("smtp_server", ""))
        self.req_smtp_port_var.set(str(push_settings.get("smtp_port", 587)))

        # --- SMS Vars (Loaded but not used in UI) ---
        self.sms_number_var.set(push_settings.get("sms_number", ""))
        self.sms_carrier_gateway_var.set(push_settings.get("sms_carrier_gateway", ""))
        
        # Helper for aligned rows
        def add_row(parent_frame, label_text, string_var, show_char=None, notes=None, is_dropdown=False, options=None, unit_text=None):
            row_frame = ttk.Frame(parent_frame); row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=label_text, width=30, anchor='w').pack(side="left", padx=(5, 5))
            
            widget = None # Define widget variable
            
            if is_dropdown:
                widget = ttk.Combobox(row_frame, textvariable=string_var, values=options, state="readonly", width=30)
            else:
                widget = ttk.Entry(row_frame, textvariable=string_var, width=30, show=show_char)
            
            widget.pack(side="left", fill="x", expand=True) 
            
            if unit_text:
                 ttk.Label(row_frame, text=unit_text).pack(side='right', padx=(5, 0))
            
            if notes:
                notes_label = ttk.Label(parent_frame, text=notes, font=('TkDefaultFont', 8, 'italic'), wraplength=550, justify='left')
                notes_label.pack(fill="x", padx=(5, 5), pady=(0, 5), anchor="w") 
                
            return widget # Return the created widget (Entry or Combobox)

        form_frame = ttk.Frame(popup, padding="10"); form_frame.pack(expand=True, fill="both")

        # --- 1. Push Notifications (Section 1) ---
        section1_frame = ttk.Frame(form_frame)
        section1_frame.pack(fill="x", anchor="w", pady=(0, 10))
        
        ttk.Label(section1_frame, text="Push Notifications", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.push_enable_check = ttk.Checkbutton(
            section1_frame, 
            text="Enable Push Notifications", 
            variable=self.push_enable_var
        )
        self.push_enable_check.pack(anchor='w', padx=5, pady=(5, 0))
        
        push_notes = (
            "When enabled, the app's current status and settings are emailed to the specified "
            "Recipient on the selected schedule. It is recommended that you use a dedicated "
            "email account set up exclusively for this app, and enter that account's "
            "configuration settings below under 'RPi Email Configuration'."
        )
        ttk.Label(section1_frame, text=push_notes, font=('TkDefaultFont', 8, 'italic'), wraplength=550, justify='left').pack(anchor='w', fill='x', padx=(25, 5), pady=(0, 5))
        
        # --- MODIFICATION: Removed "None" from options ---
        freq_options = ["Every 1 hour", "Every 2 hours", "Every 4 hours", "Every 8 hours", "Every 12 hours", "Every 24 hours"]
        self.notif_freq_dropdown = add_row(section1_frame, "Notification Frequency:", self.notif_freq_h_var, unit_text=None, is_dropdown=True, options=freq_options)
        
        self.push_recipient_entry = add_row(section1_frame, "Recipient Email:", self.push_recipient_var, notes=None)


        # --- 2. Email Control (Section 2) ---
        section2_frame = ttk.Frame(form_frame)
        section2_frame.pack(fill="x", anchor="w", pady=(0, 10))

        ttk.Label(section2_frame, text="Email Control (Status & Commands)", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        self.req_enable_check = ttk.Checkbutton(
            section2_frame, 
            text="Enable Email Control (Status & Commands)", 
            variable=self.req_enable_var
        )
        self.req_enable_check.pack(anchor='w', padx=5, pady=(5, 0))
        
        # --- MODIFICATION: Use the new user-approved text ---
        warning_text = (
            "WARNING: When enabled, the app checks the 'RPi Email Configuration' account for new messages "
            "from the Authorized Sender. If new messages exist, the app marks them as 'read', and "
            "processes them for 'Status' or 'Command' actions. Only enable this feature if you are using "
            "a dedicated email account set up exclusively for this app, and enter that email account's "
            "configuration settings below under 'RPi Email Configuration'."
        )
        # --- END MODIFICATION ---
        
        ttk.Label(section2_frame, text=warning_text, font=('TkDefaultFont', 8, 'italic'), wraplength=550, justify='left').pack(anchor='w', fill='x', padx=(25, 5), pady=(0, 5))

        self.req_sender_entry = add_row(section2_frame, "Authorized Sender:", self.req_sender_var, notes=None)


        # --- 3. RPi Email Configuration (Section 3) ---
        section3_frame = ttk.Frame(form_frame)
        section3_frame.pack(fill="x", pady=(10, 5), anchor="w")
        
        ttk.Label(section3_frame, text="RPi Email Configuration", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        # Store widget references for enable/disable
        self.rpi_email_entry = add_row(section3_frame, "RPi email address:", self.req_rpi_email_var)
        self.rpi_password_entry = add_row(section3_frame, "RPi email password (2FA pw):", self.req_rpi_password_var, show_char="*", notes=None)
        self.imap_server_entry = add_row(section3_frame, "IMAP (incoming) server:", self.req_imap_server_var)
        self.imap_port_entry = add_row(section3_frame, "IMAP (incoming) port:", self.req_imap_port_var)
        self.smtp_server_entry = add_row(section3_frame, "SMTP (outgoing) server:", self.req_smtp_server_var)
        self.smtp_port_entry = add_row(section3_frame, "SMTP (outgoing) port:", self.req_smtp_port_var)


        # --- Buttons ---
        btns_frame = ttk.Frame(popup, padding="10"); btns_frame.pack(fill="x", side="bottom")
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_notification_settings(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # --- MODIFICATION: Add traces to both checkboxes ---
        self.push_enable_var.trace_add("write", self._toggle_email_fields_state)
        self.req_enable_var.trace_add("write", self._toggle_email_fields_state)
        
        # Call toggle function to set initial state
        self._toggle_email_fields_state()
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 600
        popup_height = popup.winfo_height()
        popup.withdraw() # Hide window
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
        
    def _save_notification_settings(self, popup):
        try:
            # 1. Input Parsing and Validation
            push_port_str = self.req_smtp_port_var.get()
            imap_port_str = self.req_imap_port_var.get()
            
            # --- MODIFICATION: Only validate ports if they are enabled ---
            push_enabled = self.push_enable_var.get()
            req_enabled = self.req_enable_var.get()
            
            push_port = 0
            imap_port = 0

            # If any service is enabled, we need the SMTP ports
            if push_enabled or req_enabled:
                push_port = self._to_int_or_error(push_port_str)
                if push_port <= 0 or push_port > 65535:
                     messagebox.showerror("Input Error", "SMTP Port must be 1-65535.", parent=popup); return
            
            # Only if Email Control is enabled do we need the IMAP port
            if req_enabled:
                imap_port = self._to_int_or_error(imap_port_str)
                if imap_port <= 0 or imap_port > 65535:
                     messagebox.showerror("Input Error", "IMAP Port must be 1-65535.", parent=popup); return
            # --- END MODIFICATION ---

            # --- MODIFICATION: Get new frequency logic ---
            notif_freq_h = 0
            freq_str = ""
            if push_enabled:
                freq_str = self.notif_freq_h_var.get()
                notif_freq_h = self._to_int_or_error(freq_str.split()[1]) # e.g., "Every 4 hours" -> "4"
            # --- END MODIFICATION ---

            # Define helper to get old values
            def _get_old_val(key, default=""):
                if key == "frequency_hours":
                    return int(self.settings_manager.get(key, default=24))
                return self.settings_manager.get(key, default=default)

            # --- OLD VALUES FOR COMPARISON ---
            old_freq = _get_old_val("frequency_hours", default=24)
            old_smtp_settings = self.settings_manager.get_all_smtp_settings()
            old_req_settings = self.settings_manager.get_all_status_request_settings()
            
            # 2. Save All Settings
            
            # A. Save Notification Settings (Frequency only)
            self.settings_manager.set("frequency_hours", notif_freq_h)
            
            # B. Prepare & Save SMTP Settings
            new_smtp_settings = {
                "server_email": self.req_rpi_email_var.get().strip(),
                "server_password": self.req_rpi_password_var.get(),
                "email_recipient": self.push_recipient_var.get().strip(), # <-- Use new push var
                "smtp_server": self.req_smtp_server_var.get().strip(),
                "smtp_port": push_port if (push_enabled or req_enabled) else old_smtp_settings.get('smtp_port', 587),
            }
            self.settings_manager.settings['smtp_settings'].update(new_smtp_settings) 

            # C. Prepare & Save Status Request Settings
            new_req_settings = {
                "enable_status_request": self.req_enable_var.get(),
                "authorized_sender": self.req_sender_var.get().strip(), # <-- Use req sender var
                "rpi_email_address": self.req_rpi_email_var.get().strip(),
                "rpi_email_password": self.req_rpi_password_var.get(),
                "imap_server": self.req_imap_server_var.get().strip(),
                "imap_port": imap_port if req_enabled else old_req_settings.get('imap_port', 993),
            }
            self.settings_manager.save_status_request_settings(new_req_settings)
            
            # D. Save all changes to disk
            self.settings_manager._save_all_settings()
            
            # 3. Generate Descriptive Log Message
            log_parts = []
            
            # --- MODIFICATION: Check for Push Notification change (ON/OFF) ---
            if push_enabled and (old_freq == 0 or old_freq == "None"):
                log_parts.append(f"Push Notifications enabled (Frequency: {freq_str}).")
            elif not push_enabled and (old_freq > 0 and old_freq != "None"):
                log_parts.append("Push Notifications disabled.")
            elif push_enabled and notif_freq_h != old_freq:
                 log_parts.append(f"Push Frequency changed to {freq_str}.")
            
            if push_enabled and new_smtp_settings['email_recipient'] != old_smtp_settings['email_recipient']:
                log_parts.append("Push Recipient updated.")
            # --- END MODIFICATION ---
            
            # --- Check for Email Control change ---
            new_enable_state = new_req_settings["enable_status_request"]
            old_enable_state = old_req_settings.get("enable_status_request", False)
            if new_enable_state != old_enable_state:
                log_parts.append(f"Email Control {'enabled' if new_enable_state else 'disabled'}.")
                
            if new_enable_state and new_req_settings['authorized_sender'] != old_req_settings['authorized_sender']:
                log_parts.append("Authorized Sender updated.")
            
            # --- Check RPi Config fields (only if one of the services is enabled) ---
            if push_enabled or req_enabled:
                if new_smtp_settings['server_email'] != old_smtp_settings['server_email']:
                    log_parts.append("RPi Email Address updated.")
                if new_smtp_settings['smtp_port'] != old_smtp_settings['smtp_port']:
                     log_parts.append(f"SMTP Port set to {new_smtp_settings['smtp_port']}.")
            
            if req_enabled:
                if new_req_settings['imap_port'] != old_req_settings['imap_port']:
                     log_parts.append(f"IMAP Port set to {new_req_settings['imap_port']}.")
            
            # Construct the final message
            if log_parts:
                message = "Notification settings saved. " + " ".join(log_parts)
            else:
                message = "Notification settings saved. (No changes detected.)"

            # Pass old and new freq to the scheduler
            self.notification_manager.force_reschedule(old_freq, notif_freq_h)
            
            self.ui.log_system_message(message)
            
            popup.destroy()
            self.root.update()
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Port or frequency must be valid whole numbers. ({e})", parent=popup)
            
    def _toggle_email_fields_state(self, *args):
        """
        Enables or disables all fields based on the state of the two master checkboxes.
        """
        try:
            push_enabled = self.push_enable_var.get()
            req_enabled = self.req_enable_var.get()

            # --- 1. Toggle Push Notification Section ---
            push_section_state = 'normal' if push_enabled else 'disabled'
            if hasattr(self, 'notif_freq_dropdown'):
                self.notif_freq_dropdown.config(state=push_section_state)
            if hasattr(self, 'push_recipient_entry'):
                self.push_recipient_entry.config(state=push_section_state)

            # --- 2. Toggle Email Control Section ---
            req_section_state = 'normal' if req_enabled else 'disabled'
            if hasattr(self, 'req_sender_entry'):
                self.req_sender_entry.config(state=req_section_state)

            # --- 3. Toggle RPi Email Configuration Section (3-state logic) ---
            smtp_state = 'disabled'
            imap_state = 'disabled'

            if req_enabled:
                # If Email Control is ON, all 6 fields are enabled
                smtp_state = 'normal'
                imap_state = 'normal'
            elif push_enabled:
                # If Push is ON (and Control is OFF), only SMTP fields are enabled
                smtp_state = 'normal'
                imap_state = 'disabled'
            # else: (both OFF) all 6 fields remain 'disabled'

            # Apply SMTP states (4 fields)
            if hasattr(self, 'rpi_email_entry'):
                self.rpi_email_entry.config(state=smtp_state)
            if hasattr(self, 'rpi_password_entry'):
                self.rpi_password_entry.config(state=smtp_state)
            if hasattr(self, 'smtp_server_entry'):
                self.smtp_server_entry.config(state=smtp_state)
            if hasattr(self, 'smtp_port_entry'):
                self.smtp_port_entry.config(state=smtp_state)
                
            # Apply IMAP states (2 fields)
            if hasattr(self, 'imap_server_entry'):
                self.imap_server_entry.config(state=imap_state)
            if hasattr(self, 'imap_port_entry'):
                self.imap_port_entry.config(state=imap_state)

        except Exception as e:
            # This can fail if the widgets haven't been created yet
            print(f"UI Info: State toggle failed (widget not ready?): {e}")

    # --- API SETTINGS ---
    def _open_api_settings_popup(self):
        # --- MODIFICATION: Removed initial geometry ---
        popup = tk.Toplevel(self.root); popup.title("API & FG Settings"); popup.transient(self.root); popup.grab_set()
        # --- END MODIFICATION ---
        
        api_settings = self.settings_manager.get_all_api_settings()
        self.api_key_var.set(api_settings['api_key'])
        self.api_freq_min_var.set(str(int(api_settings['api_call_frequency_s'] / 60)))
        
        # --- NEW: Load API logging var ---
        self.api_logging_var.set(api_settings.get("api_logging_enabled", False))
        # --- END NEW ---
        
        self.fg_check_freq_h_var.set(str(api_settings['fg_check_frequency_h']))
        self.fg_tolerance_var.set(str(api_settings['tolerance']))
        self.fg_window_size_var.set(str(api_settings['window_size']))
        self.fg_max_outliers_var.set(str(api_settings['max_outliers']))
        
        form_frame = ttk.Frame(popup, padding="15"); form_frame.pack(fill="both", expand=True)
        
        # --- Adjusted add_api_row helper for required padding/justification ---
        def add_api_row(parent, label, var, unit=None, notes=None, is_key=False):
            row_frame = ttk.Frame(parent); row_frame.pack(fill="x", pady=5)
            
            # Label (always left)
            ttk.Label(row_frame, text=label, width=25, anchor='w').pack(side='left')
            
            # Input Widget
            # --- MODIFICATION: Increased API Key field width from 45 to 60 ---
            entry = ttk.Entry(row_frame, textvariable=var, width=(60 if is_key else 15))
            entry.pack(side='left', padx=(5, 5), fill=('x' if is_key else 'none'), expand=is_key)
            
            if unit: ttk.Label(row_frame, text=unit).pack(side='left')
            
            if notes: 
                 notes_label = ttk.Label(parent, text=notes, font=('TkDefaultFont', 8, 'italic'), wraplength=400)
                 # FIX 3: Left-justify help text below the left column
                 notes_label.pack(anchor='w', padx=(5, 5)) 
        
        # FIX 1 & 2: Removed 'BrewersFriend' and passed is_key=True for wide field
        add_api_row(form_frame, "API Key:", self.api_key_var, is_key=True)
        
        add_api_row(form_frame, "API Call Frequency:", self.api_freq_min_var, unit="minutes", notes="Data refresh rate for OG/SG/Temp.")

        # --- NEW: Add Checkbox for API Logging ---
        ttk.Checkbutton(form_frame, 
                        text="Enable API call logging to System Messages", 
                        variable=self.api_logging_var).pack(anchor='w', padx=5, pady=(5, 0))
        # --- END NEW ---

        ttk.Separator(form_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(form_frame, text="Final Gravity Calculation Parameters", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))

        # Fixes 3 applied to all notes via the helper change
        add_api_row(form_frame, "FG Check Frequency:", self.fg_check_freq_h_var, unit="hours", notes="How often the scheduler runs the FG stability analysis.")
        add_api_row(form_frame, "SG Range Tolerance:", self.fg_tolerance_var, notes="Max allowed change in SG (e.g., 0.0005).")
        add_api_row(form_frame, "SG Records Window:", self.fg_window_size_var, notes="Number of consecutive readings to check (e.g., 450).")
        add_api_row(form_frame, "Max SG Outliers:", self.fg_max_outliers_var, notes="Maximum readings outside tolerance allowed in window.")
        
        btns_frame = ttk.Frame(popup, padding="10"); btns_frame.pack(fill="x", side="bottom")
        
        # --- MODIFICATION: Updated button text ---
        ttk.Button(btns_frame, text="Custom API Services Help", command=self._open_api_help_popup).pack(side="left", padx=5)
        # --- END MODIFICATION ---
        
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_api_settings(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 600
        popup_height = popup.winfo_height()
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
        
    def _save_api_settings(self, popup):
        try:
            # 1. Validation and New Settings Collection
            # Note: _to_float_or_error is suitable for simple float/int validation when is_temp=False
            
            new_api_key = self.api_key_var.get().strip()
            new_api_freq_s = int(self._to_float_or_error(self.api_freq_min_var.get()) * 60)
            
            # --- NEW: Get API logging state ---
            new_api_logging_enabled = self.api_logging_var.get()
            # --- END NEW ---
            
            new_fg_freq_h = self._to_int_or_error(self.fg_check_freq_h_var.get())
            new_tolerance = self._to_float_or_error(self.fg_tolerance_var.get())
            new_window_size = self._to_int_or_error(self.fg_window_size_var.get())
            new_max_outliers = self._to_int_or_error(self.fg_max_outliers_var.get())

            if new_api_freq_s <= 0 or new_fg_freq_h <= 0:
                 messagebox.showerror("Input Error", "Frequencies must be positive.", parent=popup); return
            if new_window_size <= 0:
                 messagebox.showerror("Input Error", "Window Size must be positive.", parent=popup); return

            new_settings = {
                "api_key": new_api_key,
                "api_call_frequency_s": new_api_freq_s,
                "api_logging_enabled": new_api_logging_enabled, # <-- NEW
                "fg_check_frequency_h": new_fg_freq_h,
                "tolerance": new_tolerance,
                "window_size": new_window_size,
                "max_outliers": new_max_outliers,
            }

            # 2. Retrieve Old Settings for Comparison
            old_settings = self.settings_manager.get_all_api_settings()
            
            # 3. Perform Save
            self.settings_manager.save_api_settings(new_settings)

            # 4. Generate Granular Log Message
            log_parts = []
            
            # API Key (Log if key length changes or is initially set)
            if new_api_key != old_settings['api_key'] and new_api_key != "":
                 log_parts.append("API Key updated.")
            elif new_api_key == "" and old_settings['api_key'] != "":
                 log_parts.append("API Key cleared.")

            # API Frequency
            if new_api_freq_s != old_settings['api_call_frequency_s']:
                log_parts.append(f"API Call Freq. set to {new_api_freq_s // 60} min.")

            # --- NEW: Check for API logging change ---
            old_api_logging_enabled = old_settings.get("api_logging_enabled", False)
            if new_api_logging_enabled != old_api_logging_enabled:
                log_parts.append(f"API Call Logging {'enabled' if new_api_logging_enabled else 'disabled'}.")
            # --- END NEW ---

            # FG Check Frequency
            if new_fg_freq_h != old_settings['fg_check_frequency_h']:
                log_parts.append(f"FG Check Freq. set to {new_fg_freq_h} hours.")
                
            # SG Range Tolerance
            if new_tolerance != old_settings['tolerance']:
                log_parts.append(f"Tolerance set to {new_tolerance}.")

            # SG Records Window
            if new_window_size != old_settings['window_size']:
                log_parts.append(f"Window Size set to {new_window_size}.")

            # Max SG Outliers
            if new_max_outliers != old_settings['max_outliers']:
                log_parts.append(f"Max Outliers set to {new_max_outliers}.")

            # Construct the final message
            if log_parts:
                message = "API settings saved. " + " ".join(log_parts)
            else:
                message = "API settings saved. (No changes detected.)"

            self.ui.log_system_message(message)
            
            # --- THIS IS THE FIX ---
            if self.notification_manager:
                self.notification_manager.reset_api_timers()
            # --- END OF THE FIX ---
            
            popup.destroy()
            self.root.update() # <-- FIX: Force UI loop to run
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid positive numbers for all fields. ({e})", parent=popup)

    # --- SYSTEM SETTINGS ---
    def _open_system_settings_popup(self):
        # --- MODIFICATION: Removed initial geometry ---
        popup = tk.Toplevel(self.root); popup.title("System Settings"); popup.transient(self.root); popup.grab_set() 
        # --- END MODIFICATION ---
        
        comp_settings = self.settings_manager.get_all_compressor_protection_settings()
        sys_settings = self.settings_manager.get_system_settings()

        # Load values (convert seconds to minutes)
        self.dwell_time_min_var.set(str(int(comp_settings['cooling_dwell_time_s'] / MINUTES_TO_SECONDS)))
        self.max_run_time_min_var.set(str(int(comp_settings['max_cool_runtime_s'] / MINUTES_TO_SECONDS)))
        self.fail_safe_shutdown_min_var.set(str(int(comp_settings['fail_safe_shutdown_time_s'] / MINUTES_TO_SECONDS)))
        
        self.beer_sensor_var.set(sys_settings.get("ds18b20_beer_sensor", "unassigned"))
        self.ambient_sensor_var.set(sys_settings.get("ds18b20_ambient_sensor", "unassigned"))
        
        # --- MODIFICATION: PID logging var is loaded, but not used in this UI ---
        self.pid_logging_var.set(sys_settings.get("pid_logging_enabled", False))
        # --- END MODIFICATION ---

        form_frame = ttk.Frame(popup, padding="15"); form_frame.pack(fill="both", expand=True)

        def add_sys_row(parent, label, var, unit=None, is_dropdown=False, options=None):
            row_frame = ttk.Frame(parent); row_frame.pack(fill="x", pady=5)
            ttk.Label(row_frame, text=label, width=30, anchor='w').pack(side='left')
            if is_dropdown:
                 widget = ttk.Combobox(row_frame, textvariable=var, values=options, state="readonly", width=15)
            else:
                 widget = ttk.Entry(row_frame, textvariable=var, width=15)
            widget.pack(side='left', padx=(5, 5))
            if unit: ttk.Label(row_frame, text=unit).pack(side='left')
        
        # --- Compressor Protection ---
        ttk.Label(form_frame, text="Compressor Protection (Input in Minutes)", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        add_sys_row(form_frame, "Dwell Time (Min On/Off Cycle):", self.dwell_time_min_var, unit="minutes")
        add_sys_row(form_frame, "Max Run Time:", self.max_run_time_min_var, unit="minutes")
        add_sys_row(form_frame, "Fail-Safe Shutdown Time:", self.fail_safe_shutdown_min_var, unit="minutes")
        
        # --- Temperature Sensors ---
        ttk.Separator(form_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(form_frame, text="Temperature Sensor Assignment", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        available_sensors = self.temp_controller.detect_ds18b20_sensors()
        sensor_options = ["unassigned"] + (available_sensors if available_sensors else ["No sensors found"])

        add_sys_row(form_frame, "Beer Temp Sensor ID:", self.beer_sensor_var, is_dropdown=True, options=sensor_options)
        add_sys_row(form_frame, "Ambient Temp Sensor ID:", self.ambient_sensor_var, is_dropdown=True, options=sensor_options)
        
        # --- MODIFICATION: Removed Debugging Section & Checkbox ---
        # ttk.Separator(form_frame, orient='horizontal').pack(fill='x', pady=10)
        # ttk.Label(form_frame, text="Debugging", ...).pack(...)
        # ttk.Checkbutton(form_frame, ...).pack(...)
        # --- END MODIFICATION ---
        
        btns_frame = ttk.Frame(popup, padding="10"); btns_frame.pack(fill="x", side="bottom")
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_system_settings(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 500
        popup_height = popup.winfo_height()
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
        
    def _save_system_settings(self, popup):
        try:
            # --- FIX: Get OLD settings *before* saving new ones ---
            old_comp_settings = self.settings_manager.get_all_compressor_protection_settings()
            old_beer_sensor = self.settings_manager.get("ds18b20_beer_sensor", "unassigned")
            old_amb_sensor = self.settings_manager.get("ds18b20_ambient_sensor", "unassigned")
            # --- MODIFICATION: Get old PID logging state (REMOVED) ---
            # old_pid_logging_state = self.settings_manager.get("pid_logging_enabled", False)
            # --- END MODIFICATION ---

            # 1. Save Compressor Protection (convert minutes to seconds)
            new_dwell_min = int(self._to_float_or_error(self.dwell_time_min_var.get()))
            new_max_run_min = int(self._to_float_or_error(self.max_run_time_min_var.get()))
            new_fail_safe_min = int(self._to_float_or_error(self.fail_safe_shutdown_min_var.get()))
            
            comp_settings = {
                "cooling_dwell_time_s": new_dwell_min * MINUTES_TO_SECONDS,
                "max_cool_runtime_s": new_max_run_min * MINUTES_TO_SECONDS,
                "fail_safe_shutdown_time_s": new_fail_safe_min * MINUTES_TO_SECONDS,
            }
            if any(v <= 0 for v in comp_settings.values()):
                 messagebox.showerror("Input Error", "All protection times must be positive.", parent=popup); return

            self.settings_manager.save_compressor_protection_settings(comp_settings)

            # --- 2. Sensor Assignment Logic ---
            new_beer_sensor = self.beer_sensor_var.get()
            new_amb_sensor = self.ambient_sensor_var.get()
            
            self.settings_manager.set("ds18b20_beer_sensor", new_beer_sensor)
            self.settings_manager.set("ds18b20_ambient_sensor", new_amb_sensor)
            
            # --- MODIFICATION: Save PID logging state (REMOVED) ---
            # new_pid_logging_state = self.pid_logging_var.get()
            # self.settings_manager.set("pid_logging_enabled", new_pid_logging_state)
            # --- END MODIFICATION ---
            
            # --- 3. Generate "Robust" System Message ---
            log_parts = []

            # Check Compressor settings
            old_dwell_min = int(old_comp_settings['cooling_dwell_time_s'] / MINUTES_TO_SECONDS)
            if new_dwell_min != old_dwell_min:
                log_parts.append(f"Dwell Time changed to {new_dwell_min} min.")

            old_max_run_min = int(old_comp_settings['max_cool_runtime_s'] / MINUTES_TO_SECONDS)
            if new_max_run_min != old_max_run_min:
                log_parts.append(f"Max Run Time changed to {new_max_run_min} min.")
            
            old_fail_safe_min = int(old_comp_settings['fail_safe_shutdown_time_s'] / MINUTES_TO_SECONDS)
            if new_fail_safe_min != old_fail_safe_min:
                log_parts.append(f"Fail-Safe Time changed to {new_fail_safe_min} min.")

            # Check for Beer Sensor change/assignment
            if new_beer_sensor != old_beer_sensor and new_beer_sensor != 'unassigned':
                log_parts.append("Beer sensor assigned.")
            elif new_beer_sensor == 'unassigned' and old_beer_sensor != 'unassigned':
                 log_parts.append("Beer sensor unassigned.")

            # Check for Ambient Sensor change/assignment
            if new_amb_sensor != old_amb_sensor and new_amb_sensor != 'unassigned':
                log_parts.append("Ambient sensor assigned.")
            elif new_amb_sensor == 'unassigned' and old_amb_sensor != 'unassigned':
                 log_parts.append("Ambient sensor unassigned.")
            
            # --- MODIFICATION: Check for PID logging change (REMOVED) ---
            # if new_pid_logging_state != old_pid_logging_state:
            #    log_parts.append(f"PID Logging {'enabled' if new_pid_logging_state else 'disabled'}.")
            # --- END MODIFICATION ---
            
            if log_parts:
                message = "System settings saved. " + " ".join(log_parts)
            else:
                message = "System settings saved. (No changes detected.)" 
            
            self.ui.log_system_message(message)
            # ---------------------------------------------------------------------------------
            
            popup.destroy()
            self.root.update() # <-- FIX: Force UI loop to run
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid whole numbers for times. ({e})", parent=popup)
            
    def _open_brew_sessions_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Brew Sessions")
        # --- MODIFICATION: Removed initial geometry ---
        popup.transient(self.root); popup.grab_set()

        form_frame = ttk.Frame(popup, padding="15"); 
        form_frame.pack(fill="both", expand=True)

        # Retrieve current titles (a list of strings)
        current_sessions = self.settings_manager.brew_sessions
        
        ttk.Label(form_frame, text="Used when API mode is OFF or API brew session data is unavailable or invalid.", 
                  font=('TkDefaultFont', 9, 'italic')).grid(row=0, column=0, columnspan=1, sticky='w', pady=(0, 10))

        # Populate fields and store references
        self.brew_input_widgets = []
        for i in range(10):
            # Load existing title or default empty string
            session_title = current_sessions[i] if i < len(current_sessions) else ""
            self.brew_session_vars[i].set(session_title)
            
            # Entry Widget (Now only a single column for input fields)
            entry = ttk.Entry(form_frame, textvariable=self.brew_session_vars[i], width=50)
            entry.grid(row=i+1, column=0, sticky='ew', padx=5, pady=2)
            self.brew_input_widgets.append(entry)

        form_frame.grid_columnconfigure(0, weight=1) # Only one column needs to expand

        # Buttons
        btns_frame = ttk.Frame(popup, padding="10"); 
        btns_frame.pack(fill="x", side="bottom")
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_brew_sessions(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 550
        popup_height = popup.winfo_height()
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
    
    def _save_brew_sessions(self, popup):
        try:
            # 1. Collect New Titles
            new_sessions = [var.get().strip() for var in self.brew_session_vars]
            
            # 2. Retrieve Old Titles
            old_sessions = self.settings_manager.brew_sessions
            
            # 3. Perform Save
            self.settings_manager.save_brew_sessions(new_sessions)
            
            # 4. Generate Granular Log Message (Logic retained from previous fix)
            log_parts = []
            
            # Pad old list to length 10 for comparison
            padded_old_sessions = old_sessions + [""] * (10 - len(old_sessions))

            for i in range(10):
                old_title = padded_old_sessions[i]
                new_title = new_sessions[i]
                
                # Compare. If an entry title changed (or was cleared/set)
                if old_title != new_title:
                    if new_title:
                        log_parts.append(f"Recipe {i+1} set to '{new_title}'.")
                    else:
                        log_parts.append(f"Recipe {i+1} cleared.")

            # Construct the final message
            if log_parts:
                message = "Brew Sessions settings saved. " + " ".join(log_parts)
            else:
                message = "Brew Sessions settings saved. (No changes detected.)"

            self.ui.log_system_message(message)
            
            # --- FIX: Repopulate the main UI dropdown immediately after saving ---
            if hasattr(self.ui, '_populate_brew_session_dropdown'):
                self.ui._populate_brew_session_dropdown()
            # ---------------------------------------------------------------------
            
            popup.destroy()
            self.root.update() # <-- FIX: Force UI loop to run
            
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=popup)

    # --- STUB POPUPS ---
    
    def _load_wiring_diagram_image(self):
        """Loads the wiring.gif image and stores it."""
        if self.wiring_diagram_image:
            return # Already loaded
            
        try:
            # --- MODIFICATION ---
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Path is now src/assets/wiring.gif
            image_path = os.path.join(base_dir, "assets", "wiring.gif")
            # --- END MODIFICATION ---
            
            # Use tk.PhotoImage directly, which supports GIF natively
            self.wiring_diagram_image = tk.PhotoImage(file=image_path)
            
        except FileNotFoundError:
            self.ui.log_system_message("Error: wiring.gif image not found.")
            self.wiring_diagram_image = None # Ensure it's None
        except tk.TclError as e:
            # This is the error tk.PhotoImage throws for bad files
            self.ui.log_system_message(f"Error loading wiring.gif (is it a valid GIF?): {e}")
            self.wiring_diagram_image = None
        except Exception as e:
            self.ui.log_system_message(f"Error loading wiring diagram image: {e}")
            self.wiring_diagram_image = None

    def _open_wiring_diagram_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Wiring Diagram")
        popup.transient(self.root); popup.grab_set()

        # Load the image
        self._load_wiring_diagram_image()

        # Main frame with 15px padding
        main_frame = ttk.Frame(popup, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- Image container frame ---
        # Set this frame to 690x400 (which is 720 - 15 - 15 padding)
        image_frame = ttk.Frame(main_frame, width=690, height=400, relief="sunken", borderwidth=1)
        image_frame.pack(fill="both", expand=True)
        
        # This prevents the frame from shrinking to fit the label if the image is small
        image_frame.pack_propagate(False) 

        if self.wiring_diagram_image:
            image_label = ttk.Label(image_frame, image=self.wiring_diagram_image)
            # Center the label (and thus the image) inside the 690x400 frame
            image_label.pack(expand=True) 
        else:
            placeholder_text = "[ wiring.gif not found ]\n\nPlace wiring.gif in the same directory as the application."
            placeholder_label = ttk.Label(image_frame, text=placeholder_text, anchor="center", justify="center")
            placeholder_label.pack(expand=True)

        # --- Button frame ---
        btns_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0)) # Padding on top
        btns_frame.pack(fill="x", side="bottom")
        ttk.Button(btns_frame, text="Close", command=popup.destroy).pack(side="right")

        # --- Finalize sizing and centering ---
        popup.update_idletasks()
        
        popup_width = 720 # Force 720 width
        popup_height = popup.winfo_height()
        
        # Hide the popup *after* getting its size
        popup.withdraw()
        
        # Center and reveal
        self._center_popup(popup, popup_width, popup_height)
    
    def _on_link_click(self, url):
        """Callback to open a URL in the default web browser."""
        try:
            print(f"Opening link: {url}")
            webbrowser.open_new(url)
        except Exception as e:
            self.ui.log_system_message(f"Error: Could not open URL. {e}")

    def _create_formatted_help_popup(self, title, help_text):
        """
        [NEW HELPER]
        Creates a new Toplevel window and populates it with formatted
        text parsed from the help_text string.
        """
        popup = tk.Toplevel(self.root)
        popup.title(title)
        # --- MODIFICATION: Removed initial geometry ---
        popup.transient(self.root); popup.grab_set()
        
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            default_family = default_font.actual("family")
            default_size = default_font.actual("size")
        except:
            default_family = "TkDefaultFont"
            default_size = 10
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        text_widget = tk.Text(main_frame, wrap='word', yscrollcommand=scrollbar.set, 
                              relief='sunken', borderwidth=1, padx=10, pady=10,
                              font=(default_family, default_size))
        text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=text_widget.yview)

        # --- Define Formatting Tags ---
        text_widget.tag_configure("heading", font=(default_family, default_size + 2, 'bold', 'underline'), spacing1=5, spacing3=10)
        text_widget.tag_configure("bold", font=(default_family, default_size, 'bold'))
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=20, offset=10)
        text_widget.tag_configure("link", font=(default_family, default_size, 'underline'), foreground="blue")
        
        text_widget.config(state='normal')
        
        link_regex = r'\[(.*?)\]\((.*?)\)'
        bold_regex = r'(\*\*.*?\*\*)'
        link_count = 0
        
        # --- Helper function to parse bold/links within a line ---
        def parse_line_content(line_str, base_tags=()):
            """Parses a line for bold/links and inserts it."""
            parts = re.split(r'(\[.*?\]\(.*?\))', line_str) # Split by links
            
            for part in parts:
                link_match = re.match(link_regex, part)
                
                if link_match:
                    link_text = link_match.group(1)
                    link_url = link_match.group(2)
                    
                    nonlocal link_count
                    tag_name = f"link_{link_count}"
                    link_count += 1
                    
                    all_tags = base_tags + (tag_name,)
                    
                    text_widget.tag_configure(tag_name, font=(default_family, default_size, 'underline'), foreground="blue")
                    text_widget.tag_bind(tag_name, "<Button-1>", lambda e, url=link_url: self._on_link_click(url))
                    text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
                    text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))
                    
                    text_widget.insert("end", link_text, all_tags)
                
                else:
                    bold_parts = re.split(bold_regex, part)
                    for bold_part in bold_parts:
                        if bold_part.startswith("**") and bold_part.endswith("**"):
                            all_tags = base_tags + ("bold",)
                            text_widget.insert("end", bold_part[2:-2], all_tags)
                        else:
                            text_widget.insert("end", bold_part, base_tags)
        # --- END Helper ---

        try:
            for line in help_text.strip().splitlines():
                line_stripped = line.strip()
                
                if line_stripped.startswith("##") and line_stripped.endswith("##"):
                    text_widget.insert("end", line_stripped[2:-2].strip() + "\n", "heading")
                
                elif line_stripped.startswith("* "):
                    text_widget.insert("end", "• ", ("bullet",)) 
                    parse_line_content(line_stripped[2:], base_tags=("bullet",))
                    text_widget.insert("end", "\n") 
                
                elif not line_stripped:
                    text_widget.insert("end", "\n")
                    
                else:
                    parse_line_content(line_stripped, base_tags=())
                    text_widget.insert("end", "\n") 
                    
        except Exception as e:
            text_widget.insert("end", f"An error occurred while parsing help text: {e}")
        
        text_widget.config(state='disabled') # Make read-only
        
        btn_frame = ttk.Frame(popup, padding=(10, 0, 10, 10))
        btn_frame.pack(fill="x", side="bottom")
        ttk.Button(btn_frame, text="Close", command=popup.destroy).pack(side="right")
        
        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 720
        popup_height = 550 # Fixed height is fine for this
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
        
    def _open_help_popup(self):
        """
        [MODIFIED IMPLEMENTATION]
        Loads the 'main' help text from the consolidated file.
        """
        help_text = self._get_help_section("main")
        self._create_formatted_help_popup("Fermentation Vault - Help", help_text)       
    
    def _open_about_popup(self): self.ui.log_system_message("About not yet implemented.")
    
    
    def _get_help_section(self, section_name):
        """
        Loads the consolidated help.txt file and extracts a specific section.
        Sections are defined by [SECTION: section_name].
        """
        try:
            # --- MODIFICATION ---
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Path is now src/assets/help.txt
            help_file_path = os.path.join(base_dir, "assets", "help.txt") # New file name
            # --- END MODIFICATION ---
            
            with open(help_file_path, 'r', encoding='utf-8') as f:
                full_help_text = f.read()
            
            # Use regex to find the section
            # Pattern: [SECTION: section_name] ...content... [SECTION: ...or EOF
            # re.S (DOTALL) makes '.' match newlines
            pattern = re.compile(r'\[SECTION:\s*' + re.escape(section_name) + r'\](.*?)(?=\[SECTION:|\Z)', re.S)
            match = pattern.search(full_help_text)
            
            if match:
                return match.group(1).strip() # Return the content
            else:
                return f"## ERROR ##\nSection '[SECTION: {section_name}]' not found in help.txt."
                
        except FileNotFoundError:
            return "##ERROR##\nConsolidated 'help.txt' file not found."
        except Exception as e:
            return f"##ERROR##\nAn error occurred loading the help file:\n{e}"

# --- NEW: PID & TUNING POPUP ---
    
    def _open_pid_tuning_popup(self):
        
        # --- 1. Entrance Gate ---
        title = "Expert Settings Warning"
        message = ("WARNING! These settings are for expert users only. "
                   "Improper settings may produce unexpected results and "
                   "potentially dangerous (overheating) conditions.\n\n"
                   "CANCEL now unless you accept full responsibility for "
                   "changes you make to these settings.")
        
        if not messagebox.askokcancel(title, message):
            return # User clicked Cancel

        # --- 2. Create Popup ---
        # --- MODIFICATION: Removed initial geometry ---
        popup = tk.Toplevel(self.root); popup.title("PID & Tuning"); popup.transient(self.root); popup.grab_set()
        
        # --- 3. Load Values ---
        self._load_pid_tuning_vars()
        
        # --- 4. Build UI ---
        
        # Main frame holds the Notebook and the Buttons
        main_frame = ttk.Frame(popup, padding=(15, 15, 15, 0)); main_frame.pack(fill="both", expand=True)
        
        # Create the Notebook (Tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 15))
        
        # Create Tab 1: PID Settings
        pid_tab = ttk.Frame(notebook, padding="15")
        notebook.add(pid_tab, text='PID Settings')
        
        # Create Tab 2: Tuning Parameters
        tuning_tab = ttk.Frame(notebook, padding="15")
        notebook.add(tuning_tab, text='Tuning Parameters')
        
        # --- Helper for adding rows ---
        def add_tuning_row(parent, label, var, unit=None):
            row_frame = ttk.Frame(parent); row_frame.pack(fill="x", pady=4)
            ttk.Label(row_frame, text=label, width=30, anchor='w').pack(side='left')
            entry = ttk.Entry(row_frame, textvariable=var, width=10)
            entry.pack(side='left', padx=(5, 5))
            if unit: ttk.Label(row_frame, text=unit).pack(side='left')

        # --- Populate Tab 1: PID Settings ---
        add_tuning_row(pid_tab, "Proportional (Kp)", self.pid_kp_var)
        add_tuning_row(pid_tab, "Integral (Ki)", self.pid_ki_var)
        add_tuning_row(pid_tab, "Derivative (Kd)", self.pid_kd_var)
        
        ttk.Separator(pid_tab, orient='horizontal').pack(fill='x', pady=10)
        
        # --- MODIFICATION: Renamed section and checkbox text ---
        ttk.Label(pid_tab, text="Data Logging", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        ttk.Checkbutton(pid_tab, 
                        text="Log data for PID & Tuning analysis (pid_tuning_log.csv)", 
                        variable=self.pid_logging_var).pack(anchor='w', padx=5, pady=5)
        # --- END MODIFICATION ---

        # --- Populate Tab 2: Tuning Parameters ---
        add_tuning_row(tuning_tab, "PID Idle Zone (All Modes)", self.pid_idle_zone_var, unit="F")
        ttk.Separator(tuning_tab, orient='horizontal').pack(fill='x', pady=10)
        
        add_tuning_row(tuning_tab, "Ambient Mode Deadband", self.ambient_deadband_var, unit="F")
        ttk.Separator(tuning_tab, orient='horizontal').pack(fill='x', pady=10)
        
        add_tuning_row(tuning_tab, "Standard PID Envelope (Beer/Ramp)", self.beer_pid_envelope_width_var, unit="F")
        ttk.Separator(tuning_tab, orient='horizontal').pack(fill='x', pady=10)

        add_tuning_row(tuning_tab, "Crash Mode Envelope Width", self.crash_pid_envelope_width_var, unit="F")
        ttk.Separator(tuning_tab, orient='horizontal').pack(fill='x', pady=10)
        
        add_tuning_row(tuning_tab, "Ramp: Pre-Ramp Tolerance", self.ramp_pre_ramp_tolerance_var, unit="F")
        add_tuning_row(tuning_tab, "Ramp: Thermostatic Deadband", self.ramp_thermo_deadband_var, unit="F")
        add_tuning_row(tuning_tab, "Ramp: PID Landing Zone", self.ramp_pid_landing_zone_var, unit="F")

        # --- 5. Buttons (Placed OUTSIDE the notebook) ---
        btns_frame = ttk.Frame(popup, padding="10"); btns_frame.pack(fill="x", side="bottom")
        
        # Right-justified buttons
        ttk.Button(btns_frame, text="Save", command=lambda: self._save_pid_tuning_settings(popup)).pack(side="right", padx=5)
        ttk.Button(btns_frame, text="Cancel", command=popup.destroy).pack(side="right")
        
        # Left-justified buttons
        ttk.Button(btns_frame, text="Help", command=self._open_pid_tuning_help).pack(side="left", padx=5)
        ttk.Button(btns_frame, text="Reset to Defaults", command=self._reset_pid_tuning_to_defaults).pack(side="left")

        # --- MODIFICATION: Use dynamic centering ---
        popup.update_idletasks()
        popup_width = 500
        popup_height = popup.winfo_height()
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---

    def _load_pid_tuning_vars(self):
        """Helper to load all 10 tuning values + 1 checkbox from settings_manager."""
        self.pid_kp_var.set(str(self.settings_manager.get("pid_kp", 2.0)))
        self.pid_ki_var.set(str(self.settings_manager.get("pid_ki", 0.03)))
        self.pid_kd_var.set(str(self.settings_manager.get("pid_kd", 20.0)))
        self.pid_idle_zone_var.set(str(self.settings_manager.get("pid_idle_zone", 0.5)))
        self.ambient_deadband_var.set(str(self.settings_manager.get("ambient_deadband", 1.0)))
        self.beer_pid_envelope_width_var.set(str(self.settings_manager.get("beer_pid_envelope_width", 1.0)))
        self.ramp_pre_ramp_tolerance_var.set(str(self.settings_manager.get("ramp_pre_ramp_tolerance", 0.2)))
        self.ramp_thermo_deadband_var.set(str(self.settings_manager.get("ramp_thermo_deadband", 0.1)))
        self.ramp_pid_landing_zone_var.set(str(self.settings_manager.get("ramp_pid_landing_zone", 0.5)))
        self.crash_pid_envelope_width_var.set(str(self.settings_manager.get("crash_pid_envelope_width", 2.0)))
        
        # --- MODIFICATION: Load PID logging var ---
        self.pid_logging_var.set(self.settings_manager.get("pid_logging_enabled", False))
        # --- END MODIFICATION ---
        
    def _save_pid_tuning_settings(self, popup):
        
        # 1. Get current (old) values for comparison
        old_vals = {
            "pid_kp": str(self.settings_manager.get("pid_kp", 2.0)),
            "pid_ki": str(self.settings_manager.get("pid_ki", 0.03)),
            "pid_kd": str(self.settings_manager.get("pid_kd", 20.0)),
            "pid_idle_zone": str(self.settings_manager.get("pid_idle_zone", 0.5)),
            "ambient_deadband": str(self.settings_manager.get("ambient_deadband", 1.0)),
            "beer_pid_envelope_width": str(self.settings_manager.get("beer_pid_envelope_width", 1.0)),
            "ramp_pre_ramp_tolerance": str(self.settings_manager.get("ramp_pre_ramp_tolerance", 0.2)),
            "ramp_thermo_deadband": str(self.settings_manager.get("ramp_thermo_deadband", 0.1)),
            "ramp_pid_landing_zone": str(self.settings_manager.get("ramp_pid_landing_zone", 0.5)),
            "crash_pid_envelope_width": str(self.settings_manager.get("crash_pid_envelope_width", 2.0))
        }
        # --- MODIFICATION: Add PID logging state ---
        old_pid_logging_state = self.settings_manager.get("pid_logging_enabled", False)
        # --- END MODIFICATION ---

        # 2. Get new values from UI
        new_vals = {
            "pid_kp": self.pid_kp_var.get(),
            "pid_ki": self.pid_ki_var.get(),
            "pid_kd": self.pid_kd_var.get(),
            "pid_idle_zone": self.pid_idle_zone_var.get(),
            "ambient_deadband": self.ambient_deadband_var.get(),
            "beer_pid_envelope_width": self.beer_pid_envelope_width_var.get(),
            "ramp_pre_ramp_tolerance": self.ramp_pre_ramp_tolerance_var.get(),
            "ramp_thermo_deadband": self.ramp_thermo_deadband_var.get(),
            "ramp_pid_landing_zone": self.ramp_pid_landing_zone_var.get(),
            "crash_pid_envelope_width": self.crash_pid_envelope_width_var.get()
        }
        # --- MODIFICATION: Add PID logging state ---
        new_pid_logging_state = self.pid_logging_var.get()
        # --- END MODIFICATION ---
        
        # 3. Check for changes
        has_changed = False
        for key in new_vals:
            if new_vals[key] != old_vals[key]:
                has_changed = True
                break
        
        if not has_changed and new_pid_logging_state == old_pid_logging_state:
            self.ui.log_system_message("PID & Tuning settings saved. (No changes detected.)")
            popup.destroy()
            return

        # 4. Exit Gate (askyesnocancel)
        title = "Confirm Expert Settings"
        message = ("You have made changes to the PID & Tuning settings.\n\n"
                   "- Yes:   Save all changes and close.\n"
                   "- No:    Exit without saving.\n"
                   "- Cancel: Return to the settings window.")
        
        choice = messagebox.askyesnocancel(title, message, parent=popup)
        
        if choice is None: # Cancel
            return # Return to settings
        elif choice is False: # No
            popup.destroy() # Exit without saving
            return

        # 5. User clicked YES. Validate and Save.
        try:
            log_parts = []
            
            # Validate all, then save all
            validated_settings = {}
            for key, str_val in new_vals.items():
                val = self._to_float_or_error(str_val)
                validated_settings[key] = val
                
                # Check for changes to log
                if str(val) != old_vals[key]:
                    log_parts.append(f"{key} set to {val}.")
            
            # If all are valid, save them
            for key, val in validated_settings.items():
                self.settings_manager.set(key, val)
                
            # --- MODIFICATION: Save PID logging state ---
            if new_pid_logging_state != old_pid_logging_state:
                self.settings_manager.set("pid_logging_enabled", new_pid_logging_state)
                log_parts.append(f"PID Logging {'enabled' if new_pid_logging_state else 'disabled'}.")
            # --- END MODIFICATION ---

            # --- CRITICAL: Force PID to reload new Kp/Ki/Kd values ---
            self.temp_controller.pid.Kp = validated_settings['pid_kp']
            self.temp_controller.pid.Ki = validated_settings['pid_ki']
            self.temp_controller.pid.Kd = validated_settings['pid_kd']
            print("[TempController] PID values updated by user.")
            # ---
            
            if log_parts:
                message = "PID & Tuning settings saved. " + " ".join(log_parts)
            else:
                message = "PID & Tuning settings saved. (No changes detected.)"
            
            self.ui.log_system_message(message)
            popup.destroy()

        except ValueError as e:
            messagebox.showerror("Input Error", f"All values must be valid numbers. ({e})", parent=popup)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=popup)

    def _reset_pid_tuning_to_defaults(self):
        """Asks for confirmation, then resets the StringVars in the popup to the hard-coded defaults."""
        
        # --- NEW: Add confirmation dialog ---
        title = "Confirm Reset to Defaults"
        message = "Resets PID settings & tuning parameters to defaults."
        
        # Use askokcancel, consistent with the popup's entry warning
        if not messagebox.askokcancel(title, message):
            return # User clicked Cancel
        # --- END NEW ---
        
        self.pid_kp_var.set("2.0")
        self.pid_ki_var.set("0.03")
        self.pid_kd_var.set("20.0")
        self.pid_idle_zone_var.set("0.5")
        self.ambient_deadband_var.set("1.0")
        self.beer_pid_envelope_width_var.set("1.0")
        self.ramp_pre_ramp_tolerance_var.set("0.2")
        self.ramp_thermo_deadband_var.set("0.1")
        self.ramp_pid_landing_zone_var.set("0.5")
        self.crash_pid_envelope_width_var.set("2.0")
        
        # --- MODIFICATION: Reset PID logging var ---
        self.pid_logging_var.set(False)
        # --- END MODIFICATION ---
        
    def _open_pid_tuning_help(self):
        """
        [MODIFIED IMPLEMENTATION]
        Loads the 'pid' help text from the consolidated file.
        """
        help_text = self._get_help_section("pid")
        self._create_formatted_help_popup("PID & Tuning Help", help_text)
        
    def _open_api_help_popup(self):
        """
        [MODIFIED IMPLEMENTATION]
        Loads the 'api' help text from the consolidated file.
        """
        help_text = self._get_help_section("api")
        self._create_formatted_help_popup("API & FG Help", help_text) 

    # --- EULA / SUPPORT POPUP ---

    def _load_support_image(self):
        """Loads the QR code image and stores it."""
        if self.support_qr_image:
            return # Already loaded
            
        try:
            # --- MODIFICATION ---
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Path is now src/assets/support.gif
            image_path = os.path.join(base_dir, "assets", "support.gif")
            # --- END MODIFICATION ---
            
            # --- THIS IS THE CHANGE ---
            # Use tk.PhotoImage directly, which supports GIF natively
            self.support_qr_image = tk.PhotoImage(file=image_path)
            # --- END CHANGE ---
            
        except FileNotFoundError:
            self.ui.log_system_message("Error: support.gif image not found.")
            self.support_qr_image = None # Ensure it's None
        except tk.TclError as e:
            # This is the error tk.PhotoImage throws for bad files
            self.ui.log_system_message(f"Error loading support.gif (is it a valid GIF?): {e}")
            self.support_qr_image = None
        except Exception as e:
            self.ui.log_system_message(f"Error loading support image: {e}")
            self.support_qr_image = None
            
    def _open_support_popup(self, is_launch=False):
        """
        Displays the 'Support this Project' popup, which includes the EULA.
        'is_launch=True' modifies behavior (e.g., forces modal).
        """
        popup = tk.Toplevel(self.root)
        popup.title("Support This Project & EULA")
        
        # --- 1. Load Image ---
        self._load_support_image() # Load/check image

        # --- 2. Reset UI Variables ---
        
        # --- MODIFICATION: Pre-select "I agree" if previously agreed ---
        has_agreed = self.settings_manager.get("eula_agreed", False)
        if has_agreed:
            self.eula_agreement_var.set(1) # 1 = agree
        else:
            self.eula_agreement_var.set(0) # 0 = unset
        # --- END MODIFICATION ---
        
        # Load the saved setting for "show on launch"
        # The checkbox var is "Do not show", so its state is the *inverse*
        show_on_launch_setting = self.settings_manager.get("show_eula_on_launch", True)
        self.show_eula_checkbox_var.set(not show_on_launch_setting)
        
        # --- 3. Build UI ---
        main_frame = ttk.Frame(popup, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- Top Section ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 15))
        top_frame.grid_columnconfigure(0, weight=1) # Text column
        top_frame.grid_columnconfigure(1, weight=0) # Image column

        support_text = (
            "This project took hundreds of hours to develop, test, and optimize. "
            "Please consider donating to this project so improvements and enhancements "
            "can be made. If you wish to receive customer support via email, please "
            "make a reasonable donation in support of this project. Customer support "
            "requests without a donation may not be considered for response."
        )
        
        # --- MODIFICATION: Increased wraplength from 400 to 520 ---
        text_label = ttk.Label(top_frame, text=support_text, wraplength=520, justify="left")
        text_label.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        if self.support_qr_image:
            qr_label = ttk.Label(top_frame, image=self.support_qr_image)
            qr_label.grid(row=0, column=1, sticky="e")
        else:
            qr_placeholder = ttk.Label(top_frame, text="[QR Code Image Missing]", relief="sunken", padding=20)
            qr_placeholder.grid(row=0, column=1, sticky="e")
            
        # --- EULA Section ---
        eula_frame = ttk.LabelFrame(main_frame, text="End User License Agreement (EULA)", padding=10)
        eula_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        eula_text_widget = scrolledtext.ScrolledText(eula_frame, height=10, wrap="word", relief="flat")
        eula_text_widget.pack(fill="both", expand=True)
        
        eula_content = """**End User License Agreement (EULA)**

**1. Scope of Agreement**
This Agreement applies to the "Fermentation Vault" software (hereafter "this app"). "This app" includes the main software program and all related software and hardware components, including commercially supplied, home-made, or independently supplied hardware and software components of any kind.

**2. Acceptance of Responsibility**
By using this app, you, the user, accept all responsibility for any consequence or outcome arising from the use of, or inability to use, this app.

**3. No Guarantee or Warranty**
This app is provided "as is." It provides no guarantee of usefulness or fitness for any particular purpose. The app provides no warranty, expressed or implied. You use this app entirely at your own risk.
"""
        # Add tags for basic formatting
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            bold_font = default_font.copy()
            bold_font.config(weight="bold")
            eula_text_widget.tag_configure("bold", font=bold_font)
        except:
            eula_text_widget.tag_configure("bold", font=('TkDefaultFont', 10, 'bold'))

        eula_text_widget.insert("1.0", eula_content)
        eula_text_widget.tag_add("bold", "1.0", "1.30")
        eula_text_widget.tag_add("bold", "3.0", "3.20")
        eula_text_widget.tag_add("bold", "7.0", "7.30")
        eula_text_widget.tag_add("bold", "11.0", "11.27")
        
        eula_text_widget.config(state="disabled")

        # --- Agreement Section ---
        agreement_frame = ttk.Frame(main_frame)
        agreement_frame.pack(fill="x")

        # Radio 1: Agree
        agree_rb = ttk.Radiobutton(agreement_frame, 
                                   text="I agree with the above End User License Agreement", 
                                   variable=self.eula_agreement_var, value=1)
        agree_rb.pack(anchor="w")
        agree_note = ttk.Label(agreement_frame, text="User may proceed to the app after closing this popup",
                               font=('TkDefaultFont', 8, 'italic'))
        agree_note.pack(anchor="w", padx=(20, 0), pady=(0, 5))

        # Radio 2: Disagree
        disagree_rb = ttk.Radiobutton(agreement_frame, 
                                     text="I do not agree with the above End User License Agreement", 
                                     variable=self.eula_agreement_var, value=2)
        disagree_rb.pack(anchor="w")
        disagree_note = ttk.Label(agreement_frame, text="User will exit the app after closing this popup",
                                 font=('TkDefaultFont', 8, 'italic'))
        disagree_note.pack(anchor="w", padx=(20, 0), pady=(0, 10))

        # --- Bottom Section (Checkbox & Close) ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", side="bottom")

        show_again_cb = ttk.Checkbutton(bottom_frame, 
                                        text="This popup can be found on the Settings & Info menu. Do not show this popup at launch again.",
                                        variable=self.show_eula_checkbox_var)
        show_again_cb.pack(anchor="w", pady=(0, 10))

        close_btn = ttk.Button(bottom_frame, text="Close", 
                               command=lambda: self._handle_support_popup_close(popup))
        close_btn.pack(side="right")

        # --- 4. Finalize Popup ---
        popup.update_idletasks()
        
        # --- MODIFICATION: Use dynamic centering ---
        popup_width = 720
        popup_height = popup.winfo_height()
        self._center_popup(popup, popup_width, popup_height)
        # --- END MODIFICATION ---
        
        popup.resizable(False, False)
        
        # Force modal interaction if on launch
        if is_launch:
            popup.protocol("WM_DELETE_WINDOW", lambda: self._handle_support_popup_close(popup))
            popup.transient(self.root)
            popup.grab_set()
            self.root.wait_window(popup)
        else:
            popup.transient(self.root)
            popup.grab_set()
            
    def _handle_support_popup_close(self, popup):
        """Handles the logic for the 'Close' button on the Support/EULA popup."""
        
        # --- NEW: Check if the popup is already being destroyed ---
        if not popup.winfo_exists():
            return
        # --- END NEW ---
        
        agreement_state = self.eula_agreement_var.get()
        do_not_show_checked = self.show_eula_checkbox_var.get()
        
        # --- 2. Check Agreement State ---
        if agreement_state == 1: # "I agree"
            # --- MODIFICATION: Save both settings ---
            self.settings_manager.set("show_eula_on_launch", not do_not_show_checked)
            self.settings_manager.set("eula_agreed", True)
            # --- END MODIFICATION ---
            
            popup.destroy()
            return

        elif agreement_state == 2: # "I do not agree"
            # --- MODIFICATION: Save both settings ---
            # Reset the "do not show" setting if they disagreed
            if do_not_show_checked:
                self.settings_manager.set("show_eula_on_launch", True)
            
            self.settings_manager.set("eula_agreed", False)
            # --- END MODIFICATION ---
            
            popup.destroy()
            self._show_disagree_dialog()
            return
            
        else: # State is 0 (neither selected)
            # --- NEW: Check again before showing a message ---
            if not popup.winfo_exists():
                return
            # --- END NEW ---
            messagebox.showwarning("Agreement Required", 
                                   "You must select 'I agree' or 'I do not agree' to proceed.", 
                                   parent=popup)
            # Do not close the popup
            return

    def _show_disagree_dialog(self):
        """Shows the final confirmation dialog when user disagrees with EULA."""
        
        # --- MODIFICATION: Updated dialog text ---
        if messagebox.askokcancel("EULA Disagreement",
                                "You chose to not agree with the End User License Agreement, so the app will terminate when you click OK.\n\n"
                                "Click Cancel to return to the agreement or click OK to exit the app."):
            # --- END MODIFICATION ---
            
            # User clicked OK (True) -> Terminate the app
            self.ui.log_system_message("User disagreed with EULA. Terminating application.")
            
            # We must call the root's destroy method
            self.root.destroy()
            
        else:
            # User clicked Cancel (False) -> Re-open the EULA popup
            # Force it as a 'launch' popup to ensure it's modal
            self._open_support_popup(is_launch=True)
            
            
