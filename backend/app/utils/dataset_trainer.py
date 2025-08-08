import os
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import json
from pathlib import Path

from .feature_extractor import BellPepperFeatureExtractor
from .anfis_trainer import ANFISModel, ANFISTrainer

class BellPepperDatasetTrainer:
    """Trainer for bell pepper dataset using ANFIS"""
    
    def __init__(self, dataset_path: str = "../datasets/Bell Pepper dataset 1"):
        self.dataset_path = Path(dataset_path)
        self.feature_extractor = BellPepperFeatureExtractor()
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        
        # Create output directories
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)
        
        self.training_output_dir = Path("./training_output")
        self.training_output_dir.mkdir(exist_ok=True)
    
    def load_dataset(self) -> Tuple[List[Dict[str, float]], List[str], List[str]]:
        """Load and extract features from the bell pepper dataset"""
        features_list = []
        labels = []
        image_paths = []
        
        print("Loading bell pepper dataset...")
        
        for category in self.categories:
            category_path = self.dataset_path / category
            if not category_path.exists():
                print(f"Warning: Category path {category_path} does not exist")
                continue
            
            print(f"Processing category: {category}")
            image_files = list(category_path.glob("*.jpg"))
            
            for img_path in image_files:
                try:
                    # Extract features
                    features = self.feature_extractor.extract_features_from_file(str(img_path))
                    
                    features_list.append(features)
                    labels.append(category)
                    image_paths.append(str(img_path))
                    
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    continue
        
        print(f"Loaded {len(features_list)} images with features")
        print(f"Category distribution: {pd.Series(labels).value_counts().to_dict()}")
        
        return features_list, labels, image_paths
    
    def prepare_data(self, features_list: List[Dict[str, float]], 
                    labels: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Prepare data for training"""
        # Convert features to numpy array
        feature_names = self.feature_extractor.get_feature_names()
        X = np.array([[f[name] for name in feature_names] for f in features_list])
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(labels)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create label mapping
        label_mapping = {i: label for i, label in enumerate(self.label_encoder.classes_)}
        
        return X_scaled, y_encoded, {
            'feature_names': feature_names,
            'label_mapping': label_mapping,
            'n_classes': len(self.label_encoder.classes_)
        }
    
    def create_multi_class_anfis(self, n_inputs: int, n_classes: int, 
                                n_rules: int = 10) -> ANFISModel:
        """Create ANFIS model for multi-class classification"""
        # For multi-class, we'll use one-vs-all approach
        # Each class will have its own ANFIS model
        models = []
        
        for class_idx in range(n_classes):
            model = ANFISModel(
                n_inputs=n_inputs,
                n_rules=n_rules,
                n_membership_functions=7
            )
            models.append(model)
        
        return models
    
    def train_multi_class_anfis(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray,
                               n_rules: int = 10, epochs: int = 300,
                               learning_rate: float = 0.01) -> List[ANFISModel]:
        """Train ANFIS models for multi-class classification using one-vs-all"""
        n_classes = len(np.unique(y_train))
        n_inputs = X_train.shape[1]
        
        print(f"Training {n_classes} ANFIS models (one-vs-all approach)...")
        
        models = []
        training_histories = []
        
        for class_idx in range(n_classes):
            print(f"\nTraining model for class {class_idx}...")
            
            # Create binary labels for this class
            y_train_binary = (y_train == class_idx).astype(int)
            y_val_binary = (y_val == class_idx).astype(int)
            
            # Create and train model
            model = ANFISModel(
                n_inputs=n_inputs,
                n_rules=n_rules,
                n_membership_functions=7
            )
            
            # Train the model
            history = model.train(
                X_train, y_train_binary,
                X_val, y_val_binary,
                epochs=epochs,
                learning_rate=learning_rate,
                patience=30
            )
            
            models.append(model)
            training_histories.append(history)
            
            # Evaluate this model
            val_pred = model.predict(X_val)
            val_acc = accuracy_score(y_val_binary, val_pred)
            print(f"Class {class_idx} validation accuracy: {val_acc:.4f}")
        
        return models, training_histories
    
    def predict_multi_class(self, models: List[ANFISModel], X: np.ndarray) -> np.ndarray:
        """Predict using multiple ANFIS models"""
        n_samples = X.shape[0]
        n_classes = len(models)
        
        # Get probabilities from each model
        probabilities = np.zeros((n_samples, n_classes))
        
        for i, model in enumerate(models):
            proba = model.predict_proba(X)
            probabilities[:, i] = proba
        
        # Normalize probabilities
        row_sums = probabilities.sum(axis=1)
        probabilities = probabilities / row_sums[:, np.newaxis]
        
        # Return class with highest probability
        predictions = np.argmax(probabilities, axis=1)
        
        return predictions, probabilities
    
    def evaluate_multi_class(self, models: List[ANFISModel], X: np.ndarray, 
                           y: np.ndarray, label_mapping: Dict) -> Dict:
        """Evaluate multi-class ANFIS models"""
        predictions, probabilities = self.predict_multi_class(models, X)
        
        # Calculate metrics
        accuracy = accuracy_score(y, predictions)
        
        # Classification report
        target_names = [label_mapping[i] for i in range(len(label_mapping))]
        report = classification_report(y, predictions, target_names=target_names, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y, predictions)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'predictions': predictions.tolist(),
            'probabilities': probabilities.tolist()
        }
    
    def save_training_results(self, models: List[ANFISModel], 
                            training_histories: List[Dict],
                            evaluation_results: Dict,
                            data_info: Dict,
                            filename_prefix: str = "bell_pepper_anfis"):
        """Save training results and models"""
        
        # Save models
        for i, model in enumerate(models):
            model_path = self.models_dir / f"{filename_prefix}_class_{i}.pkl"
            model.save_model(str(model_path))
        
        # Save training histories
        history_path = self.training_output_dir / f"{filename_prefix}_training_history.json"
        with open(history_path, 'w') as f:
            json.dump(training_histories, f, indent=2)
        
        # Save evaluation results
        eval_path = self.training_output_dir / f"{filename_prefix}_evaluation.json"
        with open(eval_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        # Save data preprocessing info
        preprocess_path = self.training_output_dir / f"{filename_prefix}_preprocessing.pkl"
        preprocess_data = {
            'label_encoder': self.label_encoder,
            'scaler': self.scaler,
            'data_info': data_info
        }
        with open(preprocess_path, 'wb') as f:
            pickle.dump(preprocess_data, f)
        
        print(f"Training results saved to {self.training_output_dir}")
        print(f"Models saved to {self.models_dir}")
    
    def train_full_pipeline(self, test_size: float = 0.2, random_state: int = 42,
                           n_rules: int = 10, epochs: int = 300,
                           learning_rate: float = 0.01) -> Dict:
        """Complete training pipeline"""
        
        print("Starting Bell Pepper ANFIS Training Pipeline")
        print("=" * 50)
        
        # 1. Load dataset
        features_list, labels, image_paths = self.load_dataset()
        
        if len(features_list) == 0:
            raise ValueError("No features extracted from dataset")
        
        # 2. Prepare data
        X, y, data_info = self.prepare_data(features_list, labels)
        
        # 3. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Further split training data
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=random_state, stratify=y_train
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Validation set: {X_val.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # 4. Train models
        models, training_histories = self.train_multi_class_anfis(
            X_train, y_train, X_val, y_val,
            n_rules=n_rules, epochs=epochs, learning_rate=learning_rate
        )
        
        # 5. Evaluate on test set
        test_results = self.evaluate_multi_class(models, X_test, y_test, data_info['label_mapping'])
        
        # 6. Save results
        self.save_training_results(
            models, training_histories, test_results, data_info
        )
        
        # 7. Print summary
        print("\n" + "=" * 50)
        print("TRAINING COMPLETE")
        print("=" * 50)
        print(f"Overall Test Accuracy: {test_results['accuracy']:.4f}")
        print("\nClassification Report:")
        print(classification_report(
            y_test, test_results['predictions'],
            target_names=[data_info['label_mapping'][i] for i in range(len(data_info['label_mapping']))]
        ))
        
        return {
            'models': models,
            'training_histories': training_histories,
            'test_results': test_results,
            'data_info': data_info
        }

def main():
    """Main training function"""
    # Initialize trainer
    trainer = BellPepperDatasetTrainer()
    
    # Train the model
    results = trainer.train_full_pipeline(
        test_size=0.2,
        random_state=42,
        n_rules=10,
        epochs=300,
        learning_rate=0.01
    )
    
    print("\nTraining completed successfully!")
    return results

if __name__ == "__main__":
    main() 