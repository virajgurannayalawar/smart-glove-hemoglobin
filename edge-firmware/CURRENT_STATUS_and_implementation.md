# Edge Firmware — Current Status Report

**Date:** May 27, 2026  
**Target Device:** Raspberry Pi (Smart Glove)

---

## Overview

The current edge firmware implementation is a **prototype/demo stage**. It does not function as production-ready hardware integration and relies on simulated data and processes.

---

## What Currently Exists

### 1. **AI Inference Pipeline** (`ai_interference_pipeline.py`)
- **Status:** Stub implementation only
- **Current behavior:**
  - Simulates image preprocessing (resizing to 224×224, normalization)
  - Generates a **random hemoglobin value** using `random.uniform(8.0, 16.0)`
  - Does not load any real model weights
  - Does not process actual sensor/camera input
  - Returns mock results with hardcoded output `"ANEMIC"` or `"NON-ANEMIC"` (using a single threshold: `hb < 12`)

### 2. **Cloud API Client** (`cloud_api_client.py`)
- **Status:** Simulation/demo only
- **Current behavior:**
  - Generates fake patient data
  - Creates a SHA256 hash of the payload
  - Simulates API handshake and secure HTTPS connection
  - **Does NOT actually call the backend API**
  - Hardcodes a fake endpoint: `https://api.smartglovecloud.com/upload`
  - Does not use real JWT authentication
  - Does not send multipart form data
  - Randomly decides upload success/failure

### 3. **Missing Components**
- ❌ No real Raspberry Pi camera integration
- ❌ No actual hardware sensor drivers
- ❌ No AI model files or weights in `ai-model/` folder (only placeholder)
- ❌ No real image encryption/decryption pipeline
- ❌ No JWT-based authentication flow
- ❌ No real backend API communication

---

## Current Limitations

| Issue | Impact |
|-------|--------|
| Random hemoglobin generation | Cannot produce medical-grade readings |
| No model inference | Cannot classify anemia based on real image analysis |
| No JWT authentication | Cannot authenticate with backend |
| No real image capture | Cannot process actual finger images |
| No multipart upload | Does not match backend API contract |
| Single anemia threshold | Misclassifies children, pregnant patients, males |

---

## Backend Contract (What Backend Expects)

The backend is ready to receive uploads at:
- **Endpoint:** `POST /api/v1/upload/`
- **Authentication:** `Authorization: Bearer <JWT_TOKEN>`
- **Payload:** Multipart form with:
  - `image` (encrypted binary file)
  - `metadata` (JSON string)

### Metadata Schema
```json
{
  "hemoglobin_level": 12.5,
  "capture_timestamp": 1716825600,
  "sync_timestamp": 1716825605,
  "patient_id": "PATIENT123",
  "is_pregnant": false
}
```

### Image Encryption
- Algorithm: AES-256-CBC
- IV: 16 random bytes prepended to ciphertext
- Padding: PKCS7
- Key: `32byte-long-secret-key-for-aes-!`

---

## Summary

**The current edge firmware is a mock/demo implementation, not a working integration.** It needs to be completely refactored to:
- Capture real images from Raspberry Pi camera
- Authenticate with the backend
- Encrypt image payloads correctly
- Send data in the backend's expected format
- Remove all fake generators and simulations




# Edge Firmware — Implementation Plan (New Workflow)

**Date:** May 27, 2026  
**Target Device:** Raspberry Pi (Smart Glove)  
**Owner:** Edge Firmware Engineer (Intern)

---

## New Architecture Overview

```
Frontend (Mobile App)
    ↓
    └─→ POST /api/v1/upload/ (request to activate glove)
            ↓
    Backend (Receives request, processes image, returns result)
            ↓
    Raspberry Pi (Captures image, encrypts, sends to backend)
            ↓
    Backend (Decrypts image, preprocesses, feeds to AI model)
            ↓
    AI Engineer (Model inference happens here)
            ↓
    Backend (Returns hemoglobin result to Frontend)
            ↓
    Frontend (Displays result to patient)
```

---

## Key Change: No AI Model on Raspberry Pi

**OLD WORKFLOW:**
- Image captured → Processed on Pi → Model runs on Pi → Result sent to backend

**NEW WORKFLOW:**
- Image captured → **Immediately encrypted** → Sent to backend
- **All processing and AI inference happens on backend/cloud** (not on Pi)

---

## What You (Edge Firmware Engineer) Must Implement

### Phase 1: Real Hardware Integration

#### 1. **Image Capture from Camera** (`camera_capture.py`)
Replace fake image generation with real Pi camera capture:

```python
import cv2
from picamera2 import Picamera2

def capture_finger_image() -> bytes:
    """
    Capture a single image of patient's finger using Raspberry Pi camera.
    Returns raw image bytes.
    """
    picam2 = Picamera2()
    picam2.start()
    
    # Capture image
    frame = picam2.capture_array()
    picam2.close()
    
    # Convert to bytes
    _, image_bytes = cv2.imencode('.jpg', frame)
    return image_bytes.tobytes()
```

**Requirements:**
- Install `picamera2` and `opencv-python`
- Test on actual Raspberry Pi with camera connected
- Ensure image is at least 224×224 pixels
- Store image temporarily in memory (do NOT save to disk)

---

#### 2. **AES-256 Encryption** (`image_encryptor.py`)
Implement proper encryption that matches backend decryption:

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

AES_SECRET_KEY = b"32byte-long-secret-key-for-aes-!"[:32]

def encrypt_image(image_bytes: bytes) -> bytes:
    """
    Encrypt image using AES-256-CBC.
    Returns: IV (16 bytes) + ciphertext
    """
    # Generate random 16-byte IV
    iv = os.urandom(16)
    
    # Pad image data to AES block size (PKCS7)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(image_bytes) + padder.finalize()
    
    # Encrypt
    cipher = Cipher(algorithms.AES(AES_SECRET_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return IV + ciphertext (backend expects this format)
    return iv + ciphertext
```

**Requirements:**
- Use exact same AES key as backend: `32byte-long-secret-key-for-aes-!`
- Prepend 16-byte IV to output
- Use PKCS7 padding
- Match backend's `decrypt_image_payload()` expectations

---

#### 3. **Backend Authentication** (`auth_client.py`)
Authenticate with backend to get JWT token:

```python
import requests
import json

BACKEND_BASE = "https://<your-backend-url>"  # Replace with actual URL
API_PREFIX = "/api/v1"

def login_to_backend(email: str, password: str) -> str:
    """
    Login to backend and return JWT token.
    This token must be stored and used for all subsequent requests.
    """
    login_url = f"{BACKEND_BASE}{API_PREFIX}/auth/login"
    response = requests.post(login_url, json={
        "email": email,
        "password": password
    })
    response.raise_for_status()
    token = response.json()["token"]
    return token
```

**Requirements:**
- Use valid credentials (email/password) for a registered user
- Store token securely
- Token expires every 7 days; re-login periodically
- Handle authentication failures gracefully

---

#### 4. **Metadata Collection** (`metadata_builder.py`)
Build metadata that matches backend schema:

```python
import time

def build_metadata(patient_id: str, is_pregnant: bool = False) -> str:
    """
    Build metadata JSON matching UploadMetadata schema.
    """
    now = int(time.time())
    
    metadata = {
        "hemoglobin_level": 0.0,  # Leave as 0.0 - backend will calculate this
        "capture_timestamp": now,   # When image was captured on Pi
        "sync_timestamp": now,      # When upload starts
        "patient_id": patient_id,
        "is_pregnant": is_pregnant
    }
    
    return json.dumps(metadata)
```

**Requirements:**
- Use Unix timestamp (seconds since epoch)
- `capture_timestamp` = when image was taken
- `sync_timestamp` = when upload begins
- `patient_id` must be valid and belong to authenticated user
- `hemoglobin_level` = 0.0 (backend will compute this from image)

---

#### 5. **Multipart Upload** (`upload_client.py`)
Send encrypted image + metadata to backend:

```python
import requests

def upload_reading(token: str, encrypted_image: bytes, metadata: str) -> dict:
    """
    Upload encrypted image and metadata to backend.
    """
    upload_url = f"{BACKEND_BASE}{API_PREFIX}/upload/"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        "image": ("image.bin", encrypted_image, "application/octet-stream"),
        "metadata": (None, metadata, "application/json")
    }
    
    response = requests.post(upload_url, headers=headers, files=files)
    response.raise_for_status()
    
    return response.json()
```

**Requirements:**
- Send as multipart/form-data (not JSON)
- Include `Authorization: Bearer <token>` header
- `image` field = encrypted bytes
- `metadata` field = JSON string
- Handle 5MB file size limit
- Retry on timeout/connection failure

---

### Phase 2: Remove All Fake/Demo Code

**DELETE or REPLACE:**
- ❌ `ai_interference_pipeline.py` — Remove fake model, random generation
- ❌ `cloud_api_client.py` — Remove fake upload simulation
- ✅ Keep only directory structure; add real implementations above

---

### Phase 3: Testing on Raspberry Pi

Before deployment, test locally:

```bash
# 1. Install dependencies
pip install picamera2 opencv-python cryptography requests

# 2. Test image capture
python camera_capture.py

# 3. Test encryption/decryption with backend
python image_encryptor.py

# 4. Test authentication
python auth_client.py --email user@example.com --password yourpassword

# 5. End-to-end test
python main_workflow.py --patient-id PATIENT123 --is-pregnant false
```

---

## Exact File Structure Expected

```
edge-firmware/smart-glove-hemoglobin/
├── main_workflow.py              (orchestrates full flow)
├── camera_capture.py              (image capture)
├── image_encryptor.py             (AES encryption)
├── auth_client.py                 (JWT authentication)
├── metadata_builder.py            (metadata creation)
├── upload_client.py               (multipart upload)
├── config.py                      (constants: backend URL, AES key, etc.)
├── requirements.txt               (dependencies)
└── README.md                      (how to run)
```

---

## What You Should NOT Do

- ❌ Do NOT load any AI model on Raspberry Pi
- ❌ Do NOT calculate hemoglobin on Pi
- ❌ Do NOT preprocess/enhance images on Pi
- ❌ Do NOT use random.uniform() for hemoglobin
- ❌ Do NOT hardcode fake endpoints
- ❌ Do NOT skip JWT authentication
- ❌ Do NOT send plaintext images (encrypt always)

---

## Dependencies to Add

Update `requirements.txt`:

```
picamera2==0.3.17
opencv-python==4.8.0.76
cryptography==41.0.7
requests==2.31.0
```

---

## Important: Keep Backend Code Updated

⚠️ **Critical for you:**

The backend is being actively developed by the Backend Team. As they implement image processing and model integration features, you must:

1. **Pull updates regularly** (at least daily during development):
   ```bash
   cd cloud-backend
   git pull origin main
   ```

2. **Check for API contract changes** in:
   - `app/api/routes/upload.py` — upload endpoint behavior
   - `app/schemas/history.py` — metadata schema changes
   - `app/core/config.py` — encryption key or settings changes

3. **Update your code immediately** if:
   - The `UploadMetadata` schema changes
   - The AES key or encryption algorithm changes
   - The upload endpoint URL or authentication changes
   - New fields are required in metadata

4. **Communicate with Backend Team** if:
   - You need to know when image processing is ready
   - You discover API contract mismatches
   - You need to test against a staging backend

---

## Success Criteria

Your implementation is complete when:

- ✅ Real image captured from Pi camera (not fake)
- ✅ Image encrypted with AES-256-CBC (not plaintext)
- ✅ Metadata collected with correct patient/timestamp info
- ✅ JWT authentication works (token obtained and used)
- ✅ Multipart upload to `POST /api/v1/upload/` succeeds
- ✅ Backend returns `200 OK` with `reading_id`
- ✅ Image appears in backend logs or database
- ✅ No random number generators for hemoglobin
- ✅ No model code on Raspberry Pi

---

## Next Steps

1. Set up Raspberry Pi with camera and required libraries
2. Implement real image capture
3. Implement encryption matching backend expectations
4. Implement JWT authentication flow
5. Implement multipart upload
6. End-to-end test with backend
7. Deploy to production Raspberry Pi

---

**Questions?** Contact backend team or refer to `cloud-backend/BACKEND_API_REFERENCE.md` for detailed endpoint specs.
