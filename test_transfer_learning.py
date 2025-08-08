#!/usr/bin/env python3
"""
Test script to debug transfer learning model predictions
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

import numpy as np
import cv2
from pathlib import Path
import pickle
import tensorflow as tf
from tensorflow.keras.models import load_model

def test_transfer_learning_prediction():
    """Test Transfer Learning prediction"""
    print("=== Testing Transfer Learning Prediction ===")
    
    try:
        # Load preprocessing data
        preprocess_path = Path("./training_output/ensemble_preprocessing.pkl")
        with open(preprocess_path, 'rb') as f:
            preprocessing_data = pickle.load(f)
            label_mapping = preprocessing_data['data_info']['label_mapping']
        
        # Load transfer learning model
        models_dir = Path("./models")
        transfer_model_path = models_dir / "ensemble_transfer_model.h5"
        
        if transfer_model_path.exists():
            transfer_model = load_model(str(transfer_model_path))
            print("✅ Loaded transfer learning model")
        else:
            print("❌ Transfer learning model not found")
            return
        
        # Create test images for different categories
        test_cases = [
            ("red_bell_pepper", np.random.randint(100, 255, (224, 224, 3), dtype=np.uint8)),  # Red
            ("green_bell_pepper", np.random.randint(0, 100, (224, 224, 3), dtype=np.uint8)),  # Green
            ("yellow_bell_pepper", np.random.randint(150, 255, (224, 224, 3), dtype=np.uint8)),  # Yellow
        ]
        
        for test_name, test_img in test_cases:
            print(f"\n--- Testing {test_name} ---")
            
            # Preprocess image
            img = cv2.resize(test_img, (224, 224))
            img = img.astype('float32') / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Make prediction
            predictions = transfer_model.predict(img)
            probabilities = predictions[0]
            
            # Create probability dictionary
            prob_dict = {}
            for i, class_name in enumerate(label_mapping.values()):
                prob_dict[class_name] = float(probabilities[i])
            
            print(f"Raw probabilities: {prob_dict}")
            
            # Get best prediction
            predicted_class_idx = np.argmax(probabilities)
            predicted_class = list(label_mapping.values())[predicted_class_idx]
            confidence = float(probabilities[predicted_class_idx])
            
            print(f"Best classification: {predicted_class} with confidence {confidence:.3f}")
            
            # Show top 3 predictions
            sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            print("Top 3 predictions:")
            for i, (class_name, prob) in enumerate(sorted_probs[:3]):
                print(f"  {i+1}. {class_name}: {prob:.3f} ({prob*100:.1f}%)")
        
    except Exception as e:
        print(f"Error in transfer learning prediction test: {e}")

def test_with_real_image():
    """Test with a real image from the dataset"""
    print("\n=== Testing with Real Dataset Image ===")
    
    try:
        # Try to find a real image from the dataset
        dataset_path = Path("../../datasets/Bell Pepper dataset 1")
        if dataset_path.exists():
            # Look for a ripe bell pepper image
            ripe_path = dataset_path / "Ripe"
            if ripe_path.exists():
                image_files = list(ripe_path.glob("*.jpg")) + list(ripe_path.glob("*.png"))
                if image_files:
                    test_image_path = str(image_files[0])
                    print(f"Using real image: {test_image_path}")
                    
                    # Load preprocessing data
                    preprocess_path = Path("./training_output/ensemble_preprocessing.pkl")
                    with open(preprocess_path, 'rb') as f:
                        preprocessing_data = pickle.load(f)
                        label_mapping = preprocessing_data['data_info']['label_mapping']
                    
                    # Load transfer learning model
                    models_dir = Path("./models")
                    transfer_model_path = models_dir / "ensemble_transfer_model.h5"
                    transfer_model = load_model(str(transfer_model_path))
                    
                    # Load and preprocess image
                    img = cv2.imread(test_image_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (224, 224))
                    img = img.astype('float32') / 255.0
                    img = np.expand_dims(img, axis=0)
                    
                    # Make prediction
                    predictions = transfer_model.predict(img)
                    probabilities = predictions[0]
                    
                    # Create probability dictionary
                    prob_dict = {}
                    for i, class_name in enumerate(label_mapping.values()):
                        prob_dict[class_name] = float(probabilities[i])
                    
                    print(f"Probabilities: {prob_dict}")
                    
                    # Get best prediction
                    predicted_class_idx = np.argmax(probabilities)
                    predicted_class = list(label_mapping.values())[predicted_class_idx]
                    confidence = float(probabilities[predicted_class_idx])
                    
                    print(f"Best classification: {predicted_class} with confidence {confidence:.3f}")
                    
                    # Show all predictions
                    sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
                    print("All predictions:")
                    for class_name, prob in sorted_probs:
                        print(f"  {class_name}: {prob:.3f} ({prob*100:.1f}%)")
                    
                else:
                    print("No image files found in Ripe directory")
            else:
                print("Ripe directory not found")
        else:
            print("Dataset not found")
            
    except Exception as e:
        print(f"Error testing with real image: {e}")

if __name__ == "__main__":
    test_transfer_learning_prediction()
    test_with_real_image() 