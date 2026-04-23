from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    enforce_application_access,
    get_actor_context,
    require_authenticated_actor,
    require_registered_actor,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.schemas.application_document import ApplicationDocumentResponse

router = APIRouter(prefix="/api/application-documents", tags=["Application Documents"])


@router.get("/{application_id}", response_model=list[ApplicationDocumentResponse])
def list_application_documents(
    application_id: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_application_access(
        actor=actor, applicant_user_id=application.applicant_user_id
    )

    return (
        db.query(ApplicationDocument)
        .filter(ApplicationDocument.application_id == application_id)
        .order_by(ApplicationDocument.uploaded_at.desc())
        .all()
    )
