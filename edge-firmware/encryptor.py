import os

from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from config import AES_SECRET_KEY


def encrypt_image(image_bytes: bytes) -> bytes:
    """
    Encrypt image using AES-256-CBC.

    Returns:
        IV + encrypted ciphertext
    """

    # Generate random IV
    iv = os.urandom(16)

    # PKCS7 padding
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(image_bytes) + padder.finalize()

    # AES Cipher
    cipher = Cipher(
        algorithms.AES(AES_SECRET_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(padded_data)
    ciphertext += encryptor.finalize()

    # Backend expects IV + ciphertext
    encrypted_payload = iv + ciphertext

    return encrypted_payload


if __name__ == "__main__":

    sample_data = b"SMART_GLOVE_TEST_IMAGE"

    encrypted = encrypt_image(sample_data)

    print("Encryption Successful")
    print(f"Encrypted Size: {len(encrypted)} bytes")