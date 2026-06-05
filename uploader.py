import json
import requests

from config import BACKEND_BASE_URL
from config import UPLOAD_ENDPOINT
from config import GLOVE_API_KEY
from config import UPLOAD_TIMEOUT

from cache_manager import save_failed_upload


def upload_to_backend(encrypted_image: bytes, metadata: dict):
    """
    Upload encrypted image and metadata
    to backend server.
    """

    upload_url = BACKEND_BASE_URL + UPLOAD_ENDPOINT

    headers = {
        "X-Glove-Key": GLOVE_API_KEY
    }

    files = {
        "image": (
            "encrypted_image.bin",
            encrypted_image,
            "application/octet-stream"
        ),

        "metadata": (
            None,
            json.dumps(metadata),
            "application/json"
        )
    }

    try:

        print("\n========== UPLOAD STARTED ==========")
        print(f"Upload URL: {upload_url}")

        response = requests.post(
            upload_url,
            headers=headers,
            files=files,
            timeout=UPLOAD_TIMEOUT
        )

        print(f"Status Code: {response.status_code}")

        # Success
        if response.status_code in [200, 201]:

            print("Upload Successful")

            try:
                print("Server Response:")
                print(response.json())
            except Exception:
                print(response.text)

            return True

        # Failure
        else:

            print("Upload Failed")

            try:
                print("Server Response:")
                print(response.json())
            except Exception:
                print(response.text)

            save_failed_upload(
                encrypted_image,
                metadata
            )

            return False

    except Exception as error:

        print("\n========== NETWORK ERROR ==========")
        print(error)

        save_failed_upload(
            encrypted_image,
            metadata
        )

        return False