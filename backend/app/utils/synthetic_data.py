import cv2
import numpy as np
import albumentations as A
from typing import Dict, Tuple, List, Optional
import random
import os
from dataclasses import dataclass

@dataclass
class DefectParams:
    color: Tuple[int, int, int]  # HSV
    pattern: str
    size: Tuple[float, float]  # % of pepper area
    texture: str
    intensity: Tuple[float, float] = (0.3, 0.8)

# Defect type definitions
DEFECT_TYPES = {
    'anthracnose': DefectParams(
        color=(10, 50, 30),
        pattern='circular',
        size=(0.05, 0.15),
        texture='sunken'
    ),
    'blight': DefectParams(
        color=(20, 40, 25),
        pattern='irregular',
        size=(0.08, 0.25),
        texture='necrotic'
    ),
    'sunscald': DefectParams(
        color=(15, 30, 80),
        pattern='patchy',
        size=(0.10, 0.30),
        texture='blistered'
    ),
    'mildew': DefectParams(
        color=(120, 20, 60),
        pattern='powdery',
        size=(0.05, 0.20),
        texture='fuzzy'
    ),
    'rot': DefectParams(
        color=(0, 80, 40),
        pattern='spreading',
        size=(0.15, 0.40),
        texture='soft'
    ),
    'insect': DefectParams(
        color=(30, 150, 40),
        pattern='irregular',
        size=(0.01, 0.08),
        texture='punctured'
    )
}

class BellPepperSyntheticGenerator:
    def __init__(self, output_dir: str = "./synthetic_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Base pepper color ranges (HSV)
        self.healthy_colors = {
            'green': [(35, 40, 60), (85, 255, 255)],
            'red': [(0, 50, 50), (10, 255, 255)],
            'yellow': [(20, 50, 50), (30, 255, 255)],
            'orange': [(10, 50, 50), (20, 255, 255)]
        }
        
        # Augmentation pipeline
        self.augmentation = A.Compose([
            A.RandomBrightnessContrast(p=0.3),
            A.RandomShadow(p=0.2),
            A.RandomSunFlare(p=0.1),
            A.RandomRain(p=0.1),
            A.GaussNoise(p=0.2),
            A.MotionBlur(p=0.1),
            A.OpticalDistortion(p=0.1),
            A.GridDistortion(p=0.1),
        ])
    
    def generate_base_pepper(self, size: Tuple[int, int] = (512, 512)) -> np.ndarray:
        """Generate a base healthy bell pepper image"""
        img = np.zeros((size[0], size[1], 3), dtype=np.uint8)
        
        # Create pepper shape using ellipses
        center = (size[1]//2, size[0]//2)
        axes = (size[1]//3, size[0]//2)
        
        # Random pepper color
        color_name = random.choice(list(self.healthy_colors.keys()))
        hsv_range = self.healthy_colors[color_name]
        
        # Generate base color with variation
        h = random.randint(hsv_range[0][0], hsv_range[1][0])
        s = random.randint(hsv_range[0][1], hsv_range[1][1])
        v = random.randint(hsv_range[0][2], hsv_range[1][2])
        
        # Create mask for pepper shape
        mask = np.zeros(size[:2], dtype=np.uint8)
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # Add texture and shading
        noise = np.random.normal(0, 20, size[:2]).astype(np.uint8)
        shading = cv2.GaussianBlur(noise, (21, 21), 0)
        
        # Apply color and shading
        hsv_img = np.zeros((size[0], size[1], 3), dtype=np.uint8)
        hsv_img[mask > 0] = [h, s, v]
        
        # Add shading variation
        for i in range(3):
            hsv_img[:, :, i] = np.clip(hsv_img[:, :, i] + shading, 0, 255)
        
        # Convert to BGR
        bgr_img = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
        
        # Add highlights and shadows
        highlight_mask = np.zeros_like(mask)
        cv2.ellipse(highlight_mask, (center[0]-20, center[1]-30), (axes[0]//3, axes[1]//4), 0, 0, 180, 255, -1)
        bgr_img[highlight_mask > 0] = np.clip(bgr_img[highlight_mask > 0] * 1.3, 0, 255)
        
        return bgr_img, mask
    
    def apply_defect(self, img: np.ndarray, mask: np.ndarray, defect_type: str) -> np.ndarray:
        """Apply a specific defect to the pepper image"""
        if defect_type == 'healthy':
            return img
        
        defect = DEFECT_TYPES[defect_type]
        
        # Find pepper region
        pepper_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not pepper_contours:
            return img
        
        pepper_contour = max(pepper_contours, key=cv2.contourArea)
        pepper_area = cv2.contourArea(pepper_contour)
        
        # Calculate defect size
        defect_size = random.uniform(defect.size[0], defect.size[1])
        defect_area = pepper_area * defect_size
        
        # Generate defect mask
        defect_mask = np.zeros_like(mask)
        
        if defect.pattern == 'circular':
            # Circular defect
            center = tuple(map(int, cv2.minEnclosingCircle(pepper_contour)[0]))
            radius = int(np.sqrt(defect_area / np.pi))
            cv2.circle(defect_mask, center, radius, 255, -1)
            
        elif defect.pattern == 'irregular':
            # Irregular defect using random polygons
            center = tuple(map(int, cv2.minEnclosingCircle(pepper_contour)[0]))
            points = []
            for _ in range(random.randint(5, 8)):
                angle = random.uniform(0, 2*np.pi)
                radius = random.uniform(radius*0.5, radius)
                x = center[0] + int(radius * np.cos(angle))
                y = center[1] + int(radius * np.sin(angle))
                points.append([x, y])
            points = np.array(points, dtype=np.int32)
            cv2.fillPoly(defect_mask, [points], 255)
            
        elif defect.pattern == 'patchy':
            # Multiple small patches
            for _ in range(random.randint(3, 6)):
                center = tuple(map(int, cv2.minEnclosingCircle(pepper_contour)[0]))
                radius = int(np.sqrt(defect_area / (np.pi * random.randint(3, 6))))
                x = center[0] + random.randint(-radius, radius)
                y = center[1] + random.randint(-radius, radius)
                cv2.circle(defect_mask, (x, y), radius, 255, -1)
                
        elif defect.pattern == 'powdery':
            # Powdery mildew effect
            for _ in range(random.randint(20, 40)):
                center = tuple(map(int, cv2.minEnclosingCircle(pepper_contour)[0]))
                x = center[0] + random.randint(-radius, radius)
                y = center[1] + random.randint(-radius, radius)
                cv2.circle(defect_mask, (x, y), random.randint(2, 5), 255, -1)
                
        elif defect.pattern == 'spreading':
            # Spreading rot effect
            center = tuple(map(int, cv2.minEnclosingCircle(pepper_contour)[0]))
            for i in range(3):
                radius = int(np.sqrt(defect_area / (np.pi * 3))) + i * 10
                cv2.circle(defect_mask, center, radius, 255, -1)
        
        # Apply defect color and texture
        defect_intensity = random.uniform(defect.intensity[0], defect.intensity[1])
        
        # Convert defect color to BGR
        defect_hsv = np.array([defect.color], dtype=np.uint8)
        defect_bgr = cv2.cvtColor(defect_hsv, cv2.COLOR_HSV2BGR)[0, 0]
        
        # Apply defect
        defect_region = defect_mask > 0
        if defect.texture == 'sunken':
            # Darken the region
            img[defect_region] = np.clip(img[defect_region] * (1 - defect_intensity), 0, 255)
        elif defect.texture == 'necrotic':
            # Brown/black necrotic tissue
            img[defect_region] = np.clip(img[defect_region] * (1 - defect_intensity) + defect_bgr * defect_intensity, 0, 255)
        elif defect.texture == 'blistered':
            # Lighter, raised areas
            img[defect_region] = np.clip(img[defect_region] * (1 + defect_intensity), 0, 255)
        elif defect.texture == 'fuzzy':
            # Add noise for fuzzy texture
            noise = np.random.normal(0, 30, img[defect_region].shape).astype(np.uint8)
            img[defect_region] = np.clip(img[defect_region] + noise, 0, 255)
        elif defect.texture == 'soft':
            # Soft, mushy appearance
            img[defect_region] = np.clip(img[defect_region] * (1 - defect_intensity * 0.5), 0, 255)
        elif defect.texture == 'punctured':
            # Small puncture marks
            for _ in range(random.randint(5, 15)):
                x = random.randint(0, img.shape[1]-1)
                y = random.randint(0, img.shape[0]-1)
                if defect_mask[y, x] > 0:
                    cv2.circle(img, (x, y), random.randint(1, 3), (0, 0, 0), -1)
        
        return img
    
    def generate_dataset(self, num_images: int = 500, real_to_synthetic_ratio: float = 0.2) -> List[Dict]:
        """Generate synthetic dataset with specified ratios"""
        dataset = []
        
        # Calculate class distribution
        num_real = int(num_images * real_to_synthetic_ratio)
        num_synthetic = num_images - num_real
        
        defect_classes = list(DEFECT_TYPES.keys()) + ['healthy']
        class_ratios = {
            'healthy': 0.4,
            'anthracnose': 0.1,
            'blight': 0.1,
            'sunscald': 0.1,
            'mildew': 0.1,
            'rot': 0.1,
            'insect': 0.1
        }
        
        # Generate synthetic images
        for i in range(num_synthetic):
            # Select defect type based on ratios
            defect_type = np.random.choice(defect_classes, p=[class_ratios[c] for c in defect_classes])
            
            # Generate base pepper
            img, mask = self.generate_base_pepper()
            
            # Apply defect
            img = self.apply_defect(img, mask, defect_type)
            
            # Apply augmentations
            augmented = self.augmentation(image=img)
            img = augmented['image']
            
            # Save image
            filename = f"synthetic_{i:04d}_{defect_type}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            cv2.imwrite(filepath, img)
            
            dataset.append({
                'image_path': filepath,
                'defect_type': defect_type,
                'is_synthetic': True
            })
        
        return dataset
    
    def generate_single_image(self, defect_type: str = 'healthy') -> Tuple[np.ndarray, str]:
        """Generate a single synthetic image for testing"""
        img, mask = self.generate_base_pepper()
        img = self.apply_defect(img, mask, defect_type)
        
        # Apply augmentations
        augmented = self.augmentation(image=img)
        img = augmented['image']
        
        return img, defect_type

if __name__ == "__main__":
    # Test the synthetic data generator
    generator = BellPepperSyntheticGenerator()
    
    # Generate test images for each defect type
    defect_types = list(DEFECT_TYPES.keys()) + ['healthy']
    
    for defect_type in defect_types:
        img, label = generator.generate_single_image(defect_type)
        filename = f"test_{defect_type}.jpg"
        cv2.imwrite(filename, img)
        print(f"Generated test image: {filename}") 