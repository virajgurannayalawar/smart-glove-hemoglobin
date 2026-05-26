# =========================================================
# SMART GLOVE IMAGE CACHE SYSTEM
# Temporary Image Storage During Wi-Fi Failure
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import os
import time
import random
import shutil
from datetime import datetime

# =========================================================
# CREATE STORAGE FOLDERS
# =========================================================

# Simulated microSD card folder
MICRO_SD_FOLDER = "microSD_cache"

# Simulated cloud upload folder
CLOUD_FOLDER = "cloud_storage"

# Create folders if not present
os.makedirs(MICRO_SD_FOLDER, exist_ok=True)
os.makedirs(CLOUD_FOLDER, exist_ok=True)

# =========================================================
# SIMULATE IMAGE CAPTURE
# =========================================================
def capture_image():

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")

    image_name = f"patient_image_{timestamp}.jpg"

    print("\nCapturing Patient Finger Image...")
    time.sleep(2)

    # Create dummy image file
    with open(image_name, "w") as file:
        file.write("Simulated Finger Image Data")

    print(f"Image Captured : {image_name}")

    return image_name


# =========================================================
# SIMULATE WIFI STATUS
# =========================================================
def check_wifi_connection():

    # Randomly simulate Wi-Fi status
    wifi_status = random.choice([True, False])

    return wifi_status


# =========================================================
# UPLOAD IMAGE TO CLOUD
# =========================================================
def upload_to_cloud(image_file):

    print("\nWi-Fi Connected")
    print("Uploading Image To Cloud...")

    time.sleep(2)

    # Simulated cloud upload
    destination = os.path.join(CLOUD_FOLDER,
                               os.path.basename(image_file))

    shutil.copy(image_file, destination)

    print("Cloud Upload Successful")


# =========================================================
# CACHE IMAGE TO MICRO SD CARD
# =========================================================
def cache_to_micro_sd(image_file):

    print("\nWi-Fi Connection Lost")
    print("Caching Image To microSD Card...")

    time.sleep(2)

    destination = os.path.join(MICRO_SD_FOLDER,
                               os.path.basename(image_file))

    shutil.copy(image_file, destination)

    print("Image Cached Successfully")
    print(f"Cache Location : {destination}")


# =========================================================
# RETRY CACHED IMAGE UPLOAD
# =========================================================
def retry_cached_uploads():

    cached_files = os.listdir(MICRO_SD_FOLDER)

    if len(cached_files) == 0:

        print("\nNo Cached Files Found")
        return

    print("\nChecking Cached Files...")
    time.sleep(2)

    for file_name in cached_files:

        source = os.path.join(MICRO_SD_FOLDER, file_name)

        print(f"\nRetrying Upload : {file_name}")

        time.sleep(2)

        # Simulated successful upload
        destination = os.path.join(CLOUD_FOLDER, file_name)

        shutil.copy(source, destination)

        print("Upload Successful")

        # Remove cache after upload
        os.remove(source)

        print("Cache Cleared")


# =========================================================
# MAIN PROGRAM
# =========================================================

print("================================================")
print(" SMART GLOVE IMAGE CACHE MANAGEMENT SYSTEM ")
print("================================================")

# =========================================================
# CAPTURE IMAGE
# =========================================================
captured_image = capture_image()

# =========================================================
# CHECK WIFI
# =========================================================
wifi_available = check_wifi_connection()

# =========================================================
# DECISION LOGIC
# =========================================================
if wifi_available:

    upload_to_cloud(captured_image)

else:

    cache_to_micro_sd(captured_image)

# =========================================================
# SIMULATE WIFI RESTORATION
# =========================================================
print("\nAttempting Wi-Fi Reconnection...")
time.sleep(3)

print("Wi-Fi Restored Successfully")

# =========================================================
# RETRY UPLOAD OF CACHED FILES
# =========================================================
retry_cached_uploads()

# =========================================================
# FINAL STATUS
# =========================================================
print("\n================================================")
print(" SYSTEM EXECUTION COMPLETED ")
print("================================================")

print("""
PROGRAM LOGIC:
1. Image captured using smart glove camera
2. Wi-Fi connection checked
3. If Wi-Fi available:
      -> Upload image to cloud
4. If Wi-Fi unavailable:
      -> Store image temporarily in microSD cache
5. After Wi-Fi restoration:
      -> Upload cached images automatically
6. Clear cache after successful upload
""")

print("Thank You")
print("================================================")