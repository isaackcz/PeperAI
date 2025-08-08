import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

class ANFISModel:
    """Adaptive Neuro-Fuzzy Inference System for bell pepper defect detection"""
    
    def __init__(self, n_inputs: int = 11, n_rules: int = 7, n_membership_functions: int = 7):
        self.n_inputs = n_inputs
        self.n_rules = n_rules
        self.n_membership_functions = n_membership_functions
        
        # Initialize membership function parameters (Gaussian)
        self.membership_params = self._initialize_membership_functions()
        
        # Initialize rule consequents (Takagi-Sugeno)
        self.rule_consequents = self._initialize_rule_consequents()
        
        # Training history
        self.training_history = {
            'loss': [],
            'val_loss': [],
            'accuracy': [],
            'val_accuracy': []
        }
        
        # Best model state
        self.best_weights = None
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        
    def _initialize_membership_functions(self) -> Dict[str, np.ndarray]:
        """Initialize Gaussian membership function parameters"""
        membership_params = {}
        
        for i in range(self.n_inputs):
            # Initialize centers and widths for each input
            centers = np.linspace(0, 1, self.n_membership_functions)
            widths = np.ones(self.n_membership_functions) * 0.2
            
            membership_params[f'input_{i}_centers'] = centers
            membership_params[f'input_{i}_widths'] = widths
        
        return membership_params
    
    def _initialize_rule_consequents(self) -> np.ndarray:
        """Initialize rule consequent parameters (Takagi-Sugeno)"""
        # Each rule has n_inputs + 1 parameters (linear function + bias)
        return np.random.randn(self.n_rules, self.n_inputs + 1) * 0.1
    
    def gaussian_membership(self, x: np.ndarray, center: float, width: float) -> np.ndarray:
        """Calculate Gaussian membership function"""
        return np.exp(-0.5 * ((x - center) / width) ** 2)
    
    def calculate_membership_degrees(self, x: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculate membership degrees for all inputs and membership functions"""
        membership_degrees = {}
        
        for i in range(self.n_inputs):
            centers = self.membership_params[f'input_{i}_centers']
            widths = self.membership_params[f'input_{i}_widths']
            
            # Calculate membership degrees for this input
            input_memberships = np.zeros((len(x), self.n_membership_functions))
            for j in range(self.n_membership_functions):
                input_memberships[:, j] = self.gaussian_membership(x[:, i], centers[j], widths[j])
            
            membership_degrees[f'input_{i}'] = input_memberships
        
        return membership_degrees
    
    def generate_rules(self, membership_degrees: Dict[str, np.ndarray]) -> np.ndarray:
        """Generate fuzzy rules using grid partitioning"""
        n_samples = list(membership_degrees.values())[0].shape[0]
        rule_strengths = np.ones((n_samples, self.n_rules))
        
        # Simple grid-based rule generation
        # Each rule combines one membership function from each input
        rule_idx = 0
        for i in range(self.n_membership_functions):
            for j in range(self.n_membership_functions):
                if rule_idx >= self.n_rules:
                    break
                
                # Combine membership functions from different inputs
                for input_idx in range(self.n_inputs):
                    input_key = f'input_{input_idx}'
                    if input_idx == 0:
                        rule_strengths[:, rule_idx] = membership_degrees[input_key][:, i]
                    elif input_idx == 1:
                        rule_strengths[:, rule_idx] *= membership_degrees[input_key][:, j]
                    else:
                        # For additional inputs, use the first membership function
                        rule_strengths[:, rule_idx] *= membership_degrees[input_key][:, 0]
                
                rule_idx += 1
        
        return rule_strengths
    
    def calculate_rule_outputs(self, x: np.ndarray, rule_strengths: np.ndarray) -> np.ndarray:
        """Calculate rule outputs using Takagi-Sugeno consequents"""
        n_samples = x.shape[0]
        rule_outputs = np.zeros((n_samples, self.n_rules))
        
        for i in range(self.n_rules):
            # Linear function: y = a1*x1 + a2*x2 + ... + an*xn + b
            consequent_params = self.rule_consequents[i]
            
            # Calculate linear combination
            linear_output = np.dot(x, consequent_params[:-1]) + consequent_params[-1]
            rule_outputs[:, i] = linear_output
        
        return rule_outputs
    
    def forward_pass(self, x: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Forward pass through the ANFIS network"""
        # Calculate membership degrees
        membership_degrees = self.calculate_membership_degrees(x)
        
        # Generate fuzzy rules
        rule_strengths = self.generate_rules(membership_degrees)
        
        # Calculate rule outputs
        rule_outputs = self.calculate_rule_outputs(x, rule_strengths)
        
        # Weighted average of rule outputs
        weighted_sum = np.sum(rule_strengths * rule_outputs, axis=1)
        rule_strength_sum = np.sum(rule_strengths, axis=1)
        
        # Avoid division by zero
        rule_strength_sum = np.where(rule_strength_sum == 0, 1e-10, rule_strength_sum)
        
        # Final output
        output = weighted_sum / rule_strength_sum
        
        # Apply sigmoid activation for binary classification
        output = 1 / (1 + np.exp(-output))
        
        return output, {
            'membership_degrees': membership_degrees,
            'rule_strengths': rule_strengths,
            'rule_outputs': rule_outputs
        }
    
    def backward_pass(self, x: np.ndarray, y_true: np.ndarray, learning_rate: float = 0.01) -> float:
        """Backward pass for parameter updates using gradient descent"""
        # Forward pass
        y_pred, cache = self.forward_pass(x)
        
        # Calculate loss (binary cross-entropy)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        loss = -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        
        # Calculate gradients
        grad_output = (y_pred - y_true) / len(y_true)
        
        # Update rule consequents using least squares approximation
        rule_strengths = cache['rule_strengths']
        rule_outputs = cache['rule_outputs']
        
        # Simple gradient update for consequents
        for i in range(self.n_rules):
            # Calculate gradient for linear parameters (inputs)
            grad_linear = np.mean(grad_output[:, np.newaxis] * rule_strengths[:, i:i+1] * x, axis=0)
            
            # Calculate gradient for bias term
            grad_bias = np.mean(grad_output * rule_strengths[:, i])
            
            # Combine gradients
            grad_consequent = np.concatenate([grad_linear, [grad_bias]])
            self.rule_consequents[i] -= learning_rate * grad_consequent
        
        # Update membership function parameters
        membership_degrees = cache['membership_degrees']
        
        for input_idx in range(self.n_inputs):
            input_key = f'input_{input_idx}'
            centers = self.membership_params[f'{input_key}_centers']
            widths = self.membership_params[f'{input_key}_widths']
            
            # Simple gradient update for membership functions
            for j in range(self.n_membership_functions):
                # Update centers
                grad_center = np.mean(grad_output * membership_degrees[input_key][:, j] * 
                                    (x[:, input_idx] - centers[j]) / (widths[j] ** 2))
                centers[j] -= learning_rate * grad_center
                
                # Update widths
                grad_width = np.mean(grad_output * membership_degrees[input_key][:, j] * 
                                   ((x[:, input_idx] - centers[j]) ** 2) / (widths[j] ** 3))
                widths[j] -= learning_rate * grad_width
                
                # Ensure widths are positive
                widths[j] = max(widths[j], 0.01)
        
        return loss
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 500, learning_rate: float = 0.01,
              patience: int = 20, batch_size: int = 32) -> Dict[str, List[float]]:
        """Train the ANFIS model with early stopping"""
        
        n_samples = X_train.shape[0]
        n_batches = (n_samples + batch_size - 1) // batch_size
        
        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(n_samples)
            X_train_shuffled = X_train[indices]
            y_train_shuffled = y_train[indices]
            
            # Training
            train_loss = 0.0
            for batch_idx in range(n_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, n_samples)
                
                X_batch = X_train_shuffled[start_idx:end_idx]
                y_batch = y_train_shuffled[start_idx:end_idx]
                
                batch_loss = self.backward_pass(X_batch, y_batch, learning_rate)
                train_loss += batch_loss
            
            train_loss /= n_batches
            
            # Validation
            y_val_pred, _ = self.forward_pass(X_val)
            val_loss = -np.mean(y_val * np.log(y_val_pred + 1e-15) + 
                               (1 - y_val) * np.log(1 - y_val_pred + 1e-15))
            
            # Calculate metrics
            train_acc = accuracy_score(y_train, (self.forward_pass(X_train)[0] > 0.5).astype(int))
            val_acc = accuracy_score(y_val, (y_val_pred > 0.5).astype(int))
            
            # Store history
            self.training_history['loss'].append(train_loss)
            self.training_history['val_loss'].append(val_loss)
            self.training_history['accuracy'].append(train_acc)
            self.training_history['val_accuracy'].append(val_acc)
            
            # Early stopping
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_weights = {
                    'membership_params': self.membership_params.copy(),
                    'rule_consequents': self.rule_consequents.copy()
                }
                self.patience_counter = 0
            else:
                self.patience_counter += 1
            
            if self.patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
            
            if epoch % 50 == 0:
                print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
                      f"Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")
        
        # Restore best weights
        if self.best_weights:
            self.membership_params = self.best_weights['membership_params']
            self.rule_consequents = self.best_weights['rule_consequents']
        
        return self.training_history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        y_pred, _ = self.forward_pass(X)
        return (y_pred > 0.5).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities"""
        y_pred, _ = self.forward_pass(X)
        return y_pred
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        f1 = f1_score(y, y_pred, average='binary')
        precision = precision_score(y, y_pred, average='binary')
        recall = recall_score(y, y_pred, average='binary')
        
        return {
            'accuracy': accuracy,
            'f1_score': f1,
            'precision': precision,
            'recall': recall
        }
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        model_data = {
            'membership_params': self.membership_params,
            'rule_consequents': self.rule_consequents,
            'n_inputs': self.n_inputs,
            'n_rules': self.n_rules,
            'n_membership_functions': self.n_membership_functions,
            'training_history': self.training_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.membership_params = model_data['membership_params']
        self.rule_consequents = model_data['rule_consequents']
        self.n_inputs = model_data['n_inputs']
        self.n_rules = model_data['n_rules']
        self.n_membership_functions = model_data['n_membership_functions']
        self.training_history = model_data['training_history']

class ANFISTrainer:
    """Trainer class for ANFIS model with dataset management"""
    
    def __init__(self, model_save_path: str = "./models"):
        self.model_save_path = model_save_path
        os.makedirs(model_save_path, exist_ok=True)
        self.model = None
        self.feature_stats = None
    
    def prepare_dataset(self, features_list: List[Dict[str, float]], 
                       labels: List[str], defect_to_binary: Dict[str, int]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare dataset for training"""
        # Convert features to numpy array
        feature_names = list(features_list[0].keys())
        X = np.array([[f[name] for name in feature_names] for f in features_list])
        
        # Convert labels to binary
        y = np.array([defect_to_binary[label] for label in labels])
        
        return X, y
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray,
                   n_rules: int = 7, epochs: int = 500,
                   learning_rate: float = 0.01, patience: int = 20) -> ANFISModel:
        """Train ANFIS model"""
        
        # Initialize model
        self.model = ANFISModel(
            n_inputs=X_train.shape[1],
            n_rules=n_rules,
            n_membership_functions=7
        )
        
        # Train model
        history = self.model.train(
            X_train, y_train, X_val, y_val,
            epochs=epochs,
            learning_rate=learning_rate,
            patience=patience
        )
        
        return self.model
    
    def save_trained_model(self, filename: str = "anfis_model.pkl"):
        """Save the trained model"""
        if self.model is None:
            raise ValueError("No trained model to save")
        
        filepath = os.path.join(self.model_save_path, filename)
        self.model.save_model(filepath)
        print(f"Model saved to {filepath}")
    
    def load_trained_model(self, filename: str = "anfis_model.pkl") -> ANFISModel:
        """Load a trained model"""
        filepath = os.path.join(self.model_save_path, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        self.model = ANFISModel()
        self.model.load_model(filepath)
        print(f"Model loaded from {filepath}")
        
        return self.model

if __name__ == "__main__":
    # Test the ANFIS trainer
    trainer = ANFISTrainer()
    
    # Create dummy data
    n_samples = 100
    n_features = 11
    
    X = np.random.rand(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = trainer.train_model(X_train, y_train, X_val, y_val, epochs=10)
    
    # Evaluate
    metrics = model.evaluate(X_val, y_val)
    print("Validation metrics:", metrics) 