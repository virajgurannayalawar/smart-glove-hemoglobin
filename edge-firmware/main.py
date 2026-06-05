import time

from monitor import print_system_status
from encryptor import encrypt_image
from uploader import upload_to_backend
from config import DEVICE_NAME


def build_metadata():
    """
    Creates metadata required by backend.
    """

    current_time = int(time.time())

    metadata = {
        "patient_id": "PATIENT001",

        # REQUIRED BY BACKEND
        "owner_id": "OWNER001",

        "capture_timestamp": current_time,
        "sync_timestamp": current_time,

        "is_pregnant": False,

        "device_name": DEVICE_NAME
    }

    return metadata


def simulate_image_capture() -> bytes:
    """
    Temporary simulated image capture.

    Later this will be replaced
    with Raspberry Pi camera capture.
    """

    print("Capturing image...")

    sample_image = b"REAL_CAMERA_IMAGE_WILL_COME_HERE"

    return sample_image


def main():

    print("\nSMART GLOVE EDGE FIRMWARE STARTED\n")

    # STEP 1
    # Monitor system resources
    print_system_status()

    # STEP 2
    # Capture image
    image_data = simulate_image_capture()

    if not image_data:
        print("Camera capture failed")
        return

    # STEP 3
    # Encrypt image
    encrypted_data = encrypt_image(image_data)

    print("Encryption Completed")

    # STEP 4
    # Build metadata
    metadata = build_metadata()

    print("\nMetadata Generated:")
    print(metadata)

    # STEP 5
    # Upload to backend
    upload_success = upload_to_backend(
        encrypted_data,
        metadata
    )

    # STEP 6
    # Final result
    if upload_success:

        print("\nWORKFLOW COMPLETED SUCCESSFULLY")

    else:

        print("\nUPLOAD FAILED - CACHED LOCALLY")


if __name__ == "__main__":
    main()