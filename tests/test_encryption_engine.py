import pytest
import base64
from cryptography.fernet import Fernet
from src.blank_business_builder.all_features_implementation import EncryptionEngine

class TestEncryptionEngine:
    """Test the EncryptionEngine class."""

    def test_initialization(self):
        """Test initial state of EncryptionEngine."""
        engine = EncryptionEngine()
        assert engine.algorithm == "AES-256-GCM"

    def test_encrypt_data_without_key(self):
        """Test encryption without providing a key."""
        engine = EncryptionEngine()
        data = "sensitive data"
        result = engine.encrypt_data(data)

        assert "encrypted_data" in result
        assert "key" in result
        assert result["algorithm"] == "AES-256-GCM"

        # Verify key is valid base64
        key_bytes = base64.b64decode(result["key"])
        # Fernet keys are base64-encoded 32-byte keys, so length should be 44
        assert len(key_bytes) == 44

        # Verify underlying key is 32 bytes
        raw_key = base64.urlsafe_b64decode(key_bytes)
        assert len(raw_key) == 32

    def test_encrypt_data_with_key(self):
        """Test encryption with a provided key."""
        engine = EncryptionEngine()
        data = "sensitive data"
        key = Fernet.generate_key()

        result = engine.encrypt_data(data, key=key)

        assert result["key"] == base64.b64encode(key).decode()
        assert result["algorithm"] == "AES-256-GCM"

    def test_decrypt_data(self):
        """Test decryption of data."""
        engine = EncryptionEngine()
        data = "secret message"

        # First encrypt
        encrypted_result = engine.encrypt_data(data)
        encrypted_data = encrypted_result["encrypted_data"]
        key = encrypted_result["key"]

        # Then decrypt
        decrypted_data = engine.decrypt_data(encrypted_data, key)
        assert decrypted_data == data

    def test_round_trip(self):
        """Test round-trip encryption and decryption."""
        engine = EncryptionEngine()
        original_data = "This is a test string for round trip encryption."

        encrypted_result = engine.encrypt_data(original_data)
        decrypted_data = engine.decrypt_data(
            encrypted_result["encrypted_data"],
            encrypted_result["key"]
        )

        assert decrypted_data == original_data
