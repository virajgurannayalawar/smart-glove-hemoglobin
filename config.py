import os

# =========================
# BACKEND CONFIGURATION
# =========================

BACKEND_BASE_URL = "https://smart-glove-hemoglobin.onrender.com"

# Replace later with real scan ID
SCAN_ID = "550e8400-e29b-41d4-a716-446655440000"

UPLOAD_ENDPOINT = f"/api/v1/scan/sessions/{SCAN_ID}/upload"

# =========================
# API AUTHENTICATION
# =========================

# Replace with REAL glove API key
GLOVE_API_KEY = "PASTE_REAL_GLOVE_API_KEY_HERE"

# =========================
# AES-256 SECRET KEY
# MUST BE EXACTLY 32 BYTES
# =========================

AES_SECRET_KEY = b"12345678901234567890123456789012"

# =========================
# REQUEST SETTINGS
# =========================

UPLOAD_TIMEOUT = 20
MAX_RETRY_COUNT = 3

# =========================
# CACHE DIRECTORY
# =========================

CACHE_DIRECTORY = "uploads_cache"

# =========================
# DEVICE SETTINGS
# =========================

DEVICE_NAME = "SMART_GLOVE_PI"

# =========================
# CREATE CACHE DIRECTORY
# =========================

os.makedirs(CACHE_DIRECTORY, exist_ok=True)