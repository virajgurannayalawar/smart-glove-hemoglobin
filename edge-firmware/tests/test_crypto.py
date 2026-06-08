"""
Unit tests for crypto module.

Tests encryption/decryption compatibility with backend's decrypt_image_payload.
"""

import pytest
from edge_firmware.crypto import encrypt_image, decrypt_image, encrypt_image_to_hex, decrypt_image_from_hex


class TestCrypto:
    """Test AES-256-CBC encryption/decryption."""
    
    def test_encrypt_decrypt_basic(self):
        """Test basic encrypt-decrypt roundtrip."""
        original_data = b"Hello, World! This is a test image."
        
        encrypted = encrypt_image(original_data)
        decrypted = decrypt_image(encrypted)
        
        assert decrypted == original_data
    
    def test_encrypt_decrypt_large_data(self):
        """Test with larger data (simulating image)."""
        # Simulate a 10KB image
        original_data = b"\x00" * 10240
        
        encrypted = encrypt_image(original_data)
        decrypted = decrypt_image(encrypted)
        
        assert decrypted == original_data
    
    def test_encrypt_iv_prefix(self):
        """Test that encrypted data has 16-byte IV prefix."""
        original_data = b"Test data"
        encrypted = encrypt_image(original_data)
        
        # IV should be first 16 bytes
        iv = encrypted[:16]
        ciphertext = encrypted[16:]
        
        assert len(iv) == 16
        assert len(ciphertext) > 0
        # IV should be random (different each time)
        encrypted2 = encrypt_image(original_data)
        assert encrypted[:16] != encrypted2[:16]
    
    def test_encrypt_empty_data_raises_error(self):
        """Test that encrypting empty data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot encrypt empty data"):
            encrypt_image(b"")
    
    def test_decrypt_invalid_size_raises_error(self):
        """Test that decrypting data smaller than 16 bytes raises error."""
        with pytest.raises(ValueError, match="Invalid encrypted payload size"):
            decrypt_image(b"short")
    
    def test_decrypt_invalid_ciphertext_length_raises_error(self):
        """Test that decrypting with invalid ciphertext length raises error."""
        # 16 bytes IV + 15 bytes ciphertext (not multiple of 16)
        invalid_data = b"\x00" * 31
        with pytest.raises(ValueError, match="Invalid ciphertext length"):
            decrypt_image(invalid_data)
    
    def test_encrypt_decrypt_hex_format(self):
        """Test hex encoding/decoding functions."""
        original_data = b"Test image data for hex encoding"
        
        encrypted_hex = encrypt_image_to_hex(original_data)
        decrypted = decrypt_image_from_hex(encrypted_hex)
        
        assert decrypted == original_data
        assert isinstance(encrypted_hex, str)
    
    def test_encrypt_decrypt_realistic_image(self):
        """Test with realistic JPEG header (simulating actual image)."""
        # JPEG file header (simplified)
        jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        # Add some random data to simulate image content
        image_data = jpeg_header + b"\x00" * 5000
        
        encrypted = encrypt_image(image_data)
        decrypted = decrypt_image(encrypted)
        
        assert decrypted == image_data
        assert decrypted[:2] == b"\xff\xd8"  # JPEG signature preserved
    
    def test_multiple_encryptions_different_ivs(self):
        """Test that multiple encryptions of same data produce different IVs."""
        data = b"Same data"
        
        encrypted1 = encrypt_image(data)
        encrypted2 = encrypt_image(data)
        
        # IVs should be different (random)
        assert encrypted1[:16] != encrypted2[:16]
        # But decryption should produce same result
        assert decrypt_image(encrypted1) == decrypt_image(encrypted2) == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
