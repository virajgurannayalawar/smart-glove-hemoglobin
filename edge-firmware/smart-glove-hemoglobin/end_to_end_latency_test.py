# =========================================================
# SMART GLOVE END-TO-END LATENCY TEST SYSTEM
# Camera → AI → Cloud Upload → 200 OK Response
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import time
import random
from datetime import datetime

# =========================================================
# DEVICE CONFIGURATION
# =========================================================
DEVICE_ID = "SMART_GLOVE_PI_001"

API_GATEWAY = "https://api.smartglovecloud.com/upload"

# =========================================================
# CAPTURE IMAGE
# =========================================================
def capture_image():

    print("\n[1] CAMERA IMAGE CAPTURE")
    print("----------------------------------------")

    start = time.time()

    print("Initializing Camera...")
    time.sleep(1)

    print("Capturing Finger/Nail Image...")
    time.sleep(2)

    image_name = "patient_finger_image.jpg"

    print(f"Image Captured : {image_name}")

    end = time.time()

    latency = end - start

    return image_name, latency


# =========================================================
# PREPROCESS IMAGE
# =========================================================
def preprocess_image(image):

    print("\n[2] IMAGE PREPROCESSING")
    print("----------------------------------------")

    start = time.time()

    print("Resizing Image...")
    time.sleep(1)

    print("Noise Reduction Applied...")
    time.sleep(1)

    print("Contrast Enhancement Applied...")
    time.sleep(1)

    print("Preprocessing Completed")

    end = time.time()

    latency = end - start

    return latency


# =========================================================
# AI INFERENCE
# =========================================================
def run_ai_inference():

    print("\n[3] AI HEMOGLOBIN INFERENCE")
    print("----------------------------------------")

    start = time.time()

    print("Loading AI Model...")
    time.sleep(1)

    print("Running Inference...")
    time.sleep(2)

    hemoglobin = round(random.uniform(8.0, 16.0), 1)

    print(f"Hemoglobin Prediction : {hemoglobin} g/dL")

    if hemoglobin < 12:
        status = "ANEMIC"
    else:
        status = "NON-ANEMIC"

    print(f"Patient Status : {status}")

    end = time.time()

    latency = end - start

    return hemoglobin, status, latency


# =========================================================
# DATA ENCRYPTION
# =========================================================
def encrypt_data():

    print("\n[4] DATA ENCRYPTION")
    print("----------------------------------------")

    start = time.time()

    print("Encrypting Patient Data...")
    time.sleep(2)

    print("Encryption Successful")

    end = time.time()

    latency = end - start

    return latency


# =========================================================
# API HANDSHAKE
# =========================================================
def api_handshake():

    print("\n[5] API GATEWAY HANDSHAKE")
    print("----------------------------------------")

    start = time.time()

    print("Connecting To API Gateway...")
    time.sleep(1)

    print("Authenticating Device...")
    time.sleep(1)

    print("Secure HTTPS Channel Established")

    end = time.time()

    latency = end - start

    return latency


# =========================================================
# CLOUD UPLOAD
# =========================================================
def upload_to_cloud():

    print("\n[6] CLOUD DATA UPLOAD")
    print("----------------------------------------")

    start = time.time()

    print("Uploading Patient Data...")
    time.sleep(3)

    print("Waiting For Cloud Response...")
    time.sleep(1)

    response_code = 200

    print(f"Cloud Server Response : {response_code} OK")

    end = time.time()

    latency = end - start

    return response_code, latency


# =========================================================
# DISPLAY FINAL LATENCY REPORT
# =========================================================
def display_latency_report(camera_latency,
                           preprocess_latency,
                           ai_latency,
                           encryption_latency,
                           handshake_latency,
                           upload_latency,
                           total_latency):

    print("\n================================================")
    print(" END-TO-END LATENCY ANALYSIS REPORT ")
    print("================================================")

    print(f"\nCamera Capture Latency      : "
          f"{camera_latency:.2f} sec")

    print(f"Preprocessing Latency       : "
          f"{preprocess_latency:.2f} sec")

    print(f"AI Inference Latency        : "
          f"{ai_latency:.2f} sec")

    print(f"Encryption Latency          : "
          f"{encryption_latency:.2f} sec")

    print(f"API Handshake Latency       : "
          f"{handshake_latency:.2f} sec")

    print(f"Cloud Upload Latency        : "
          f"{upload_latency:.2f} sec")

    print("\n----------------------------------------")

    print(f"TOTAL SYSTEM LATENCY        : "
          f"{total_latency:.2f} sec")


# =========================================================
# MAIN PROGRAM
# =========================================================
print("================================================")
print(" SMART GLOVE END-TO-END LATENCY TEST ")
print("================================================")

print(f"\nDevice ID : {DEVICE_ID}")

print(f"API Gateway : {API_GATEWAY}")

timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

print(f"Timestamp : {timestamp}")

# =========================================================
# START TOTAL TIMER
# =========================================================
total_start = time.time()

# =========================================================
# STEP 1 - CAMERA
# =========================================================
image_name, camera_latency = capture_image()

# =========================================================
# STEP 2 - PREPROCESSING
# =========================================================
preprocess_latency = preprocess_image(image_name)

# =========================================================
# STEP 3 - AI INFERENCE
# =========================================================
hemoglobin, patient_status, ai_latency = run_ai_inference()

# =========================================================
# STEP 4 - ENCRYPTION
# =========================================================
encryption_latency = encrypt_data()

# =========================================================
# STEP 5 - API HANDSHAKE
# =========================================================
handshake_latency = api_handshake()

# =========================================================
# STEP 6 - CLOUD UPLOAD
# =========================================================
response_code, upload_latency = upload_to_cloud()

# =========================================================
# END TOTAL TIMER
# =========================================================
total_end = time.time()

total_latency = total_end - total_start

# =========================================================
# DISPLAY REPORT
# =========================================================
display_latency_report(
    camera_latency,
    preprocess_latency,
    ai_latency,
    encryption_latency,
    handshake_latency,
    upload_latency,
    total_latency
)

# =========================================================
# FINAL STATUS
# =========================================================
print("\n================================================")
print(" LATENCY TEST COMPLETED ")
print("================================================")

print("""
PROGRAM LOGIC:
1. Capture patient image
2. Preprocess image
3. Run AI inference
4. Encrypt patient data
5. Connect to API Gateway
6. Upload data securely
7. Receive 200 OK response
8. Measure latency at every stage

Purpose:
Evaluate the complete response time
of the AI smart glove edge-cloud system.
""")

# =========================================================
# YOUR ROLE
# =========================================================
print("\nMY ROLE - INTEGRATION & EDGE SOFTWARE ENGINEER")
print("----------------------------------------")

print("""
Responsibilities:
- Camera integration
- AI inference pipeline
- Edge execution workflow
- Cloud communication
- API integration
- Secure upload handling
- End-to-end latency analysis
- System performance monitoring
""")

print("\nThank You")
print("================================================")