import pytest
import hashlib
from blank_business_builder.auth import _SimpleCryptContext, AuthService

class TestAuthSecurity:
    """Security specific tests for authentication."""

    def test_legacy_sha256_vulnerability_fixed(self):
        """Ensure that legacy unsalted SHA-256 hashes are NO LONGER accepted."""
        password = "password123"
        # Create a legacy unsalted SHA-256 hash
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        # Verify it using the method directly
        # It should return False now (after fix)
        # Before fix, this would return True
        assert not _SimpleCryptContext.verify(password, legacy_hash), \
            "Vulnerability still exists: Legacy unsalted SHA-256 hash was accepted."

    def test_secure_hashing_still_works(self):
        """Ensure that the secure hashing mechanism still works."""
        password = "secure_password"
        hashed = _SimpleCryptContext.hash(password)

        # It should be a secure hash (pbkdf2_sha256)
        assert hashed.startswith("pbkdf2_sha256$")

        # Verify should return True
        assert _SimpleCryptContext.verify(password, hashed)

        # Verify with wrong password should return False
        assert not _SimpleCryptContext.verify("wrong_password", hashed)

    def test_auth_service_hashing(self):
        """Ensure AuthService uses the context correctly."""
        password = "my_password"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed)
