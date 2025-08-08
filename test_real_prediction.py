#!/usr/bin/env python3
"""
Test script to debug real model predictions
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

import numpy as np
import cv2
from pathlib import Path
import pickle

# Import our modules
from utils.feature_extractor import BellPepperFeatureExtractor
from utils.anfis_trainer import ANFISModel

def test_model_loading():
    """Test if models are loading correctly"""
    print("=== Testing Model Loading ===")
    
    # Check if models exist
    models_dir = Path("./models")
    training_output_dir = Path("./training_output")
    
    print(f"Models directory exists: {models_dir.exists()}")
    print(f"Training output directory exists: {training_output_dir.exists()}")
    
    # Check model files
    model_files = list(models_dir.glob("*.pkl"))
    print(f"ANFIS model files: {len(model_files)}")
    for f in model_files:
        print(f"  - {f.name}")
    
    # Check transfer learning model
    transfer_model = models_dir / "ensemble_transfer_model.h5"
    print(f"Transfer model exists: {transfer_model.exists()}")
    
    # Check preprocessing data
    preprocess_path = training_output_dir / "ensemble_preprocessing.pkl"
    print(f"Preprocessing data exists: {preprocess_path.exists()}")
    
    if preprocess_path.exists():
        with open(preprocess_path, 'rb') as f:
            preprocessing_data = pickle.load(f)
            print(f"Preprocessing data keys: {list(preprocessing_data.keys())}")
            if 'data_info' in preprocessing_data:
                print(f"Label mapping: {preprocessing_data['data_info']['label_mapping']}")

def test_feature_extraction():
    """Test feature extraction"""
    print("\n=== Testing Feature Extraction ===")
    
    # Create a test image (you can replace this with a real image path)
    test_image_path = "./test_image.jpg"
    
    if not os.path.exists(test_image_path):
        print("No test image found, creating dummy image...")
        # Create a dummy image
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(test_image_path, img)
    
    try:
        feature_extractor = BellPepperFeatureExtractor()
        features = feature_extractor.extract_features_from_file(test_image_path)
        
        print(f"Extracted features: {len(features)}")
        print(f"Feature names: {list(features.keys())}")
        
        # Show some feature values
        for name, value in list(features.items())[:5]:
            print(f"  {name}: {value}")
            
        return features
        
    except Exception as e:
        print(f"Error in feature extraction: {e}")
        return None

def test_anfis_prediction():
    """Test ANFIS prediction"""
    print("\n=== Testing ANFIS Prediction ===")
    
    try:
        # Load preprocessing data
        preprocess_path = Path("./training_output/ensemble_preprocessing.pkl")
        with open(preprocess_path, 'rb') as f:
            preprocessing_data = pickle.load(f)
            label_mapping = preprocessing_data['data_info']['label_mapping']
        
        # Load ANFIS models
        models_dir = Path("./models")
        trained_models = []
        
        for i in range(len(label_mapping)):
            model_path = models_dir / f"ensemble_anfis_class_{i}.pkl"
            if model_path.exists():
                model = ANFISModel()
                model.load_model(str(model_path))
                trained_models.append(model)
                print(f"Loaded ANFIS model for class {i}: {label_mapping.get(i, 'unknown')}")
        
        print(f"Loaded {len(trained_models)} ANFIS models")
        
        # Test prediction
        if trained_models:
            # Create dummy features
            feature_names = ['h_mean', 's_mean', 'v_mean', 'h_std', 's_std', 
                           'v_std', 'glcm_contrast', 'glcm_homogeneity', 
                           'contour_area', 'circularity', 'solidity']
            
            # Create realistic feature values for a red bell pepper
            dummy_features = {
                'h_mean': 0.0,  # Red hue
                's_mean': 0.8,  # High saturation
                'v_mean': 0.7,  # Bright value
                'h_std': 0.1,
                's_std': 0.2,
                'v_std': 0.3,
                'glcm_contrast': 0.5,
                'glcm_homogeneity': 0.6,
                'contour_area': 50000,
                'circularity': 0.8,
                'solidity': 0.9
            }
            
            X = np.array([[dummy_features[name] for name in feature_names]])
            
            # Apply preprocessing
            scaler = preprocessing_data['scaler']
            X_scaled = scaler.transform(X)
            
            print(f"Input features shape: {X.shape}")
            print(f"Scaled features shape: {X_scaled.shape}")
            
            # Get predictions from all models
            probabilities = {}
            for i, model in enumerate(trained_models):
                try:
                    proba = model.predict_proba(X_scaled)[0]
                    class_name = label_mapping.get(i, f'class_{i}')
                    probabilities[class_name] = float(proba)
                    print(f"Model {i} ({class_name}) raw prediction: {proba}")
                except Exception as e:
                    print(f"Error with model {i}: {e}")
            
            # Normalize probabilities to sum to 1
            total_prob = sum(probabilities.values())
            if total_prob > 0:
                probabilities = {k: v / total_prob for k, v in probabilities.items()}
            else:
                # If all probabilities are 0, assign equal probability
                n_classes = len(probabilities)
                probabilities = {k: 1.0 / n_classes for k in probabilities.keys()}
            
            print(f"Normalized probabilities: {probabilities}")
            
            if probabilities:
                best_class = max(probabilities, key=probabilities.get)
                confidence = probabilities[best_class]
                print(f"Best classification: {best_class} with confidence {confidence}")
            
    except Exception as e:
        print(f"Error in ANFIS prediction test: {e}")

if __name__ == "__main__":
    test_model_loading()
    test_feature_extraction()
    test_anfis_prediction() 