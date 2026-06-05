# =========================================================
# SMART GLOVE SYSTEM RESOURCE MONITOR
# CPU/RAM Monitoring for Raspberry Pi
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import time
import random
import os

# =========================================================
# TRY IMPORTING PSUTIL
# =========================================================
# psutil gives real CPU/RAM usage
# If unavailable, simulation mode is used
# =========================================================

psutil_available = True

try:
    import psutil
except:
    psutil_available = False

# =========================================================
# CLEAR SCREEN
# =========================================================
def clear_screen():

    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        pass


# =========================================================
# GET CPU USAGE
# =========================================================
def get_cpu_usage():

    if psutil_available:
        return psutil.cpu_percent(interval=1)

    else:
        return random.randint(20, 60)


# =========================================================
# GET RAM USAGE
# =========================================================
def get_ram_usage():

    if psutil_available:

        ram = psutil.virtual_memory()

        return ram.percent

    else:
        return random.randint(30, 75)


# =========================================================
# CHECK SYSTEM SAFETY
# =========================================================
def check_system_health(cpu, ram):

    print("\nSystem Health Analysis")
    print("----------------------------------------")

    # CPU Safety Check
    if cpu > 85:
        print("WARNING : High CPU Usage Detected")
        print("Risk     : Image processing may crash")

    else:
        print("CPU Status : Stable")

    # RAM Safety Check
    if ram > 85:
        print("WARNING : High RAM Usage Detected")
        print("Risk     : Memory overflow possible")

    else:
        print("RAM Status : Stable")


# =========================================================
# SIMULATE IMAGE CAPTURE
# =========================================================
def image_capture_task():

    print("\nStarting Image Capture Task...")
    time.sleep(2)

    print("Capturing Finger/Nail Image...")
    time.sleep(2)

    print("Image Capture Successful")


# =========================================================
# SIMULATE IMAGE PREPROCESSING
# =========================================================
def preprocessing_task():

    print("\nStarting Image Preprocessing...")
    time.sleep(2)

    print("Image Resized")
    time.sleep(1)

    print("Noise Reduction Applied")
    time.sleep(1)

    print("Contrast Enhancement Applied")
    time.sleep(1)

    print("Preprocessing Completed")


# =========================================================
# SIMULATE DATA ENCRYPTION
# =========================================================
def encryption_task():

    print("\nStarting Patient Data Encryption...")
    time.sleep(2)

    print("Encrypting Patient Image...")
    time.sleep(1)

    print("Encrypting Hemoglobin Data...")
    time.sleep(1)

    print("Secure Encryption Successful")


# =========================================================
# DISPLAY RESOURCE MONITOR
# =========================================================
def display_resources():

    cpu = get_cpu_usage()
    ram = get_ram_usage()

    print("\n========================================")
    print("     RASPBERRY PI RESOURCE MONITOR")
    print("========================================")

    print(f"\nCPU Usage : {cpu}%")
    print(f"RAM Usage : {ram}%")

    return cpu, ram


# =========================================================
# MAIN PROGRAM
# =========================================================
clear_screen()

print("================================================")
print(" SMART GLOVE RESOURCE MONITORING SYSTEM ")
print("================================================")

# =========================================================
# INITIAL RESOURCE CHECK
# =========================================================
print("\nChecking System Resources...")
time.sleep(2)

cpu_usage, ram_usage = display_resources()

# =========================================================
# SYSTEM HEALTH CHECK
# =========================================================
check_system_health(cpu_usage, ram_usage)

# =========================================================
# SAFE EXECUTION LOGIC
# =========================================================
if cpu_usage < 90 and ram_usage < 90:

    print("\nSystem Safe For Execution")

    # =====================================================
    # TASK 1 - IMAGE CAPTURE
    # =====================================================
    image_capture_task()

    # Resource Check
    cpu_usage, ram_usage = display_resources()

    # =====================================================
    # TASK 2 - PREPROCESSING
    # =====================================================
    preprocessing_task()

    # Resource Check
    cpu_usage, ram_usage = display_resources()

    # =====================================================
    # TASK 3 - ENCRYPTION
    # =====================================================
    encryption_task()

    # Final Resource Check
    cpu_usage, ram_usage = display_resources()

    print("\nAll Tasks Executed Successfully")

else:

    print("\nSystem Resources Too High")
    print("Execution Stopped To Prevent Raspberry Pi Crash")

# =========================================================
# FINAL REPORT
# =========================================================
print("\n================================================")
print(" SYSTEM MONITORING COMPLETED ")
print("================================================")

print("""
PROGRAM LOGIC:
1. Monitor CPU usage
2. Monitor RAM usage
3. Check Raspberry Pi stability
4. Execute image capture task
5. Execute preprocessing task
6. Execute data encryption task
7. Recheck resources after each task
8. Stop execution if system overload detected

Purpose:
Prevent Raspberry Pi crashes during
AI smart glove execution.
""")

# =========================================================
# IMPORTANT NOTE
# =========================================================
print("\nNOTE")
print("----------------------------------------")

print("""
If psutil library is installed:
-> Real CPU/RAM monitoring used

If psutil library is unavailable:
-> Simulation mode activated
""")

print("\nThank You")
print("================================================")