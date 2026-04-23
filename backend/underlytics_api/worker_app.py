import base64
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from underlytics_api.db.database import SessionLocal
from underlytics_api.services.orchestrator_service import materialize_underwriting_plan
from underlytics_api.services.worker_service import run_workflow_plan

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
        plan = materialize_underwriting_plan(db, application_id)
        job = run_workflow_plan(db, plan)
        return {
            "status": "processed",
            "workflow_plan_id": plan.id,
            "underwriting_job_id": job.id,
        }
    finally:
        db.close()
