from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    get_actor_context,
    require_authenticated_actor,
    require_registered_actor,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.schemas.application_document import ApplicationDocumentResponse
from underlytics_api.services.workflow_dispatch_service import dispatch_underwriting_workflow

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_DOCUMENT_TYPES = {"id_document", "payslip", "bank_statement"}


@router.post("/upload", response_model=ApplicationDocumentResponse)
async def upload_document(
    application_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported document type")

    if not actor.has_review_access:
        if actor.backend_user_id != application.applicant_user_id:
            raise HTTPException(
                status_code=403,
                detail="Authenticated user cannot upload documents for another applicant",
            )

    safe_name = f"{uuid4()}_{file.filename}"
    destination = UPLOAD_DIR / safe_name

    content = await file.read()
    destination.write_bytes(content)

    document = (
        db.query(ApplicationDocument)
        .filter(
            ApplicationDocument.application_id == application_id,
            ApplicationDocument.document_type == document_type,
        )
        .order_by(ApplicationDocument.uploaded_at.desc())
        .first()
    )

    if document:
        document.file_name = file.filename or safe_name
        document.file_path = str(destination)
        document.mime_type = file.content_type or "application/octet-stream"
        document.file_size_bytes = len(content)
        document.upload_status = "replaced"
        document.is_required = True
        document.uploaded_at = datetime.utcnow()
    else:
        document = ApplicationDocument(
            application_id=application_id,
            document_type=document_type,
            file_name=file.filename or safe_name,
            file_path=str(destination),
            mime_type=file.content_type or "application/octet-stream",
            file_size_bytes=len(content),
            upload_status="uploaded",
            is_required=True,
        )
        db.add(document)

    db.commit()
    db.refresh(document)

    dispatch_underwriting_workflow(db, application.id)

    return document
