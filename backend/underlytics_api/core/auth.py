from __future__ import annotations

import base64
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from underlytics_api.core.config import (
    CLERK_AUTHORIZED_PARTIES,
    CLERK_JWT_ISSUER,
    CLERK_JWT_KEY,
    CLERK_PUBLISHABLE_KEY,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.user import User


@dataclass
class ActorContext:
    clerk_user_id: str | None = None
    backend_user_id: str | None = None
    role: str | None = None
    token_verified: bool = False
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.token_verified and bool(self.clerk_user_id)

    @property
    def is_registered(self) -> bool:
        return bool(self.backend_user_id)

    @property
    def is_reviewer(self) -> bool:
        return self.role == "reviewer"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def has_review_access(self) -> bool:
        return self.role in {"reviewer", "admin"}


def _decode_publishable_key_frontend_api() -> str | None:
    if not CLERK_PUBLISHABLE_KEY:
        return None

    try:
        encoded = CLERK_PUBLISHABLE_KEY.split("_", 2)[-1]
        padding = "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(f"{encoded}{padding}").decode().rstrip("$")
    except (UnicodeDecodeError, ValueError):
        return None


def _get_expected_issuer() -> str:
    if CLERK_JWT_ISSUER:
        return CLERK_JWT_ISSUER.rstrip("/")

    frontend_api = _decode_publishable_key_frontend_api()
    if frontend_api:
        return f"https://{frontend_api}".rstrip("/")

    raise HTTPException(
        status_code=500,
        detail="Clerk issuer is not configured for backend token verification",
    )


@lru_cache(maxsize=4)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        raise HTTPException(status_code=401, detail="Bearer token is required")

    return value


def _verify_clerk_token(token: str) -> dict[str, Any]:
    issuer = _get_expected_issuer()

    try:
        signing_key = CLERK_JWT_KEY
        if not signing_key:
            jwks_url = f"{issuer}/.well-known/jwks.json"
            signing_key = _get_jwk_client(jwks_url).get_signing_key_from_jwt(token).key

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "require": ["exp", "iat", "iss", "nbf", "sub"],
                "verify_aud": False,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Clerk bearer token") from exc

    if CLERK_AUTHORIZED_PARTIES:
        authorized_party = claims.get("azp")
        if authorized_party not in CLERK_AUTHORIZED_PARTIES:
            raise HTTPException(
                status_code=401,
                detail="Clerk bearer token was issued for an unexpected party",
            )

    return claims


def get_actor_context(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> ActorContext:
    token = _extract_bearer_token(authorization)
    if not token:
        return ActorContext()

    claims = _verify_clerk_token(token)
    clerk_user_id = claims.get("sub")
    user = None
    if clerk_user_id:
        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()

    return ActorContext(
        clerk_user_id=clerk_user_id,
        backend_user_id=user.id if user else None,
        role=user.role if user else None,
        token_verified=True,
        claims=claims,
    )


def enforce_application_access(
    *,
    actor: ActorContext,
    applicant_user_id: str,
) -> None:
    if not actor.is_authenticated:
        return

    if actor.has_review_access:
        return

    require_registered_actor(actor)

    if actor.backend_user_id != applicant_user_id:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user cannot access another applicant's records",
        )


def require_authenticated_actor(actor: ActorContext) -> None:
    if actor.is_authenticated:
        return

    raise HTTPException(
        status_code=401,
        detail="Verified Clerk authentication is required",
    )


def require_registered_actor(actor: ActorContext) -> None:
    require_authenticated_actor(actor)

    if actor.is_registered:
        return

    raise HTTPException(
        status_code=403,
        detail="Authenticated user has not been provisioned in the backend yet",
    )


def require_reviewer_actor(actor: ActorContext) -> None:
    require_registered_actor(actor)

    if actor.has_review_access:
        return

    raise HTTPException(
        status_code=403,
        detail="Reviewer access is required",
    )


def require_admin_actor(actor: ActorContext) -> None:
    require_registered_actor(actor)

    if actor.is_admin:
        return

    raise HTTPException(
        status_code=403,
        detail="Admin access is required",
    )
