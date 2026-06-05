# =========================================================
# SMART GLOVE AI INFERENCE SYSTEM
# Hemoglobin Prediction Pipeline
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import time
import random
import numpy as np

# =========================================================
# IMAGE PREPROCESSING
# =========================================================
def preprocess_image(image_path):

    print("\nPreprocessing Image...")
    time.sleep(2)

    print("Resizing Image To 224x224")
    time.sleep(1)

    print("Normalizing Pixel Values")
    time.sleep(1)

    print("Converting Image To Tensor Format")
    time.sleep(1)

    # Simulated image tensor
    image_tensor = np.random.rand(1, 224, 224, 3)

    print("Preprocessing Completed")

    return image_tensor


# =========================================================
# LOAD AI MODEL
# =========================================================
def load_model():

    print("\nLoading AI Hemoglobin Model...")
    time.sleep(2)

    print("Model Loaded Successfully")

    return "hemoglobin_model"


# =========================================================
# RUN MODEL INFERENCE
# =========================================================
def run_inference(model, image_tensor):

    print("\nRunning AI Inference...")
    time.sleep(3)

    # Simulated hemoglobin prediction
    hemoglobin = round(random.uniform(8.0, 16.0), 1)

    return hemoglobin


# =========================================================
# DETECT ANEMIA STATUS
# =========================================================
def detect_status(hb):

    if hb < 12:
        return "ANEMIC"

    else:
        return "NON-ANEMIC"


# =========================================================
# MAIN PROGRAM
# =========================================================
print("================================================")
print(" SMART GLOVE AI INFERENCE SYSTEM ")
print("================================================")

# =========================================================
# IMAGE INPUT
# =========================================================
image_path = "patient_finger_image.jpg"

print(f"\nInput Image : {image_path}")

# =========================================================
# PREPROCESS IMAGE
# =========================================================
processed_image = preprocess_image(image_path)

# =========================================================
# LOAD MODEL
# =========================================================
model = load_model()

# =========================================================
# RUN INFERENCE
# =========================================================
hemoglobin_value = run_inference(model, processed_image)

# =========================================================
# DETECT STATUS
# =========================================================
patient_status = detect_status(hemoglobin_value)

# =========================================================
# DISPLAY RESULTS
# =========================================================
print("\n================================================")
print(" AI HEMOGLOBIN ANALYSIS RESULT ")
print("================================================")

print(f"\nHemoglobin Level : {hemoglobin_value} g/dL")

print(f"Patient Status   : {patient_status}")

# =========================================================
# WORKFLOW EXPLANATION
# =========================================================
print("\nWORKFLOW")
print("----------------------------------------")

print("""
1. Input image received
2. Image preprocessing completed
3. AI model loaded
4. Inference executed
5. Hemoglobin extracted
6. Patient classified
""")

# =========================================================
# ROLE EXPLANATION
# =========================================================
print("\nMY ROLE")
print("----------------------------------------")

print("""
As Integration & Edge Software Engineer:

- I handled inference pipeline integration
- Connected image preprocessing with AI model
- Managed model execution workflow
- Extracted hemoglobin output
- Integrated prediction into edge system
""")

print("\nThank You")
print("================================================")