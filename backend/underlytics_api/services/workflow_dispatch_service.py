import json
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from underlytics_api.core.config import (
    GOOGLE_CLOUD_PROJECT,
    PUBSUB_WORKFLOW_TOPIC,
    WORKFLOW_EXECUTION_MODE,
)
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.services.workflow_service import create_underwriting_workflow

if TYPE_CHECKING:
    from google.cloud.pubsub_v1 import PublisherClient


def _resolve_topic_path(publisher: "PublisherClient") -> str | None:
    if not PUBSUB_WORKFLOW_TOPIC:
        return None

    if PUBSUB_WORKFLOW_TOPIC.startswith("projects/"):
        return PUBSUB_WORKFLOW_TOPIC

    if not GOOGLE_CLOUD_PROJECT:
        return None

    return publisher.topic_path(GOOGLE_CLOUD_PROJECT, PUBSUB_WORKFLOW_TOPIC)


def use_async_workflow_dispatch() -> bool:
    return WORKFLOW_EXECUTION_MODE == "pubsub" and bool(PUBSUB_WORKFLOW_TOPIC)


def dispatch_underwriting_workflow(
    db: Session,
    application_id: str,
) -> UnderwritingJob | None:
    if not use_async_workflow_dispatch():
        return create_underwriting_workflow(db, application_id)

    from google.cloud.pubsub_v1 import PublisherClient

    publisher = PublisherClient()
    topic_path = _resolve_topic_path(publisher)
    if not topic_path:
        return create_underwriting_workflow(db, application_id)

    payload = json.dumps({"application_id": application_id}).encode("utf-8")
    publisher.publish(
        topic_path,
        payload,
        application_id=application_id,
        source="underlytics-api",
    ).result()
    return None
