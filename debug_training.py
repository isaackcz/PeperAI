#!/usr/bin/env python3
"""
Debug script to test training functionality step by step
"""

import sys
import os
from pathlib import Path

print("=== Debug Training Script ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Test dataset access
dataset_path = "/app/datasets/Bell Pepper dataset 1"
print(f"\nDataset path exists: {os.path.exists(dataset_path)}")
if os.path.exists(dataset_path):
    print(f"Dataset contents: {os.listdir(dataset_path)}")

# Test imports
print("\n=== Testing Imports ===")
try:
    sys.path.append('/app/utils')
    print("Added /app/utils to Python path")
    
    from anfis_trainer import ANFISModel
    print("✓ ANFISModel imported successfully")
    
    from feature_extractor import BellPepperFeatureExtractor
    print("✓ BellPepperFeatureExtractor imported successfully")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()

# Test basic functionality
print("\n=== Testing Basic Functionality ===")
try:
    feature_extractor = BellPepperFeatureExtractor()
    print("✓ Feature extractor created successfully")
    
    # Test if we can create directories
    test_dirs = ['models', 'training_output', 'data']
    for dir_name in test_dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ Directory '{dir_name}' created/verified")
        
except Exception as e:
    print(f"✗ Basic functionality error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")