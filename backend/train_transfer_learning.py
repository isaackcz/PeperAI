#!/usr/bin/env python3
"""
Transfer Learning Training Script for Bell Pepper Classification
==============================================================

This script uses pre-trained CNN models (ResNet) for high-accuracy
bell pepper classification. It can work with the current dataset
and easily incorporate additional photos.
"""

import os
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
import pickle
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Deep Learning imports
import tensorflow as tf
from tensorflow.keras.applications import ResNet50V2, EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.utils import to_categorical

class TransferLearningBellPepperTrainer:
    """Transfer learning trainer for bell pepper classification"""
    
    def __init__(self, dataset_path: str = "../datasets/Bell Pepper dataset 1"):
        self.dataset_path = Path(dataset_path)
        self.label_encoder = LabelEncoder()
        self.categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        
        # Create output directories
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)
        
        self.training_output_dir = Path("./training_output")
        self.training_output_dir.mkdir(exist_ok=True)
        
        # Model parameters
        self.img_size = (224, 224)  # Standard size for ResNet
        self.batch_size = 32
        self.epochs = 100
        
    def load_and_preprocess_dataset(self) -> Tuple[List[str], List[str]]:
        """Load and prepare image paths and labels"""
        image_paths = []
        labels = []
        
        print("Loading bell pepper dataset...")
        
        for category in self.categories:
            category_path = self.dataset_path / category
            if not category_path.exists():
                print(f"Warning: Category path {category_path} does not exist")
                continue
            
            print(f"Processing category: {category}")
            image_files = list(category_path.glob("*.jpg"))
            
            for img_path in image_files:
                image_paths.append(str(img_path))
                labels.append(category)
        
        print(f"Loaded {len(image_paths)} images")
        print(f"Category distribution: {pd.Series(labels).value_counts().to_dict()}")
        
        return image_paths, labels
    
    def create_data_generators(self, train_paths: List[str], train_labels: List[str],
                             val_paths: List[str], val_labels: List[str]) -> Tuple:
        """Create data generators for training and validation"""
        
        # Data augmentation for training
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest'
        )
        
        # Only rescaling for validation
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        # Create custom data generators
        def create_generator(paths, labels, datagen):
            def generator():
                for path, label in zip(paths, labels):
                    # Load and preprocess image
                    img = cv2.imread(path)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = cv2.resize(img, self.img_size)
                        img = img.astype('float32')
                        
                        # Apply augmentation
                        img = datagen.random_transform(img)
                        img = datagen.standardize(img)
                        
                        yield img, label
            return generator
        
        # Create generators
        train_gen = create_generator(train_paths, train_labels, train_datagen)
        val_gen = create_generator(val_paths, val_labels, val_datagen)
        
        return train_gen, val_gen
    
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
            Dense(512, activation='relu'),
            Dropout(0.5),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(n_classes, activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model, base_model
    
    def train_model(self, train_paths: List[str], train_labels: List[str],
                   val_paths: List[str], val_labels: List[str],
                   class_weights: Dict[int, float]) -> Tuple[Model, Dict]:
        """Train the transfer learning model"""
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(train_labels)
        y_val_encoded = self.label_encoder.transform(val_labels)
        
        # Convert to categorical
        y_train_cat = to_categorical(y_train_encoded)
        y_val_cat = to_categorical(y_val_encoded)
        
        # Build model
        n_classes = len(self.label_encoder.classes_)
        model, base_model = self.build_transfer_learning_model(n_classes)
        
        print(f"Training model with {n_classes} classes")
        print(f"Class weights: {class_weights}")
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-7),
            ModelCheckpoint(
                str(self.models_dir / "best_transfer_model.h5"),
                save_best_only=True,
                monitor='val_accuracy'
            )
        ]
        
        # Phase 1: Train only the top layers
        print("Phase 1: Training top layers...")
        history1 = model.fit(
            self.create_data_generator(train_paths, train_labels, 
                                     ImageDataGenerator(rescale=1./255)),
            steps_per_epoch=len(train_paths) // self.batch_size,
            epochs=30,
            validation_data=self.create_data_generator(val_paths, val_labels,
                                                     ImageDataGenerator(rescale=1./255)),
            validation_steps=len(val_paths) // self.batch_size,
            callbacks=callbacks,
            class_weight=class_weights
        )
        
        # Phase 2: Fine-tune the base model
        print("Phase 2: Fine-tuning base model...")
        base_model.trainable = True
        
        # Freeze early layers, train later layers
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        
        model.compile(
            optimizer=Adam(learning_rate=1e-5),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        history2 = model.fit(
            self.create_data_generator(train_paths, train_labels,
                                     ImageDataGenerator(rescale=1./255)),
            steps_per_epoch=len(train_paths) // self.batch_size,
            epochs=self.epochs - 30,
            validation_data=self.create_data_generator(val_paths, val_labels,
                                                     ImageDataGenerator(rescale=1./255)),
            validation_steps=len(val_paths) // self.batch_size,
            callbacks=callbacks,
            class_weight=class_weights
        )
        
        # Combine histories
        combined_history = {
            'accuracy': history1.history['accuracy'] + history2.history['accuracy'],
            'val_accuracy': history1.history['val_accuracy'] + history2.history['val_accuracy'],
            'loss': history1.history['loss'] + history2.history['loss'],
            'val_loss': history1.history['val_loss'] + history2.history['val_loss']
        }
        
        return model, combined_history
    
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
    
    def evaluate_model(self, model: Model, test_paths: List[str], 
                      test_labels: List[str]) -> Dict:
        """Evaluate the trained model"""
        
        # Encode test labels
        y_test_encoded = self.label_encoder.transform(test_labels)
        y_test_cat = to_categorical(y_test_encoded)
        
        # Create test dataset
        test_dataset = self.create_data_generator(
            test_paths, test_labels,
            ImageDataGenerator(rescale=1./255)
        )
        
        # Make predictions
        predictions = model.predict(test_dataset)
        y_pred = np.argmax(predictions, axis=1)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test_encoded, y_pred)
        
        # Classification report
        target_names = self.label_encoder.classes_
        report = classification_report(y_test_encoded, y_pred, 
                                     target_names=target_names, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y_test_encoded, y_pred)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'predictions': y_pred.tolist(),
            'probabilities': predictions.tolist()
        }
    
    def save_training_results(self, model: Model, training_history: Dict,
                            evaluation_results: Dict, class_weights: Dict):
        """Save training results and model"""
        
        # Save model
        model_path = self.models_dir / "transfer_learning_bell_pepper.h5"
        model.save(str(model_path))
        
        # Save label encoder
        encoder_path = self.training_output_dir / "transfer_learning_label_encoder.pkl"
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        # Save training history
        history_path = self.training_output_dir / "transfer_learning_history.json"
        with open(history_path, 'w') as f:
            json.dump(training_history, f, indent=2)
        
        # Save evaluation results
        eval_path = self.training_output_dir / "transfer_learning_evaluation.json"
        with open(eval_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        # Save class weights
        weights_path = self.training_output_dir / "transfer_learning_class_weights.json"
        with open(weights_path, 'w') as f:
            json.dump(class_weights, f, indent=2)
        
        print(f"Model saved to: {model_path}")
        print(f"Training results saved to: {self.training_output_dir}")
    
    def train_full_pipeline(self) -> Dict:
        """Complete transfer learning training pipeline"""
        
        print("Starting Transfer Learning Bell Pepper Training Pipeline")
        print("=" * 60)
        
        # 1. Load dataset
        image_paths, labels = self.load_and_preprocess_dataset()
        
        if len(image_paths) == 0:
            raise ValueError("No images found in dataset")
        
        # 2. Split data
        train_paths, test_paths, train_labels, test_labels = train_test_split(
            image_paths, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            train_paths, train_labels, test_size=0.2, random_state=42, stratify=train_labels
        )
        
        print(f"Training set: {len(train_paths)} samples")
        print(f"Validation set: {len(val_paths)} samples")
        print(f"Test set: {len(test_paths)} samples")
        
        # 3. Calculate class weights
        y_train_encoded = self.label_encoder.fit_transform(train_labels)
        class_weights = compute_class_weight(
            'balanced', 
            classes=np.unique(y_train_encoded), 
            y=y_train_encoded
        )
        class_weight_dict = {i: weight for i, weight in enumerate(class_weights)}
        
        # 4. Train model
        model, training_history = self.train_model(
            train_paths, train_labels, val_paths, val_labels, class_weight_dict
        )
        
        # 5. Evaluate model
        evaluation_results = self.evaluate_model(model, test_paths, test_labels)
        
        # 6. Save results
        self.save_training_results(model, training_history, evaluation_results, class_weight_dict)
        
        # 7. Print summary
        print("\n" + "=" * 60)
        print("TRANSFER LEARNING TRAINING COMPLETE")
        print("=" * 60)
        print(f"Overall Test Accuracy: {evaluation_results['accuracy']:.4f}")
        print("\nClassification Report:")
        print(classification_report(
            self.label_encoder.transform(test_labels),
            evaluation_results['predictions'],
            target_names=self.label_encoder.classes_
        ))
        
        return {
            'model': model,
            'training_history': training_history,
            'evaluation_results': evaluation_results,
            'label_encoder': self.label_encoder
        }

def main():
    """Main training function"""
    print("Transfer Learning Bell Pepper Training")
    print("=" * 50)
    
    try:
        # Initialize trainer
        trainer = TransferLearningBellPepperTrainer()
        
        # Train the model
        results = trainer.train_full_pipeline()
        
        print("\n" + "=" * 50)
        print("TRANSFER LEARNING SUCCESSFULLY COMPLETED!")
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