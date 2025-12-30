
import warnings
import os
import sys

# Simulate the environment
# We don't have creds, but we can check if import triggers warning
try:
    print("--- Attempting suppressed import ---")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, message=".*deprecated.*")
        # warnings.simplefilter("ignore") # Try cleaner sweep if regex fails
        from vertexai.generative_models import GenerativeModel
        import vertexai
        
    print("--- Import successful without crash (warning should be silenced) ---")
    
except ImportError:
    print("vertexai not installed")
except Exception as e:
    print(f"Broke: {e}")
