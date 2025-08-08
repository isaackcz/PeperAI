# Extended color mapping for bell peppers
def map_hue_to_color(hue: float, sat: float, val: float) -> str:
    # Use saturation and value for brown/white/black detection
    if sat < 40 and val < 60:
        return "black"
    if sat < 40 and val > 180:
        return "white"
    if sat < 40 and 60 <= val <= 180:
        return "brown"
    # Hue-based mapping
    if hue >= 345 or hue <= 15:
        return "red"
    elif hue <= 30:
        return "vermilion"
    elif hue <= 45:
        return "orange"
    elif hue <= 55:
        return "gold"
    elif hue <= 65:
        return "yellow"
    elif hue <= 85:
        return "lime"
    elif hue <= 110:
        return "light green"
    elif hue <= 140:
        return "green"
    elif hue <= 165:
        return "olive"
    elif hue <= 200:
        return "teal"
    elif hue <= 260:
        return "purple"
    elif hue <= 320:
        return "magenta"
    else:
        return "unknown"

# Multi-color detection using k-means clustering
def detect_bell_pepper_colors_opencv(image_path: str, k: int = 3, region: tuple = None) -> list:
    import cv2
    import numpy as np
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)
    # Filter out very dark/bright pixels (optional)
    pixels = pixels[(pixels[:,1] > 20) & (pixels[:,2] > 20)]
    if len(pixels) == 0:
        return ["unknown"]
    # K-means clustering
    from sklearn.cluster import KMeans
    k = min(k, len(pixels))
    kmeans = KMeans(n_clusters=k, n_init=5, random_state=42)
    labels = kmeans.fit_predict(pixels)
    centers = kmeans.cluster_centers_
    color_names = []
    for center in centers:
        h, s, v = center
        color_name = map_hue_to_color(h*2, s, v)  # OpenCV hue to 0-360
        color_names.append(color_name)
    # Remove duplicates and sort by cluster size
    counts = np.bincount(labels)
    sorted_colors = [color_names[i] for i in np.argsort(-counts)]
    return list(dict.fromkeys(sorted_colors))
def detect_bell_pepper_color(hue: int) -> str:
    """
    Maps hue value to bell pepper color with ripeness-specific ranges.
    Hue range: 0-360 degrees (standard HSL/HSV) or 0-180 (OpenCV scaled).
    This version accepts standard 0-360 degree hue.
    """
    # Handle red wraparound at 0/360
    if hue >= 345 or hue <= 15:
        return "red"
    elif hue <= 45:
        return "orange"
    elif hue <= 65:
        return "yellow"
    elif hue <= 165:
        return "green"
    # Purple/brown transition zone
    elif hue <= 260:
        return "purple"  # or chocolate brown
    else:
        return "unknown"

# OpenCV version (hue range 0-180)
def detect_bell_pepper_color_opencv(hue: int) -> str:
    """Version for OpenCV's 0-180 hue range"""
    scaled_hue = hue * 2  # Convert to 0-360 scale
    return detect_bell_pepper_color(scaled_hue)
import cv2
import numpy as np
from typing import Tuple, List
from sklearn.cluster import KMeans
from skimage import color as skcolor
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops
import mahotas
from PIL import Image

def get_average_hsv(image_path: str, region: Tuple[int, int, int, int] = None) -> Tuple[float, float, float]:
    """
    Calculate the average HSV value of the image or a region.
    region: (x, y, w, h) or None for full image
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_h = np.mean(hsv[:,:,0])
    avg_s = np.mean(hsv[:,:,1])
    avg_v = np.mean(hsv[:,:,2])
    return avg_h, avg_s, avg_v

def classify_ripeness_from_hsv(avg_h: float, avg_s: float, avg_v: float) -> str:
    """
    Classify bell pepper ripeness based on average HSV values.
    Returns: Very_Unripe, Unripe, Half_Ripe, Ripe, Overripe
    """
    # These thresholds are illustrative and may need tuning for your dataset
    if avg_h < 30 and avg_s > 80 and avg_v < 100:
        return "Very_Unripe"  # Dark green
    elif avg_h < 40 and avg_s > 60:
        return "Unripe"  # Green
    elif 40 <= avg_h < 60:
        return "Half_Ripe"  # Green-yellow
    elif 60 <= avg_h < 100:
        return "Ripe"  # Yellow/orange/red
    elif avg_h >= 100:
        return "Overripe"  # Deep red/orange, possibly wrinkled
    else:
        return "Unknown"

def detect_bell_pepper_colors_advanced(image_path: str, k: int = 3, region: tuple = None) -> List[str]:
    """
    Advanced color detection using both HSV and LAB color spaces, KMeans, and color histograms.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    pixels_hsv = hsv.reshape(-1, 3)
    pixels_lab = lab.reshape(-1, 3)
    # Filter out very dark/bright pixels
    pixels_hsv = pixels_hsv[(pixels_hsv[:,1] > 20) & (pixels_hsv[:,2] > 20)]
    if len(pixels_hsv) == 0:
        return ["unknown"]
    # KMeans in HSV
    k_hsv = min(k, len(pixels_hsv))
    kmeans_hsv = KMeans(n_clusters=k_hsv, n_init=5, random_state=42)
    labels_hsv = kmeans_hsv.fit_predict(pixels_hsv)
    centers_hsv = kmeans_hsv.cluster_centers_
    color_names_hsv = [map_hue_to_color(h*2, s, v) for h, s, v in centers_hsv]
    # KMeans in LAB
    k_lab = min(k, len(pixels_lab))
    kmeans_lab = KMeans(n_clusters=k_lab, n_init=5, random_state=42)
    labels_lab = kmeans_lab.fit_predict(pixels_lab)
    centers_lab = kmeans_lab.cluster_centers_
    # Use LAB a* and b* for color clustering
    color_names_lab = [f"LAB({int(l)},{int(a)},{int(b)})" for l, a, b in centers_lab]
    # Color histogram (HSV)
    hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
    hist_h = hist_h.flatten()
    dominant_hue = np.argmax(hist_h)
    dom_color = map_hue_to_color(dominant_hue*2, 255, 255)
    # Combine and deduplicate
    all_colors = color_names_hsv + color_names_lab + [dom_color]
    return list(dict.fromkeys(all_colors))

def get_color_moments(image_path: str, region: Tuple[int, int, int, int] = None) -> dict:
    """
    Compute color moments (mean, std, skewness) for each channel in LAB color space.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    moments = {}
    for i, ch in enumerate(['L', 'A', 'B']):
        channel = lab[:,:,i].flatten()
        moments[f'{ch}_mean'] = np.mean(channel)
        moments[f'{ch}_std'] = np.std(channel)
        moments[f'{ch}_skew'] = (np.mean((channel - np.mean(channel))**3)) / (np.std(channel)**3 + 1e-8)
    return moments

def get_haralick_features(image_path: str, region: Tuple[int, int, int, int] = None) -> dict:
    """
    Extract Haralick texture features using Mahotas.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    features = mahotas.features.haralick(img).mean(axis=0)
    return {f'haralick_{i}': feat for i, feat in enumerate(features)}

def get_lbp_features(image_path: str, region: Tuple[int, int, int, int] = None, P: int = 8, R: int = 1) -> dict:
    """
    Extract Local Binary Pattern (LBP) features for texture analysis.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Image not found or not readable: {image_path}")
    if region:
        x, y, w, h = region
        img = img[y:y+h, x:x+w]
    lbp = local_binary_pattern(img, P, R, method='uniform')
    (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, P + 3), range=(0, P + 2))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-8)
    return {f'lbp_{i}': v for i, v in enumerate(hist)}
