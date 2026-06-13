from io import BytesIO
from typing import Tuple
import logging
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class ImageProcessingError(ValueError):
    pass


def extract_roi(image: np.ndarray) -> np.ndarray:
    """
    Extracts the Region of Interest (ROI) from an image.
    Uses HSV and YCrCb color spaces to detect skin/nail regions and crops to the largest contour.
    
    Args:
        image: A BGR numpy array representing the image.
    
    Returns:
        The cropped ROI as a BGR numpy array. Returns original image if no ROI found.
    """
    if image is None or image.size == 0:   
        return image

    try:
        # Convert to HSV and YCrCb color spaces for skin detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

        # Define skin color bounds in HSV
        lower_hsv = np.array([0, 20, 70], dtype=np.uint8)
        upper_hsv = np.array([20, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        # Define skin color bounds in YCrCb
        lower_ycrcb = np.array([0, 135, 85], dtype=np.uint8)
        upper_ycrcb = np.array([255, 180, 135], dtype=np.uint8)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        # Combine masks
        combined_mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)

        # Apply morphological operations to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image # Return original if nothing found
            
        # Find the largest contour (assumed hand/finger)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding box for the largest contour
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add a small padding
        padding = 10
        h_img, w_img = image.shape[:2]
        
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(w_img, x + w + padding)
        y2 = min(h_img, y + h + padding)

        return image[y1:y2, x1:x2]
    except Exception as e:
        logger.warning(f"Error extracting ROI: {e}. Falling back to original image.")
        return image


def calibrate_color(image: np.ndarray) -> np.ndarray:
    """
    Normalizes the color of the image to handle varying lighting conditions.
    Applies Gray World assumption to estimate and correct illuminant.
    
    Args:
        image: A BGR numpy array representing the image.
    
    Returns:
        Color-calibrated BGR image.
    """
    if image is None or image.size == 0:
        return image

    try:
        # Convert to floating point for calculations
        img_float = image.astype(np.float32)

        # Calculate average of each channel
        avg_b = np.mean(img_float[:, :, 0])
        avg_g = np.mean(img_float[:, :, 1])
        avg_r = np.mean(img_float[:, :, 2])

        # Overall gray value
        avg_gray = (avg_b + avg_g + avg_r) / 3.0

        # Calculate scale factors to align all channels to average gray
        scale_b = avg_gray / avg_b if avg_b > 0 else 1.0
        scale_g = avg_gray / avg_g if avg_g > 0 else 1.0
        scale_r = avg_gray / avg_r if avg_r > 0 else 1.0

        # Apply scaling
        calibrated_img = np.zeros_like(img_float)
        calibrated_img[:, :, 0] = img_float[:, :, 0] * scale_b
        calibrated_img[:, :, 1] = img_float[:, :, 1] * scale_g
        calibrated_img[:, :, 2] = img_float[:, :, 2] * scale_r

        # Clip to valid 8-bit range and convert back
        calibrated_img = np.clip(calibrated_img, 0, 255).astype(np.uint8)
        
        return calibrated_img
    except Exception as e:
        logger.warning(f"Error calibrating color: {e}. Falling back to input image.")
        return image


def preprocess_for_model(
    image_bytes: bytes,
    *,
    size: int,
    grayscale: bool = False,
    autocontrast: bool = False,
) -> Tuple[bytes, str]:
    """
    Deterministic preprocessing matching the AI model requirements:
    - decode
    - extract region of interest (ROI)
    - color calibration (Gray World assumption)
    - resize to target (size, size) using area interpolation
    - convert BGR to RGB
    - encode back to PNG bytes

    Returns: (processed_bytes, format)
    """
    if not image_bytes:
        raise ImageProcessingError("Empty image payload")
    if size <= 0 or size > 2048:
        raise ImageProcessingError("Invalid target size")

    try:
        # 1. Decode bytes using cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise ImageProcessingError("Invalid image format or corrupted bytes")
    except Exception as e:
        raise ImageProcessingError(f"Failed to decode image: {e}")

    # 2. Extract ROI
    roi_image = extract_roi(image)

    # 3. Color Calibration
    calibrated_image = calibrate_color(roi_image)

    try:
        # 4. Resize to target dimensions
        resized_image = cv2.resize(calibrated_image, (size, size), interpolation=cv2.INTER_AREA)

        # 5. Convert BGR to RGB
        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
    except Exception as e:
        raise ImageProcessingError(f"Failed to resize/convert color space: {e}")

    try:
        # 6. Encode back to PNG bytes
        img_pil = Image.fromarray(rgb_image)
        out = BytesIO()
        img_pil.save(out, format="PNG", optimize=True)
        return out.getvalue(), "png"
    except Exception as e:
        raise ImageProcessingError(f"Failed to encode processed image: {e}")
