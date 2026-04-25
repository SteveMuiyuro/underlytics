import pytest
from fastapi import HTTPException

from underlytics_api.core import auth


def test_normalize_authorized_party_strips_whitespace_and_trailing_slash():
    assert (
        auth._normalize_authorized_party(" https://underlytics.vercel.app/ ")
        == "https://underlytics.vercel.app"
    )


def test_verify_clerk_token_accepts_normalized_authorized_party(monkeypatch):
    monkeypatch.setattr(auth, "CLERK_JWT_KEY", "test-key")
    monkeypatch.setattr(auth, "CLERK_JWT_ISSUER", "https://issuer.example.com")
    monkeypatch.setattr(
        auth,
        "CLERK_AUTHORIZED_PARTIES",
        ["https://underlytics.vercel.app"],
    )
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "user_123",
            "iss": "https://issuer.example.com",
            "azp": "https://underlytics.vercel.app/",
        },
    )

    claims = auth._verify_clerk_token("test-token")

    assert claims["sub"] == "user_123"


def test_verify_clerk_token_rejects_unexpected_authorized_party(monkeypatch):
    monkeypatch.setattr(auth, "CLERK_JWT_KEY", "test-key")
    monkeypatch.setattr(auth, "CLERK_JWT_ISSUER", "https://issuer.example.com")
    monkeypatch.setattr(
        auth,
        "CLERK_AUTHORIZED_PARTIES",
        ["https://underlytics.vercel.app"],
    )
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "user_123",
            "iss": "https://issuer.example.com",
            "azp": "https://example.com",
        },
    )

    with pytest.raises(HTTPException) as excinfo:
        auth._verify_clerk_token("test-token")

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Clerk bearer token was issued for an unexpected party"
