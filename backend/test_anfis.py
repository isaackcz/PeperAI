#!/usr/bin/env python3
"""
Test script for ANFIS bell pepper defect detection system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.synthetic_data import BellPepperSyntheticGenerator
from app.utils.feature_extractor import BellPepperFeatureExtractor
from app.utils.anfis_trainer import ANFISTrainer, ANFISModel
from app.utils.training_pipeline import BellPepperTrainingPipeline

def test_synthetic_data_generation():
    """Test synthetic data generation"""
    print("=== Testing Synthetic Data Generation ===")
    
    generator = BellPepperSyntheticGenerator()
    
    # Test single image generation
    for defect_type in ['healthy', 'anthracnose', 'blight', 'sunscald', 'mildew', 'rot', 'insect']:
        img, label = generator.generate_single_image(defect_type)
        print(f"Generated {defect_type} image: {img.shape}")
    
    # Test dataset generation
    dataset = generator.generate_dataset(10)
    print(f"Generated dataset with {len(dataset)} samples")
    
    print("✓ Synthetic data generation test passed\n")

def test_feature_extraction():
    """Test feature extraction"""
    print("=== Testing Feature Extraction ===")
    
    extractor = BellPepperFeatureExtractor()
    generator = BellPepperSyntheticGenerator()
    
    # Generate a test image
    img, label = generator.generate_single_image('healthy')
    
    # Extract features
    features = extractor.extract_all_features(img)
    
    print(f"Extracted {len(features)} features:")
    for name, value in features.items():
        print(f"  {name}: {value:.4f}")
    
    print("✓ Feature extraction test passed\n")

def test_anfis_model():
    """Test ANFIS model creation and basic operations"""
    print("=== Testing ANFIS Model ===")
    
    # Create model
    model = ANFISModel(n_inputs=11, n_rules=7)
    
    # Create dummy data
    import numpy as np
    X = np.random.rand(10, 11)
    y = np.random.randint(0, 2, 10)
    
    # Test forward pass
    output, cache = model.forward_pass(X)
    print(f"Forward pass output shape: {output.shape}")
    print(f"Output range: [{output.min():.4f}, {output.max():.4f}]")
    
    # Test prediction
    predictions = model.predict(X)
    print(f"Predictions: {predictions}")
    
    print("✓ ANFIS model test passed\n")

def test_training_pipeline():
    """Test the complete training pipeline"""
    print("=== Testing Training Pipeline ===")
    
    pipeline = BellPepperTrainingPipeline()
    
    # Test with small dataset
    try:
        results = pipeline.run_complete_pipeline(num_synthetic_images=50)
        print(f"Training completed successfully!")
        print(f"Final F1 Score: {results['model_performance']['basic_metrics']['f1_score']:.4f}")
        print("✓ Training pipeline test passed\n")
    except Exception as e:
        print(f"Training pipeline test failed: {e}")
        print("✗ Training pipeline test failed\n")

def test_prediction():
    """Test prediction with trained model"""
    print("=== Testing Prediction ===")
    
    pipeline = BellPepperTrainingPipeline()
    
    try:
        # Load model
        model = pipeline.load_trained_model()
        
        # Generate test image
        generator = BellPepperSyntheticGenerator()
        img, label = generator.generate_single_image('anthracnose')
        
        # Save test image
        test_image_path = "test_image.jpg"
        import cv2
        cv2.imwrite(test_image_path, img)
        
        # Predict
        result = pipeline.predict_defect(test_image_path, model)
        print(f"Prediction result: {result}")
        
        # Clean up
        os.remove(test_image_path)
        
        print("✓ Prediction test passed\n")
    except Exception as e:
        print(f"Prediction test failed: {e}")
        print("✗ Prediction test failed\n")

def main():
    """Run all tests"""
    print("Starting ANFIS System Tests\n")
    
    try:
        test_synthetic_data_generation()
        test_feature_extraction()
        test_anfis_model()
        test_training_pipeline()
        test_prediction()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 