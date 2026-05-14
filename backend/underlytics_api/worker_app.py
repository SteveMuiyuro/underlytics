import base64
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from underlytics_api.db.database import SessionLocal
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.services.workflow_service import create_underwriting_workflow

app = FastAPI(title="Underlytics Worker")


class PubSubMessage(BaseModel):
    data: str
    message_id: str | None = None


class PubSubEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None


def _decode_payload(data: str) -> dict:
    try:
        raw = base64.b64decode(data)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Pub/Sub payload must decode to an object")

    return payload


@app.get("/")
def root():
    return {"message": "Underlytics worker is running"}


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


@app.post("/pubsub/workflows")
def run_workflow_from_pubsub(envelope: PubSubEnvelope):
    payload = _decode_payload(envelope.message.data)
    application_id = payload.get("application_id")

    if not application_id:
        raise HTTPException(status_code=400, detail="application_id is required")

    db = SessionLocal()

    try:
        job = create_underwriting_workflow(db, application_id)
        plan = (
            db.query(WorkflowPlan)
            .filter(WorkflowPlan.application_id == application_id)
            .order_by(WorkflowPlan.created_at.desc())
            .first()
        )
        return {
            "status": "processed",
            "workflow_plan_id": plan.id if plan else None,
            "underwriting_job_id": job.id,
        }
    finally:
        db.close()
