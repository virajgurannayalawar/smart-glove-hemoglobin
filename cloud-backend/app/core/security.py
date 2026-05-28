import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import settings
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

#AES-256 Payload Encryption ✅

def decrypt_image_payload(encrypted_data: bytes) -> bytes:
    """
    Decrypts the AES-256 encrypted image payload.
    Assumes standard AES-CBC mode where the first 16 bytes are the IV.
    """
    if len(encrypted_data) < 16:
        raise ValueError("Invalid encrypted payload size")
        
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    if len(ciphertext) == 0 or (len(ciphertext) % 16) != 0:
        raise ValueError("Invalid ciphertext length")
    
    # Ensure key is 32 bytes for AES-256
    key = settings.AES_SECRET_KEY.encode('utf-8')[:32].ljust(32, b'\0')
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # PKCS7 Unpadding (validated)
    if not padded_data:
        raise ValueError("Invalid decrypted payload")
    padding_length = padded_data[-1]
    if padding_length < 1 or padding_length > 16:
        raise ValueError("Invalid PKCS7 padding")
    if padded_data[-padding_length:] != bytes([padding_length]) * padding_length:
        raise ValueError("Invalid PKCS7 padding")
    unpadded_data = padded_data[:-padding_length]
    
    return unpadded_data
