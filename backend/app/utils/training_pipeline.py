import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import time
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from .synthetic_data import BellPepperSyntheticGenerator, DEFECT_TYPES
from .feature_extractor import BellPepperFeatureExtractor
from .anfis_trainer import ANFISTrainer, ANFISModel
from .active_learning import ActiveLearningSystem

class BellPepperTrainingPipeline:
    """Complete training pipeline for bell pepper defect detection using ANFIS"""
    
    def __init__(self, 
                 output_dir: str = "./training_output",
                 model_save_path: str = "./models",
                 synthetic_data_dir: str = "./synthetic_data"):
        
        self.output_dir = output_dir
        self.model_save_path = model_save_path
        self.synthetic_data_dir = synthetic_data_dir
        
        # Create directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(model_save_path, exist_ok=True)
        os.makedirs(synthetic_data_dir, exist_ok=True)
        
        # Initialize components
        self.synthetic_generator = BellPepperSyntheticGenerator(synthetic_data_dir)
        self.feature_extractor = BellPepperFeatureExtractor()
        self.trainer = ANFISTrainer(model_save_path)
        self.active_learning = ActiveLearningSystem()
        
        # Training configuration
        self.config = {
            'n_rules': 7,
            'epochs': 500,
            'learning_rate': 0.01,
            'patience': 20,
            'confidence_threshold': 0.7,
            'max_active_learning_iterations': 10,
            'samples_per_iteration': 50,
            'real_to_synthetic_ratio': 0.2,
            'target_f1_score': 0.9,
            'max_false_positive_rate': 0.05
        }
        
        # Training state
        self.training_history = {}
        self.model = None
        self.feature_stats = None
        
    def generate_synthetic_dataset(self, num_images: int = 500) -> List[Dict[str, Any]]:
        """Generate synthetic dataset with specified defect distribution"""
        print(f"Generating {num_images} synthetic images...")
        
        # Generate synthetic dataset
        synthetic_dataset = self.synthetic_generator.generate_dataset(num_images)
        
        print(f"Generated {len(synthetic_dataset)} synthetic images")
        
        # Extract features from synthetic images
        print("Extracting features from synthetic images...")
        synthetic_features = []
        synthetic_labels = []
        
        for i, sample in enumerate(synthetic_dataset):
            try:
                features = self.feature_extractor.extract_features_from_file(sample['image_path'])
                synthetic_features.append(features)
                synthetic_labels.append(sample['defect_type'])
                
                if (i + 1) % 50 == 0:
                    print(f"Processed {i + 1}/{len(synthetic_dataset)} images")
                    
            except Exception as e:
                print(f"Error processing {sample['image_path']}: {e}")
                continue
        
        print(f"Successfully extracted features from {len(synthetic_features)} images")
        
        return synthetic_features, synthetic_labels
    
    def process_real_images(self, real_image_paths: List[str], 
                          real_labels: List[str]) -> Tuple[List[Dict[str, float]], List[str]]:
        """Process real images and extract features"""
        print(f"Processing {len(real_image_paths)} real images...")
        
        real_features = []
        processed_labels = []
        
        for i, (image_path, label) in enumerate(zip(real_image_paths, real_labels)):
            try:
                features = self.feature_extractor.extract_features_from_file(image_path)
                real_features.append(features)
                processed_labels.append(label)
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(real_image_paths)} real images")
                    
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue
        
        print(f"Successfully processed {len(real_features)} real images")
        
        return real_features, processed_labels
    
    def create_hybrid_dataset(self, 
                            real_features: List[Dict[str, float]],
                            real_labels: List[str],
                            synthetic_features: List[Dict[str, float]],
                            synthetic_labels: List[str]) -> Tuple[List[Dict[str, float]], List[str]]:
        """Create hybrid dataset mixing real and synthetic data"""
        
        print("Creating hybrid dataset...")
        
        # Calculate target synthetic size based on ratio
        target_synthetic = int(len(real_features) * (1 - self.config['real_to_synthetic_ratio']) / 
                              self.config['real_to_synthetic_ratio'])
        
        # Sample synthetic data if needed
        if len(synthetic_features) > target_synthetic:
            indices = np.random.choice(len(synthetic_features), target_synthetic, replace=False)
            synthetic_features = [synthetic_features[i] for i in indices]
            synthetic_labels = [synthetic_labels[i] for i in indices]
        
        # Combine datasets
        hybrid_features = real_features + synthetic_features
        hybrid_labels = real_labels + synthetic_labels
        
        # Shuffle the combined dataset
        indices = np.random.permutation(len(hybrid_features))
        hybrid_features = [hybrid_features[i] for i in indices]
        hybrid_labels = [hybrid_labels[i] for i in indices]
        
        print(f"Created hybrid dataset with {len(hybrid_features)} samples")
        print(f"Real samples: {len(real_features)}, Synthetic samples: {len(synthetic_features)}")
        
        return hybrid_features, hybrid_labels
    
    def prepare_training_data(self, features: List[Dict[str, float]], 
                            labels: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
        """Prepare data for training"""
        
        # Define defect to binary mapping
        defect_to_binary = {
            'healthy': 0,
            'anthracnose': 1, 'blight': 1, 'sunscald': 1,
            'mildew': 1, 'rot': 1, 'insect': 1
        }
        
        # Convert features to numpy array
        feature_names = self.feature_extractor.get_feature_names()
        X = np.array([[f[name] for name in feature_names] for f in features])
        
        # Convert labels to binary
        y = np.array([defect_to_binary[label] for label in labels])
        
        return X, y, defect_to_binary
    
    def train_initial_model(self, X_train: np.ndarray, y_train: np.ndarray,
                           X_val: np.ndarray, y_val: np.ndarray) -> ANFISModel:
        """Train initial ANFIS model"""
        
        print("Training initial ANFIS model...")
        
        model = self.trainer.train_model(
            X_train, y_train, X_val, y_val,
            n_rules=self.config['n_rules'],
            epochs=self.config['epochs'],
            learning_rate=self.config['learning_rate'],
            patience=self.config['patience']
        )
        
        # Evaluate initial model
        initial_metrics = model.evaluate(X_val, y_val)
        print(f"Initial model performance: {initial_metrics}")
        
        return model
    
    def run_active_learning(self, model: ANFISModel,
                           initial_features: List[Dict[str, float]],
                           initial_labels: List[str],
                           X_val: np.ndarray,
                           y_val: np.ndarray,
                           defect_to_binary: Dict[str, int]) -> Tuple[ANFISModel, Dict[str, Any]]:
        """Run active learning to improve model performance"""
        
        print("Starting active learning process...")
        
        # Configure active learning
        self.active_learning.confidence_threshold = self.config['confidence_threshold']
        self.active_learning.max_iterations = self.config['max_active_learning_iterations']
        self.active_learning.samples_per_iteration = self.config['samples_per_iteration']
        
        # Run active learning
        improved_model, al_results = self.active_learning.active_learning_loop(
            initial_features, initial_labels, X_val, y_val, defect_to_binary
        )
        
        print("Active learning completed")
        
        return improved_model, al_results
    
    def evaluate_model_performance(self, model: ANFISModel,
                                 X_test: np.ndarray,
                                 y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluate model performance comprehensively"""
        
        print("Evaluating model performance...")
        
        # Basic metrics
        metrics = model.evaluate(X_test, y_test)
        
        # Detailed classification report
        y_pred = model.predict(X_test)
        classification_rep = classification_report(y_test, y_pred, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Robustness evaluation
        robustness_metrics = self.active_learning.evaluate_model_robustness(model, X_test, y_test)
        
        # Performance summary
        performance_summary = {
            'basic_metrics': metrics,
            'classification_report': classification_rep,
            'confusion_matrix': cm.tolist(),
            'robustness_metrics': robustness_metrics,
            'meets_targets': {
                'f1_score_target': metrics['f1_score'] >= self.config['target_f1_score'],
                'false_positive_target': (cm[0, 1] / (cm[0, 0] + cm[0, 1])) <= self.config['max_false_positive_rate']
            }
        }
        
        return performance_summary
    
    def run_complete_pipeline(self, 
                            real_image_paths: Optional[List[str]] = None,
                            real_labels: Optional[List[str]] = None,
                            num_synthetic_images: int = 500) -> Dict[str, Any]:
        """Run the complete training pipeline"""
        
        start_time = time.time()
        
        print("=== Starting Bell Pepper Defect Detection Training Pipeline ===")
        
        # Step 1: Generate synthetic data
        synthetic_features, synthetic_labels = self.generate_synthetic_dataset(num_synthetic_images)
        
        # Step 2: Process real images (if provided)
        real_features = []
        processed_real_labels = []
        
        if real_image_paths and real_labels:
            real_features, processed_real_labels = self.process_real_images(real_image_paths, real_labels)
        
        # Step 3: Create hybrid dataset
        if real_features:
            hybrid_features, hybrid_labels = self.create_hybrid_dataset(
                real_features, processed_real_labels, synthetic_features, synthetic_labels
            )
        else:
            # Use only synthetic data if no real images provided
            hybrid_features, hybrid_labels = synthetic_features, synthetic_labels
        
        # Step 4: Prepare training data
        X, y, defect_to_binary = self.prepare_training_data(hybrid_features, hybrid_labels)
        
        # Step 5: Split data
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Validation set: {len(X_val)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Step 6: Train initial model
        initial_model = self.train_initial_model(X_train, y_train, X_val, y_val)
        
        # Step 7: Run active learning
        improved_model, al_results = self.run_active_learning(
            initial_model, hybrid_features, hybrid_labels, X_val, y_val, defect_to_binary
        )
        
        # Step 8: Evaluate final model
        final_performance = self.evaluate_model_performance(improved_model, X_test, y_test)
        
        # Step 9: Save model and results
        self.trainer.save_trained_model("final_anfis_model.pkl")
        
        # Save training results
        training_results = {
            'config': self.config,
            'dataset_info': {
                'total_samples': len(hybrid_features),
                'real_samples': len(real_features),
                'synthetic_samples': len(synthetic_features),
                'class_distribution': pd.Series(hybrid_labels).value_counts().to_dict()
            },
            'model_performance': final_performance,
            'active_learning_results': al_results,
            'training_time': time.time() - start_time
        }
        
        # Save results to file
        results_file = os.path.join(self.output_dir, "training_results.json")
        with open(results_file, 'w') as f:
            json.dump(training_results, f, indent=2, default=str)
        
        print(f"\n=== Training Pipeline Completed ===")
        print(f"Training time: {training_results['training_time']:.2f} seconds")
        print(f"Final F1 Score: {final_performance['basic_metrics']['f1_score']:.4f}")
        print(f"Results saved to: {results_file}")
        
        return training_results
    
    def load_trained_model(self, model_filename: str = "final_anfis_model.pkl") -> ANFISModel:
        """Load a trained model"""
        return self.trainer.load_trained_model(model_filename)
    
    def predict_defect(self, image_path: str, model: Optional[ANFISModel] = None) -> Dict[str, Any]:
        """Predict defect for a single image"""
        
        if model is None:
            model = self.load_trained_model()
        
        # Extract features
        features = self.feature_extractor.extract_features_from_file(image_path)
        
        # Prepare input
        feature_names = self.feature_extractor.get_feature_names()
        X = np.array([[features[name] for name in feature_names]])
        
        # Make prediction
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0]
        
        # Determine defect type
        defect_type = "healthy" if prediction == 0 else "defective"
        confidence = abs(probability - 0.5) * 2  # Scale to 0-1
        
        return {
            'defect_type': defect_type,
            'confidence': float(confidence),
            'probability': float(probability),
            'features': features
        }

if __name__ == "__main__":
    # Test the complete training pipeline
    pipeline = BellPepperTrainingPipeline()
    
    # Run pipeline with synthetic data only
    results = pipeline.run_complete_pipeline(num_synthetic_images=100)
    
    print("Training completed successfully!")
    print(f"Final F1 Score: {results['model_performance']['basic_metrics']['f1_score']:.4f}") 