from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os
import uuid
import cv2
import numpy as np
import pickle
from pathlib import Path
import sys

# Add utils to path
sys.path.append('/app')

# Import model components
from utils.anfis_trainer import ANFISModel
from utils.feature_extractor import BellPepperFeatureExtractor
from utils.color_grading import get_average_hsv, classify_ripeness_from_hsv

# Disable object detection for now to avoid startup issues
OBJECT_DETECTION_AVAILABLE = False

def detect_and_crop_object(*args, **kwargs):
    print("Object detection disabled")
    return None

# Try to import TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
    print("TensorFlow imported successfully")
except Exception as e:
    print(f"Warning: TensorFlow not available: {e}")
    TENSORFLOW_AVAILABLE = False
    tf = None
    load_model = None

app = FastAPI(title="Bell Pepper Models Service", version="1.0.0")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
feature_extractor = BellPepperFeatureExtractor()

# Global variables for models
trained_models = []
preprocessing_data = None
label_mapping = {}
transfer_model = None
ensemble_mode = True

def load_trained_models():
    """Load trained ANFIS models and preprocessing data"""
    global trained_models, preprocessing_data, label_mapping, transfer_model
    
    try:
        models_dir = Path("/app/models")
        training_output_dir = Path("/app/training_output")
        
        # Initialize fallback values first
        label_mapping = {
            0: 'damaged',
            1: 'dried', 
            2: 'old',
            3: 'ripe',
            4: 'unripe'
        }
        trained_models = []
        preprocessing_data = None
        transfer_model = None
        
        print("Starting model loading...")
        
        # Load ensemble preprocessing data
        preprocess_path = training_output_dir / "ensemble_preprocessing.pkl"
        if preprocess_path.exists():
            try:
                with open(preprocess_path, 'rb') as f:
                    preprocessing_data = pickle.load(f)
                    label_mapping = preprocessing_data['data_info']['label_mapping']
                    print(f"Loaded ensemble preprocessing data with {len(label_mapping)} classes")
            except Exception as e:
                print(f"Error loading preprocessing data: {e}")
        else:
            print("No preprocessing data found, using fallback label mapping")
        
        # Load ensemble ANFIS models
        models_loaded = 0
        for i in range(len(label_mapping)):
            model_path = models_dir / f"ensemble_anfis_class_{i}.pkl"
            if model_path.exists():
                try:
                    model = ANFISModel()
                    model.load_model(str(model_path))
                    trained_models.append(model)
                    models_loaded += 1
                    print(f"Loaded ensemble ANFIS model for class {i}: {label_mapping.get(i, 'unknown')}")
                except Exception as e:
                    print(f"Error loading ANFIS model {i}: {e}")
        
        # Load transfer learning model if available
        if TENSORFLOW_AVAILABLE:
            transfer_path = models_dir / "ensemble_transfer_model.h5"
            if transfer_path.exists():
                try:
                    transfer_model = load_model(str(transfer_path))
                    print("Loaded ensemble transfer learning model")
                except Exception as e:
                    print(f"Error loading transfer learning model: {e}")
        
        print(f"Model loading complete. Loaded {models_loaded} ANFIS models")
        if models_loaded == 0:
            print("WARNING: No trained models found. Service will start but predictions will use fallback methods.")
        
    except Exception as e:
        print(f"Critical error in load_trained_models: {e}")
        # Ensure fallback values are set
        label_mapping = {
            0: 'damaged',
            1: 'dried', 
            2: 'old',
            3: 'ripe',
            4: 'unripe'
        }
        trained_models = []
        preprocessing_data = None
        transfer_model = None

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    load_trained_models()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "models_loaded": len(trained_models)}

@app.post("/predict")
async def predict_pepper_grade(
    image: UploadFile = File(...),
    region: Optional[str] = None,
    model_type: Optional[str] = "ensemble"
):
    """Predict bell pepper grade using specified model type"""
    try:
        # Read and process image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Detect and crop object (if available)
        if OBJECT_DETECTION_AVAILABLE:
            try:
                cropped_image = detect_and_crop_object(image)
                if cropped_image is not None:
                    image = cropped_image
            except Exception as e:
                print(f"Object detection failed, using original image: {e}")
        else:
            print("Object detection not available, using original image")
        
        # Extract features
        features = feature_extractor.extract_features(image)
        
        # Get color-based prediction
        avg_hsv = get_average_hsv(image)
        color_prediction = classify_ripeness_from_hsv(avg_hsv)
        
        predictions = {}
        
        # ANFIS ensemble prediction
        if trained_models and preprocessing_data:
            try:
                # Prepare features for ANFIS
                feature_vector = np.array(list(features.values())).reshape(1, -1)
                
                # Apply preprocessing
                if 'scaler' in preprocessing_data:
                    feature_vector = preprocessing_data['scaler'].transform(feature_vector)
                
                # Get predictions from all ANFIS models
                anfis_scores = []
                for i, model in enumerate(trained_models):
                    try:
                        score = model.predict(feature_vector[0])
                        anfis_scores.append(float(score))
                    except Exception as e:
                        print(f"Error with ANFIS model {i}: {e}")
                        anfis_scores.append(0.0)
                
                # Convert to probabilities
                anfis_scores = np.array(anfis_scores)
                if np.sum(anfis_scores) > 0:
                    anfis_probs = anfis_scores / np.sum(anfis_scores)
                else:
                    anfis_probs = np.ones(len(anfis_scores)) / len(anfis_scores)
                
                anfis_prediction = label_mapping[np.argmax(anfis_probs)]
                anfis_confidence = float(np.max(anfis_probs))
                
                predictions['anfis'] = {
                    'prediction': anfis_prediction,
                    'confidence': anfis_confidence,
                    'probabilities': {label_mapping[i]: float(prob) for i, prob in enumerate(anfis_probs)}
                }
                
            except Exception as e:
                print(f"ANFIS prediction error: {e}")
                predictions['anfis'] = {'error': str(e)}
        
        # Transfer learning prediction
        if transfer_model is not None:
            try:
                # Preprocess image for transfer learning
                img_resized = cv2.resize(image, (224, 224))
                img_array = np.expand_dims(img_resized, axis=0) / 255.0
                
                # Get prediction
                transfer_probs = transfer_model.predict(img_array)[0]
                transfer_prediction = label_mapping[np.argmax(transfer_probs)]
                transfer_confidence = float(np.max(transfer_probs))
                
                predictions['transfer_learning'] = {
                    'prediction': transfer_prediction,
                    'confidence': transfer_confidence,
                    'probabilities': {label_mapping[i]: float(prob) for i, prob in enumerate(transfer_probs)}
                }
                
            except Exception as e:
                print(f"Transfer learning prediction error: {e}")
                predictions['transfer_learning'] = {'error': str(e)}
        
        # Ensemble prediction (combine ANFIS and Transfer Learning)
        if 'anfis' in predictions and 'transfer_learning' in predictions:
            try:
                anfis_probs = np.array(list(predictions['anfis']['probabilities'].values()))
                transfer_probs = np.array(list(predictions['transfer_learning']['probabilities'].values()))
                
                # Weighted ensemble (equal weights)
                ensemble_probs = (anfis_probs + transfer_probs) / 2
                ensemble_prediction = label_mapping[np.argmax(ensemble_probs)]
                ensemble_confidence = float(np.max(ensemble_probs))
                
                predictions['ensemble'] = {
                    'prediction': ensemble_prediction,
                    'confidence': ensemble_confidence,
                    'probabilities': {label_mapping[i]: float(prob) for i, prob in enumerate(ensemble_probs)}
                }
            except Exception as e:
                print(f"Ensemble prediction error: {e}")
        
        # Final result based on model_type
        if model_type == "anfis" and 'anfis' in predictions:
            selected_prediction = predictions['anfis']
        elif model_type == "transfer" and 'transfer_learning' in predictions:
            selected_prediction = predictions['transfer_learning']
        elif model_type == "ensemble" and 'ensemble' in predictions:
            selected_prediction = predictions['ensemble']
        else:
            # Fallback to any available prediction
            if 'ensemble' in predictions:
                selected_prediction = predictions['ensemble']
            elif 'anfis' in predictions:
                selected_prediction = predictions['anfis']
            elif 'transfer_learning' in predictions:
                selected_prediction = predictions['transfer_learning']
            else:
                selected_prediction = {'prediction': 'unknown', 'confidence': 0.0}
        
        result = {
            'prediction': selected_prediction.get('prediction', 'unknown'),
            'confidence': selected_prediction.get('confidence', 0.0),
            'probabilities': selected_prediction.get('probabilities', {}),
            'color_analysis': {
                'prediction': color_prediction,
                'avg_hsv': avg_hsv
            },
            'features': features,
            'model_type': model_type,
            'all_predictions': predictions,
            'status': 'success'
        }
        
        return result
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/models/status")
async def get_models_status():
    """Get status of loaded models"""
    return {
        'anfis_models': len(trained_models),
        'transfer_model_loaded': transfer_model is not None,
        'label_mapping': label_mapping,
        'tensorflow_available': TENSORFLOW_AVAILABLE
    }

@app.post("/models/reload")
async def reload_models():
    """Reload all models"""
    try:
        load_trained_models()
        return {'status': 'success', 'message': 'Models reloaded successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)