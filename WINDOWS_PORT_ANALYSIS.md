# FermVault Windows Port – Analysis & Recommended Fixes

## Executive Summary

FermVault's Windows installation fails because it unconditionally installs `lgpio` and `rpi-lgpio`, which are Raspberry Pi–specific packages. `lgpio` cannot build on Windows (requires SWIG, native toolchain). KegLevel Lite works on Windows by (1) limiting those packages to Linux in `requirements.txt` and (2) using a try/except + MockGPIO pattern in Python for hardware detection.

---

## Detailed Findings

### 1. requirements.txt

| App        | lgpio                     | rpi-lgpio                 | Result on Windows         |
|-----------|---------------------------|---------------------------|---------------------------|
| **KegLevel Lite** | `; sys_platform == 'linux'` | `; sys_platform == 'linux'` | Skipped, install succeeds |
| **FermVault**    | Unconditional              | Unconditional              | Fails – lgpio build error |

**FermVault error:** `lgpio` has no Windows wheels. Pip builds from source, which requires SWIG; build fails with `error: command 'swig.exe' failed: None`.

---

### 2. install.bat

Both apps use the same approach:

- Create venv  
- `pip install -r requirements.txt`  
- Create shortcut  

No install-script changes are needed; success depends on `requirements.txt` not pulling Pi-only deps on Windows.

---

### 3. Python Hardware Detection / MockGPIO

| App             | Location          | Pattern                                                | Windows behavior          |
|-----------------|-------------------|--------------------------------------------------------|---------------------------|
| **KegLevel Lite** | `sensor_logic.py` | `try: import RPi.GPIO` + `except: use MockGPIO`        | Uses MockGPIO, runs in sim |
| **FermVault**     | `relay_control.py`| Direct `import RPi.GPIO as GPIO` at top                | Import fails, app crashes |

KegLevel Lite’s `sensor_logic.py`:

```python
# --- HARDWARE IMPORT SAFETY ---
try:
    import RPi.GPIO as GPIO
    IS_RASPBERRY_PI_MODE = True
except (ImportError, RuntimeError):
    print("WARNING: RPi.GPIO not found. Running in simulation mode.")
    IS_RASPBERRY_PI_MODE = False
    class MockGPIO:
        BCM = "BCM"; IN = "IN"; PUD_DOWN = "PUD_DOWN"; RISING = "RISING"
        @staticmethod
        def setmode(mode): pass
        # ... (setup, output, input, cleanup, etc.)
    GPIO = MockGPIO
```

FermVault’s `relay_control.py`:

```python
import RPi.GPIO as GPIO  # No fallback – fails on Windows
```

On Windows, without `rpi-lgpio`, `RPi.GPIO` does not exist. So `relay_control.py` must use the same kind of try/except + MockGPIO pattern.

---

### 4. MockGPIO Interface Required for relay_control.py

FermVault’s `relay_control.py` uses:

- `GPIO.BCM`
- `GPIO.HIGH`, `GPIO.LOW`
- `GPIO.setmode(mode)`
- `GPIO.setwarnings(False)`
- `GPIO.setup(pin, IN)` and `GPIO.setup(pin, OUT)`
- `GPIO.output(pin, state)`
- `GPIO.input(pin)`
- `GPIO.cleanup()`

MockGPIO must provide compatible stubs for all of these.

---

## Recommended Changes (FermVault only)

### Change 1: requirements.txt – platform markers

Add `; sys_platform == 'linux'` to both Pi-only packages so they are installed only on Linux/Raspberry Pi:

```
certifi==2025.11.12
charset-normalizer==3.4.4
idna==3.11
lgpio==0.2.2.0; sys_platform == 'linux'
pytz==2025.2
requests==2.32.5
rpi-lgpio==0.6; sys_platform == 'linux'
urllib3==2.5.0
kivy[base]
```

This keeps Pi behavior unchanged and makes Windows installs succeed.

---

### Change 2: relay_control.py – hardware detection + MockGPIO

Replace the direct `import RPi.GPIO as GPIO` with a try/except pattern and a MockGPIO class that matches the API used by `relay_control.py`:

- `BCM`, `HIGH`, `LOW`, `IN`, `OUT`
- `setmode()`, `setwarnings()`, `setup()`, `output()`, `input()`, `cleanup()`

On success: use real GPIO as today.  
On failure: use MockGPIO and print a simulation warning.

No changes are needed to `main_kivy.py`, `temperature_controller.py`, or the batch scripts, since they already call RelayControl methods that MockGPIO will implement as no-ops or simple stubs.

---

## Impact on Raspberry Pi

- **requirements.txt:** On Linux, `sys_platform == 'linux'` is true; `lgpio` and `rpi-lgpio` are still installed. No change in behavior.
- **relay_control.py:** On Linux, `import RPi.GPIO` succeeds; MockGPIO is never used. No change in behavior.

---

## Optional: install.bat robustness

If you want install.bat to explicitly avoid Pi packages on Windows (belt-and-suspenders), you could add a Windows-only requirements file (e.g. `requirements-win.txt`) that omits lgpio and rpi-lgpio, and use that on Windows instead of `requirements.txt`. This is optional; the platform markers in `requirements.txt` alone are sufficient.
