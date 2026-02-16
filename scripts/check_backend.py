#!/usr/bin/env python3
import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("✅ Successfully imported app.main")
except Exception as e:
    print(f"❌ Failed to import app.main: {e}")
    import traceback
    traceback.print_exc()
