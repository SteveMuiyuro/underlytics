import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    get_actor_context,
    require_admin_actor,
    require_authenticated_actor,
    require_reviewer_actor,
)
from underlytics_api.core.config import ADMIN_BOOTSTRAP_SECRET
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.user import User
from underlytics_api.schemas.user import UserResponse, UserSyncRequest

router = APIRouter(prefix="/api/users", tags=["Users"])

ALLOWED_USER_ROLES = {"applicant", "reviewer", "admin"}


class UserRoleUpdateRequest(BaseModel):
    role: str


class AdminBootstrapRequest(BaseModel):
    bootstrap_secret: str


@router.get("/applicants", response_model=list[UserResponse])
def list_applicant_users(
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_reviewer_actor(actor)

    return db.query(User).filter(User.role == "applicant").all()


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_admin_actor(actor)

    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/sync", response_model=UserResponse)
def sync_user(
    payload: UserSyncRequest,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)

    if payload.role is not None and payload.role not in ALLOWED_USER_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported user role")

    if payload.clerk_user_id != actor.clerk_user_id:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user cannot sync a different Clerk identity",
        )

    existing_user = (
        db.query(User)
        .filter(User.clerk_user_id == payload.clerk_user_id)
        .first()
    )

    if existing_user:
        existing_user.email = payload.email
        existing_user.full_name = payload.full_name
        existing_user.phone_number = payload.phone_number
        if payload.role is not None:
            existing_user.role = payload.role
        db.commit()
        db.refresh(existing_user)
        return existing_user

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        existing_user.clerk_user_id = payload.clerk_user_id
        existing_user.full_name = payload.full_name
        existing_user.phone_number = payload.phone_number
        if payload.role is not None:
            existing_user.role = payload.role
        db.commit()
        db.refresh(existing_user)
        return existing_user

    user = User(
        id=str(uuid.uuid4()),
        clerk_user_id=payload.clerk_user_id,
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=payload.role or "applicant",
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User sync conflicted with an existing account record",
        ) from exc
    db.refresh(user)

    return user


@router.post("/bootstrap-admin", response_model=UserResponse)
def bootstrap_admin(
    payload: AdminBootstrapRequest,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)

    if not ADMIN_BOOTSTRAP_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Admin bootstrap is not configured",
        )

    if payload.bootstrap_secret != ADMIN_BOOTSTRAP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid bootstrap secret")

    user = db.query(User).filter(User.clerk_user_id == actor.clerk_user_id).first()
    if not user:
        raise HTTPException(
            status_code=409,
            detail="Authenticated user must be synced before admin bootstrap",
        )

    user.role = "admin"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_admin_actor(actor)

    if payload.role not in ALLOWED_USER_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported user role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
