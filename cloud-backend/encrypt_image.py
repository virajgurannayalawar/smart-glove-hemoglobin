from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

AES_SECRET_KEY ="0a1f5216bac030bab4fc76a9bd36cb54cd7ed8dda6a84c3b00b512c0cc5259ff"

key = bytes.fromhex(AES_SECRET_KEY)

with open("enrollment.png", "rb") as f:
    image_data = f.read()

# PKCS7 padding
padding_length = 16 - (len(image_data) % 16)
padded_data = image_data + bytes([padding_length]) * padding_length

# Random IV 
iv = os.urandom(16)

cipher = Cipher(
    algorithms.AES(key),
    modes.CBC(iv),
    backend=default_backend()
)

encryptor = cipher.encryptor()
ciphertext = encryptor.update(padded_data) + encryptor.finalize()

# Output format expected by server:
encrypted_payload = iv + ciphertext

with open("image.enc", "wb") as f:
    f.write(encrypted_payload)

print("Encrypted file created: image.enc")