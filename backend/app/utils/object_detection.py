
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
    torch.serialization.add_safe_globals([
        SegmentationModel,
        Sequential,
        ModuleList,
        Conv,
        C2f,
        Bottleneck,
        SPPF,  # Added missing SPPF module
        Conv2d,
        BatchNorm2d,
        SiLU
    ])
    print("PyTorch safe globals configured for YOLO model loading")
except ImportError as e:
    print(f"Warning: PyTorch or Ultralytics not available: {e}")

from ultralytics import YOLO
import cv2
import numpy as np
import os
"""
from skimage.feature import greycomatrix, greycoprops
"""
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.measure import regionprops, label
from skimage import filters
import mahotas
from sklearn.cluster import KMeans

def detect_and_crop_object(image_path: str, click_x: int, click_y: int, output_dir: str = None):
    import torch
    
    # Configure PyTorch 2.6+ compatibility
    original_load = torch.load
    
    try:
        # Load YOLOv8 model with compatibility handling
        try:
            model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"YOLO loading failed with safe globals, trying weights_only=False: {e}")
            torch.load = lambda *args, **kwargs: original_load(*args, **{**kwargs, 'weights_only': False})
            model = YOLO('yolov8n.pt')
        
        results = model(image_path)
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Image not found: {image_path}")
        print(f"Click: ({click_x}, {click_y})")
        found = False
        for box in results[0].boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = map(int, box[:4])
            print(f"Detected box: {x1}, {y1}, {x2}, {y2}")
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                found = True
                cropped = img[y1:y2, x1:x2]
                if output_dir is None:
                    output_dir = os.path.dirname(image_path)
                os.makedirs(output_dir, exist_ok=True)
                cropped_path = os.path.join(output_dir, f"cropped_{os.path.basename(image_path)}")
                cv2.imwrite(cropped_path, cropped)
                return cropped_path, (x1, y1, x2, y2)
        if not found:
            print("No object detected at the selected location.")
        return None
    finally:
        torch.load = original_load


# --- Feature Extraction Functions ---
def extract_size_shape_features(image_path: str):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {}
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    x, y, w, h = cv2.boundingRect(c)
    aspect_ratio = float(w) / h if h != 0 else 0
    roundness = (4 * np.pi * area) / (perimeter ** 2) if perimeter != 0 else 0
    compactness = area / (w * h) if (w * h) != 0 else 0
    return {
        "area": area,
        "perimeter": perimeter,
        "aspect_ratio": aspect_ratio,
        "roundness": roundness,
        "compactness": compactness
    }

def extract_color_vibrancy(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    vibrancy = np.mean(hsv[:,:,1])  # Mean saturation
    return vibrancy

def extract_glossiness(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Glossy surfaces have high specular highlights (bright spots)
    glossiness = np.percentile(gray, 99) - np.percentile(gray, 50)
    return glossiness

def extract_weight(image_path: str):
    # Stub: Weight usually requires a scale, but can be estimated by area if pixel-to-mm is known
    shape = extract_size_shape_features(image_path)
    area = shape.get("area", 0)
    # Assume 1 pixel = 1 mm^2 for stub (replace with calibration)
    estimated_weight = area * 0.002  # Example: 0.002g per mm^2
    return estimated_weight

def extract_surface_features(image_path: str):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    # Smoothness: low stddev, Roughness: high stddev
    stddev = np.std(img)
    mean = np.mean(img)
    smoothness = 1 / (1 + stddev)
    roughness = stddev / mean if mean != 0 else 0
    return {
        "smoothness": smoothness,
        "roughness": roughness
    }

def extract_advanced_shape_features(image_path: str):
    """
    Extract advanced shape features using regionprops and contour analysis.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    lbl = label(thresh)
    props = regionprops(lbl)
    if not props:
        return {}
    p = max(props, key=lambda x: x.area)
    features = {
        "area": p.area,
        "perimeter": p.perimeter,
        "eccentricity": p.eccentricity,
        "solidity": p.solidity,
        "extent": p.extent,
        "orientation": p.orientation,
        "major_axis_length": p.major_axis_length,
        "minor_axis_length": p.minor_axis_length,
        "convex_area": p.convex_area,
        "bbox_area": p.bbox_area,
        "circularity": (4 * np.pi * p.area) / (p.perimeter ** 2) if p.perimeter != 0 else 0,
        "elongation": p.major_axis_length / p.minor_axis_length if p.minor_axis_length != 0 else 0
    }
    return features

def extract_glcm_features(image_path: str, distances=[5], angles=[0]) -> dict:
    """
    Extract GLCM (texture) features using skimage.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    glcm = graycomatrix(img, distances=distances, angles=angles, symmetric=True, normed=True)
    features = {
        'contrast': graycoprops(glcm, 'contrast')[0, 0],
        'dissimilarity': graycoprops(glcm, 'dissimilarity')[0, 0],
        'homogeneity': graycoprops(glcm, 'homogeneity')[0, 0],
        'energy': graycoprops(glcm, 'energy')[0, 0],
        'correlation': graycoprops(glcm, 'correlation')[0, 0],
        'ASM': graycoprops(glcm, 'ASM')[0, 0]
    }
    return features

def extract_lbp_features(image_path: str, P: int = 8, R: int = 1) -> dict:
    """
    Extract Local Binary Pattern (LBP) features for texture analysis.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    lbp = local_binary_pattern(img, P, R, method='uniform')
    (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, P + 3), range=(0, P + 2))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-8)
    return {f'lbp_{i}': v for i, v in enumerate(hist)}

def extract_haralick_features(image_path: str) -> dict:
    """
    Extract Haralick texture features using Mahotas.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {}
    features = mahotas.features.haralick(img).mean(axis=0)
    return {f'haralick_{i}': feat for i, feat in enumerate(features)}

def extract_grade_ripeness(features: dict):
    """Rule-based ripeness and grade assignment with improved accuracy"""
    avg_h = features.get("avg_h", None)
    avg_s = features.get("avg_s", None)
    avg_v = features.get("avg_v", None)
    defect_count = features.get("defect_count", 0)
    defect_severity = features.get("defect_severity", 0)
    largest_defect = features.get("largest_defect", 0)
    area = features.get("area", 0)
    color_vibrancy = features.get("color_vibrancy", 0)
    glossiness = features.get("glossiness", 0)
    smoothness = features.get("smoothness", 0)
    
    ripeness = "Unknown"
    grade = "Unknown"
    
    # Improved ripeness logic based on HSV values
    if avg_h is not None and avg_s is not None and avg_v is not None:
        # For bell peppers, hue ranges: Green (35-85), Yellow (20-35), Red (0-20 or 160-180)
        if 35 <= avg_h <= 85:  # Green range
            if avg_s > 80 and avg_v < 100:
                ripeness = "Very Unripe"
            elif avg_s > 60:
                ripeness = "Unripe"
            else:
                ripeness = "Partially Ripe"
        elif 20 <= avg_h < 35:  # Yellow range
            ripeness = "Ripe"
        elif (0 <= avg_h < 20) or (160 <= avg_h <= 180):  # Red range
            ripeness = "Fully Ripe"
        else:
            ripeness = "Unknown"
    
    # Improved grade logic with more realistic thresholds for bell peppers
    # Grade A: Excellent quality, minimal defects
    if (defect_count <= 5 and 
        defect_severity <= 3.0 and 
        largest_defect <= 800 and
        color_vibrancy > 60 and 
        glossiness > 20 and  # Natural bell peppers have some glossiness
        smoothness > 0.3):   # Lowered threshold for natural surface variations
        grade = "Grade A"
    
    # Grade B: Good quality, minor defects
    elif (defect_count <= 12 and 
          defect_severity <= 8.0 and 
          largest_defect <= 1500 and
          color_vibrancy > 40 and 
          glossiness > 15):
        grade = "Grade B"
    
    # Grade C: Acceptable quality, moderate defects
    elif (defect_count <= 20 and 
          defect_severity <= 15.0 and 
          largest_defect <= 2500):
        grade = "Grade C"
    
    # Grade D: Poor quality, significant defects
    elif (defect_count <= 30 and 
          defect_severity <= 25.0):
        grade = "Grade D"
    
    # Rejected: Too many defects
    else:
        grade = "Rejected"
    
    return ripeness, grade

def extract_texture_features(image_path: str):
    """Extract texture features using GLCM"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {
                "texture_contrast": 0.0,
                "texture_homogeneity": 0.0,
                "texture_entropy": 0.0
            }
        
        # Normalize image
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Calculate GLCM
        distances = [1]
        angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        
        glcm = graycomatrix(img, distances, angles, levels=256, symmetric=True, normed=True)
        
        # Extract texture properties
        contrast = graycoprops(glcm, 'contrast').mean()
        homogeneity = graycoprops(glcm, 'homogeneity').mean()
        
        # Calculate entropy from GLCM
        glcm_normalized = glcm / (glcm.sum() + 1e-8)
        entropy = -np.sum(glcm_normalized * np.log2(glcm_normalized + 1e-8))
        
        return {
            "texture_contrast": float(contrast),
            "texture_homogeneity": float(homogeneity),
            "texture_entropy": float(entropy)
        }
    except Exception as e:
        print(f"Error extracting texture features: {e}")
        return {
            "texture_contrast": 0.0,
            "texture_homogeneity": 0.0,
            "texture_entropy": 0.0
        }

def extract_defect_features(image_path: str):
    """Extract defect features with improved accuracy"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {
            "defect_count": 0,
            "total_defect_area": 0,
            "largest_defect": 0,
            "defect_severity": 0
        }
    
    try:
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        
        # Use adaptive thresholding with more conservative parameters
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 15, 5)  # Increased block size and C value
        
        # Morphological operations to remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # Increased kernel size
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area to remove very small noise and natural variations
        min_area = 200  # Increased minimum area to avoid detecting natural surface variations
        valid_defects = []
        total_defect_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                # Additional filtering: check aspect ratio to avoid detecting natural curves
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h != 0 else 0
                if 0.2 < aspect_ratio < 5.0:  # Filter out very elongated or very narrow contours
                    valid_defects.append(contour)
                    total_defect_area += area
        
        defect_count = len(valid_defects)
        largest_defect = max([cv2.contourArea(c) for c in valid_defects]) if valid_defects else 0
        
        # Calculate defect severity (percentage of total area)
        total_area = img.shape[0] * img.shape[1]
        defect_severity = (total_defect_area / total_area) * 100 if total_area > 0 else 0
        
        return {
            "defect_count": defect_count,
            "total_defect_area": total_defect_area,
            "largest_defect": largest_defect,
            "defect_severity": defect_severity
        }
        
    except Exception as e:
        print(f"Error in defect detection: {e}")
        return {
            "defect_count": 0,
            "total_defect_area": 0,
            "largest_defect": 0,
            "defect_severity": 0
        }
