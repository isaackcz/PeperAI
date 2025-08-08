import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import os
import cv2
from sklearn.model_selection import train_test_split
from .synthetic_data import BellPepperSyntheticGenerator
from .feature_extractor import BellPepperFeatureExtractor
from .anfis_trainer import ANFISModel, ANFISTrainer

class ActiveLearningSystem:
    """Active Learning system for ANFIS model improvement"""
    
    def __init__(self, 
                 confidence_threshold: float = 0.7,
                 max_iterations: int = 10,
                 samples_per_iteration: int = 50):
        self.confidence_threshold = confidence_threshold
        self.max_iterations = max_iterations
        self.samples_per_iteration = samples_per_iteration
        
        # Initialize components
        self.synthetic_generator = BellPepperSyntheticGenerator()
        self.feature_extractor = BellPepperFeatureExtractor()
        self.trainer = ANFISTrainer()
        
        # Active learning state
        self.uncertain_samples = []
        self.training_history = []
        self.model_performance = []
        
    def identify_uncertain_samples(self, model: ANFISModel, 
                                 X_val: np.ndarray, 
                                 y_val: np.ndarray) -> List[int]:
        """Identify samples with low prediction confidence"""
        predictions = model.predict_proba(X_val)
        
        # Calculate confidence as distance from 0.5
        confidence = np.abs(predictions - 0.5) * 2  # Scale to 0-1
        
        # Find samples with confidence below threshold
        uncertain_indices = np.where(confidence < self.confidence_threshold)[0]
        
        return uncertain_indices.tolist()
    
    def generate_targeted_synthetic_samples(self, uncertain_defect_types: List[str],
                                          n_samples: int = 50) -> List[Dict[str, Any]]:
        """Generate synthetic samples targeting uncertain defect types"""
        synthetic_samples = []
        
        # Calculate samples per defect type
        defect_counts = {}
        for defect_type in uncertain_defect_types:
            defect_counts[defect_type] = defect_counts.get(defect_type, 0) + 1
        
        # Generate samples for each uncertain defect type
        for defect_type, count in defect_counts.items():
            samples_needed = max(1, int(n_samples * count / len(uncertain_defect_types)))
            
            for i in range(samples_needed):
                # Generate synthetic image
                img, label = self.synthetic_generator.generate_single_image(defect_type)
                
                # Save image
                filename = f"active_learning_{defect_type}_{i}.jpg"
                filepath = os.path.join(self.synthetic_generator.output_dir, filename)
                cv2.imwrite(filepath, img)
                
                # Extract features
                features = self.feature_extractor.extract_all_features(img)
                
                synthetic_samples.append({
                    'image_path': filepath,
                    'defect_type': defect_type,
                    'features': features,
                    'is_synthetic': True
                })
        
        return synthetic_samples
    
    def update_training_data(self, current_features: List[Dict[str, float]],
                           current_labels: List[str],
                           new_samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, float]], List[str]]:
        """Update training data with new synthetic samples"""
        # Add new samples to existing data
        updated_features = current_features.copy()
        updated_labels = current_labels.copy()
        
        for sample in new_samples:
            updated_features.append(sample['features'])
            updated_labels.append(sample['defect_type'])
        
        return updated_features, updated_labels
    
    def active_learning_loop(self, 
                           initial_features: List[Dict[str, float]],
                           initial_labels: List[str],
                           X_val: np.ndarray,
                           y_val: np.ndarray,
                           defect_to_binary: Dict[str, int]) -> Tuple[ANFISModel, Dict[str, Any]]:
        """Main active learning loop"""
        
        current_features = initial_features.copy()
        current_labels = initial_labels.copy()
        
        best_model = None
        best_performance = 0.0
        
        for iteration in range(self.max_iterations):
            print(f"\n=== Active Learning Iteration {iteration + 1} ===")
            
            # Prepare current dataset
            X_train, y_train = self.trainer.prepare_dataset(
                current_features, current_labels, defect_to_binary
            )
            
            # Train model
            model = self.trainer.train_model(
                X_train, y_train, X_val, y_val,
                epochs=100,  # Reduced epochs for active learning
                patience=10
            )
            
            # Evaluate current model
            performance = model.evaluate(X_val, y_val)
            print(f"Current Performance: {performance}")
            
            # Store performance
            self.model_performance.append({
                'iteration': iteration,
                'performance': performance,
                'n_samples': len(current_features)
            })
            
            # Check if this is the best model so far
            if performance['f1_score'] > best_performance:
                best_performance = performance['f1_score']
                best_model = model
                self.trainer.save_trained_model(f"best_model_iteration_{iteration}.pkl")
            
            # Identify uncertain samples
            uncertain_indices = self.identify_uncertain_samples(model, X_val, y_val)
            print(f"Found {len(uncertain_indices)} uncertain samples")
            
            if len(uncertain_indices) == 0:
                print("No uncertain samples found. Stopping active learning.")
                break
            
            # Analyze uncertain samples to determine target defect types
            uncertain_defect_types = self.analyze_uncertain_samples(
                model, X_val, y_val, uncertain_indices
            )
            
            # Generate targeted synthetic samples
            new_samples = self.generate_targeted_synthetic_samples(
                uncertain_defect_types, self.samples_per_iteration
            )
            
            # Update training data
            current_features, current_labels = self.update_training_data(
                current_features, current_labels, new_samples
            )
            
            print(f"Added {len(new_samples)} new synthetic samples")
            print(f"Total training samples: {len(current_features)}")
            
            # Store iteration info
            self.training_history.append({
                'iteration': iteration,
                'uncertain_samples': len(uncertain_indices),
                'new_samples': len(new_samples),
                'performance': performance
            })
        
        return best_model, {
            'training_history': self.training_history,
            'model_performance': self.model_performance
        }
    
    def analyze_uncertain_samples(self, model: ANFISModel,
                                X_val: np.ndarray,
                                y_val: np.ndarray,
                                uncertain_indices: List[int]) -> List[str]:
        """Analyze uncertain samples to determine target defect types for synthetic generation"""
        
        # Get predictions for uncertain samples
        uncertain_predictions = model.predict_proba(X_val[uncertain_indices])
        uncertain_true_labels = y_val[uncertain_indices]
        
        # Analyze prediction patterns
        defect_types_needed = []
        
        # Check for false positives (predicted defective but actually healthy)
        false_positive_mask = (uncertain_predictions > 0.5) & (uncertain_true_labels == 0)
        if np.sum(false_positive_mask) > 0:
            defect_types_needed.append('healthy')
        
        # Check for false negatives (predicted healthy but actually defective)
        false_negative_mask = (uncertain_predictions <= 0.5) & (uncertain_true_labels == 1)
        if np.sum(false_negative_mask) > 0:
            # Add common defect types for false negatives
            defect_types_needed.extend(['anthracnose', 'blight', 'rot'])
        
        # Check for low confidence predictions
        low_confidence_mask = np.abs(uncertain_predictions - 0.5) < 0.2
        if np.sum(low_confidence_mask) > 0:
            # Add variety of defect types for low confidence
            defect_types_needed.extend(['sunscald', 'mildew', 'insect'])
        
        # Remove duplicates and ensure we have some defect types
        defect_types_needed = list(set(defect_types_needed))
        if not defect_types_needed:
            defect_types_needed = ['healthy', 'anthracnose', 'blight']
        
        return defect_types_needed
    
    def create_hybrid_dataset(self, 
                            real_features: List[Dict[str, float]],
                            real_labels: List[str],
                            synthetic_features: List[Dict[str, float]],
                            synthetic_labels: List[str],
                            real_to_synthetic_ratio: float = 0.2) -> Tuple[List[Dict[str, float]], List[str]]:
        """Create hybrid dataset mixing real and synthetic data"""
        
        # Calculate target sizes
        total_real = len(real_features)
        target_synthetic = int(total_real * (1 - real_to_synthetic_ratio) / real_to_synthetic_ratio)
        
        # Sample synthetic data if we have too much
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
        
        return hybrid_features, hybrid_labels
    
    def evaluate_model_robustness(self, model: ANFISModel,
                                X_test: np.ndarray,
                                y_test: np.ndarray,
                                lighting_variations: bool = True,
                                rotation_variations: bool = True) -> Dict[str, float]:
        """Evaluate model robustness under various conditions"""
        
        robustness_metrics = {}
        
        # Base performance
        base_metrics = model.evaluate(X_test, y_test)
        robustness_metrics['base_performance'] = base_metrics
        
        if lighting_variations:
            # Test with different lighting conditions
            lighting_metrics = self._test_lighting_robustness(model, X_test, y_test)
            robustness_metrics['lighting_robustness'] = lighting_metrics
        
        if rotation_variations:
            # Test with different rotations
            rotation_metrics = self._test_rotation_robustness(model, X_test, y_test)
            robustness_metrics['rotation_robustness'] = rotation_metrics
        
        return robustness_metrics
    
    def _test_lighting_robustness(self, model: ANFISModel,
                                 X_test: np.ndarray,
                                 y_test: np.ndarray) -> Dict[str, float]:
        """Test model performance under different lighting conditions"""
        # Simulate different lighting conditions by adjusting brightness
        lighting_variations = [0.5, 0.7, 1.3, 1.5]  # Brightness multipliers
        
        lighting_metrics = {}
        
        for variation in lighting_variations:
            # Apply brightness variation to features (simplified)
            X_varied = X_test * variation
            X_varied = np.clip(X_varied, 0, 1)  # Ensure values stay in [0,1]
            
            metrics = model.evaluate(X_varied, y_test)
            lighting_metrics[f'lighting_{variation}'] = metrics
        
        return lighting_metrics
    
    def _test_rotation_robustness(self, model: ANFISModel,
                                 X_test: np.ndarray,
                                 y_test: np.ndarray) -> Dict[str, float]:
        """Test model performance under different rotations"""
        # Simulate rotations by adjusting feature values (simplified)
        rotation_angles = [-15, -7.5, 7.5, 15]  # Degrees
        
        rotation_metrics = {}
        
        for angle in rotation_angles:
            # Apply rotation effect to features (simplified simulation)
            rotation_factor = 1 + (angle / 90) * 0.1  # Small variation
            X_rotated = X_test * rotation_factor
            X_rotated = np.clip(X_rotated, 0, 1)
            
            metrics = model.evaluate(X_rotated, y_test)
            rotation_metrics[f'rotation_{angle}'] = metrics
        
        return rotation_metrics
    
    def generate_performance_report(self, model: ANFISModel,
                                  X_test: np.ndarray,
                                  y_test: np.ndarray) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        # Basic evaluation
        basic_metrics = model.evaluate(X_test, y_test)
        
        # Robustness evaluation
        robustness_metrics = self.evaluate_model_robustness(model, X_test, y_test)
        
        # Active learning summary
        al_summary = {
            'total_iterations': len(self.training_history),
            'total_uncertain_samples': sum([h['uncertain_samples'] for h in self.training_history]),
            'total_new_samples': sum([h['new_samples'] for h in self.training_history]),
            'performance_improvement': self.model_performance[-1]['performance']['f1_score'] - 
                                    self.model_performance[0]['performance']['f1_score'] if self.model_performance else 0
        }
        
        report = {
            'basic_metrics': basic_metrics,
            'robustness_metrics': robustness_metrics,
            'active_learning_summary': al_summary,
            'training_history': self.training_history,
            'model_performance': self.model_performance
        }
        
        return report

if __name__ == "__main__":
    # Test the active learning system
    al_system = ActiveLearningSystem()
    
    # Create dummy data
    n_samples = 100
    n_features = 11
    
    X = np.random.rand(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
    
    # Create dummy features and labels
    features = [{'feature_' + str(i): np.random.rand() for i in range(n_features)} for _ in range(len(X_train))]
    labels = ['healthy' if label == 0 else 'defective' for label in y_train]
    
    defect_to_binary = {'healthy': 0, 'defective': 1}
    
    # Test active learning
    model, results = al_system.active_learning_loop(
        features, labels, X_val, y_val, defect_to_binary
    )
    
    print("Active Learning Results:", results) 