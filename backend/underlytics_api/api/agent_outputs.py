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
from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.application import Application
from underlytics_api.schemas.agent_output import AgentOutputResponse

router = APIRouter(prefix="/api/agent-outputs", tags=["Agent Outputs"])


@router.get("/applications/{application_id}", response_model=list[AgentOutputResponse])
def list_agent_outputs(
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
        db.query(AgentOutput)
        .filter(AgentOutput.application_id == application_id)
        .order_by(AgentOutput.created_at.asc())
        .all()
    )
