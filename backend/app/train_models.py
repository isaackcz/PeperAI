#!/usr/bin/env python3
"""
Comprehensive training script for Pepper Vision AI Models
Trains ANFIS and Transfer Learning models on bell pepper dataset
"""

import os
import sys
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import tensorflow as tf
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import cv2

# Add utils directory to path
sys.path.append('/app/utils')

# Import custom modules
from anfis_trainer import ANFISModel
from feature_extractor import BellPepperFeatureExtractor

def setup_directories():
    """Create necessary directories"""
    directories = ['models', 'training_output', 'data']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

def load_and_preprocess_dataset():
    """Load and preprocess the bell pepper dataset"""
    print("🫑 Loading bell pepper dataset...")
    
    dataset_path = Path("/app/datasets/Bell Pepper dataset 1")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    # Initialize feature extractor
    feature_extractor = BellPepperFeatureExtractor()
    feature_names = feature_extractor.get_feature_names()
    
    # Collect data
    data = []
    labels = []
    
    # Expected categories
    categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
    
    for category in categories:
        category_path = dataset_path / category
        if category_path.exists():
            print(f"📁 Processing category: {category}")
            image_files = list(category_path.glob("*.jpg")) + list(category_path.glob("*.png"))
            
            for img_path in image_files[:50]:  # Limit to 50 images per category for faster training
                try:
                    # Extract features
                    features_dict = feature_extractor.extract_features_from_file(str(img_path))
                    
                    # Convert dictionary to array using feature names
                    features_array = [features_dict[name] for name in feature_names]
                    
                    # Add to dataset
                    data.append(features_array)
                    labels.append(category)
                    
                except Exception as e:
                    print(f"⚠️ Error processing {img_path}: {e}")
                    continue
    
    if not data:
        raise ValueError("No valid images found in dataset")
    
    print(f"✅ Loaded {len(data)} samples with {len(set(labels))} categories")
    return np.array(data), np.array(labels), feature_names

def train_anfis_models(X, y, feature_names):
    """Train ANFIS models for each class (one-vs-all approach)"""
    print("🧠 Training ANFIS models...")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Save label mapping
    label_mapping = {i: label for i, label in enumerate(label_encoder.classes_)}
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save preprocessing data
    preprocessing_data = {
        'scaler': scaler,
        'label_encoder': label_encoder,
        'feature_names': feature_names,
        'data_info': {
            'n_samples': len(X),
            'n_features': len(feature_names),
            'label_mapping': label_mapping,
            'categories': list(label_encoder.classes_)
        }
    }
    
    with open('training_output/ensemble_preprocessing.pkl', 'wb') as f:
        pickle.dump(preprocessing_data, f)
    
    print("✅ Saved preprocessing data")
    
    # Train ANFIS models for each class
    trained_models = []
    n_classes = len(label_encoder.classes_)
    
    for class_idx in range(n_classes):
        print(f"🔄 Training ANFIS model for class {class_idx}: {label_mapping[class_idx]}")
        
        # Create binary labels for this class
        y_binary = (y_encoded == class_idx).astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_binary, test_size=0.2, random_state=42, stratify=y_binary
        )
        
        # Create and train ANFIS model
        anfis_model = ANFISModel(
            n_inputs=len(feature_names),
            n_rules=7,
            n_membership_functions=3
        )
        
        # Train the model
        history = anfis_model.train(
            X_train, y_train,
            X_test, y_test,
            epochs=100,
            learning_rate=0.01,
            patience=10,
            batch_size=32
        )
        
        # Evaluate
        y_pred = anfis_model.predict(X_test)
        y_pred_binary = (y_pred > 0.5).astype(int)
        accuracy = accuracy_score(y_test, y_pred_binary)
        
        print(f"   📊 Accuracy for {label_mapping[class_idx]}: {accuracy:.3f}")
        
        # Save model
        model_path = f'models/ensemble_anfis_class_{class_idx}.pkl'
        anfis_model.save_model(model_path)
        trained_models.append(anfis_model)
    
    print(f"✅ Trained {len(trained_models)} ANFIS models")
    return trained_models, preprocessing_data

def train_transfer_learning_model(X, y, feature_names):
    """Train transfer learning model using ResNet50V2 with actual images"""
    print("🔄 Training Transfer Learning model...")
    
    # For proper transfer learning, we need to load actual images
    # Let's load images from the dataset and use ResNet50V2
    
    dataset_path = Path("../../datasets/Bell Pepper dataset 1")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    # Collect image paths and labels
    image_paths = []
    labels = []
    categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
    
    for category in categories:
        category_path = dataset_path / category
        if category_path.exists():
            image_files = list(category_path.glob("*.jpg")) + list(category_path.glob("*.png"))
            for img_path in image_files[:50]:  # Limit to 50 images per category
                image_paths.append(str(img_path))
                labels.append(category)
    
    if not image_paths:
        raise ValueError("No images found in dataset")
    
    print(f"📁 Loaded {len(image_paths)} images for transfer learning")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(labels)
    
    # Split data
    X_train_paths, X_test_paths, y_train, y_test = train_test_split(
        image_paths, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Convert to one-hot encoding
    y_train_onehot = tf.keras.utils.to_categorical(y_train, num_classes=len(label_encoder.classes_))
    y_test_onehot = tf.keras.utils.to_categorical(y_test, num_classes=len(label_encoder.classes_))
    
    # Create data generators
    def load_and_preprocess_image(image_path):
        """Load and preprocess a single image"""
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))
        img = img.astype('float32') / 255.0
        return img
    
    # Load training images
    print("📸 Loading training images...")
    X_train_images = np.array([load_and_preprocess_image(path) for path in X_train_paths])
    X_test_images = np.array([load_and_preprocess_image(path) for path in X_test_paths])
    
    print(f"Training images shape: {X_train_images.shape}")
    print(f"Test images shape: {X_test_images.shape}")
    
    # Create ResNet50V2 model
    base_model = ResNet50V2(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Create model
    model = tf.keras.Sequential([
        base_model,
        GlobalAveragePooling2D(),
        Dense(512, activation='relu'),
        Dropout(0.5),
        Dense(256, activation='relu'),
        Dropout(0.3),
        Dense(len(label_encoder.classes_), activation='softmax')
    ])
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks
    callbacks = [
        EarlyStopping(patience=10, restore_best_weights=True),
        ReduceLROnPlateau(factor=0.5, patience=5)
    ]
    
    # Train model
    print("🏋️ Training transfer learning model...")
    history = model.fit(
        X_train_images, y_train_onehot,
        validation_data=(X_test_images, y_test_onehot),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate
    y_pred = model.predict(X_test_images)
    y_pred_classes = np.argmax(y_pred, axis=1)
    accuracy = accuracy_score(y_test, y_pred_classes)
    
    print(f"📊 Transfer Learning model accuracy: {accuracy:.3f}")
    
    # Save model
    model.save('models/ensemble_transfer_model.h5')
    print("✅ Saved transfer learning model")
    
    return model

def main():
    """Main training function"""
    print("🚀 Starting Pepper Vision AI Model Training")
    print("=" * 50)
    
    try:
        # Setup directories
        setup_directories()
        
        # Load and preprocess dataset
        X, y, feature_names = load_and_preprocess_dataset()
        
        # Train ANFIS models
        anfis_models, preprocessing_data = train_anfis_models(X, y, feature_names)
        
        # Train transfer learning model
        transfer_model = train_transfer_learning_model(X, y, feature_names)
        
        print("\n🎉 Training Complete!")
        print("=" * 50)
        print("✅ Trained models saved:")
        print("   📁 models/ensemble_anfis_class_*.pkl (ANFIS models)")
        print("   📁 models/ensemble_transfer_model.h5 (Transfer Learning model)")
        print("   📁 training_output/ensemble_preprocessing.pkl (Preprocessing data)")
        print("\n🔄 Restart the backend to use the trained models!")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()