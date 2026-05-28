# =========================================================
# SMART GLOVE BATTERY MANAGEMENT SYSTEM
# Raspberry Pi Sleep Mode Logic
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================
import time
import random

# =========================================================
# DEVICE STATUS VARIABLES
# =========================================================
device_active = False

battery_level = random.randint(70, 100)

# =========================================================
# DISPLAY BATTERY STATUS
# =========================================================
def display_battery():

    print(f"\nBattery Level : {battery_level}%")


# =========================================================
# ENTER LOW POWER MODE
# =========================================================
def sleep_mode():

    print("\n========================================")
    print(" DEVICE ENTERING LOW POWER MODE ")
    print("========================================")

    print("\nNo Active Capture Or Processing Detected")

    print("\nReducing CPU Activity...")
    time.sleep(1)

    print("Disabling Unused Background Tasks...")
    time.sleep(1)

    print("Lowering Power Consumption...")
    time.sleep(1)

    print("\nSystem In Sleep Mode")
    print("Waiting For Capture Request...")


# =========================================================
# WAKE DEVICE
# =========================================================
def wake_device():

    print("\n========================================")
    print(" DEVICE WAKE-UP EVENT DETECTED ")
    print("========================================")

    print("\nActivating Camera Module...")
    time.sleep(1)

    print("Restoring Processing Tasks...")
    time.sleep(1)

    print("System Ready")


# =========================================================
# IMAGE CAPTURE TASK
# =========================================================
def capture_image():

    global battery_level

    print("\nCapturing Finger/Nail Image...")
    time.sleep(2)

    print("Image Capture Successful")

    # Battery Consumption
    battery_level -= random.randint(1, 3)

    display_battery()


# =========================================================
# PREPROCESSING TASK
# =========================================================
def preprocess_image():

    global battery_level

    print("\nPreprocessing Image...")
    time.sleep(2)

    print("Noise Reduction Applied")
    time.sleep(1)

    print("Contrast Enhancement Applied")
    time.sleep(1)

    print("Preprocessing Completed")

    # Battery Consumption
    battery_level -= random.randint(1, 2)

    display_battery()


# =========================================================
# AI PROCESSING TASK
# =========================================================
def run_ai_inference():

    global battery_level

    print("\nRunning AI Inference...")
    time.sleep(3)

    hemoglobin = round(random.uniform(8.0, 16.0), 1)

    print(f"Hemoglobin Prediction : {hemoglobin} g/dL")

    # Battery Consumption
    battery_level -= random.randint(2, 4)

    display_battery()


# =========================================================
# MAIN PROGRAM
# =========================================================
print("================================================")
print(" SMART GLOVE BATTERY MANAGEMENT SYSTEM ")
print("================================================")

display_battery()

# =========================================================
# DEVICE IDLE STATE
# =========================================================
device_active = False

# Enter Sleep Mode
if not device_active:

    sleep_mode()

# =========================================================
# SIMULATED USER CAPTURE REQUEST
# =========================================================
print("\nIncoming Image Capture Request...")
time.sleep(3)

# Wake Device
device_active = True

wake_device()

# =========================================================
# EXECUTE TASKS
# =========================================================
capture_image()

preprocess_image()

run_ai_inference()

# =========================================================
# TASKS COMPLETED
# =========================================================
print("\nAll Tasks Completed")

# =========================================================
# RETURN TO IDLE MODE
# =========================================================
device_active = False

print("\nNo More Active Tasks Detected")

time.sleep(2)

sleep_mode()

# =========================================================
# FINAL STATUS
# =========================================================
print("\n================================================")
print(" BATTERY MANAGEMENT COMPLETED ")
print("================================================")

print("""
PROGRAM LOGIC:
1. Monitor device activity
2. Detect idle condition
3. Enter low-power sleep mode
4. Wake device during capture request
5. Execute image processing tasks
6. Reduce battery consumption
7. Return to sleep after processing

Purpose:
Improve Raspberry Pi battery efficiency
during smart glove operation.
""")

print("\nThank You")
print("================================================")