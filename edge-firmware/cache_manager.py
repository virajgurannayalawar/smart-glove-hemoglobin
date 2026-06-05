import os
import time
import json

from config import CACHE_DIRECTORY


def save_failed_upload(encrypted_data: bytes, metadata: dict):
    """
    Save encrypted upload locally if internet fails.
    """

    timestamp = int(time.time())

    binary_filename = os.path.join(
        CACHE_DIRECTORY,
        f"failed_upload_{timestamp}.bin"
    )

    metadata_filename = os.path.join(
        CACHE_DIRECTORY,
        f"failed_upload_{timestamp}.json"
    )

    # Save encrypted image
    with open(binary_filename, "wb") as binary_file:
        binary_file.write(encrypted_data)

    # Save metadata
    with open(metadata_filename, "w") as metadata_file:
        json.dump(metadata, metadata_file, indent=4)

    print(f"Upload cached locally: {binary_filename}")


def get_cached_uploads():
    """
    Returns all cached uploads.
    """

    files = os.listdir(CACHE_DIRECTORY)

    binary_files = [
        file for file in files
        if file.endswith(".bin")
    ]

    return binary_files


if __name__ == "__main__":

    sample_metadata = {
        "patient_id": "PATIENT001",
        "status": "FAILED"
    }

    save_failed_upload(b"TEST_DATA", sample_metadata)

    cached = get_cached_uploads()

    print("Cached Uploads:")
    print(cached)