"""Tests for app/services/encryption.py - TokenEncryption."""

import pytest
from cryptography.fernet import Fernet

from app.services.encryption import TokenEncryption
from app.exceptions import EncryptionError


class TestTokenEncryption:
    """Tests for the TokenEncryption class."""

    def test_encrypt_returns_non_empty_string(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        result = enc.encrypt("my-secret-token")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypt_decrypt_roundtrip(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        original = "uFz7s8dK_test-token-abc123"
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == original

    def test_encrypted_value_differs_from_original(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        original = "plaintext-token"
        encrypted = enc.encrypt(original)
        assert encrypted != original

    def test_decrypt_with_wrong_key_raises_encryption_error(self, fernet_key):
        enc1 = TokenEncryption(key=fernet_key)
        encrypted = enc1.encrypt("secret")

        other_key = Fernet.generate_key().decode()
        enc2 = TokenEncryption(key=other_key)

        with pytest.raises(EncryptionError):
            enc2.decrypt(encrypted)

    def test_decrypt_corrupted_data_raises_encryption_error(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        with pytest.raises(EncryptionError):
            enc.decrypt("not-a-valid-fernet-token")

    def test_invalid_key_raises_encryption_error(self):
        with pytest.raises(EncryptionError):
            TokenEncryption(key="invalid-key")

    def test_encrypt_empty_string(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        encrypted = enc.encrypt("")
        decrypted = enc.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode_token(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        original = "token-with-unicode-\u0443\u043a\u0440"
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == original

    def test_each_encryption_produces_different_ciphertext(self, fernet_key):
        """Fernet uses a nonce, so encrypting the same value twice yields different ciphertext."""
        enc = TokenEncryption(key=fernet_key)
        token = "same-token"
        encrypted1 = enc.encrypt(token)
        encrypted2 = enc.encrypt(token)
        assert encrypted1 != encrypted2

    def test_decrypt_empty_string_raises_error(self, fernet_key):
        enc = TokenEncryption(key=fernet_key)
        with pytest.raises(EncryptionError):
            enc.decrypt("")
