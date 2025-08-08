#!/usr/bin/env python3
"""
ANFIS Training Script for Bell Pepper Classification
===================================================

This script trains ANFIS models for multi-class classification of bell peppers
using the dataset located at 'datasets/Bell Pepper dataset 1'.

The script will:
1. Load images from all 5 categories (damaged, dried, old, ripe, unripe)
2. Extract 11 features from each image
3. Train 5 ANFIS models (one for each class using one-vs-all approach)
4. Save the trained models and evaluation results
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.utils.dataset_trainer import BellPepperDatasetTrainer

def main():
    """Main training function"""
    print("Bell Pepper ANFIS Training")
    print("=" * 40)
    
    try:
        # Initialize trainer
        trainer = BellPepperDatasetTrainer()
        
        # Train the model with optimized parameters
        results = trainer.train_full_pipeline(
            test_size=0.2,          # 20% for testing
            random_state=42,        # For reproducibility
            n_rules=12,             # Number of fuzzy rules
            epochs=400,             # Training epochs
            learning_rate=0.008     # Learning rate
        )
        
        print("\n" + "=" * 40)
        print("TRAINING SUCCESSFULLY COMPLETED!")
        print("=" * 40)
        
        # Print final results
        test_accuracy = results['test_results']['accuracy']
        print(f"Final Test Accuracy: {test_accuracy:.4f}")
        
        # Print per-class results
        print("\nPer-class Performance:")
        report = results['test_results']['classification_report']
        for class_name, metrics in report.items():
            if isinstance(metrics, dict) and 'precision' in metrics:
                print(f"{class_name}:")
                print(f"  Precision: {metrics['precision']:.3f}")
                print(f"  Recall: {metrics['recall']:.3f}")
                print(f"  F1-Score: {metrics['f1-score']:.3f}")
        
        print(f"\nModels saved to: {trainer.models_dir}")
        print(f"Training results saved to: {trainer.training_output_dir}")
        
        return results
        
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 