# =========================================================
# SMART GLOVE CLOUD COMMUNICATION CLIENT
# Secure Upload To API Gateway
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import time
import json
import random
import hashlib
from datetime import datetime

# =========================================================
# DEVICE CONFIGURATION
# =========================================================
DEVICE_ID = "SMART_GLOVE_PI_001"

API_GATEWAY = "https://api.smartglovecloud.com/upload"

AUTH_TOKEN = "EDGE_AI_SECURE_TOKEN"

# =========================================================
# GENERATE PATIENT DATA
# =========================================================
def generate_patient_data():

    hemoglobin = round(random.uniform(8.0, 16.0), 1)

    if hemoglobin < 12:
        status = "ANEMIC"
    else:
        status = "NON-ANEMIC"

    patient_data = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "hemoglobin": hemoglobin,
        "status": status,
        "image_name": "patient_finger_image.jpg"
    }

    return patient_data


# =========================================================
# CREATE SECURITY HASH
# =========================================================
def encrypt_payload(data):

    print("\nEncrypting Patient Data...")
    time.sleep(2)

    # Convert dictionary to JSON string
    json_data = json.dumps(data)

    # Generate SHA256 hash
    secure_hash = hashlib.sha256(
        json_data.encode()
    ).hexdigest()

    print("Data Encryption Successful")

    return secure_hash


# =========================================================
# API HANDSHAKE
# =========================================================
def api_handshake():

    print("\n========================================")
    print(" API GATEWAY HANDSHAKE ")
    print("========================================")

    print("\nConnecting To API Gateway...")
    time.sleep(2)

    print(f"API Endpoint : {API_GATEWAY}")

    time.sleep(1)

    print("\nAuthenticating Device Token...")
    time.sleep(2)

    print("Authentication Successful")

    print("\nSecure HTTPS Channel Established")
    time.sleep(1)

    print("Handshake Completed")


# =========================================================
# SECURE DATA UPLOAD
# =========================================================
def secure_upload(patient_data, encrypted_hash):

    print("\n========================================")
    print(" SECURE CLOUD UPLOAD ")
    print("========================================")

    print("\nUploading Encrypted Payload...")
    time.sleep(3)

    upload_success = random.choice([True, True, True, False])

    if upload_success:

        print("Upload Successful")
        print("Cloud Server Response : 200 OK")

        return True

    else:

        print("Upload Failed")
        print("Server Timeout Detected")

        return False


# =========================================================
# RETRY LOGIC
# =========================================================
def retry_upload():

    print("\nRetrying Secure Upload...")
    time.sleep(2)

    print("Backup Connection Established")
    time.sleep(1)

    print("Upload Successful On Retry")


# =========================================================
# DISPLAY DATA
# =========================================================
def display_data(data):

    print("\n========================================")
    print(" PATIENT DATA ")
    print("========================================")

    for key, value in data.items():

        print(f"{key} : {value}")


# =========================================================
# MAIN PROGRAM
# =========================================================
print("================================================")
print(" SMART GLOVE CLOUD CLIENT SYSTEM ")
print("================================================")

# =========================================================
# GENERATE DATA
# =========================================================
patient_data = generate_patient_data()

# =========================================================
# DISPLAY DATA
# =========================================================
display_data(patient_data)

# =========================================================
# ENCRYPT PAYLOAD
# =========================================================
encrypted_hash = encrypt_payload(patient_data)

print(f"\nSecurity Hash : {encrypted_hash[:25]}...")

# =========================================================
# API HANDSHAKE
# =========================================================
api_handshake()

# =========================================================
# SECURE UPLOAD
# =========================================================
upload_status = secure_upload(
    patient_data,
    encrypted_hash
)

# =========================================================
# RETRY IF FAILED
# =========================================================
if not upload_status:

    retry_upload()

# =========================================================
# FINAL STATUS
# =========================================================
print("\n================================================")
print(" CLOUD COMMUNICATION COMPLETED ")
print("================================================")

print("""
PROGRAM LOGIC:
1. Generate patient hemoglobin data
2. Create encrypted payload hash
3. Connect to API Gateway
4. Authenticate device token
5. Establish secure HTTPS communication
6. Upload patient data securely
7. Retry upload if failure occurs

Purpose:
Enable secure cloud communication
between Raspberry Pi smart glove
and healthcare cloud server.
""")

# =========================================================
# YOUR ROLE
# =========================================================
print("\nMY ROLE - CLOUD COMMUNICATION ENGINEER")
print("----------------------------------------")

print("""
Responsibilities:
- API client integration
- Secure upload handling
- Device authentication
- Payload encryption
- Retry management
- Edge-to-cloud communication
""")

print("\nThank You")
print("================================================")