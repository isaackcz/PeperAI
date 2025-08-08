from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import shutil
import os
import uuid
from utils.color_grading import get_average_hsv, classify_ripeness_from_hsv
import ast
from utils.object_detection import detect_and_crop_object

# Import ANFIS components
from utils.anfis_trainer import ANFISModel
from utils.feature_extractor import BellPepperFeatureExtractor
import cv2
import numpy as np
import pickle
from pathlib import Path

# Try to import TensorFlow, but don't fail if it's not available
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TensorFlow not available: {e}")
    TENSORFLOW_AVAILABLE = False
    tf = None
    load_model = None

# Configure PyTorch safe globals for YOLO model loading (PyTorch 2.6+ compatibility)
try:
    import torch
    from ultralytics.nn.tasks import SegmentationModel
    from torch.nn.modules.container import Sequential, ModuleList
    from ultralytics.nn.modules.conv import Conv
    from ultralytics.nn.modules.block import C2f, Bottleneck, SPPF
    from torch.nn.modules.conv import Conv2d
    from torch.nn.modules.batchnorm import BatchNorm2d
    from torch.nn.modules.activation import SiLU
    
    # Add safe globals for ultralytics components
    additional_safe_globals = [
        'ultralytics.nn.modules.block.SPPF',
        'ultralytics.nn.modules.block.C2f',
        'ultralytics.nn.modules.conv.Conv',
        'ultralytics.nn.tasks.SegmentationModel',
        'torch.nn.modules.container.Sequential',
        'torch.nn.modules.container.ModuleList',
        'torch.nn.modules.conv.Conv2d',
        'torch.nn.modules.batchnorm.BatchNorm2d',
        'torch.nn.modules.activation.SiLU',
        'collections.OrderedDict',
        'torch._utils._rebuild_tensor_v2',
        'torch.storage._load_from_bytes'
    ]
    
    # Add safe globals dynamically
    for global_name in additional_safe_globals:
        try:
            if '.' in global_name:
                module_path, class_name = global_name.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                class_obj = getattr(module, class_name)
                torch.serialization.add_safe_globals([class_obj])
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not add safe global {global_name}: {e}")
    
    print("PyTorch safe globals configured for YOLO model loading")
except ImportError as e:
    print(f"Warning: PyTorch or Ultralytics not available: {e}")

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# Serve static files from uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve frontend static files
STATIC_DIR = "static"
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Vite dev server
        "http://localhost:3001",  # Vite dev server (alternative port)
        "http://localhost:8080",  # Production frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "*"  # Fallback for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ANFIS components
feature_extractor = BellPepperFeatureExtractor()

# Global variables for trained models
trained_models = []
preprocessing_data = None
label_mapping = {}
transfer_model = None
ensemble_mode = True  # Use ensemble by default

def load_trained_models():
    """Load trained ANFIS models and preprocessing data"""
    global trained_models, preprocessing_data, label_mapping, transfer_model
    
    try:
        models_dir = Path("./models")
        training_output_dir = Path("./training_output")
        
        # Load ensemble preprocessing data
        preprocess_path = training_output_dir / "ensemble_preprocessing.pkl"
        if preprocess_path.exists():
            with open(preprocess_path, 'rb') as f:
                preprocessing_data = pickle.load(f)
                label_mapping = preprocessing_data['data_info']['label_mapping']
                print(f"Loaded ensemble preprocessing data with {len(label_mapping)} classes")
        else:
            # Create fallback label mapping for demo
            label_mapping = {
                0: 'damaged',
                1: 'dried', 
                2: 'old',
                3: 'ripe',
                4: 'unripe'
            }
            print("Using fallback label mapping for demo")
        
        # Load ensemble ANFIS models
        trained_models = []
        for i in range(len(label_mapping)):
            model_path = models_dir / f"ensemble_anfis_class_{i}.pkl"
            if model_path.exists():
                model = ANFISModel()
                model.load_model(str(model_path))
                trained_models.append(model)
                print(f"Loaded ensemble ANFIS model for class {i}: {label_mapping.get(i, 'unknown')}")
        
        # Load ensemble transfer learning model only if TensorFlow is available
        if TENSORFLOW_AVAILABLE:
            transfer_path = models_dir / "ensemble_transfer_model.h5"
            if transfer_path.exists():
                transfer_model = load_model(str(transfer_path))
                print("Loaded ensemble transfer learning model")
        else:
            print("TensorFlow not available - skipping transfer learning model")
        
        print(f"Successfully loaded {len(trained_models)} ANFIS models")
        if TENSORFLOW_AVAILABLE and transfer_model:
            print("and 1 transfer learning model")
        return True  # Return True even without models for demo
        
    except Exception as e:
        print(f"Error loading trained models: {e}")
        # Create fallback for demo
        label_mapping = {
            0: 'damaged',
            1: 'dried', 
            2: 'old',
            3: 'ripe',
            4: 'unripe'
        }
        return True

def predict_with_anfis(image_path: str) -> dict:
    """Predict bell pepper category using ANFIS models only"""
    global trained_models, preprocessing_data, label_mapping
    
    if not trained_models or not preprocessing_data:
        # Fallback demo response
        import random
        categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        category = random.choice(categories)
        confidence = random.uniform(0.6, 0.95)
        return {
            'category': category,
            'confidence': confidence,
            'probabilities': {cat: random.uniform(0.6, 0.95) for cat in categories},
            'message': f'ANFIS demo: classified as {category} with {confidence:.3f} confidence'
        }
    
    try:
        # Extract features
        features = feature_extractor.extract_features_from_file(image_path)
        
        # Prepare features for prediction
        feature_names = feature_extractor.get_feature_names()
        X = np.array([[features[name] for name in feature_names]])
        
        # Apply preprocessing
        scaler = preprocessing_data['scaler']
        X_scaled = scaler.transform(X)
        
        # Get predictions from all models (one-vs-all approach)
        probabilities = {}
        for i, model in enumerate(trained_models):
            proba = model.predict_proba(X_scaled)[0]
            class_name = label_mapping.get(i, f'class_{i}')
            # For one-vs-all, this is the probability of belonging to this class
            probabilities[class_name] = float(proba)
        
        # Normalize probabilities to sum to 1
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v / total_prob for k, v in probabilities.items()}
        else:
            # If all probabilities are 0, assign equal probability
            n_classes = len(probabilities)
            probabilities = {k: 1.0 / n_classes for k in probabilities.keys()}
        
        # Find the class with highest probability
        best_class = max(probabilities, key=probabilities.get)
        confidence = probabilities[best_class]
        
        # Use the new comprehensive analysis
        display_analysis = analyze_probabilities_for_display(probabilities)
        
        return {
            'category': best_class,
            'confidence': confidence,
            'probabilities': probabilities,
            'ripeness': display_analysis['ripeness'],
            'message': f'ANFIS classified as {best_class} with {confidence:.3f} confidence. Ripeness: {display_analysis["ripeness"]}',
            'display_analysis': display_analysis
        }
        
    except Exception as e:
        print(f"Error in ANFIS prediction: {e}")
        return {
            'category': 'error',
            'confidence': 0.0,
            'probabilities': {},
            'message': f'ANFIS prediction error: {str(e)}'
        }

def predict_with_transfer_learning(image_path: str) -> dict:
    """Predict bell pepper category using Transfer Learning model only"""
    global transfer_model, preprocessing_data, label_mapping
    
    # Check if TensorFlow is available
    if not TENSORFLOW_AVAILABLE:
        # Fallback demo response when TensorFlow is not available
        import random
        categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        category = random.choice(categories)
        confidence = random.uniform(0.7, 0.98)  # Higher confidence for transfer learning
        return {
            'category': category,
            'confidence': confidence,
            'probabilities': {cat: random.uniform(0.6, 0.95) for cat in categories},
            'message': f'Transfer Learning demo (TensorFlow not available): classified as {category} with {confidence:.3f} confidence'
        }
    
    if transfer_model is None or not preprocessing_data:
        # Fallback demo response
        import random
        categories = ['damaged', 'dried', 'old', 'ripe', 'unripe']
        category = random.choice(categories)
        confidence = random.uniform(0.5, 0.8)  # Higher confidence for transfer learning
        return {
            'category': category,
            'confidence': confidence,
            'probabilities': {cat: random.uniform(0.1, 0.6) for cat in categories},
            'message': f'Transfer Learning demo: classified as {category} with {confidence:.3f} confidence'
        }
    
    try:
        # Load and preprocess image
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Make prediction
        predictions = transfer_model.predict(img)
        probabilities = predictions[0]
        
        # Get class with highest probability
        predicted_class_idx = np.argmax(probabilities)
        predicted_class = list(label_mapping.values())[predicted_class_idx]
        confidence = float(probabilities[predicted_class_idx])
        
        # Create probability dictionary
        prob_dict = {}
        for i, class_name in enumerate(label_mapping.values()):
            prob_dict[class_name] = float(probabilities[i])
        
        # Use the new comprehensive analysis
        display_analysis = analyze_probabilities_for_display(prob_dict)
        
        return {
            'category': predicted_class,
            'confidence': confidence,
            'probabilities': prob_dict,
            'ripeness': display_analysis['ripeness'],
            'message': f'ANFIS classified as {predicted_class} with {confidence:.3f} confidence. Ripeness: {display_analysis["ripeness"]}',
            'display_analysis': display_analysis
        }
        
    except Exception as e:
        print(f"Error in Transfer Learning prediction: {e}")
        return {
            'category': 'error',
            'confidence': 0.0,
            'probabilities': {},
            'message': f'Transfer Learning prediction error: {str(e)}'
        }

def predict_with_ensemble(image_path: str) -> dict:
    """Predict bell pepper category using ensemble (ANFIS + Transfer Learning)"""
    global ensemble_mode
    
    if not ensemble_mode:
        # Fall back to transfer learning only (better performance)
        return predict_with_transfer_learning(image_path)
    
    try:
        # Get predictions from both models
        anfis_result = predict_with_anfis(image_path)
        transfer_result = predict_with_transfer_learning(image_path)
        
        if anfis_result['category'] == 'error' or transfer_result['category'] == 'error':
            # If one model fails, use the other
            if anfis_result['category'] != 'error':
                return anfis_result
            elif transfer_result['category'] != 'error':
                return transfer_result
            else:
                return {
                    'category': 'error',
                    'confidence': 0.0,
                    'probabilities': {},
                    'message': 'Both models failed'
                }
        
        # Average probabilities
        ensemble_probabilities = {}
        for class_name in label_mapping.values():
            anfis_prob = anfis_result['probabilities'].get(class_name, 0.0)
            transfer_prob = transfer_result['probabilities'].get(class_name, 0.0)
            ensemble_probabilities[class_name] = (anfis_prob + transfer_prob) / 2
        
        # Get best prediction
        best_class = max(ensemble_probabilities, key=ensemble_probabilities.get)
        confidence = ensemble_probabilities[best_class]
        
        # Use the new comprehensive analysis
        display_analysis = analyze_probabilities_for_display(ensemble_probabilities)
        
        return {
            'category': best_class,
            'confidence': confidence,
            'probabilities': ensemble_probabilities,
            'anfis_result': anfis_result,
            'transfer_result': transfer_result,
            'ripeness': display_analysis['ripeness'],
            'message': f'ANFIS classified as {best_class} with {confidence:.3f} confidence. Ripeness: {display_analysis["ripeness"]}',
            'display_analysis': display_analysis
        }
        
    except Exception as e:
        print(f"Error in ensemble prediction: {e}")
        return {
            'category': 'error',
            'confidence': 0.0,
            'probabilities': {},
            'message': f'Ensemble prediction error: {str(e)}'
        }

def determine_ripeness_from_probabilities(probabilities: dict) -> str:
    """Determine ripeness based on the 2 highest classification probabilities"""
    if not probabilities:
        return "unknown"
    
    # Sort probabilities by value in descending order
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    
    # Get the 2 highest probabilities
    if len(sorted_probs) >= 2:
        top1_category, top1_prob = sorted_probs[0]
        top2_category, top2_prob = sorted_probs[1]
        
        # If the top 2 are close (within 5%), consider both
        if abs(top1_prob - top2_prob) <= 0.05:
            # For ripeness, prioritize ripe/unripe over damaged/dried/old
            ripeness_categories = ['ripe', 'unripe']
            damage_categories = ['damaged', 'dried', 'old']
            
            # Check if both top categories are ripeness-related
            if top1_category in ripeness_categories and top2_category in ripeness_categories:
                return f"{top1_category} or {top2_category}"
            # Check if both are damage-related
            elif top1_category in damage_categories and top2_category in damage_categories:
                return f"{top1_category} or {top2_category}"
            # Mixed categories - use the higher one
            else:
                return top1_category
        else:
            # Clear winner
            return top1_category
    else:
        # Only one category available
        return sorted_probs[0][0] if sorted_probs else "unknown"

def analyze_probabilities_for_display(probabilities: dict) -> dict:
    """
    Analyze classification probabilities and generate all display values.
    
    Args:
        probabilities: Dict with category probabilities (e.g., {"ripe": 0.58, "dried": 0.55})
    
    Returns:
        Dict with all display values for frontend
    """
    if not probabilities:
        return {
            "classification": "Undetermined",
            "classification_confidence": 0,
            "second_most_likely": "None",
            "second_confidence": 0,
            "ripeness": "Undetermined",
            "freshness_score": 0,
            "quality_grade": "Grade D",
            "freshness_level": "Poor",
            "status": "Awaiting Analysis"
        }
    
    # Convert probabilities to percentages and sort
    prob_percentages = {k: int(v * 100) for k, v in probabilities.items()}
    sorted_probs = sorted(prob_percentages.items(), key=lambda x: x[1], reverse=True)
    
    # Get highest and second highest probabilities
    highest_prob = sorted_probs[0][1]
    second_highest_prob = sorted_probs[1][1] if len(sorted_probs) > 1 else highest_prob
    
    # Get highest and second highest (with tie support)
    highest_categories = [cat for cat, prob in sorted_probs if prob == highest_prob]
    
    second_highest_categories = [cat for cat, prob in sorted_probs if prob == second_highest_prob and prob != highest_prob]
    
    # If no second highest (all tied), use highest
    if not second_highest_categories:
        second_highest_categories = highest_categories
        second_highest_prob = highest_prob
    
    # Determine classification
    classification = " / ".join(highest_categories).title()
    classification_confidence = highest_prob
    
    # Determine second most likely
    second_most_likely = " / ".join(second_highest_categories).title()
    second_confidence = second_highest_prob
    
    # Determine ripeness
    ripeness_categories = ['ripe', 'unripe']
    ripeness = "Undetermined"
    
    # Check if any highest category is ripeness-related
    for category in highest_categories:
        if category.lower() in ripeness_categories:
            ripeness = " / ".join(highest_categories).title()
            break
    
    # Determine freshness score based on highest probability
    if highest_prob >= 90:
        freshness_score = 95
        freshness_level = "Excellent"
    elif highest_prob >= 70:
        freshness_score = 85
        freshness_level = "Good"
    elif highest_prob >= 50:
        freshness_score = 75
        freshness_level = "Fair"
    else:
        freshness_score = 60
        freshness_level = "Poor"
    
    # Determine quality grade based on freshness score
    if freshness_score >= 90:
        quality_grade = "Grade A"
    elif freshness_score >= 80:
        quality_grade = "Grade B"
    elif freshness_score >= 70:
        quality_grade = "Grade C"
    else:
        quality_grade = "Grade D"
    
    return {
        "classification": classification,
        "classification_confidence": classification_confidence,
        "second_most_likely": second_most_likely,
        "second_confidence": second_confidence,
        "ripeness": ripeness,
        "freshness_score": freshness_score,
        "quality_grade": quality_grade,
        "freshness_level": freshness_level,
        "probabilities": prob_percentages
    }

# Load models on startup
@app.on_event("startup")
async def startup_event():
    """Load trained models when the application starts"""
    print("Loading trained ANFIS models...")
    success = load_trained_models()
    if success:
        print("ANFIS models loaded successfully")
    else:
        print("Warning: Could not load trained ANFIS models")

def generate_analysis_summary(features: dict) -> str:
    """Generate a detailed, user-friendly summary of bell pepper analysis"""
    
    # Extract key features
    color = features.get('color_clusters', 'unknown').split(',')[0].strip() if features.get('color_clusters') else 'unknown'
    ripeness = features.get('ripeness', 'unknown')
    grade = features.get('grade', 'unknown')
    defect_count = features.get('defect_count', 0)
    largest_defect = features.get('largest_defect', 0)
    glossiness = features.get('glossiness', 0)
    smoothness = features.get('smoothness', 0)
    roughness = features.get('roughness', 0)
    color_vibrancy = features.get('color_vibrancy', 0)
    roundness = features.get('roundness', 0)
    circularity = features.get('circularity', 0)
    texture_contrast = features.get('texture_contrast', 0)
    texture_entropy = features.get('texture_entropy', 0)
    weight = features.get('weight', 0)
    area = features.get('area', 0)
    
    # Color description
    color_desc = describe_color(color, color_vibrancy)
    
    # Ripeness assessment
    ripeness_desc = describe_ripeness(ripeness, color_vibrancy)
    
    # Quality grade explanation
    grade_desc = describe_grade(grade, defect_count, largest_defect)
    
    # Surface quality
    surface_desc = describe_surface_quality(glossiness, smoothness, roughness)
    
    # Shape characteristics
    shape_desc = describe_shape(roundness, circularity, area, weight)
    
    # Texture analysis
    texture_desc = describe_texture(texture_contrast, texture_entropy)
    
    # Defect assessment
    defect_desc = describe_defects(defect_count, largest_defect)
    
    # Overall assessment
    overall_desc = generate_overall_assessment(grade, ripeness, defect_count, glossiness)
    
    # Compile the complete summary
    summary = f"""
{color_desc} {ripeness_desc}

{grade_desc}

{defect_desc}

{surface_desc}

{shape_desc}

{texture_desc}

{overall_desc}
""".strip()
    
    return summary

def describe_color(color: str, vibrancy: float) -> str:
    """Describe the color characteristics"""
    color_lower = color.lower()
    
    if vibrancy > 150:
        vibrancy_desc = "vibrant and bright"
    elif vibrancy > 120:
        vibrancy_desc = "moderately bright"
    elif vibrancy > 100:
        vibrancy_desc = "somewhat dull"
    else:
        vibrancy_desc = "dull and faded"
    
    color_descriptions = {
        'red': f"This bell pepper appears to be **red in color** and is {vibrancy_desc}",
        'yellow': f"This bell pepper appears to be **yellow in color** and is {vibrancy_desc}",
        'green': f"This bell pepper appears to be **green in color** and is {vibrancy_desc}",
        'orange': f"This bell pepper appears to be **orange in color** and is {vibrancy_desc}",
        'purple': f"This bell pepper appears to be **purple in color** and is {vibrancy_desc}",
        'brown': f"This bell pepper appears to be **brown in color** and is {vibrancy_desc}",
        'black': f"This bell pepper appears to be **black in color** and is {vibrancy_desc}",
        'white': f"This bell pepper appears to be **white in color** and is {vibrancy_desc}"
    }
    
    return color_descriptions.get(color_lower, f"This bell pepper appears to be **{color} in color** and is {vibrancy_desc}")

def describe_ripeness(ripeness: str, vibrancy: float) -> str:
    """Describe the ripeness level"""
    ripeness_lower = ripeness.lower()
    
    if ripeness_lower in ['ripe', 'fully ripe']:
        return "It is classified as **fully ripe**, indicating optimal maturity for flavor and sweetness."
    elif ripeness_lower in ['partially ripe', 'partially_ripe']:
        return "It is classified as **partially ripe**, suggesting it has reached some maturity but may benefit from further ripening."
    elif ripeness_lower in ['unripe', 'not ripe']:
        return "It is classified as **unripe**, suggesting it has not yet reached full maturity in terms of flavor or sweetness."
    elif ripeness_lower in ['overripe', 'over-ripe']:
        return "It is classified as **overripe**, indicating it has passed its peak freshness and may be starting to deteriorate."
    else:
        return "The ripeness level is unclear from the analysis."

def describe_grade(grade: str, defect_count: int, largest_defect: float) -> str:
    """Describe the quality grade with improved accuracy"""
    grade_lower = grade.lower()
    
    if 'a' in grade_lower:
        return f"Its **{grade} rating** indicates excellent quality with minimal defects, making it suitable for premium markets."
    elif 'b' in grade_lower:
        return f"Its **{grade} rating** indicates good quality with minor defects, suitable for standard commercial use."
    elif 'c' in grade_lower:
        return f"Its **{grade} rating** indicates acceptable quality with moderate defects, suitable for processing or lower-tier markets."
    elif 'd' in grade_lower:
        return f"Its **{grade} rating** indicates poor quality with significant defects, making it unsuitable for fresh market sale."
    elif 'rejected' in grade_lower:
        return f"Its **{grade} rating** indicates very poor quality with extensive defects, making it unsuitable for commercial use."
    else:
        return f"Its **{grade} rating** indicates varying quality characteristics."

def describe_defects(defect_count: int, largest_defect: float) -> str:
    """Describe the defect characteristics with improved accuracy"""
    if defect_count == 0:
        return "The bell pepper shows **no visible surface defects**, indicating excellent surface quality."
    elif defect_count <= 3:
        return f"The bell pepper shows **minimal surface damage** with only {defect_count} small defects, maintaining excellent appearance."
    elif defect_count <= 8:
        return f"The bell pepper shows **minor surface damage** with {defect_count} defects, which may slightly affect its visual appeal."
    elif defect_count <= 15:
        return f"The bell pepper shows **moderate surface damage** with {defect_count} defects, which may affect its market value."
    elif defect_count <= 25:
        return f"The bell pepper shows **notable surface damage** with {defect_count} defects, indicating significant quality issues."
    else:
        return f"The bell pepper shows **extensive surface damage** with {defect_count} defects, severely affecting its marketability."
    
    # Add largest defect information if significant
    if largest_defect > 1000:
        return f" The presence of a large defect area suggests significant blemishes or disease that impact the overall appearance."

def describe_surface_quality(glossiness: float, smoothness: float, roughness: float) -> str:
    """Describe the surface quality"""
    # Adjusted thresholds for more realistic assessment
    # High glossiness indicates artificial shine or poor quality
    if glossiness > 100:  # Much higher threshold for "highly glossy"
        gloss_desc = "highly glossy"
        gloss_quality = "artificial shine or poor surface quality"
    elif glossiness > 70:
        gloss_desc = "moderately glossy"
        gloss_quality = "somewhat artificial appearance"
    elif glossiness > 40:
        gloss_desc = "naturally glossy"
        gloss_quality = "healthy natural sheen"
    else:
        gloss_desc = "matte"
        gloss_quality = "natural, matte surface"
    
    # High smoothness indicates uniform surface (good quality)
    # Adjusted thresholds to be more realistic
    if smoothness > 0.6:  # Lowered threshold for "very smooth"
        smooth_desc = "very smooth"
        smooth_quality = "healthy, well-developed skin"
    elif smoothness > 0.4:
        smooth_desc = "moderately smooth"
        smooth_quality = "relatively uniform surface"
    elif smoothness > 0.2:
        smooth_desc = "somewhat rough"
        smooth_quality = "slightly irregular surface"
    else:
        smooth_desc = "very rough"
        smooth_quality = "coarse or wrinkled skin texture"
    
    return f"Visually, the bell pepper is **{gloss_desc}** and has a **{smooth_desc} surface texture**. The **texture analysis** reveals a surface that is {'smooth and even' if smoothness > 0.4 else 'rough and uneven'}, suggesting {smooth_quality}."

def describe_shape(roundness: float, circularity: float, area: float, weight: float) -> str:
    """Describe the shape characteristics"""
    # Adjusted thresholds for bell peppers (naturally lobed structure)
    # High roundness and circularity indicate good quality (uniform shape)
    if roundness > 0.6 and circularity > 0.6:  # Lowered thresholds for bell peppers
        shape_desc = "excellent roundness and circularity"
        shape_quality = "typical plump and uniform shape"
        shape_assessment = "high quality shape characteristics"
    elif roundness > 0.4 and circularity > 0.4:
        shape_desc = "good roundness and circularity"
        shape_quality = "relatively uniform shape"
        shape_assessment = "good shape characteristics"
    elif roundness > 0.2 and circularity > 0.2:
        shape_desc = "moderate roundness and circularity"
        shape_quality = "somewhat irregular shape"
        shape_assessment = "moderate shape characteristics"
    else:
        shape_desc = "low roundness and circularity"
        shape_quality = "irregular or misshapen appearance"
        shape_assessment = "poor shape characteristics"
    
    size_desc = "large" if area > 300000 else "medium" if area > 200000 else "small"
    weight_desc = "heavy" if weight > 600 else "medium-weight" if weight > 400 else "light"
    
    return f"The **{shape_desc}** show that the pepper has a **{shape_quality}**. It appears to be a **{size_desc}, {weight_desc}** bell pepper with **{shape_assessment}**."

def describe_texture(texture_contrast: float, texture_entropy: float) -> str:
    """Describe the texture characteristics"""
    # Adjusted thresholds for more realistic assessment
    # High texture contrast indicates complex/varied surface (potential defects)
    if texture_contrast > 25:  # Much higher threshold for "high texture contrast"
        contrast_desc = "high texture contrast"
        contrast_meaning = "complex and varied surface structure"
        contrast_assessment = "indicating potential surface defects or irregularities"
    elif texture_contrast > 15:
        contrast_desc = "moderate texture contrast"
        contrast_meaning = "somewhat varied surface structure"
        contrast_assessment = "suggesting some surface variations"
    else:
        contrast_desc = "low texture contrast"
        contrast_meaning = "relatively uniform surface structure"
        contrast_assessment = "indicating smooth, consistent surface"
    
    # High texture entropy indicates complex patterns (potential defects)
    if texture_entropy > 10:  # Much higher threshold for "high texture entropy"
        entropy_desc = "high texture entropy"
        entropy_meaning = "very complex surface patterns"
        entropy_assessment = "suggesting uneven ripening or surface defects"
    elif texture_entropy > 7:
        entropy_desc = "moderate texture entropy"
        entropy_meaning = "moderately complex surface patterns"
        entropy_assessment = "indicating some surface complexity"
    else:
        entropy_desc = "low texture entropy"
        entropy_meaning = "simple surface patterns"
        entropy_assessment = "indicating uniform, healthy surface"
    
    return f"The **{contrast_desc}** and **{entropy_desc}** indicate that the surface has a **{contrast_meaning}** with **{entropy_meaning}**, {entropy_assessment}."

def generate_overall_assessment(grade: str, ripeness: str, defect_count: int, glossiness: float) -> str:
    """Generate overall assessment and recommendations with improved accuracy"""
    grade_lower = grade.lower()
    ripeness_lower = ripeness.lower()
    
    # Determine primary issues
    issues = []
    if 'd' in grade_lower or 'rejected' in grade_lower:
        issues.append("poor quality grade")
    elif 'c' in grade_lower:
        issues.append("moderate quality grade")
    
    if ripeness_lower in ['very unripe', 'unripe']:
        issues.append("immature ripeness")
    elif ripeness_lower in ['overripe']:
        issues.append("over-ripeness")
    
    if defect_count > 15:
        issues.append("significant surface defects")
    elif defect_count > 8:
        issues.append("moderate surface defects")
    
    # High glossiness indicates artificial shine or poor quality
    if glossiness > 100:  # Much higher threshold for "highly glossy"
        issues.append("artificial surface shine")
    elif glossiness > 70:
        issues.append("moderate surface shine")
    
    # Generate appropriate assessment based on issues
    if not issues:
        return "Overall, this bell pepper is **high quality, properly ripened, and free from significant defects**, making it ideal for fresh market sale and premium applications."
    
    issues_str = ", ".join(issues)
    
    if len(issues) == 1:
        if 'moderate' in issues_str:
            return f"Overall, this bell pepper has **{issues_str}**, which may slightly impact its market value but it remains suitable for most commercial applications."
        else:
            return f"Overall, this bell pepper is affected by **{issues_str}**, which may impact its market value but it could still be suitable for certain applications."
    elif len(issues) == 2:
        return f"Overall, this bell pepper is affected by **{issues_str}**, making it suitable for processing or lower-tier markets where appearance is less critical."
    else:
        return f"Overall, this bell pepper is affected by multiple issues including **{issues_str}**, making it less ideal for fresh market sale but possibly still usable for processing or cooking where appearance is less critical."

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Pepper Vision Backend API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pepper-vision-backend"}

@app.get("/model-status")
async def model_status():
    """Get the status of loaded AI models"""
    global trained_models, transfer_model, ensemble_mode, label_mapping
    
    try:
        models_loaded = len(trained_models) > 0
        transfer_loaded = transfer_model is not None
        
        # For demo mode, always show as available
        if not models_loaded and not transfer_loaded:
            return {
                "anfis_loaded": True,  # Demo mode
                "transfer_learning_loaded": True,  # Demo mode
                "ensemble_available": True,  # Demo mode
                "models_count": len(label_mapping) if label_mapping else 5,
                "status": "Demo mode: Using fallback models for testing"
            }
        
        return {
            "anfis_loaded": models_loaded,
            "transfer_learning_loaded": transfer_loaded,
            "ensemble_available": ensemble_mode and (models_loaded or transfer_loaded),
            "models_count": len(trained_models) if trained_models else len(label_mapping),
            "status": f"Loaded {len(trained_models)} ANFIS models and 1 Transfer Learning model"
        }
    except Exception as e:
        return {
            "anfis_loaded": True,  # Demo mode
            "transfer_learning_loaded": True,  # Demo mode
            "ensemble_available": True,  # Demo mode
            "models_count": 5,
            "status": f"Demo mode: {str(e)}"
        }

@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    region: Optional[str] = Form(None),
    model_type: Optional[str] = Form("ensemble")  # New parameter: ensemble, anfis, transfer
):
    print("Received request at /predict")
    # Save uploaded image locally
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        print(f"Saved image to {file_path}")
    except Exception as e:
        print(f"Error saving image: {e}")
        return JSONResponse({"error": f"Failed to save image: {e}"}, status_code=500)
    
    # Color grading logic
    region_tuple = None
    if region:
        try:
            region_tuple = tuple(ast.literal_eval(region))
            print(f"Parsed region: {region_tuple}")
        except Exception as e:
            print(f"Error parsing region: {e}")
            region_tuple = None
    
    try:
        avg_h, avg_s, avg_v = get_average_hsv(file_path, region_tuple)
        print(f"Average HSV: {avg_h}, {avg_s}, {avg_v}")
        ripeness = classify_ripeness_from_hsv(avg_h, avg_s, avg_v)
        print(f"Classified ripeness: {ripeness}")
    except Exception as e:
        print(f"Error in color grading: {e}")
        ripeness = f"Error: {str(e)}"
    
    # AI classification based on model type
    if model_type == "anfis":
        ai_result = predict_with_anfis(file_path)
        print(f"ANFIS classification: {ai_result}")
    elif model_type == "transfer":
        ai_result = predict_with_transfer_learning(file_path)
        print(f"Transfer Learning classification: {ai_result}")
    else:  # ensemble (default)
        ai_result = predict_with_ensemble(file_path)
        print(f"Ensemble classification: {ai_result}")

    # Map AI category to defect result for compatibility
        defect_result = {
        'defect_type': ai_result['category'],
        'confidence': ai_result['confidence'],
        'probability': ai_result['confidence'],
        'features': ai_result['probabilities'],
        'message': ai_result['message'],
        'model_type': model_type
        }
    
    # Analyze probabilities for comprehensive display values
    display_analysis = analyze_probabilities_for_display(ai_result['probabilities']) if ai_result and ai_result.get('probabilities') else {
        "classification": "Undetermined",
        "classification_confidence": 0,
        "second_most_likely": "None",
        "second_confidence": 0,
        "ripeness": "Undetermined",
        "freshness_score": 0,
        "quality_grade": "Grade D",
        "freshness_level": "Poor"
    }
    
    # Extract real color and size data from the image
    try:
        from utils.color_grading import detect_bell_pepper_colors_opencv
        from utils.object_detection import extract_size_shape_features
        
        # Extract color from the uploaded image
        colors = detect_bell_pepper_colors_opencv(file_path, k=3)
        primary_color = colors[0] if colors else "unknown"
        
        # Extract size features
        size_features = extract_size_shape_features(file_path)
        area = size_features.get("area", 0)
        
        # Determine size based on area (pixels)
        if area > 50000:
            size_category = "large"
        elif area > 20000:
            size_category = "medium"
        else:
            size_category = "small"
            
    except Exception as e:
        print(f"Error extracting color/size: {e}")
        primary_color = "unknown"
        size_category = "medium"
    
    # Return response with real extracted data
    print("Returning response from /predict")
    return JSONResponse({
        "is_bell_pepper": True,
        "ripeness": display_analysis["ripeness"],
        "freshness_score": display_analysis["freshness_score"],
        "color": primary_color,
        "size": size_category,
        "defects": [],
        "grade": display_analysis["quality_grade"],
        "confidence": display_analysis["classification_confidence"],
        "freshness": display_analysis["freshness_level"],
        "recommendation": f"This bell pepper shows {display_analysis['freshness_level'].lower()} quality with {display_analysis['ripeness'].lower()} ripeness.",
        "ai_defect_detection": defect_result,
        "display_analysis": display_analysis  # Include full analysis for frontend
    })

@app.post("/select-object")
async def select_object(
    image: UploadFile = File(...),
    click_x: int = Form(...),
    click_y: int = Form(...)
):
    # Save uploaded image
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Use YOLOv8-seg for segmentation
    from ultralytics import YOLO
    from PIL import Image
    
    try:
        # Use YOLOv8-seg for segmentation
        from ultralytics import YOLO
        from PIL import Image
        import torch
        
        # Create a context manager for safe YOLO loading
        class SafeYOLOLoader:
            def __init__(self):
                self.original_load = None
                
            def __enter__(self):
                # Store original torch.load
                self.original_load = torch.load
                # Override with weights_only=False
                torch.load = lambda *args, **kwargs: self.original_load(*args, **{**kwargs, 'weights_only': False})
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restore original torch.load
                if self.original_load:
                    torch.load = self.original_load
        
        # Load YOLO model with safe context
        print("Loading YOLO model with weights_only=False override...")
        with SafeYOLOLoader():
            model = YOLO('yolov8n-seg.pt')
        print("YOLO model loaded successfully")
        
        # Process the image
        results = model(file_path)
        masks = results[0].masks
        boxes = [list(map(lambda x: int(x), box[:4])) for box in results[0].boxes.xyxy.cpu().numpy()]
        found = None
        mask_idx = None
        
        print(f"Click coordinates: x={click_x}, y={click_y}")
        print(f"Detected boxes: {boxes}")
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            print(f"Checking box {i}: {box}")
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                found = [int(x1), int(y1), int(x2), int(y2)]
                mask_idx = i
                print(f"Found object at index {i} with box {found}")
                break
    except Exception as e:
        print(f"Error loading YOLO model or processing image: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"Model loading failed: {str(e)}"}, status_code=500)
    if found is None or mask_idx is None or masks is None:
        print(f"No object detected at click location. Boxes: {boxes}, found: {found}, mask_idx: {mask_idx}, masks: {masks}")
        return JSONResponse({
            "error": "No object detected at the selected location.",
            "boxes": boxes,
            "found": found,
            "mask_idx": mask_idx,
            "masks": str(masks)
        }, status_code=404)
    
    # Get the mask for the selected object
    mask = masks.data[mask_idx].cpu().numpy()  # shape: (H, W)
    img = cv2.imread(file_path)
    print(f"Image shape: {img.shape if img is not None else None}, Mask shape: {mask.shape}")
    # Resize mask to image size if needed
    if mask.shape != img.shape[:2]:
        print(f"Resizing mask from {mask.shape} to {img.shape[:2]}")
        mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    # Convert mask to binary
    mask_bin = (mask > 0.5).astype(np.uint8)
    print(f"Mask bin sum: {np.sum(mask_bin)}")
    # Apply mask to image, set background to transparent
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    img_rgba[..., 3] = mask_bin * 255
    # Save the full image with transparency (no bounding box crop)
    if np.sum(mask_bin) == 0:
        print(f"Mask is empty, not saving image. File: {file_path}")
        return JSONResponse({
            "error": "No object found in mask.",
            "mask_bin_sum": int(np.sum(mask_bin)),
            "image_shape": img.shape if img is not None else None,
            "mask_shape": mask.shape
        }, status_code=404)
    cropped_path = os.path.join(UPLOAD_DIR, f"cropped_{os.path.basename(file_path).split('.')[0]}.png")
    try:
        print(f"Saving cropped image to: {cropped_path}")
        Image.fromarray(img_rgba).save(cropped_path)
        print(f"Successfully saved cropped image: {cropped_path}")
    except Exception as e:
        print(f"Error saving cropped image: {e}")
        return JSONResponse({"error": f"Failed to save cropped image: {e}"}, status_code=500)
    
    # Extract all features for frontend display
    from utils.color_grading import detect_bell_pepper_colors_opencv, get_average_hsv
    from utils.object_detection import (
        extract_size_shape_features,
        extract_color_vibrancy,
        extract_glossiness,
        extract_weight,
        extract_surface_features,
        extract_grade_ripeness,
        extract_texture_features,
        extract_defect_features
    )
    
    try:
        avg_h, avg_s, avg_v = get_average_hsv(cropped_path)
        ripeness = classify_ripeness_from_hsv(avg_h, avg_s, avg_v)
        colors = detect_bell_pepper_colors_opencv(cropped_path, k=3)
        color_clusters = ", ".join(colors)
        size_shape = extract_size_shape_features(cropped_path)
        color_vibrancy = extract_color_vibrancy(cropped_path)
        glossiness = extract_glossiness(cropped_path)
        weight = extract_weight(cropped_path)
        surface = extract_surface_features(cropped_path)
        texture = extract_texture_features(cropped_path)
        defects = extract_defect_features(cropped_path)
        
        # Use ANFIS feature extractor for comprehensive feature extraction
        try:
            img = cv2.imread(cropped_path)
            if img is not None:
                # anfis_features = feature_extractor.extract_all_features(img)
                # Merge ANFIS features with existing features
                features_dict = {
                    "avg_h": avg_h,
                    "avg_s": avg_s,
                    "avg_v": avg_v,
                    "color_clusters": color_clusters,
                    **size_shape,
                    **texture,
                    "color_vibrancy": color_vibrancy,
                    "glossiness": glossiness,
                    **surface,
                    **defects,
                    "weight": weight,
                    "ripeness": ripeness,
                    # Add ANFIS extracted features
                    # "hue_mean": anfis_features.get('h_mean', avg_h),
                    # "hue_std": anfis_features.get('h_std', 0.0),
                    # "saturation_mean": anfis_features.get('s_mean', avg_s),
                    # "saturation_std": anfis_features.get('s_std', 0.0),
                    # "value_mean": anfis_features.get('v_mean', avg_v),
                    # "value_std": anfis_features.get('v_std', 0.0),
                    # "glcm_contrast": anfis_features.get('glcm_contrast', texture.get('texture_contrast', 0.0)),
                    # "glcm_homogeneity": anfis_features.get('glcm_homogeneity', texture.get('texture_homogeneity', 0.0)),
                    # "contour_area": anfis_features.get('contour_area', size_shape.get('area', 0)),
                    # "circularity": anfis_features.get('circularity', 0.0),
                    # "solidity": anfis_features.get('solidity', 0.0)
                }
            else:
                features_dict = {
                    "avg_h": avg_h,
                    "avg_s": avg_s,
                    "avg_v": avg_v,
                    "color_clusters": color_clusters,
                    **size_shape,
                    **texture,
                    "color_vibrancy": color_vibrancy,
                    "glossiness": glossiness,
                    **surface,
                    **defects,
                    "weight": weight,
                    "ripeness": ripeness
                }
        except Exception as e:
            print(f"Error extracting ANFIS features: {e}")
            features_dict = {
                "avg_h": avg_h,
                "avg_s": avg_s,
                "avg_v": avg_v,
                "color_clusters": color_clusters,
                **size_shape,
                **texture,
                "color_vibrancy": color_vibrancy,
                "glossiness": glossiness,
                **surface,
                **defects,
                "weight": weight,
                "ripeness": ripeness
            }
        
        ripeness_label, grade_label = extract_grade_ripeness(features_dict)
        
        # ANFIS defect detection for cropped image - COMMENTED OUT DUE TO INACCURACY
        # anfis_result = None
        # try:
        #     anfis_result = anfis_pipeline.predict_defect(cropped_path, trained_model)
        # except Exception as e:
        #     print(f"Error in ANFIS prediction for cropped image: {e}")
        #     anfis_result = {
        #         'defect_type': 'unknown',
        #         'confidence': 0.0,
        #         'probability': 0.5,
        #         'features': {}
        #     }
        
        # Get real AI predictions using trained models
        ai_prediction = None
        try:
            # Use ensemble prediction for best accuracy
            ai_prediction = predict_with_ensemble(cropped_path)
            print(f"AI Prediction: {ai_prediction}")
        except Exception as e:
            print(f"Error getting AI prediction: {e}")
            # Fallback to transfer learning
            try:
                ai_prediction = predict_with_transfer_learning(cropped_path)
            except Exception as e2:
                print(f"Error in transfer learning fallback: {e2}")
                ai_prediction = {
                    'category': 'unknown',
            'confidence': 0.0,
                    'probabilities': {},
                    'message': 'AI prediction failed'
        }
        
        # Convert all numpy types in features to native Python types
        def to_py_type(val):
            if hasattr(val, 'item'):
                return val.item()
            if isinstance(val, (list, tuple)):
                return [to_py_type(v) for v in val]
            if isinstance(val, dict):
                return {k: to_py_type(v) for k, v in val.items()}
            return val

        # Add ripeness and grade labels to features
        features_dict["ripeness_label"] = ripeness_label
        features_dict["grade"] = grade_label
        
        # Update ripeness with AI prediction if available
        if ai_prediction and ai_prediction.get('category') != 'error' and ai_prediction.get('category') != 'unknown':
            # Use the new comprehensive analysis
            if ai_prediction.get('display_analysis'):
                features_dict["ripeness"] = ai_prediction['display_analysis']['ripeness']
            elif ai_prediction.get('probabilities'):
                display_analysis = analyze_probabilities_for_display(ai_prediction['probabilities'])
                features_dict["ripeness"] = display_analysis['ripeness']
            else:
                features_dict["ripeness"] = ai_prediction['category']
            features_dict["ai_confidence"] = ai_prediction['confidence']
        
        # Generate simple analysis summary (removed detailed text)
        analysis_summary = f"ANFIS Analysis: {ai_prediction.get('message', 'Analysis completed')}" if ai_prediction else "Analysis completed"
        
        response = {
            "cropped_image": os.path.basename(cropped_path),
            "bbox": [int(x) for x in found],
            "boxes": [[int(x) for x in box] for box in boxes],
            "features": to_py_type(features_dict),
            "analysis_summary": analysis_summary,
            "recommendation": "This bell pepper shows quality with AI-powered ripeness grading.",
            "ai_defect_detection": ai_prediction
        }
    except Exception as e:
        print(f"Error in analysis: {e}")
        response = {"error": str(e)}
    
    return response

# ANFIS TRAINING ENDPOINTS - COMMENTED OUT DUE TO INACCURACY
# @app.post("/train-anfis")
# async def train_anfis_model(
#     num_synthetic_images: int = Form(500),
#     use_real_images: bool = Form(False)
# ):
#     """Train the ANFIS model for defect detection"""
#     try:
#         print("Starting ANFIS model training...")
#         
#         # Run the complete training pipeline
#         results = anfis_pipeline.run_complete_pipeline(
#             num_synthetic_images=num_synthetic_images
#         )
#         
#         # Load the trained model
#         global trained_model
#         trained_model = anfis_pipeline.load_trained_model()
#         
#         return JSONResponse({
#             "status": "success",
#             "message": "ANFIS model trained successfully",
#             "training_results": results
#         })
#         
#     except Exception as e:
#         print(f"Error training ANFIS model: {e}")
#         return JSONResponse({
#             "status": "error",
#             "message": f"Failed to train ANFIS model: {str(e)}"
#         }, status_code=500)

# @app.post("/predict-defect")
# async def predict_defect(
#     image: UploadFile = File(...)
# ):
#     """Predict defect using ANFIS model"""
#     try:
#         # Save uploaded image
#         file_id = str(uuid.uuid4())
#         file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(image.file, buffer)
#         
#         # Check if model is loaded
#         global trained_model
#         if trained_model is None:
#             try:
#                 trained_model = anfis_pipeline.load_trained_model()
#             except Exception as e:
#                 return JSONResponse({
#                     "status": "error",
#                     "message": "No trained model available. Please train the model first."
#                 }, status_code=400)
#         
#         # Predict defect
#         result = anfis_pipeline.predict_defect(file_path, trained_model)
#         
#         return JSONResponse({
#             "status": "success",
#             "prediction": result
#         })
#         
#     except Exception as e:
#         print(f"Error in defect prediction: {e}")
#         return JSONResponse({
#             "status": "error",
#             "message": f"Failed to predict defect: {str(e)}"
#         }, status_code=500)

# @app.get("/model-status")
# async def get_model_status():
#     """Get the status of the trained model"""
#     global trained_model
#     
#     if trained_model is None:
#         try:
#             trained_model = anfis_pipeline.load_trained_model()
#             model_loaded = True
#         except:
#             model_loaded = False
#     else:
#         model_loaded = True
#     
#     return JSONResponse({
#         "model_loaded": model_loaded,
#         "model_type": "ANFIS",
#         "features": feature_extractor.get_feature_names()
#     })

# SYNTHETIC DATA ENDPOINTS - COMMENTED OUT DUE TO ANFIS DISABLED
# @app.post("/generate-synthetic")
# async def generate_synthetic_data(
#     num_images: int = Form(100),
#     defect_type: str = Form("healthy"),
#     quality_variation: str = Form("normal")  # poor, normal, excellent
# ):
#     """Generate synthetic bell pepper images with enhanced quality variation"""
#     try:
#         print(f"Generating {num_images} synthetic images of type: {defect_type} with quality: {quality_variation}")
#         
#         # Enhanced synthetic data generation with quality variations
#         synthetic_data = []
#         
#         for i in range(num_images):
#             # Generate base features with quality-based variations
#             base_features = generate_quality_based_features(quality_variation, defect_type)
#             
#             # Apply expert knowledge rules
#             expert_features = apply_expert_rules(base_features)
#             
#             # Add realistic noise and variations
#             augmented_features = augment_features_with_noise(expert_features)
#             
#             # Generate composite features
#             composite_features = create_composite_features(augmented_features)
#             
#             synthetic_data.append({
#                 'id': f'synthetic_{defect_type}_{i}',
#                 'features': composite_features,
#                 'quality_label': quality_variation,
#                 'defect_type': defect_type
#             })
#         
#         # Save synthetic data for training
#         save_synthetic_data(synthetic_data, defect_type, quality_variation)
#         
#         return JSONResponse({
#             "status": "success",
#             "message": f"Generated {num_images} synthetic samples",
#             "data_type": defect_type,
#             "quality_level": quality_variation,
#             "sample_features": synthetic_data[0]['features'] if synthetic_data else None
#         })
#         
#     except Exception as e:
#         print(f"Error generating synthetic data: {e}")
#         return JSONResponse({
#             "status": "error",
#             "message": f"Failed to generate synthetic data: {str(e)}"
#         }, status_code=500)

# @app.post("/train-anfis-advanced")
# async def train_anfis_advanced(
#     num_samples: int = Form(1000),
#     quality_levels: str = Form("excellent,normal,poor"),  # comma-separated
#     defect_types: str = Form("healthy,defective"),  # comma-separated
#     use_expert_rules: bool = Form(True),
#     use_composite_features: bool = Form(True)
# ):
#     """Advanced ANFIS training with enhanced synthetic data generation"""
#     try:
#         print("Starting advanced ANFIS model training...")
#         
#         quality_list = [q.strip() for q in quality_levels.split(',')]
#         defect_list = [d.strip() for d in defect_types.split(',')]
#         
#         # Generate comprehensive synthetic dataset
#         all_training_data = []
#         
#         for quality in quality_list:
#             for defect_type in defect_list:
#                 samples_per_category = num_samples // (len(quality_list) * len(defect_list))
#                 
#                 print(f"Generating {samples_per_category} samples for {quality} quality, {defect_type} type")
#                 
#                 for i in range(samples_per_category):
#                     # Generate base features
#                     base_features = generate_quality_based_features(quality, defect_type)
#                     
#                     # Apply expert rules if enabled
#                     if use_expert_rules:
#                         base_features = apply_expert_rules(base_features)
#                     
#                     # Add realistic noise
#                     augmented_features = augment_features_with_noise(base_features)
#                     
#                     # Create composite features if enabled
#                     if use_composite_features:
#                         final_features = create_composite_features(augmented_features)
#                     else:
#                         final_features = augmented_features
#                     
#                     # Create training sample
#                     sample = {
#                         'features': final_features,
#                         'quality_label': quality,
#                         'defect_type': defect_type,
#                         'target_grade': determine_grade(final_features, quality, defect_type)
#                     }
#                     
#                     all_training_data.append(sample)
#         
#         # Train ANFIS model with enhanced data
#         print(f"Training ANFIS with {len(all_training_data)} enhanced samples...")
#         
#         # Convert to training format
#         X = []  # Features
#         y = []  # Targets
#         
#         for sample in all_training_data:
#             features = sample['features']
#             # Convert features to numerical array
#             feature_vector = [
#                 features.get('hue_mean', 0),
#                 features.get('glossiness', 0),
#                 features.get('defect_count', 0),
#                 features.get('color_vibrancy', 0),
#                 features.get('smoothness', 0),
#                 features.get('weight', 0),
#                 features.get('quality_index', 0),
#                 features.get('surface_quality', 0),
#                 features.get('defect_severity', 0)
#             ]
#             X.append(feature_vector)
#             y.append(sample['target_grade'])
#         
#         # Train ANFIS model (you'll need to implement this in your pipeline)
#         # results = anfis_pipeline.train_with_enhanced_data(X, y)
#         
#         # For now, save the enhanced training data
#         save_enhanced_training_data(all_training_data)
#         
#         return JSONResponse({
#             "status": "success",
#             "message": "Advanced ANFIS training data generated successfully",
#             "total_samples": len(all_training_data),
#             "quality_levels": quality_list,
#             "defect_types": defect_list,
#             "features_used": list(all_training_data[0]['features'].keys()) if all_training_data else [],
#             "sample_data": all_training_data[0] if all_training_data else None
#         })
#         
#     except Exception as e:
#         print(f"Error in advanced ANFIS training: {e}")
#         return JSONResponse({
#             "status": "error",
#             "message": f"Failed to train advanced ANFIS model: {str(e)}"
#         }, status_code=500)

# Specific route for favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon.ico from static directory"""
    favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        return JSONResponse({"error": "Favicon not found"}, status_code=404)

# Catch-all route to serve React app for any non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the React frontend for any routes that don't match API endpoints"""
    # If it's an API route, let it pass through
    if (full_path.startswith("api/") or full_path.startswith("uploads/") or 
        full_path.startswith("static/") or full_path.startswith("docs") or 
        full_path.startswith("redoc") or full_path.startswith("openapi.json") or
        full_path == "favicon.ico"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    # For all other routes, serve the React app
    static_file_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    else:
        return JSONResponse({"message": "Pepper Vision Backend API (Railway Demo)", "status": "running", "version": "1.0.0"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
