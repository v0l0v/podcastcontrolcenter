import os
import sys

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.config.settings import CTA_TEXTS_DIR, AUDIO_ASSETS_DIR, DIR_CONFIG, CONFIG

print("--- CONFIGURATION VERIFICATION ---")
print(f"Directory Config in JSON: {DIR_CONFIG}")
print(f"Resolved CTA_TEXTS_DIR: {CTA_TEXTS_DIR}")
print(f"Resolved AUDIO_ASSETS_DIR: {AUDIO_ASSETS_DIR}")

# Check if they exist
print(f"CTA_TEXTS_DIR exists: {os.path.exists(CTA_TEXTS_DIR)}")
print(f"AUDIO_ASSETS_DIR exists: {os.path.exists(AUDIO_ASSETS_DIR)}")

# Check if they match the default if not changed
assert "cta_texts" in CTA_TEXTS_DIR
assert "audio_assets" in AUDIO_ASSETS_DIR

print("\n--- APP.PY CHECK ---")
# Basic syntax check for app.py to ensure no indentation errors
try:
    with open("app.py", "r") as f:
        compile(f.read(), "app.py", "exec")
    print("app.py syntax is valid.")
except Exception as e:
    print(f"app.py syntax error: {e}")
