# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Tests for IntegrationService — encryption logic only (no DB required)."""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.services.integration import IntegrationService

# Generate a valid Fernet key for testing
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()


@pytest.fixture
def service():
    return IntegrationService(encryption_key=TEST_ENCRYPTION_KEY)


def test_encrypt_decrypt_roundtrip(service: IntegrationService):
    """Encrypting then decrypting a token returns the original plaintext."""
    original = "my-secret-access-token-12345"
    encrypted = service.encrypt_token(original)
    decrypted = service.decrypt_token(encrypted)
    assert decrypted == original


def test_encrypt_produces_different_ciphertext(service: IntegrationService):
    """Fernet uses a random IV, so encrypting the same token twice produces different ciphertext."""
    token = "same-token-value"
    encrypted_a = service.encrypt_token(token)
    encrypted_b = service.encrypt_token(token)
    assert encrypted_a != encrypted_b
    # Both should still decrypt to the same value
    assert service.decrypt_token(encrypted_a) == token
    assert service.decrypt_token(encrypted_b) == token


def test_decrypt_invalid_token_raises(service: IntegrationService):
    """Decrypting garbage input raises an InvalidToken exception."""
    with pytest.raises(Exception):
        service.decrypt_token("not-a-valid-fernet-token")


def test_encrypt_raises_without_key():
    """IntegrationService raises ValueError on encrypt when no encryption key is configured."""
    # Module-level singleton tolerates empty key, but encrypt/decrypt must fail
    svc = IntegrationService.__new__(IntegrationService)
    svc._fernet = None
    with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_KEY must be set"):
        svc.encrypt_token("anything")


def test_decrypt_raises_without_key():
    """IntegrationService raises ValueError on decrypt when no encryption key is configured."""
    svc = IntegrationService.__new__(IntegrationService)
    svc._fernet = None
    with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_KEY must be set"):
        svc.decrypt_token("anything")


def test_encrypt_empty_string(service: IntegrationService):
    """Encrypting an empty string should work and round-trip correctly."""
    encrypted = service.encrypt_token("")
    assert service.decrypt_token(encrypted) == ""


def test_encrypt_unicode_token(service: IntegrationService):
    """Unicode tokens should encrypt and decrypt correctly."""
    token = "tökën-with-ünïcödë-chars-🔑"
    encrypted = service.encrypt_token(token)
    assert service.decrypt_token(encrypted) == token
