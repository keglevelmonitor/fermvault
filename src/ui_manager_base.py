"""
Fermentation Vault App
ui_manager_base.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont 
import math
import time
import queue
import os
from datetime import datetime
import threading

# Define a placeholder for UI Update Queue Handler (needed for the mixin/composed class)
class MainUIBase:
    
    # Placeholder for constants/variables that will be shared across files
    UNASSIGNED_SENSOR = "unassigned" 
    
    def __init__(self, root, settings_manager_instance, temp_controller_instance, api_manager_instance, notification_manager_instance, app_version_string):
        self.root = root
        self.settings_manager = settings_manager_instance
        self.temp_controller = temp_controller_instance
        self.api_manager = api_manager_instance
        self.notification_manager = notification_manager_instance
        
        # This queue is now primarily for system logging only
        self.ui_update_queue = queue.Queue() 
        self.app_version_string = app_version_string

        # --- FIX: Initialize Option Lists Here ---
        # --- MODIFICATION: Use new, shorter display names ---
        self.control_mode_options = ["Ambient", "Beer", "Ramp", "Crash"]
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Added "Reset to Defaults" ---
        self.action_options = ["Send Status Message", "Update API & Temp Data", "Reload Brew Sessions", "Run FG Calculator", "Reset to Defaults"]
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Added 'PID & Tuning' ---
        self.popup_list = ["Temperature Setpoints", "PID & Tuning", "Notification Settings", "API & FG Settings", "Brew Sessions", "System Settings", "Wiring Diagram", "Help", "About", "Support this Project"]
        # --- END MODIFICATION ---
        
        self.root.title("Fermentation Vault")
        self.root.geometry("800x600") # Fixed small size
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing_ui) 

        # --- Primary UI Variables ---
        # FIX: Load the previously saved session title as the initial value (or empty string if none saved)
        saved_title = settings_manager_instance.get("brew_session_title", "")
        self.brew_session_var = tk.StringVar(value=saved_title)

        # FIX: Load the last saved API service name
        saved_api_service = settings_manager_instance.get("active_api_service", "OFF")
        self.api_service_var = tk.StringVar(value=saved_api_service)
        
        # --- MODIFICATION: Removed StringVars for Combobox menus ---
        # self.settings_menu_var = tk.StringVar(value="Select...") # REMOVED
        # self.actions_menu_var = tk.StringVar(value="Select...") # REMOVED
        # --- END MODIFICATION ---
        
        self.control_mode_var = tk.StringVar()
        self.monitoring_var = tk.StringVar(value="OFF")
        self.fan_var = tk.StringVar(value="Auto")
        
        # --- MODIFICATION: Added variable for new indicator ---
        # self.monitoring_indicator_var = tk.StringVar(value="Monitoring OFF") # REMOVED
        # ------------------------------------------------------

        # --- Data Display Variables ---
        self.beer_setpoint_var = tk.StringVar(value="--.-")
        self.beer_actual_var = tk.StringVar(value="--.-")
        self.beer_timestamp_var = tk.StringVar(value="--:--:--")

        self.amb_setpoint_min_var = tk.StringVar(value="--.-")
        self.amb_actual_var = tk.StringVar(value="--.-")
        self.amb_timestamp_var = tk.StringVar(value="--:--:--")
        
        self.og_display_var = tk.StringVar(value="--.---")
        self.og_timestamp_var = tk.StringVar(value="--:--:--")
        
        self.sg_display_var = tk.StringVar(value="--.---")
        self.sg_timestamp_var = tk.StringVar(value="--:--:--")

        # --- MODIFICATION: Updated FG variable defaults ---
        self.fg_status_var = tk.StringVar(value="--.---") # This is now the VALUE field
        self.fg_message_var = tk.StringVar(value="--:--:--") # This is now the MESSAGE field
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Added var for new ramp target field ---
        self.ramp_end_target_var = tk.StringVar(value="")
        # --------------------------------------------------------
        
        # --- MODIFICATION: Added for heartbeat toggle ---
        self.heartbeat_toggle = False
        # --- END MODIFICATION ---
        
        self.heat_state_var = tk.StringVar(value="Heating OFF") # Updated default
        self.cool_state_var = tk.StringVar(value="Cooling OFF") # Updated default
        
        # --- NEW VARIABLE ---
        self.cool_restriction_var = tk.StringVar(value="")
        # --------------------
        
        self.system_messages_var = tk.StringVar(value="System Initialized.")
        
        # --- MODIFICATION: Removed trace for monitoring button color ---
        
        # --- NEW: UI Ready Flag ---
        self.ui_ready = False
        # --- END NEW ---
        
        self.root.after_idle(self._create_widgets)
        self._poll_ui_update_queue()
        
        # --- MODIFICATION: Removed background sensor check call ---
        # self._background_sensor_check() # <-- MOVED to _create_widgets
        # --- END MODIFICATION ---
                
    def _create_widgets(self):
        # Configure styles
        s = ttk.Style(self.root)
        s.configure('Header.TFrame', background='#e0e0e0')
        s.configure('Red.TLabel', background='lightcoral', foreground='black')
        s.configure('Blue.TLabel', background='lightblue1', foreground='black')
        s.configure('Gray.TLabel', background='gainsboro', foreground='black')
        s.configure('Green.TLabel', background='springgreen', foreground='black')
        # --- MODIFICATION: Added new Yellow style ---
        s.configure('Yellow.TLabel', background='khaki1', foreground='black')
        # ------------------------------------------
        # --- MODIFICATION: Added new DarkGreen style for heartbeat ---
        s.configure('DarkGreen.TLabel', background='green', foreground='white')
        # -------------------------------------------------------------
        
        # --- NEW STYLE: Red Background for Fail-Safe with white text ---
        s.configure('AlertRed.TLabel', background='red', foreground='white', font=('TkDefaultFont', 10, 'bold'))
        # -------------------------------------------------------------
        
        # --- NEW STYLE: MediumGreen for FG Stable ---
        s.configure('MediumGreen.TLabel', background='#3CB371', foreground='black')
        # --- END NEW STYLE ---

        # --- FIX: Custom Combobox Styles using 'map' to force fieldbackground in 'readonly' state ---
        s.map('Red.TCombobox', 
              fieldbackground=[('readonly', 'lightcoral')]) 
        
        s.map('MediumGreen.TCombobox', 
              fieldbackground=[('readonly', '#3CB371')])
              
        s.map('DarkGreen.TCombobox', 
              fieldbackground=[('readonly', 'green')])
        # -------------------------------------------------------------------------------------------

        # Define a style for centering column headers
        s.configure('Center.TLabel', anchor='center')

        # --- Grid Setup (All widgets placed directly in main_frame) ---
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill="both", expand=True)
        
        # --- Column Definitions (MODIFIED) ---
        NARROW_FIELD_WIDTH = 55   # Was 75
        UNIT_FIELD_WIDTH = 15 
        WIDE_TIMESTAMP_WIDTH = 150  # Was 55
        DATA_LABEL_MIN_WIDTH = 100  # Was 65 + 75 (140)
        # ---------------------------------
        
        self.main_frame.grid_columnconfigure(0, weight=0, minsize=80)    # Col 0: Control Labels
        self.main_frame.grid_columnconfigure(1, weight=0, minsize=110)   # Col 1: Control Dropdowns/Buttons
        self.main_frame.grid_columnconfigure(2, weight=0, minsize=DATA_LABEL_MIN_WIDTH) # Col 2: Data Labels 
        self.main_frame.grid_columnconfigure(3, weight=0, minsize=NARROW_FIELD_WIDTH) # Col 3: Setpoint Data
        self.main_frame.grid_columnconfigure(4, weight=0, minsize=UNIT_FIELD_WIDTH) # Col 4: Setpoint Unit
        self.main_frame.grid_columnconfigure(5, weight=0, minsize=NARROW_FIELD_WIDTH) # Col 5: Actual Data
        self.main_frame.grid_columnconfigure(6, weight=0, minsize=UNIT_FIELD_WIDTH) # Col 6: Actual Unit
        self.main_frame.grid_columnconfigure(7, weight=1, minsize=WIDE_TIMESTAMP_WIDTH) # Col 7: Timestamp (Expands most)
        
        # --- Header Frame (Stays the same for Dropdown placement) ---
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=0, columnspan=8, sticky='ew')
        
        # --- MODIFICATION: Reconfigured header columns for desired layout ---
        self.header_frame.grid_columnconfigure(0, weight=0, minsize=80)    # Col 0: Labels (Fixed)
        self.header_frame.grid_columnconfigure(1, weight=1, minsize=240)   # Col 1: Dropdowns (Expand/Shrink, but not too small)
        self.header_frame.grid_columnconfigure(2, weight=0, minsize=0)     # Col 2: Unused
        self.header_frame.grid_columnconfigure(3, weight=0, minsize=0)     # Col 3: Unused
        self.header_frame.grid_columnconfigure(4, weight=1)                # Col 4: Spacer (Flexible)
        self.header_frame.grid_columnconfigure(5, weight=0, minsize=338)   # Col 5: Menu Buttons (Fixed Width, 30% wider)
        # --- END MODIFICATION ---
        
        row_idx = 0 
        
        # --- Row 0 & 1: Header Dropdowns (API, Brew Session, Menus) ---
        
        # --- MODIFICATION: Added pady=(5, 5) for top spacing ---
        ttk.Label(self.header_frame, text="API Service").grid(row=row_idx, column=0, sticky='w', pady=(5, 5))
        self.api_dropdown = ttk.Combobox(self.header_frame, textvariable=self.api_service_var, values=list(self.api_manager.available_services.keys()), state="readonly")
        self.api_dropdown.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=(5, 5))
        self.api_dropdown.bind("<<ComboboxSelected>>", self._handle_api_selection_change)
        # --- END MODIFICATION ---

        # Row 1
        ttk.Label(self.header_frame, text="Brew Session").grid(row=row_idx + 1, column=0, sticky='w', pady=(5, 5))
        self.session_dropdown = ttk.Combobox(self.header_frame, textvariable=self.brew_session_var, values=[], state="readonly")
        self.session_dropdown.grid(row=row_idx + 1, column=1, sticky='ew', padx=5, pady=(5, 5))
        self.session_dropdown.bind("<<ComboboxSelected>>", self._handle_brew_session_change)
        
        # Menu Container (RIGHT JUSTIFIED)
        self.menu_container = ttk.Frame(self.header_frame)
        self.menu_container.grid(row=0, column=5, rowspan=2, sticky='e', padx=5, pady=0)
        
        # --- MODIFICATION: Configure one column for wide buttons ---
        self.menu_container.grid_columnconfigure(0, weight=1) 
        # --- END MODIFICATION ---
        
        # --- MODIFICATION: Replaced Combobox with Menubutton ---
        
        # --- Settings & Info Menu ---
        self.settings_menubutton = ttk.Menubutton(self.menu_container, text="Settings & Info")
        self.settings_menubutton.grid(row=0, column=0, sticky='ew', padx=2, pady=(5, 5))
        
        # --- MODIFICATION: THIS IS THE FIX ---
        # The 'disabledforeground' option goes on the tk.Menu constructor
        settings_menu = tk.Menu(self.settings_menubutton, tearoff=0, disabledforeground="black")
        self.settings_menubutton["menu"] = settings_menu
        
        # --- NEW: Get bold font for headings ---
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            bold_font = default_font.copy()
            bold_font.config(weight="bold")
        except:
            # Fallback if tkfont fails
            bold_font = ('TkDefaultFont', 10, 'bold')
        # --- END NEW ---
        
        # --- MODIFICATION: Manually build menu with new structure ---
        
        # 1. Settings Heading
        # --- MODIFICATION: The 'state="disabled"' is correct ---
        settings_menu.add_command(label="Settings", font=bold_font, state="disabled")
        
        # Define the items that go under the "Settings" heading
        settings_items = [
            "Temperature Setpoints", 
            "PID & Tuning", 
            "Notification Settings", 
            "API & FG Settings", 
            "Brew Sessions", 
            "System Settings"
        ]
        
        for item in settings_items:
            # Check if the item is in the official list from PopupManager
            if item in self.popup_list:
                settings_menu.add_command(
                    label=item,
                    command=lambda choice=item: self._handle_settings_menu(choice)
                )
        
        # 2. Separator
        settings_menu.add_separator()

        # 3. Info Heading
        # --- MODIFICATION: The 'state="disabled"' is correct ---
        settings_menu.add_command(label="Info", font=bold_font, state="disabled")
        
        # --- MODIFICATION: Add "Support this Project" to info list ---
        info_items = [
            "Wiring Diagram", 
            "Help", 
            "About",
            "Support this Project"
        ]
        # --- END MODIFICATION ---

        for item in info_items:
            # --- MODIFICATION: Check if item is in the popup_list ---
            # This now correctly adds all 4 items
            if item in self.popup_list:
                settings_menu.add_command(
                    label=item,
                    command=lambda choice=item: self._handle_settings_menu(choice)
                )
            # --- END MODIFICATION ---

        # --- MODIFICATION: Removed manual placeholder ---
        # item = "Support this Project"
        # settings_menu.add_command(...)
        # --- END MODIFICATION ---
        
        # --- Actions Menu ---
        self.actions_menubutton = ttk.Menubutton(self.menu_container, text="Actions")
        self.actions_menubutton.grid(row=1, column=0, sticky='ew', padx=2, pady=(5, 5))

        # Create the actual menu
        # --- MODIFICATION: Add disabledforeground and build manually ---
        actions_menu = tk.Menu(self.actions_menubutton, tearoff=0, disabledforeground="black")
        self.actions_menubutton["menu"] = actions_menu

        # 1. Actions Heading
        actions_menu.add_command(label="Actions", font=bold_font, state="disabled")
        
        # Define the items that go under the "Actions" heading
        action_items = [
            "Send Status Message", 
            "Update API & Temp Data", 
            "Reload Brew Sessions", 
            "Run FG Calculator"
        ]
        
        for item in action_items:
            if item in self.action_options: # Check against the master list
                actions_menu.add_command(
                    label=item,
                    command=lambda choice=item: self._handle_actions_menu(choice)
                )
        
        # 2. Separator
        actions_menu.add_separator()
        
        # --- NEW: Updates Heading ---
        actions_menu.add_command(label="Updates", font=bold_font, state="disabled")
        
        updates_items = [
            "Check for Updates" # <-- NEW ITEM
        ]
        
        for item in updates_items:
            if item in self.action_options:
                 actions_menu.add_command(
                    label=item,
                    command=lambda choice=item: self._handle_actions_menu(choice)
                )
                
        # 3. Separator (Separating Updates from Reset)
        actions_menu.add_separator()

        # 4. Reset Heading
        actions_menu.add_command(label="Reset", font=bold_font, state="disabled")
        
        reset_items = [
            "Reset to Defaults"
        ]

        for item in reset_items:
            if item in self.action_options: # Check against the master list
                actions_menu.add_command(
                    label=item,
                    command=lambda choice=item: self._handle_actions_menu(choice)
                )
        # --- END MODIFICATION ---
        
        # --- Horizontal Separator (Header to Data Grid) ---
        main_grid_row_idx = 1
        ttk.Separator(self.main_frame, orient='horizontal').grid(row=main_grid_row_idx, column=0, columnspan=8, sticky='ew', pady=(5, 10))
        main_grid_row_idx += 1
        
        # --- Data Grid Headers ---
        # --- MODIFICATION: Control Mode moved here ---
        ttk.Label(self.main_frame, text="Control Mode").grid(row=main_grid_row_idx, column=0, sticky='w', padx=5, pady=5)
        self.control_mode_dropdown = ttk.Combobox(self.main_frame, textvariable=self.control_mode_var, values=self.control_mode_options, state="readonly", width=13)
        self.control_mode_dropdown.grid(row=main_grid_row_idx, column=1, sticky='w', padx=5, pady=5)
        self.control_mode_dropdown.bind("<<ComboboxSelected>>", self._handle_control_mode_change)
        
        ttk.Label(self.main_frame, text="Setpoint", style='Center.TLabel').grid(row=main_grid_row_idx, column=3, columnspan=2, padx=5, pady=5)
        ttk.Label(self.main_frame, text="Actual", style='Center.TLabel').grid(row=main_grid_row_idx, column=5, columnspan=2, padx=5, pady=5)
        
        main_grid_row_idx += 1
        
        # --- Vertical Padding Constant ---
        VERTICAL_PADDING = (6, 6) 
        
        # --- DATA ROW 1: Ambient Data & Monitoring ---
        
        # --- MODIFICATION: Monitoring Combobox (Initial style set to Red.TCombobox) ---
        ttk.Label(self.main_frame, text="Monitoring").grid(row=main_grid_row_idx, column=0, sticky='w', padx=5, pady=VERTICAL_PADDING)
        self.monitoring_button = ttk.Combobox(self.main_frame, textvariable=self.monitoring_var, values=["OFF", "ON"], state="readonly", width=13, style="Red.TCombobox")
        self.monitoring_button.grid(row=main_grid_row_idx, column=1, sticky='w', padx=5, pady=VERTICAL_PADDING)
        self.monitoring_button.bind("<<ComboboxSelected>>", lambda event: self._toggle_monitoring())
        # --- END MODIFICATION ---

        # DATA SIDE: Ambient Label (Col 2), Setpoint (Col 3), Unit (Col 4), Actual (Col 5), Unit (Col 6), Timestamp (Col 7)
        ttk.Label(self.main_frame, text="Ambient").grid(row=main_grid_row_idx, column=2, sticky='e', padx=5, pady=VERTICAL_PADDING)
        
        self.amb_target_label = ttk.Label(self.main_frame, textvariable=self.amb_setpoint_min_var, style='Gray.TLabel', relief='sunken', anchor='center', width=7)
        self.amb_target_label.grid(row=main_grid_row_idx, column=3, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="F").grid(row=main_grid_row_idx, column=4, sticky='w', pady=VERTICAL_PADDING) 
        
        self.amb_actual_label = ttk.Label(self.main_frame, textvariable=self.amb_actual_var, style='Gray.TLabel', relief='sunken', anchor='center', width=7)
        self.amb_actual_label.grid(row=main_grid_row_idx, column=5, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="F").grid(row=main_grid_row_idx, column=6, sticky='w', pady=VERTICAL_PADDING) 
        
        self.amb_timestamp_label = ttk.Label(self.main_frame, textvariable=self.amb_timestamp_var, relief='sunken', anchor='center')
        self.amb_timestamp_label.grid(row=main_grid_row_idx, column=7, sticky='ew', padx=5, pady=VERTICAL_PADDING)

        main_grid_row_idx += 1
        
        # --- DATA ROW 2: Beer Data & Fan ---
        
        # --- MODIFICATION: Moved Fan up to fill the blank space ---
        ttk.Label(self.main_frame, text="Circulation Fan").grid(row=main_grid_row_idx, column=0, sticky='w', padx=5, pady=VERTICAL_PADDING)
        self.fan_dropdown = ttk.Combobox(self.main_frame, textvariable=self.fan_var, values=["Auto", "ON", "OFF"], state="readonly", width=13)
        self.fan_dropdown.grid(row=main_grid_row_idx, column=1, sticky='w', padx=5, pady=VERTICAL_PADDING)
        self.fan_dropdown.bind("<<ComboboxSelected>>", self._handle_fan_mode_change)
        # --- END MODIFICATION ---

        # DATA SIDE: Beer Label, Setpoint, Unit, Actual, Unit, Timestamp
        ttk.Label(self.main_frame, text="Beer").grid(row=main_grid_row_idx, column=2, sticky='e', padx=5, pady=VERTICAL_PADDING)
        
        self.beer_target_label = ttk.Label(self.main_frame, textvariable=self.beer_setpoint_var, style='Gray.TLabel', relief='sunken', anchor='center', width=7)
        self.beer_target_label.grid(row=main_grid_row_idx, column=3, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="F").grid(row=main_grid_row_idx, column=4, sticky='w', pady=VERTICAL_PADDING)
        
        self.beer_actual_label = ttk.Label(self.main_frame, textvariable=self.beer_actual_var, style='Gray.TLabel', relief='sunken', anchor='center', width=7)
        self.beer_actual_label.grid(row=main_grid_row_idx, column=5, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="F").grid(row=main_grid_row_idx, column=6, sticky='w', pady=VERTICAL_PADDING)
        
        self.ramp_end_target_label = ttk.Label(self.main_frame, textvariable=self.ramp_end_target_var, relief='sunken', anchor='center')
        self.ramp_end_target_label.grid(row=main_grid_row_idx, column=7, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        
        main_grid_row_idx += 1
        
        # --- DATA ROW 3: OG Data & Heating Indicator ---
        
        # --- MODIFICATION: Moved Heat indicator up ---
        self.heat_label = ttk.Label(self.main_frame, textvariable=self.heat_state_var, style='Gray.TLabel', anchor='center', relief='sunken')
        self.heat_label.grid(row=main_grid_row_idx, column=0, columnspan=2, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        # --- END MODIFICATION ---

        # DATA SIDE: OG Label, Setpoint (Empty), Unit (Empty), Actual, Unit (Empty), Timestamp
        ttk.Label(self.main_frame, text="OG").grid(row=main_grid_row_idx, column=2, sticky='e', padx=5, pady=VERTICAL_PADDING) 
        
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=3, sticky='ew', padx=5, pady=VERTICAL_PADDING) 
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=4, sticky='w', pady=VERTICAL_PADDING) 
        
        self.og_display_label = ttk.Label(self.main_frame, textvariable=self.og_display_var, relief='sunken', anchor='center', width=7)
        self.og_display_label.grid(row=main_grid_row_idx, column=5, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=6, sticky='w', pady=VERTICAL_PADDING) 
        
        self.og_timestamp_label = ttk.Label(self.main_frame, textvariable=self.og_timestamp_var, relief='sunken', anchor='center')
        self.og_timestamp_label.grid(row=main_grid_row_idx, column=7, sticky='ew', padx=5, pady=VERTICAL_PADDING)

        main_grid_row_idx += 1
        
        # --- DATA ROW 4: SG Data & Cooling Indicator ---
        
        # --- MODIFICATION: Moved Cool indicator up ---
        self.cool_label = ttk.Label(self.main_frame, textvariable=self.cool_state_var, style='Gray.TLabel', anchor='center', relief='sunken')
        self.cool_label.grid(row=main_grid_row_idx, column=0, columnspan=2, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        # --- END MODIFICATION ---

        # DATA SIDE: SG Label, Setpoint (Empty), Unit (Empty), Actual, Unit (Empty), Timestamp
        ttk.Label(self.main_frame, text="SG").grid(row=main_grid_row_idx, column=2, sticky='e', padx=5, pady=VERTICAL_PADDING) 
        
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=3, sticky='ew', padx=5, pady=VERTICAL_PADDING) 
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=4, sticky='w', pady=VERTICAL_PADDING) 
        
        self.sg_display_label = ttk.Label(self.main_frame, textvariable=self.sg_display_var, relief='sunken', anchor='center', width=7)
        self.sg_display_label.grid(row=main_grid_row_idx, column=5, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=6, sticky='w', pady=VERTICAL_PADDING) 
        
        self.sg_timestamp_label = ttk.Label(self.main_frame, textvariable=self.sg_timestamp_var, relief='sunken', anchor='center')
        self.sg_timestamp_label.grid(row=main_grid_row_idx, column=7, sticky='ew', padx=5, pady=VERTICAL_PADDING)

        main_grid_row_idx += 1
        
        # --- DATA ROW 5: FG Data & Cooling Restriction Status ---
        
        # --- MODIFICATION: Moved Cool restriction label up ---
        self.cool_restriction_label = ttk.Label(self.main_frame, textvariable=self.cool_restriction_var, style='Gray.TLabel', anchor='center', relief='sunken')
        self.cool_restriction_label.grid(row=main_grid_row_idx, column=0, columnspan=2, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        # --- END MODIFICATION ---
        
        # DATA SIDE: FG Label, Setpoint (Empty), Unit (Empty), Actual, Unit (Empty), Timestamp
        ttk.Label(self.main_frame, text="FG").grid(row=main_grid_row_idx, column=2, sticky='e', padx=5, pady=VERTICAL_PADDING) 
        
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=3, sticky='ew', padx=5, pady=VERTICAL_PADDING) 
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=4, sticky='w', pady=VERTICAL_PADDING) 
        
        self.fg_label = ttk.Label(self.main_frame, textvariable=self.fg_status_var, style='Gray.TLabel', relief='sunken', anchor='center', width=7)
        self.fg_label.grid(row=main_grid_row_idx, column=5, sticky='ew', padx=5, pady=VERTICAL_PADDING)
        ttk.Label(self.main_frame, text="").grid(row=main_grid_row_idx, column=6, sticky='w', pady=VERTICAL_PADDING) 
        
        # --- MODIFICATION: Bind label to new fg_message_var ---
        self.fg_timestamp_label = ttk.Label(self.main_frame, textvariable=self.fg_message_var, relief='sunken', anchor='center')
        self.fg_timestamp_label.grid(row=main_grid_row_idx, column=7, sticky='ew', padx=5, pady=VERTICAL_PADDING) 
        # --- END MODIFICATION ---

        main_grid_row_idx += 1
        
        # --- REMOVED ROW: Cooling Restriction Status was moved up ---
        # self.cool_restriction_label = ttk.Label(...) # REMOVED
        # main_grid_row_idx += 1 # REMOVED
        # --- END REMOVED ROW ---

        # --- Horizontal Separator (Data Grid to System Messages) ---
        ttk.Separator(self.main_frame, orient='horizontal').grid(row=main_grid_row_idx, column=0, columnspan=8, sticky='ew', pady=(10, 5))
        main_grid_row_idx += 1
        
        # --- System Messages Area (Reduced Height to 5 rows) ---
        ttk.Label(self.main_frame, text="System Messages:").grid(row=main_grid_row_idx, column=0, sticky='w', pady=5)
        
        # --- MODIFICATION START: Added Frame and Scrollbar ---
        log_frame = ttk.Frame(self.main_frame)
        log_frame.grid(row=main_grid_row_idx + 1, column=0, columnspan=8, sticky='nsew', padx=5, pady=5)
        
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical')
        self.log_scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.system_message_area = tk.Text(log_frame, height=5, state='disabled', relief='sunken', wrap='word',
                                           yscrollcommand=self.log_scrollbar.set)
        self.system_message_area.grid(row=0, column=0, sticky='nsew')
        
        self.log_scrollbar.config(command=self.system_message_area.yview)
        # --- MODIFICATION END ---
        
        self.main_frame.grid_rowconfigure(main_grid_row_idx + 1, weight=1)

        self._refresh_ui_bindings()
        
        self._populate_brew_session_dropdown()
        
        # --- THIS IS THE FIX ---
        # Start the notification scheduler *after* all widgets are created
        if self.notification_manager:
            self.notification_manager.start_scheduler()
            
        # --- NEW: Set UI Ready Flag ---
        self.ui_ready = True
        # --- END NEW ---
        
        # --- MODIFICATION: Moved background check call here ---
        # Start the check loop *after* the UI is fully built
        self.root.after(5000, self._background_sensor_check)
        # --- END MODIFICATION ---
        
        # --- NEW: Show EULA/Support Popup on Launch ---
        show_on_launch = self.settings_manager.get("show_eula_on_launch", True)
        if show_on_launch:
            # We call _open_support_popup (from PopupManager)
            # Use 'after' to ensure the main UI draws fully first
            self.root.after(100, lambda: self._open_support_popup(is_launch=True))
        # --- END NEW ---

    def _refresh_ui_bindings(self):
        # Set initial background colors
        self._update_relay_status_colors()

        # --- MODIFICATION: Add mapping from Internal Name to Display Name ---
        INTERNAL_TO_DISPLAY_MAP = {
            "Ambient Hold": "Ambient",
            "Beer Hold": "Beer",
            "Ramp-Up": "Ramp",
            "Fast Crash": "Crash",
        }
        
        # Read the full internal name (e.g., "Ramp-Up")
        initial_internal_mode = self.settings_manager.get("control_mode", "Beer Hold")
        
        # Look up the short display name (e.g., "Ramp")
        initial_display_mode = INTERNAL_TO_DISPLAY_MAP.get(initial_internal_mode, "Beer")

        if initial_display_mode in self.control_mode_options:
            self.control_mode_var.set(initial_display_mode)
        else:
            self.control_mode_var.set("Beer") # Default to "Beer"
        # --- END MODIFICATION ---
            
        # Traces for status display color change
        self.heat_state_var.trace_add("write", self._update_relay_status_colors)
        self.cool_state_var.trace_add("write", self._update_relay_status_colors)
        
        # --- NEW FIX: Load Setpoints on launch (Monitoring is OFF by default) ---
        
        # 1. Force a single pass of the controller to populate transient settings
        #    This call is now the *only* one responsible for the initial UI data push,
        #    which includes the "Ramp pre-condition" message.
        self.temp_controller.update_control_logic_and_ui_data()
        
        # 2. Call the comprehensive update which also handles static setpoints when OFF
        # --- THIS IS THE FIX for the "Flashing Message" BUG ---
        # The call below was redundant and was wiping the message. It is now removed.
        # self._update_data_display(is_startup=True) 
        # --- END FIX ---
        
        # --- MODIFICATION: Removed call to _update_monitoring_button_color ---
        
    def _update_relay_status_colors(self, *args):
        # Update HEATING/COOLING display colors
        heat_state = self.heat_state_var.get()
        cool_state = self.cool_state_var.get()
        
        heat_bg = 'lightcoral' if heat_state == "HEATING" else 'gainsboro'
        
        # --- MODIFICATION: Simple ON/OFF logic ---
        cool_bg = 'lightblue1' if cool_state == "COOLING" else 'gainsboro'
        # -------------------------------------------
        
        if self.heat_label: self.heat_label.config(background=heat_bg)
        if self.cool_label: self.cool_label.config(background=cool_bg)
        if self.cool_label: self.cool_label.config(background=cool_bg)

    # --- HANDLERS (PLACEHOLDERS) ---
    def _handle_api_selection_change(self, event):
        selected_api = self.api_service_var.get()
        self.api_manager.set_active_service(selected_api)
        self.settings_manager.set("active_api_service", selected_api) # Ensure the setting is saved immediately
        self._populate_brew_session_dropdown()

    def _handle_control_mode_change(self, event):
        # --- MODIFICATION: Add mapping from Display Name to Internal Name ---
        DISPLAY_TO_INTERNAL_MAP = {
            "Ambient": "Ambient Hold",
            "Beer": "Beer Hold",
            "Ramp": "Ramp-Up",
            "Crash": "Fast Crash",
        }
        
        selected_display_mode = self.control_mode_var.get()
        # Look up the internal name (e.g., "Ramp" -> "Ramp-Up")
        selected_internal_mode = DISPLAY_TO_INTERNAL_MAP.get(selected_display_mode, "Beer Hold")
        
        # Save the full internal name to settings for the controller
        self.settings_manager.set("control_mode", selected_internal_mode)
        # --- END MODIFICATION ---

        # --- ADDED FIX ---
        # If the user selects any mode *other* than Ramp-Up,
        # reset the controller's ramp state.
        if selected_internal_mode != "Ramp-Up":
            self.temp_controller.reset_ramp_state()
        # --- END FIX ---

        # --- NEW FIX: Always refresh setpoint display after changing mode ---
        self.refresh_setpoint_display()
        # -------------------------------------------------------------------
        
    def _handle_brew_session_change(self, event):
        """Saves the currently selected brew session title AND ID to settings."""
        selected_title = self.brew_session_var.get()
        # Find the ID associated with the title in the temporary storage
        selected_id = self.session_id_map.get(selected_title) 

        self.settings_manager.set("brew_session_title", selected_title)
        self.settings_manager.set("current_brew_session_id", selected_id) # CRITICAL: Save the ID for API calls
        
        # Action: Immediately fetch API data upon selecting a new session
        if self.notification_manager:
            self.notification_manager.fetch_api_data_now(selected_id)

    def _toggle_monitoring(self):
        # If the new state is 'ON', the user intended to START monitoring.
        if self.monitoring_var.get() == "ON":
            
            # --- CRITICAL SYNCHRONOUS WRITE ---
            # 1. Synchronously read sensors, calculate control logic, and WRITE initial data to SettingsManager.
            self.temp_controller.update_control_logic_and_ui_data() 
            # ----------------------------------
            
            # 2. Start the monitoring thread (which will periodically WRITE and QUEUE updates).
            self.temp_controller.start_monitoring()
            
            # --- CRITICAL SYNCHRONOUS READ (Final Solution) ---
            # 3. Force UI to READ the newly written data immediately. 
            self.root.after(100, self._update_data_display) # Read back data slightly delayed
            # -------------------------------------------------
        
        # If the new state is 'OFF', the user intended to STOP monitoring.
        else: 
            self.temp_controller.stop_monitoring()
            # --- MODIFICATION: Removed all calls to _update_data_display ---
            # The monitoring loop is now 100% responsible for sending
            # its own "DWELL" and final "OFF" messages.
            # ---------------------------------------------------------------

    def _handle_fan_mode_change(self, event):
        selected_mode = self.fan_var.get()
        self.settings_manager.set("fan_control_mode", selected_mode)
        if selected_mode == "ON":
            self.temp_controller.relay_control.turn_on_fan()
        elif selected_mode == "OFF":
            self.temp_controller.relay_control.turn_off_fan()

    def _handle_settings_menu(self, choice):
        if hasattr(self, '_open_popup_by_name'):
             self._open_popup_by_name(choice)

    def _handle_actions_menu(self, choice):
        print(f"Action triggered: {choice}")
        
        if choice == "Update API & Temp Data":
            # Force an API call (uses the ID set by _handle_brew_session_change)
            current_id = self.settings_manager.get("current_brew_session_id")
            if self.notification_manager:
                self.notification_manager.fetch_api_data_now(current_id) 
            # Force a single temp read/display update for immediate UI feedback
            self.temp_controller.update_control_logic_and_ui_data()
            
        elif choice == "Send Status Message":
             if self.notification_manager:
                self.notification_manager.send_manual_status_message()
             
        elif choice == "Reload Brew Sessions":
             self._populate_brew_session_dropdown()

        elif choice == "Run FG Calculator":
             # This must run on the main thread to safely update the UI when done
             if self.notification_manager:
                self.notification_manager.run_fg_calc_and_update_ui()
        
        # --- NEW HANDLER ---
        elif choice == "Check for Updates":
             self._run_check_for_updates() # Call the new update function
        # --- END NEW HANDLER ---
                
        elif choice == "Reset to Defaults":
             self._confirm_and_reset_defaults()
        
    def _populate_brew_session_dropdown(self):
        """
        [MODIFIED] This function now only sets a 'Loading' message
        and launches the background thread to fetch the data.
        """
        # Set a "loading" message immediately
        self.session_dropdown['values'] = ["Loading..."]
        self.brew_session_var.set("Loading...")
        
        # Start the background thread to do the real work
        threading.Thread(target=self._populate_brew_session_task, daemon=True).start()

    def _populate_brew_session_task(self):
        """
        [NEW] Worker thread to fetch brew sessions without freezing the UI.
        """
        selected_api = self.api_service_var.get()
        session_id_map = {} # New internal map to link titles to IDs
        
        if selected_api == "OFF":
            sessions_from_settings = self.settings_manager.brew_sessions
            sessions_to_display = [title for title in sessions_from_settings if title.strip()]
            # For OFF mode, the title is the ID
            session_id_map = {title: title for title in sessions_to_display}
            
            if not session_id_map:
                sessions_to_display = ["No Sessions Available (API OFF)"]
                session_id_map = {"No Sessions Available (API OFF)": None}
        else:
            # Load sessions via the active API Manager (THIS IS THE BLOCKING CALL)
            api_data = self.api_manager.get_api_data("list_sessions")
            
            # --- NEW ERROR CHECKING ---
            if isinstance(api_data, dict) and "error" in api_data:
                # Log the specific error to the UI's system messages
                self.root.after(0, self.log_system_message, f"API Error: {api_data['error']}")
                sessions_to_display = ["API Error"]
                session_id_map = {"API Error": None}
                # Skip the rest of the parsing
                self.root.after(0, lambda: self._update_session_dropdown_ui(sessions_to_display, session_id_map))
                return # Stop the thread
            # --- END NEW ERROR CHECKING ---
            
            sessions_to_display = []
            if api_data:
                for s in api_data:
                    title = s.get('recipe_title', s.get('id', 'Unknown'))
                    session_id = str(s.get('id'))
                    sessions_to_display.append(title)
                    session_id_map[title] = session_id # Store the actual ID
            
            if not sessions_to_display:
                sessions_to_display = ["API Fetch Failed/No Sessions"]
                session_id_map = {"API Fetch Failed/No Sessions": None}
        
        # Now that we have the data, schedule the UI update on the main thread
        self.root.after(0, lambda: self._update_session_dropdown_ui(sessions_to_display, session_id_map))

    def _update_session_dropdown_ui(self, sessions_to_display, session_id_map):
        """
        [NEW] Safely updates the brew session combobox from the main thread.
        """
        
        # Store the map for later use
        self.session_id_map = session_id_map
        
        # Update the Combobox options
        self.session_dropdown['values'] = sessions_to_display
        
        # --- MODIFICATION: Store the ID to fetch ---
        current_session_id_to_fetch = None
        # --- END MODIFICATION ---
        
        if sessions_to_display:
            current_session_title = self.settings_manager.get("brew_session_title", "")
            
            if not current_session_title or current_session_title not in self.session_id_map:
                 new_selection = sessions_to_display[0]
                 self.brew_session_var.set(new_selection)
                 
                 # Automatically save the new default selection's title and ID
                 self.settings_manager.set("brew_session_title", new_selection)
                 # --- MODIFICATION: Capture the ID ---
                 current_session_id_to_fetch = self.session_id_map.get(new_selection)
                 self.settings_manager.set("current_brew_session_id", current_session_id_to_fetch)
                 # --- END MODIFICATION ---
                 
            else:
                 # If the saved title is valid, ensure the variable is set to the correct title
                 self.brew_session_var.set(current_session_title) 
                 # And ensure the corresponding ID is saved
                 # --- MODIFICATION: Capture the ID ---
                 current_session_id_to_fetch = self.session_id_map.get(current_session_title)
                 self.settings_manager.set("current_brew_session_id", current_session_id_to_fetch)
                 # --- END MODIFICATION ---
        else:
             self.brew_session_var.set("")
             self.settings_manager.set("brew_session_title", "")
             self.settings_manager.set("current_brew_session_id", None)
             
        # --- MODIFICATION: Trigger API fetch on launch ---
        # After populating the list, if API is ON, fetch data for the selected session
        if self.api_service_var.get() != "OFF":
            if current_session_id_to_fetch and self.notification_manager:
                print(f"[UI] Triggering auto-fetch for session ID: {current_session_id_to_fetch}")
                # This function is already threaded and will log to the UI
                self.notification_manager.fetch_api_data_now(current_session_id_to_fetch)
            elif not current_session_id_to_fetch:
                self.log_system_message("Auto-fetch skipped: No valid brew session ID found.")
        # --- END MODIFICATION ---
    
    # --- QUEUE HANDLING ---
    def _poll_ui_update_queue(self):
        """Processes the queue for logging only, and reschedules itself."""
        try:
            while True:
                # Only check for log_message task
                task, args = self.ui_update_queue.get_nowait()
                if task == "log_message": self._log_system_message(*args)
                
                # NOTE: task "update_data" is ignored/removed here.
                
                self.ui_update_queue.task_done()
        except queue.Empty: pass
        finally:
            if self.root.winfo_exists(): 
                 # Final correct polling interval after previous testing
                 self.root.after(50, self._poll_ui_update_queue)    

    # --- FIX: LOGGING ORDER AND TIMESTAMP FORMAT ---
    def _log_system_message(self, message):
        # --- FIX: Check if the widget attribute exists before accessing it ---
        if hasattr(self, 'system_message_area') and self.system_message_area.winfo_exists():
        # --- END FIX ---
            # --- UPDATED TIMESTAMP FORMAT ---
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # --------------------------------
            log_entry = f"[{timestamp}] {message}\n"
            self.system_message_area.config(state='normal')
            self.system_message_area.insert("1.0", log_entry) # Insert at the top
            self.system_message_area.config(state='disabled')
    # ---------------------------------------------

    def log_system_message(self, message):
        self.ui_update_queue.put(("log_message", (message,)))

    def push_data_update(self, **kwargs):
        """
        [CRITICAL FIX] Bypasses queue.Queue and uses Tkinter's scheduler to force 
        execution of the data read on the main thread.
        
        This method receives the raw data directly from the background thread via kwargs.
        """
        if self.root.winfo_exists():
             # self.root.after(0, ...) is the most aggressive thread-safe way to update UI variables.
             # Pass the kwargs directly to the lambda wrapper, which calls _update_data_display(direct_data=kwargs)
             self.root.after(0, lambda: self._update_data_display(direct_data=kwargs))
             
    # --- UI REFRESH (COMBINED) ---
    def _update_data_display(self, is_startup=False, is_setpoint_change=False, is_stop=False, direct_data=None):
        """
        Pulls all data from SettingsManager OR uses direct_data to update UI variables.
        Called from the main thread via root.after(0).
        """
        
        # 1. Get Control Settings for unit conversion
        settings = self.settings_manager.get_all_control_settings()
        units = settings['temp_units']
        
        # --- CRITICAL FIX: Centralized data validation and display formatting ---
        def format_for_display(value, type_hint="temp"):
             if isinstance(value, str) and value in ["--.-", "-.---", "Pending", "--:--:--", "N/A"]:
                 return value
             # --- FIX: Added check for full timestamp string ---
             if isinstance(value, str) and len(value) > 10: # It's a full timestamp
                 return value
             # -------------------------------------------------
             try:
                 temp = float(value)
                 if type_hint == "temp":
                     # Apply F to C conversion if needed
                     display_val = temp if units == "F" else ((temp - 32) * 5/9)
                     return f"{display_val:.1f}"
                 elif type_hint == "sg":
                     # --- MODIFICATION: Handle non-SG values that are passed in ---
                     if value == 0.0 or value == 0: return "-.---"
                     if temp < 0.1: return "-.---" # Catch other invalid SG numbers
                     # --- END MODIFICATION ---
                     return f"{temp:.3f}"
                 else:
                     return str(value)
             except (ValueError, TypeError):
                 # Fallback for corrupted/invalid numeric data
                 # --- MODIFICATION: Return correct format for type ---
                 if type_hint == "sg": return "-.---"
                 else: return "--.-"
                 # --- END MODIFICATION ---
        # -----------------------------------------------------------------------

        # --- DATA RETRIEVAL (PRIORITIZE DIRECT PUSHED DATA) ---
        
        amb_timestamp = self.settings_manager.get("amb_temp_timestamp", "--:--:--")
        sg_timestamp = self.settings_manager.get("sg_timestamp_var", "----/--/-- --:--:--")
        og_timestamp = self.settings_manager.get("og_timestamp_var", "----/--/-- --:--:--")
        
        # --- MODIFICATION: Add map for mode translation ---
        INTERNAL_TO_DISPLAY_MAP = {
            "Ambient Hold": "Ambient",
            "Beer Hold": "Beer",
            "Ramp-Up": "Ramp",
            "Fast Crash": "Crash",
            "OFF": "OFF"
        }
        # --- END MODIFICATION ---
        
        # --- NEW: Define sensor_error variable ---
        sensor_error = ""
        # --- END NEW ---
        
        if direct_data and not is_stop:
            # Use data pushed directly from the Temperature Controller (Bypasses read failure)
            beer_actual = direct_data.get("beer_temp", "--.-")
            amb_actual = direct_data.get("amb_temp", "--.-")
            current_amb_min = direct_data.get("amb_min", "--.-")
            current_amb_max = direct_data.get("amb_max", "--.-") 
            current_amb_target = direct_data.get("amb_target", "--.-") 
            current_beer_setpoint = direct_data.get("beer_setpoint", "--.-")
            heat_state = direct_data.get("heat_state", "Heating OFF")
            cool_state = direct_data.get("cool_state", "Cooling OFF")
            
            # --- MODIFICATION: Translate internal mode to display mode ---
            internal_mode = direct_data.get("current_mode", self.control_mode_var.get())
            display_mode = INTERNAL_TO_DISPLAY_MAP.get(internal_mode, "Beer")
            # --- END MODIFICATION ---
            
            ramp_is_finished = direct_data.get("ramp_is_finished")
            
            # --- MODIFICATION: Get the pre-formatted message ---
            ramp_target_message = direct_data.get("ramp_target_message", "")
            # --- END MODIFICATION ---

            # --- NEW: Get sensor error message ---
            sensor_error = direct_data.get("sensor_error_message", "")
            # --- END NEW ---

        else:
            # Fallback for initial load (is_startup) or stop monitoring (is_stop)
            current_amb_min = self.settings_manager.get("amb_min_setpoint", settings.get("ambient_hold_f", "--.-"))
            current_amb_max = self.settings_manager.get("amb_max_setpoint", settings.get("ambient_hold_f", "--.-"))
            current_amb_target = self.settings_manager.get("amb_target_setpoint", settings.get("ambient_hold_f", "--.-")) 
            current_beer_setpoint = self.settings_manager.get("beer_setpoint_current", settings.get("beer_hold_f", "--.-"))
            
            beer_actual = self.settings_manager.get("beer_temp_actual", "--.-")
            amb_actual = self.settings_manager.get("amb_temp_actual", "--.-")

            heat_state = self.settings_manager.get("heat_state", "Heating OFF")
            cool_state = self.settings_manager.get("cool_state", "Cooling OFF")

            # --- MODIFICATION: Translate internal mode to display mode ---
            internal_mode = self.settings_manager.get("control_mode")
            display_mode = INTERNAL_TO_DISPLAY_MAP.get(internal_mode, "Beer")
            # --- END MODIFICATION ---
            
            ramp_is_finished = False
            ramp_target_message = "" # Clear message on stop

            # --- NEW: Get sensor error from settings ---
            sensor_error = self.settings_manager.get("sensor_error_message", "")
            if is_stop:
                sensor_error = "" # Clear error on stop
            # --- END NEW ---

        # --- 2. Format and Apply Final Setpoint Logic ---
        
        is_monitoring_on = self.monitoring_var.get() == "ON"

        # 2a. Get formatted values
        display_amb_target = format_for_display(current_amb_target)
        display_beer_setpoint = format_for_display(current_beer_setpoint)
        
        if is_monitoring_on:
            # --- MODIFICATION: Use display_mode ---
            if display_mode == "Ambient":
                display_beer_setpoint = "--.-"
            elif display_mode in ["Beer", "Ramp", "Crash"]:
                display_amb_target = "--.-"
            # --- END MODIFICATION ---
        
        # 2b. Set Ambient Setpoint
        self.amb_setpoint_min_var.set(display_amb_target)

        # 2c. Set Beer Setpoint
        self.beer_setpoint_var.set(display_beer_setpoint)

        # 2d. Set Actuals
        self.amb_actual_var.set(format_for_display(amb_actual))
        self.beer_actual_var.set(format_for_display(beer_actual))
        
        # 2e. Create Ambient Range String (e.g., "36.0 — 38.0")
        formatted_min = format_for_display(current_amb_min)
        formatted_max = format_for_display(current_amb_max)
        range_string = f"{formatted_min} – {formatted_max}"
        
        if formatted_min == "--.-" or formatted_max == "--.-":
            range_string = "--.-"
        elif formatted_min == "0.0" and formatted_max == "0.0":
             range_string = "--.-" # Handle the default 0.0/0.0 on init

        # 2f. Set Ambient Target Range
        # --- MODIFICATION: Check for Thermostatic Ramp ---
        if display_mode == "Ramp" and range_string == "--.-" and is_monitoring_on:
            self.amb_timestamp_var.set("N/A (Beer Control)")
        else:
            self.amb_timestamp_var.set(f"Target Range {range_string}") 
        # --- END MODIFICATION ---
        
        # 2g. Set Gravity Timestamps
        self.og_timestamp_var.set(og_timestamp) 
        self.sg_timestamp_var.set(sg_timestamp) 
        
        # --- 3. Apply Relay States ---
        if is_stop:
            self.heat_state_var.set("Heating OFF")
            self.cool_state_var.set("Cooling OFF")
        else:
            self.heat_state_var.set(heat_state)
            self.cool_state_var.set(cool_state)
        
        # 4. Apply Gravity Data (Always read from SettingsManager)
        self.sg_display_var.set(format_for_display(self.settings_manager.get("sg_display_var", "-.---"), type_hint="sg"))
        self.og_display_var.set(format_for_display(self.settings_manager.get("og_display_var", "-.---"), type_hint="sg"))
        
        # --- MODIFICATION: FG Display Logic ---
        fg_value = self.settings_manager.get("fg_value_var", "-.---")
        fg_status_message = self.settings_manager.get("fg_status_var", "Pending")
        
        self.fg_status_var.set(format_for_display(fg_value, type_hint="sg"))
        self.fg_message_var.set(fg_status_message)
        
        # Set color
        if fg_status_message == "Stable":
            self.fg_label.config(style="MediumGreen.TLabel")
        else:
            self.fg_label.config(style="Gray.TLabel")
        # --- END MODIFICATION ---
        
        # --- NEW: Cooling Restriction Display Logic (MODIFIED) ---
        restriction_status = self.settings_manager.get("cool_restriction_status", "")
        
        # --- MODIFICATION: Clear expired messages if monitoring is OFF ---
        if not is_monitoring_on and restriction_status:
            # Check for a time-based message
            if " until " in restriction_status:
                try:
                    # Extract time string (e.g., "20:55:36")
                    time_str = restriction_status.rsplit(' ', 1)[-1]
                    
                    # Parse it
                    expire_time = datetime.strptime(time_str, "%H:%M:%S").time()
                    
                    # Check if it's in the past
                    if datetime.now().time() > expire_time:
                        restriction_status = "" # Clear the local variable
                        
                        # --- THIS IS THE FIX ---
                        self.settings_manager.set("cool_restriction_status", "")
                        # --- END FIX ---
                        
                except (ValueError, IndexError):
                    pass # Failed to parse, just show the old message
        # --- END MODIFICATION ---
        
        self.cool_restriction_var.set(restriction_status)
        
        # --- LOGIC RE-ORDERED: Prioritize Sensor Error ---
        if sensor_error:
            # Sensor error (highest priority)
            self.cool_restriction_label.config(style="AlertRed.TLabel")
            self.cool_restriction_var.set(sensor_error)
            
        elif "FAIL-SAFE" in restriction_status:
            # Red background, bold white text
            self.cool_restriction_label.config(style="AlertRed.TLabel")
        
        # --- THIS IS THE FIX ---
        # Corrected typo from "restriction_s" to "restriction_status"
        elif "DWELL" in restriction_status:
        # --- END FIX ---
            # Yellow background, black text
            self.cool_restriction_label.config(style="Yellow.TLabel")
        else:
            # No restriction, default gray background, no text
            self.cool_restriction_label.config(style="Gray.TLabel")
            self.cool_restriction_var.set("") # Ensure no residual text
        # --- END NEW LOGIC ---

        # --- 5. MODIFICATION: Set Ramp-Up Target Field ---
        
        # --- THIS IS THE FIX ---
        # The redundant "if ramp_is_finished:" check is removed.
        # We now *only* trust the message from the controller.
        if display_mode == "Ramp" and (is_monitoring_on or (direct_data and not is_stop)):
            # Just set the message provided by the controller
            # This will be "Ramp pre-condition", "Target...", "Ramp Landing...", or "Ramp Finished"
            self.ramp_end_target_var.set(ramp_target_message)
        else:
            self.ramp_end_target_var.set("") # Clear if not in ramp mode
        # --- END FIX ---
        
        # --- 5b. MODIFICATION: Set Actual Temp Field Colors ---
        
        # Default to Gray
        amb_style = 'Gray.TLabel'
        beer_style = 'Gray.TLabel'

        if is_monitoring_on:
            try:
                # Convert all needed values to float for comparison
                f_amb_actual = float(amb_actual)
                f_beer_actual = float(beer_actual)

                # --- Ambient Logic ---
                # Only apply if ambient min/max are valid (not 0.0)
                f_amb_min = float(current_amb_min)
                f_amb_max = float(current_amb_max)
                if f_amb_min != 0.0 or f_amb_max != 0.0:
                    if f_amb_actual > f_amb_max:
                        amb_style = 'Red.TLabel'
                    elif f_amb_actual < f_amb_min:
                        amb_style = 'Blue.TLabel'

                # --- Beer Logic (Conditional) ---
                # --- MODIFICATION: Only run Beer logic if mode is NOT Ambient Hold ---
                if display_mode != "Ambient":
                    # Only apply if beer setpoint is valid (not 0.0)
                    f_beer_setpoint = float(current_beer_setpoint)
                    if f_beer_setpoint != 0.0:
                        deadband = 0.1 # Deadband for float comparison
                        if f_beer_actual > (f_beer_setpoint + deadband):
                            beer_style = 'Red.TLabel'
                        elif f_beer_actual < (f_beer_setpoint - deadband):
                            beer_style = 'Blue.TLabel'
                # --- END MODIFICATION ---

            except (ValueError, TypeError):
                # This catches cases where values are "--.-" or other non-floats
                pass # Styles will remain 'Gray.TLabel'
        
        # Apply the determined styles
        self.amb_actual_label.config(style=amb_style)
        self.beer_actual_label.config(style=beer_style)
        # --- END MODIFICATION ---
        
        # --- 6. MODIFICATION: Set NEW Monitoring Indicator (Integrated into Combobox) ---
        if self.monitoring_button: # Check if Combobox exists
            if is_monitoring_on:
                # --- NEW: If sensor error, force RED ---
                if sensor_error:
                    self.monitoring_button.config(style="Red.TCombobox")
                # --- END NEW ---
                else:
                    self.heartbeat_toggle = not self.heartbeat_toggle
                    # Use the new MediumGreen style for the lighter pulse
                    new_style = "MediumGreen.TCombobox" if self.heartbeat_toggle else "DarkGreen.TCombobox"
                    self.monitoring_button.config(style=new_style)
            else:
                # When monitoring is off, force to Red Combobox style
                self.monitoring_button.config(style="Red.TCombobox")
        # --- END MODIFICATION ---
        
    # --- UI REFRESH HELPER ---
    def refresh_setpoint_display(self):
        """Forces an update of only static setpoints from SettingsManager."""
        if self.root.winfo_exists():
            # Use root.after(0) for safe, main-thread execution
            
            # --- MODIFICATION START: Force controller to re-calc and push ---
            # This forces the controller to re-read the settings *now*
            # and push a new update, solving any race conditions.
            if self.temp_controller:
                self.temp_controller.update_control_logic_and_ui_data()
            # --- MODIFICATION END ---
            
            # This call ensures the UI updates even if monitoring is OFF.
            self.root.after(0, lambda: self._update_data_display(is_setpoint_change=True))
            
    def _on_closing_ui(self):
        print("UIManager: Initiating shutdown sequence...")
        if self.root and hasattr(self.root, 'winfo_exists') and self.root.winfo_exists(): self.root.destroy()
        
    def _background_sensor_check(self):
        """
        [NEW] Periodically calls the controller to read sensors and push UI data,
        but ONLY when monitoring is OFF. This is to clear stale sensor errors.
        """
        try:
            if self.root.winfo_exists():
                # Only run this check if monitoring is OFF
                if self.monitoring_var.get() == "OFF":
                    # This function only reads sensors and pushes data,
                    # it does NOT control relays.
                    if self.temp_controller:
                        self.temp_controller.update_control_logic_and_ui_data()
                
                # Reschedule itself to run again in 5 seconds
                self.root.after(5000, self._background_sensor_check)
        except Exception as e:
            print(f"Error in background sensor check: {e}")
            # Try to reschedule anyway
            if self.root.winfo_exists():
                self.root.after(5000, self._background_sensor_check)
                
    def _confirm_and_reset_defaults(self):
        """
        [NEW] Displays a confirmation dialog before resetting all settings.
        If confirmed, resets settings and forces the application to close.
        """
        title = "Confirm Reset to Defaults"
        message = (
            "Reset to Defaults will clear all custom entries and settings and reset all to defaults. "
            "ALL custom settings including Notification settings, API & FG settings, and Brew Sessions settings "
            "will be cleared and reset. Do you wish to proceed?"
        )
        
        # Use askokcancel (OK/Cancel), consistent with PID & Tuning
        if messagebox.askokcancel(title, message):
            try:
                # 1. Call the fixed reset function
                self.settings_manager.reset_all_settings_to_defaults()
                
                # 2. Inform user and shut down
                messagebox.showinfo(
                    "Reset Complete",
                    "All settings have been reset to defaults. The application will now close. Please restart it."
                )
                
                # 3. Trigger the clean shutdown sequence
                if self.root:
                    self.root.destroy()
                    
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during reset: {e}")
                
    def _run_check_for_updates(self):
        """
        Runs git pull in the background thread to check for and apply updates.
        """
        def update_task():
            # Get the path to the directory containing the project (where .git is)
            # This relies on main.py knowing it's in src/ and the repo being its parent
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            self.log_system_message("Checking for updates via Git...")
            
            try:
                # 1. Ensure the remote connection is active and fetch status
                result = subprocess.run(
                    ['git', 'fetch'], 
                    cwd=project_dir, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 2. Check for differences (local branch vs remote tracking branch)
                result = subprocess.run(
                    ['git', 'status', '-uno'], 
                    cwd=project_dir, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                status_output = result.stdout
                
                if "up to date" in status_output.lower():
                    self.log_system_message("Application is already up to date. No new updates found.")
                elif "can be fast-forwarded" in status_output.lower() or "behind" in status_output.lower():
                    self.log_system_message("New update found! Running git pull...")
                    
                    # 3. Perform the actual pull
                    pull_result = subprocess.run(
                        ['git', 'pull'], 
                        cwd=project_dir, 
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if "Already up to date" in pull_result.stdout:
                         self.log_system_message("Update finished, but no files were actually changed (git status was slightly delayed).")
                    else:
                         self.log_system_message("Update SUCCESSFUL. Please restart the application to apply changes.")
                         
                elif "Your branch is ahead" in status_output.lower():
                    self.log_system_message("Local code has been modified. Cannot update; please run 'git reset --hard' manually.")
                else:
                    self.log_system_message(f"Update failed or status unclear. Output: {status_output.splitlines()[0]}")

            except subprocess.CalledProcessError as e:
                self.log_system_message(f"ERROR: Git command failed. Output: {e.stderr.strip()}")
            except FileNotFoundError:
                self.log_system_message("ERROR: Git executable not found. Ensure Git is installed.")
            except Exception as e:
                self.log_system_message(f"Unexpected error during update: {e}")

        # Execute the task in a new thread
        import subprocess # Local import to reduce overhead
        threading.Thread(target=update_task, daemon=True).start()
