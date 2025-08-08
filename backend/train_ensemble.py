#!/usr/bin/env python3
"""
Ensemble Training Script for Bell Pepper Classification
======================================================

This script combines ANFIS and Transfer Learning models for maximum accuracy.
It can work with the current dataset and easily incorporate additional photos.
"""

import os
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import pickle
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
import sys
sys.path.append(str(Path(__file__).parent / "utils"))

from feature_extractor import BellPepperFeatureExtractor
from anfis_trainer import ANFISModel

# Deep Learning imports
import tensorflow as tf
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.utils import to_categorical

class EnsembleBellPepperTrainer:
    """Ensemble trainer combining ANFIS and Transfer Learning"""
    
    def __init__(self, dataset_path: str = "/app/datasets/Bell Pepper dataset 1"):
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
        
        # Model parameters
        self.img_size = (224, 224)
        self.batch_size = 32
        self.epochs = 50  # Reduced for ensemble training
        
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
        
        # Calculate class weights
        class_weights = compute_class_weight(
            'balanced', 
            classes=np.unique(y_encoded), 
            y=y_encoded
        )
        
        return X_scaled, y_encoded, {
            'feature_names': feature_names,
            'label_mapping': label_mapping,
            'n_classes': len(self.label_encoder.classes_),
            'class_weights': class_weights
        }
    
    def train_anfis_models(self, X_train: np.ndarray, y_train: np.ndarray,
                          X_val: np.ndarray, y_val: np.ndarray,
                          class_weights: np.ndarray) -> List[ANFISModel]:
        """Train ANFIS models for ensemble"""
        n_classes = len(np.unique(y_train))
        n_inputs = X_train.shape[1]
        
        print(f"Training {n_classes} ANFIS models for ensemble...")
        
        models = []
        
        for class_idx in range(n_classes):
            print(f"Training ANFIS model for class {class_idx}...")
            
            # Create binary labels for this class
            y_train_binary = (y_train == class_idx).astype(int)
            y_val_binary = (y_val == class_idx).astype(int)
            
            # Create and train model
            model = ANFISModel(
                n_inputs=n_inputs,
                n_rules=10,
                n_membership_functions=7
            )
            
            # Train with class weight adjustment
            class_weight = class_weights[class_idx]
            history = model.train(
                X_train, y_train_binary,
                X_val, y_val_binary,
                epochs=100,  # Reduced for ensemble
                learning_rate=0.01 * class_weight,
                patience=20
            )
            
            models.append(model)
            
            # Evaluate this model
            val_pred = model.predict(X_val)
            val_acc = accuracy_score(y_val_binary, val_pred)
            print(f"ANFIS Class {class_idx} validation accuracy: {val_acc:.4f}")
        
        return models
    
    def build_transfer_learning_model(self, n_classes: int) -> Model:
        """Build transfer learning model using ResNet50V2"""
        
        # Load pre-trained ResNet50V2
        base_model = ResNet50V2(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.img_size, 3)
        )
        
        # Freeze the base model layers
        base_model.trainable = False
        
        # Create new model on top
        model = tf.keras.Sequential([
            base_model,
            GlobalAveragePooling2D(),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(n_classes, activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_transfer_learning(self, train_paths: List[str], train_labels: List[str],
                               val_paths: List[str], val_labels: List[str],
                               class_weights: Dict[int, float]) -> Model:
        """Train transfer learning model"""
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(train_labels)
        y_val_encoded = self.label_encoder.transform(val_labels)
        
        # Convert to categorical
        y_train_cat = to_categorical(y_train_encoded)
        y_val_cat = to_categorical(y_val_encoded)
        
        # Build model
        n_classes = len(self.label_encoder.classes_)
        model = self.build_transfer_learning_model(n_classes)
        
        print(f"Training Transfer Learning model with {n_classes} classes")
        
        # Create data generators
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True
        )
        
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-7),
            ModelCheckpoint(
                str(self.models_dir / "best_transfer_ensemble.h5"),
                save_best_only=True,
                monitor='val_accuracy'
            )
        ]
        
        # Train model
        history = model.fit(
            self.create_data_generator(train_paths, train_labels, train_datagen),
            steps_per_epoch=len(train_paths) // self.batch_size,
            epochs=self.epochs,
            validation_data=self.create_data_generator(val_paths, val_labels, val_datagen),
            validation_steps=len(val_paths) // self.batch_size,
            callbacks=callbacks,
            class_weight=class_weights
        )
        
        return model
    
    def create_data_generator(self, paths: List[str], labels: List[str], datagen) -> tf.data.Dataset:
        """Create TensorFlow dataset from image paths"""
        
        def load_and_preprocess(path, label):
            # Load image
            img = tf.io.read_file(path)
            img = tf.image.decode_jpeg(img, channels=3)
            img = tf.image.resize(img, self.img_size)
            img = tf.cast(img, tf.float32) / 255.0
            
            # Apply augmentation using TensorFlow operations
            if datagen.rotation_range:
                angle = tf.random.uniform([], -datagen.rotation_range, datagen.rotation_range)
                img = tf.image.rot90(img, k=tf.cast(angle / 90, tf.int32))
            
            if datagen.horizontal_flip:
                img = tf.image.random_flip_left_right(img)
            
            if datagen.width_shift_range or datagen.height_shift_range:
                # Apply random shifts
                height_shift = tf.random.uniform([], -datagen.height_shift_range, datagen.height_shift_range)
                width_shift = tf.random.uniform([], -datagen.width_shift_range, datagen.width_shift_range)
                
                # Calculate shift amounts
                height_shift_pixels = tf.cast(height_shift * tf.cast(tf.shape(img)[0], tf.float32), tf.int32)
                width_shift_pixels = tf.cast(width_shift * tf.cast(tf.shape(img)[1], tf.float32), tf.int32)
                
                # Apply shifts using tf.roll
                img = tf.roll(img, shift=[height_shift_pixels, width_shift_pixels], axis=[0, 1])
            
            return img, label
        
        # Create dataset with encoded labels and convert to categorical
        encoded_labels = self.label_encoder.transform(labels)
        categorical_labels = to_categorical(encoded_labels, num_classes=len(self.label_encoder.classes_))
        
        dataset = tf.data.Dataset.from_tensor_slices((paths, categorical_labels))
        dataset = dataset.map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        dataset = dataset.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def predict_ensemble(self, anfis_models: List[ANFISModel], 
                        transfer_model: Model, X: np.ndarray, 
                        image_paths: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Make ensemble predictions"""
        n_samples = X.shape[0]
        n_classes = len(anfis_models)
        
        # ANFIS predictions
        anfis_probabilities = np.zeros((n_samples, n_classes))
        for i, model in enumerate(anfis_models):
            proba = model.predict_proba(X)
            anfis_probabilities[:, i] = proba
        
        # Transfer learning predictions
        transfer_probabilities = np.zeros((n_samples, n_classes))
        
        # Create test dataset for transfer learning with dummy labels
        test_datagen = ImageDataGenerator(rescale=1./255)
        # Use the first class label as dummy labels for prediction
        dummy_labels = [self.label_encoder.classes_[0]] * len(image_paths)
        test_dataset = self.create_data_generator(image_paths, dummy_labels, test_datagen)
        
        transfer_pred = transfer_model.predict(test_dataset)
        transfer_probabilities = transfer_pred
        
        # Ensemble: Average both predictions
        ensemble_probabilities = (anfis_probabilities + transfer_probabilities) / 2
        
        # Get final predictions
        predictions = np.argmax(ensemble_probabilities, axis=1)
        
        return predictions, ensemble_probabilities
    
    def evaluate_ensemble(self, anfis_models: List[ANFISModel], 
                         transfer_model: Model, X: np.ndarray, y: np.ndarray,
                         image_paths: List[str]) -> Dict:
        """Evaluate ensemble model"""
        predictions, probabilities = self.predict_ensemble(
            anfis_models, transfer_model, X, image_paths
        )
        
        # Calculate metrics
        accuracy = accuracy_score(y, predictions)
        
        # Classification report
        target_names = [self.label_encoder.classes_[i] for i in range(len(self.label_encoder.classes_))]
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
    
    def save_ensemble_results(self, anfis_models: List[ANFISModel], 
                            transfer_model: Model, evaluation_results: Dict,
                            data_info: Dict):
        """Save ensemble training results"""
        
        # Save ANFIS models
        for i, model in enumerate(anfis_models):
            model_path = self.models_dir / f"ensemble_anfis_class_{i}.pkl"
            model.save_model(str(model_path))
        
        # Save transfer learning model
        transfer_path = self.models_dir / "ensemble_transfer_model.h5"
        transfer_model.save(str(transfer_path))
        
        # Save preprocessing info
        preprocess_path = self.training_output_dir / "ensemble_preprocessing.pkl"
        preprocess_data = {
            'label_encoder': self.label_encoder,
            'scaler': self.scaler,
            'data_info': data_info
        }
        with open(preprocess_path, 'wb') as f:
            pickle.dump(preprocess_data, f)
        
        # Save evaluation results
        eval_path = self.training_output_dir / "ensemble_evaluation.json"
        with open(eval_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        print(f"Ensemble models saved to: {self.models_dir}")
        print(f"Training results saved to: {self.training_output_dir}")
    
    def train_full_pipeline(self) -> Dict:
        """Complete ensemble training pipeline"""
        
        print("Starting Ensemble Bell Pepper Training Pipeline")
        print("=" * 60)
        
        # 1. Load dataset
        features_list, labels, image_paths = self.load_dataset()
        
        if len(features_list) == 0:
            raise ValueError("No features extracted from dataset")
        
        # 2. Prepare data
        X, y, data_info = self.prepare_data(features_list, labels)
        
        # 3. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
        )
        
        # Split image paths accordingly
        train_paths, test_paths, train_labels, test_labels = train_test_split(
            image_paths, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            train_paths, train_labels, test_size=0.2, random_state=42, stratify=train_labels
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Validation set: {X_val.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # 4. Train ANFIS models
        print("\nTraining ANFIS models...")
        anfis_models = self.train_anfis_models(
            X_train, y_train, X_val, y_val, data_info['class_weights']
        )
        
        # 5. Train Transfer Learning model
        print("\nTraining Transfer Learning model...")
        class_weight_dict = {i: weight for i, weight in enumerate(data_info['class_weights'])}
        transfer_model = self.train_transfer_learning(
            train_paths, train_labels, val_paths, val_labels, class_weight_dict
        )
        
        # 6. Evaluate ensemble
        print("\nEvaluating ensemble model...")
        evaluation_results = self.evaluate_ensemble(
            anfis_models, transfer_model, X_test, y_test, test_paths
        )
        
        # 7. Save results
        self.save_ensemble_results(anfis_models, transfer_model, evaluation_results, data_info)
        
        # 8. Print summary
        print("\n" + "=" * 60)
        print("ENSEMBLE TRAINING COMPLETE")
        print("=" * 60)
        print(f"Overall Test Accuracy: {evaluation_results['accuracy']:.4f}")
        print("\nClassification Report:")
        print(classification_report(
            y_test, evaluation_results['predictions'],
            target_names=[data_info['label_mapping'][i] for i in range(len(data_info['label_mapping']))]
        ))
        
        return {
            'anfis_models': anfis_models,
            'transfer_model': transfer_model,
            'evaluation_results': evaluation_results,
            'data_info': data_info
        }

def main():
    """Main training function"""
    print("Ensemble Bell Pepper Training")
    print("=" * 50)
    
    try:
        # Initialize trainer
        trainer = EnsembleBellPepperTrainer()
        
        # Train the ensemble model
        results = trainer.train_full_pipeline()
        
        print("\n" + "=" * 50)
        print("ENSEMBLE TRAINING SUCCESSFULLY COMPLETED!")
        print("=" * 50)
        
        # Print final results
        test_accuracy = results['evaluation_results']['accuracy']
        print(f"Final Test Accuracy: {test_accuracy:.4f}")
        
        # Print per-class results
        print("\nPer-class Performance:")
        report = results['evaluation_results']['classification_report']
        for class_name, metrics in report.items():
            if isinstance(metrics, dict) and 'precision' in metrics:
                print(f"{class_name}:")
                print(f"  Precision: {metrics['precision']:.3f}")
                print(f"  Recall: {metrics['recall']:.3f}")
                print(f"  F1-Score: {metrics['f1-score']:.3f}")
        
        return results
        
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()