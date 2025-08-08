import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops
from skimage.color import rgb2gray
from typing import Dict, Tuple, Optional, List
import os

class BellPepperFeatureExtractor:
    def __init__(self):
        self.feature_names = [
            'h_mean', 's_mean', 'v_mean',
            'h_std', 's_std', 'v_std',
            'glcm_contrast', 'glcm_homogeneity',
            'contour_area', 'circularity', 'solidity'
        ]
    
    def extract_hsv_features(self, img: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Extract HSV mean and standard deviation features"""
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        if mask is not None:
            # Apply mask to focus on pepper region
            hsv_masked = hsv[mask > 0]
            if len(hsv_masked) == 0:
                # If no mask region, use entire image
                hsv_masked = hsv.reshape(-1, 3)
        else:
            hsv_masked = hsv.reshape(-1, 3)
        
        # Calculate mean and std for each channel
        h_mean = np.mean(hsv_masked[:, 0])
        s_mean = np.mean(hsv_masked[:, 1])
        v_mean = np.mean(hsv_masked[:, 2])
        
        h_std = np.std(hsv_masked[:, 0])
        s_std = np.std(hsv_masked[:, 1])
        v_std = np.std(hsv_masked[:, 2])
        
        return {
            'h_mean': float(h_mean),
            's_mean': float(s_mean),
            'v_mean': float(v_mean),
            'h_std': float(h_std),
            's_std': float(s_std),
            'v_std': float(v_std)
        }
    
    def extract_glcm_features(self, img: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Extract GLCM texture features"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Apply mask if provided
        if mask is not None:
            gray = gray * (mask > 0).astype(np.uint8)
        
        # Normalize to 0-255 range
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Calculate GLCM
        distances = [1]
        angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        
        try:
            glcm = graycomatrix(gray, distances, angles, levels=256, symmetric=True, normed=True)
            
            # Extract properties
            contrast = graycoprops(glcm, 'contrast').mean()
            homogeneity = graycoprops(glcm, 'homogeneity').mean()
            
        except Exception as e:
            # Fallback values if GLCM calculation fails
            contrast = 0.0
            homogeneity = 0.0
        
        return {
            'glcm_contrast': float(contrast),
            'glcm_homogeneity': float(homogeneity)
        }
    
    def extract_contour_features(self, img: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Extract contour-based shape features"""
        if mask is not None:
            # Use provided mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            # Create mask from image
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Apply threshold to create mask
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # Return default values if no contours found
            return {
                'contour_area': 0.0,
                'circularity': 0.0,
                'solidity': 0.0
            }
        
        # Find the largest contour (assumed to be the pepper)
        contour = max(contours, key=cv2.contourArea)
        
        # Calculate area
        area = cv2.contourArea(contour)
        
        # Calculate perimeter
        perimeter = cv2.arcLength(contour, True)
        
        # Calculate circularity (4*pi*area / perimeter^2)
        circularity = 0.0
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter * perimeter)
        
        # Calculate solidity (area / convex_hull_area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = 0.0
        if hull_area > 0:
            solidity = area / hull_area
        
        return {
            'contour_area': float(area),
            'circularity': float(circularity),
            'solidity': float(solidity)
        }
    
    def extract_all_features(self, img: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Extract all 11 features from the image"""
        features = {}
        
        # Extract HSV features
        hsv_features = self.extract_hsv_features(img, mask)
        features.update(hsv_features)
        
        # Extract GLCM features
        glcm_features = self.extract_glcm_features(img, mask)
        features.update(glcm_features)
        
        # Extract contour features
        contour_features = self.extract_contour_features(img, mask)
        features.update(contour_features)
        
        return features
    
    def extract_features_from_file(self, image_path: str, mask_path: Optional[str] = None) -> Dict[str, float]:
        """Extract features from an image file"""
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Load mask if provided
        mask = None
        if mask_path and os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        return self.extract_all_features(img, mask)
    
    def extract_features_batch(self, image_paths: List[str], mask_paths: Optional[List[str]] = None) -> List[Dict[str, float]]:
        """Extract features from multiple images"""
        features_list = []
        
        for i, image_path in enumerate(image_paths):
            mask_path = None
            if mask_paths and i < len(mask_paths):
                mask_path = mask_paths[i]
            
            try:
                features = self.extract_features_from_file(image_path, mask_path)
                features_list.append(features)
            except Exception as e:
                print(f"Error extracting features from {image_path}: {e}")
                # Add default features
                features_list.append({name: 0.0 for name in self.feature_names})
        
        return features_list
    
    def normalize_features(self, features_list: List[Dict[str, float]]) -> Tuple[List[Dict[str, float]], Dict[str, Tuple[float, float]]]:
        """Normalize features using min-max scaling"""
        if not features_list:
            return features_list, {}
        
        # Calculate min and max for each feature
        feature_stats = {}
        for feature_name in self.feature_names:
            values = [f[feature_name] for f in features_list if feature_name in f]
            if values:
                min_val = min(values)
                max_val = max(values)
                feature_stats[feature_name] = (min_val, max_val)
            else:
                feature_stats[feature_name] = (0.0, 1.0)
        
        # Normalize features
        normalized_features = []
        for features in features_list:
            normalized = {}
            for feature_name in self.feature_names:
                if feature_name in features:
                    min_val, max_val = feature_stats[feature_name]
                    if max_val > min_val:
                        normalized[feature_name] = (features[feature_name] - min_val) / (max_val - min_val)
                    else:
                        normalized[feature_name] = 0.0
                else:
                    normalized[feature_name] = 0.0
            normalized_features.append(normalized)
        
        return normalized_features, feature_stats
    
    def get_feature_names(self) -> List[str]:
        """Get the list of feature names"""
        return self.feature_names.copy()

if __name__ == "__main__":
    # Test the feature extractor
    extractor = BellPepperFeatureExtractor()
    
    # Create a test image
    test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # Extract features
    features = extractor.extract_all_features(test_img)
    
    print("Extracted features:")
    for name, value in features.items():
        print(f"{name}: {value:.4f}") 