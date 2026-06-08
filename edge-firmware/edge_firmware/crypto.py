"""
AES-256-CBC encryption/decryption module for Smart Glove Edge Firmware.

This module provides encryption functions that match the backend's decrypt_image_payload
exactly. The backend expects:
- AES-256-CBC mode
- IV (16 bytes) prepended to ciphertext
- PKCS7 padding
- Key as hex-encoded string (32 bytes when decoded)

Backend reference: cloud-backend/app/core/security.py
"""

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from typing import Union

from .config import config


def _get_encryption_key() -> bytes:
    """
    Convert the configured AES secret key to bytes.
    
    The backend expects the key to be hex-encoded (bytes.fromhex).
    If the key is not valid hex, treat it as a plain string and encode to bytes.
    
    Returns:
        32-byte key for AES-256
    """
    key_str = config.AES_SECRET_KEY
    
    # Try to decode as hex first (backend behavior)
    try:
        key = bytes.fromhex(key_str)
        if len(key) == 32:
            return key
    except ValueError:
        pass
    
    # Fallback: treat as plain string and encode
    key = key_str.encode('utf-8')[:32]  # Truncate or pad to 32 bytes
    if len(key) < 32:
        key = key + b'\x00' * (32 - len(key))
    
    return key


def encrypt_image(image_bytes: bytes) -> bytes:
    """
    Encrypt image data using AES-256-CBC.
    
    This function produces output that the backend's decrypt_image_payload can decrypt.
    
    Args:
        image_bytes: Raw image data to encrypt
        
    Returns:
        IV (16 bytes) + ciphertext (encrypted and padded)
        
    Raises:
        ValueError: If image_bytes is empty
    """
    if not image_bytes:
        raise ValueError("Cannot encrypt empty data")
    
    # Get the 32-byte encryption key
    key = _get_encryption_key()
    
    # Generate random 16-byte IV
    iv = os.urandom(16)
    
    # Pad image data to AES block size (128 bits = 16 bytes) using PKCS7
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(image_bytes) + padder.finalize()
    
    # Encrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return IV + ciphertext (backend expects this format)
    return iv + ciphertext


def decrypt_image(encrypted_data: bytes) -> bytes:
    """
    Decrypt image data using AES-256-CBC.
    
    This is the inverse of encrypt_image and matches backend's decrypt_image_payload.
    Useful for testing and verification.
    
    Args:
        encrypted_data: IV (16 bytes) + ciphertext
        
    Returns:
        Decrypted image bytes
        
    Raises:
        ValueError: If encrypted_data is invalid
    """
    if len(encrypted_data) < 16:
        raise ValueError("Invalid encrypted payload size")
    
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    if len(ciphertext) == 0 or (len(ciphertext) % 16) != 0:
        raise ValueError("Invalid ciphertext length")
    
    # Get the 32-byte encryption key
    key = _get_encryption_key()
    
    # Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    if not padded_data:
        raise ValueError("Invalid decrypted payload")
    
    padding_length = padded_data[-1]
    if padding_length < 1 or padding_length > 16:
        raise ValueError("Invalid PKCS7 padding")
    
    if padded_data[-padding_length:] != bytes([padding_length]) * padding_length:
        raise ValueError("Invalid PKCS7 padding")
    
    unpadded_data = padded_data[:-padding_length]
    
    return unpadded_data


def encrypt_image_to_hex(image_bytes: bytes) -> str:
    """
    Encrypt image and return result as hex string.
    
    Useful for debugging and logging (avoids binary in logs).
    
    Args:
        image_bytes: Raw image data to encrypt
        
    Returns:
        Hex string of IV + ciphertext
    """
    encrypted = encrypt_image(image_bytes)
    return encrypted.hex()


def decrypt_image_from_hex(hex_string: str) -> bytes:
    """
    Decrypt image from hex string.
    
    Args:
        hex_string: Hex string of IV + ciphertext
        
    Returns:
        Decrypted image bytes
    """
    encrypted = bytes.fromhex(hex_string)
    return decrypt_image(encrypted)
