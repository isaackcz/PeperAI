#!/usr/bin/env python3
"""
Test Script for Trained Bell Pepper Models
==========================================

This script tests the trained ANFIS, Transfer Learning, and Ensemble models
with sample images from the dataset.
"""

import os
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
import sys
sys.path.append(str(Path(__file__).parent / "app" / "utils"))

from feature_extractor import BellPepperFeatureExtractor
from anfis_trainer import ANFISModel

# Deep Learning imports
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder

class BellPepperModelTester:
    """Test class for trained bell pepper models"""
    
    def __init__(self):
        self.models_dir = Path("./models")
        self.training_output_dir = Path("./training_output")
        self.dataset_path = Path("../datasets/Bell Pepper dataset 1")
        
        # Initialize components
        self.feature_extractor = BellPepperFeatureExtractor()
        self.label_encoder = LabelEncoder()
        
        # Load models
        self.load_models()
        
    def load_models(self):
        """Load all trained models"""
        print("Loading trained models...")
        
        # Load ANFIS models
        self.anfis_models = []
        for i in range(5):
            model_path = self.models_dir / f"ensemble_anfis_class_{i}.pkl"
            if model_path.exists():
                model = ANFISModel()
                model.load_model(str(model_path))
                self.anfis_models.append(model)
                print(f"Loaded ANFIS model {i}")
        
        # Load Transfer Learning model
        transfer_path = self.models_dir / "ensemble_transfer_model.h5"
        if transfer_path.exists():
            self.transfer_model = load_model(str(transfer_path))
            print("Loaded Transfer Learning model")
        
        # Load preprocessing data
        preprocess_path = self.training_output_dir / "ensemble_preprocessing.pkl"
        if preprocess_path.exists():
            with open(preprocess_path, 'rb') as f:
                preprocess_data = pickle.load(f)
                self.label_encoder = preprocess_data['label_encoder']
                self.scaler = preprocess_data['scaler']
                self.data_info = preprocess_data['data_info']
                print("Loaded preprocessing data")
        
        print(f"Loaded {len(self.anfis_models)} ANFIS models and 1 Transfer Learning model")
    
    def predict_anfis(self, image_path: str) -> Dict:
        """Predict using ANFIS models"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features_from_file(image_path)
            feature_names = self.feature_extractor.get_feature_names()
            X = np.array([[features[name] for name in feature_names]])
            
            # Preprocess
            X_scaled = self.scaler.transform(X)
            
            # Get predictions from all models
            probabilities = {}
            for i, model in enumerate(self.anfis_models):
                proba = model.predict_proba(X_scaled)[0]
                class_name = self.label_encoder.classes_[i]
                probabilities[class_name] = float(proba)
            
            # Find best prediction
            best_class = max(probabilities, key=probabilities.get)
            confidence = probabilities[best_class]
            
            return {
                'method': 'ANFIS',
                'prediction': best_class,
                'confidence': confidence,
                'probabilities': probabilities
            }
            
        except Exception as e:
            return {
                'method': 'ANFIS',
                'prediction': 'error',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    def predict_transfer_learning(self, image_path: str) -> Dict:
        """Predict using Transfer Learning model"""
        try:
            # Load and preprocess image
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (224, 224))
            img = img.astype('float32') / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Make prediction
            predictions = self.transfer_model.predict(img)
            probabilities = predictions[0]
            
            # Get class with highest probability
            predicted_class_idx = np.argmax(probabilities)
            predicted_class = self.label_encoder.classes_[predicted_class_idx]
            confidence = float(probabilities[predicted_class_idx])
            
            # Create probability dictionary
            prob_dict = {}
            for i, class_name in enumerate(self.label_encoder.classes_):
                prob_dict[class_name] = float(probabilities[i])
            
            return {
                'method': 'Transfer Learning',
                'prediction': predicted_class,
                'confidence': confidence,
                'probabilities': prob_dict
            }
            
        except Exception as e:
            return {
                'method': 'Transfer Learning',
                'prediction': 'error',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    def predict_ensemble(self, image_path: str) -> Dict:
        """Predict using ensemble (average of ANFIS and Transfer Learning)"""
        try:
            # Get predictions from both models
            anfis_result = self.predict_anfis(image_path)
            transfer_result = self.predict_transfer_learning(image_path)
            
            if 'error' in anfis_result or 'error' in transfer_result:
                return {
                    'method': 'Ensemble',
                    'prediction': 'error',
                    'confidence': 0.0,
                    'probabilities': {},
                    'error': 'One or both models failed'
                }
            
            # Average probabilities
            ensemble_probabilities = {}
            for class_name in self.label_encoder.classes_:
                anfis_prob = anfis_result['probabilities'].get(class_name, 0.0)
                transfer_prob = transfer_result['probabilities'].get(class_name, 0.0)
                ensemble_probabilities[class_name] = (anfis_prob + transfer_prob) / 2
            
            # Get best prediction
            best_class = max(ensemble_probabilities, key=ensemble_probabilities.get)
            confidence = ensemble_probabilities[best_class]
            
            return {
                'method': 'Ensemble',
                'prediction': best_class,
                'confidence': confidence,
                'probabilities': ensemble_probabilities,
                'anfis_result': anfis_result,
                'transfer_result': transfer_result
            }
            
        except Exception as e:
            return {
                'method': 'Ensemble',
                'prediction': 'error',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    def test_sample_images(self, num_samples: int = 5):
        """Test models with sample images from each category"""
        print(f"\nTesting models with {num_samples} samples from each category...")
        print("=" * 80)
        
        categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        
        for category in categories:
            print(f"\n📸 Testing {category.upper()} category:")
            print("-" * 50)
            
            category_path = self.dataset_path / category
            if not category_path.exists():
                print(f"Category path {category_path} does not exist")
                continue
            
            # Get sample images
            image_files = list(category_path.glob("*.jpg"))[:num_samples]
            
            for i, img_path in enumerate(image_files):
                print(f"\n  Sample {i+1}: {img_path.name}")
                print(f"  True label: {category}")
                
                # Test all three models
                anfis_result = self.predict_anfis(str(img_path))
                transfer_result = self.predict_transfer_learning(str(img_path))
                ensemble_result = self.predict_ensemble(str(img_path))
                
                # Print results
                print(f"    ANFIS: {anfis_result['prediction']} ({anfis_result['confidence']:.3f})")
                print(f"    Transfer: {transfer_result['prediction']} ({transfer_result['confidence']:.3f})")
                print(f"    Ensemble: {ensemble_result['prediction']} ({ensemble_result['confidence']:.3f})")
                
                # Check if predictions are correct
                anfis_correct = anfis_result['prediction'] == category
                transfer_correct = transfer_result['prediction'] == category
                ensemble_correct = ensemble_result['prediction'] == category
                
                print(f"    Correct: ANFIS={anfis_correct}, Transfer={transfer_correct}, Ensemble={ensemble_correct}")
    
    def interactive_test(self):
        """Interactive testing with user-provided images"""
        print("\n🎯 Interactive Model Testing")
        print("=" * 50)
        print("You can test the models with any bell pepper image.")
        print("Enter the path to an image file, or 'quit' to exit.")
        
        while True:
            image_path = input("\nEnter image path (or 'quit'): ").strip()
            
            if image_path.lower() == 'quit':
                break
            
            if not os.path.exists(image_path):
                print("❌ File not found. Please enter a valid path.")
                continue
            
            print(f"\n🔍 Testing image: {image_path}")
            print("-" * 40)
            
            # Test all models
            anfis_result = self.predict_anfis(image_path)
            transfer_result = self.predict_transfer_learning(image_path)
            ensemble_result = self.predict_ensemble(image_path)
            
            # Print results
            print(f"ANFIS Prediction: {anfis_result['prediction']} (Confidence: {anfis_result['confidence']:.3f})")
            print(f"Transfer Learning: {transfer_result['prediction']} (Confidence: {transfer_result['confidence']:.3f})")
            print(f"Ensemble: {ensemble_result['prediction']} (Confidence: {ensemble_result['confidence']:.3f})")
            
            # Show detailed probabilities for ensemble
            print(f"\n📊 Ensemble Probabilities:")
            for class_name, prob in ensemble_result['probabilities'].items():
                print(f"  {class_name}: {prob:.3f}")

def main():
    """Main testing function"""
    print("Bell Pepper Model Testing")
    print("=" * 50)
    
    try:
        # Initialize tester
        tester = BellPepperModelTester()
        
        # Test with sample images
        tester.test_sample_images(num_samples=3)
        
        # Interactive testing
        tester.interactive_test()
        
        print("\n✅ Testing completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 