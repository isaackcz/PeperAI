#!/usr/bin/env python3

try:
    print("Starting import test...")
    import model_service
    print("model_service imported successfully")
except Exception as e:
    import traceback
    print(f"Error importing model_service: {e}")
    traceback.print_exc()