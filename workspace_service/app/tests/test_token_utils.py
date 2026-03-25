"""
Unit tests for token utility functions.

Tests cover:
- generate_invite_token: returns a tuple of (plain, hash), hash verifies
- hash_token: deterministic SHA-256
- verify_token: matching and non-matching cases
"""
import hashlib

from app.utils.token import generate_invite_token, hash_token, verify_token


class TestHashToken:
    """Tests for hash_token()."""

    def test_returns_sha256_hex(self):
        result = hash_token("hello")
        expected = hashlib.sha256(b"hello").hexdigest()
        assert result == expected

    def test_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_different_inputs_different_hashes(self):
        assert hash_token("one") != hash_token("two")

    def test_empty_string(self):
        result = hash_token("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected


class TestVerifyToken:
    """Tests for verify_token()."""

    def test_matching(self):
        token = "my-secret-token"
        token_hash = hash_token(token)
        assert verify_token(token, token_hash) is True

    def test_non_matching(self):
        assert verify_token("wrong", hash_token("correct")) is False

    def test_empty_token_matches_own_hash(self):
        assert verify_token("", hash_token("")) is True


class TestGenerateInviteToken:
    """Tests for generate_invite_token()."""

    def test_returns_tuple(self):
        result = generate_invite_token()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_plain_token_is_nonempty_string(self):
        plain, _ = generate_invite_token()
        assert isinstance(plain, str)
        assert len(plain) > 0

    def test_hash_verifies(self):
        plain, token_hash = generate_invite_token()
        assert verify_token(plain, token_hash) is True

    def test_unique_per_call(self):
        plain_a, _ = generate_invite_token()
        plain_b, _ = generate_invite_token()
        assert plain_a != plain_b

    def test_hash_is_hex_string(self):
        _, token_hash = generate_invite_token()
        # SHA-256 hex digest is exactly 64 characters
        assert len(token_hash) == 64
        int(token_hash, 16)  # should not raise for valid hex
