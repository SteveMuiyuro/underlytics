from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session

from underlytics_api.agents.prompts import EMAIL_AGENT_PROMPT
from underlytics_api.core.config import EMAIL_FROM, RESEND_API_KEY
from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.application import Application
from underlytics_api.models.communication_log import CommunicationLog
from underlytics_api.models.manual_review_action import ManualReviewAction
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.user import User
from underlytics_api.schemas.agent_execution import EmailAgentOutput
from underlytics_api.services.providers.resend_provider import (
    EmailDeliveryResult,
    ResendProvider,
)
from underlytics_api.services.tracing_service import (
    ensure_trace_context,
    start_agent_observability,
)
from underlytics_api.services.underwriting_agent_service import _run_structured_agent

EMAIL_TYPES = {
    "agent_final_approved",
    "agent_final_rejected",
    "manual_review_escalated",
    "manual_review_final_approved",
    "manual_review_final_rejected",
}
EMAIL_AGENT_TRACE_NAME = "underlytics-email-agent"


class EmailProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> EmailDeliveryResult: ...


@dataclass
class ApplicationEmailContext:
    application: Application
    applicant: User
    agent_outputs: list[AgentOutput]
    decision_output: AgentOutput | None


def _coerce_flags(raw_flags: str | None) -> list[str]:
    if not raw_flags:
        return []

    try:
        decoded = json.loads(raw_flags)
    except json.JSONDecodeError:
        return [raw_flags]

    if not isinstance(decoded, list):
        return []

    return [str(flag).replace("_", " ") for flag in decoded if flag]


def _normalize_sentence(value: str | None, fallback: str) -> str:
    normalized = " ".join((value or "").strip().split())
    if not normalized:
        return fallback
    return normalized


def _applicant_display_name(applicant: User) -> str:
    for field_name in ("full_name", "name", "first_name"):
        value = getattr(applicant, field_name, None)
        if value:
            return str(value).strip()

    return applicant.email


def _applicant_safe_reasoning(
    *,
    decision_output: AgentOutput | None,
    fallback: str,
) -> str:
    if not decision_output or not decision_output.reasoning:
        return fallback

    reasoning = decision_output.reasoning.replace("_", " ")
    for term in ("guardrail", "agent", "workflow", "retry", "trace", "json", "llm"):
        reasoning = reasoning.replace(term, "review")
        reasoning = reasoning.replace(term.title(), "Review")
        reasoning = reasoning.replace(term.upper(), "REVIEW")

    return _normalize_sentence(reasoning, fallback)


def _manual_review_summary(
    *,
    final_decision: str,
    reviewer_note: str | None,
) -> str:
    if final_decision == "approved":
        return (
            "A reviewer completed an additional review of your application and confirmed "
            "that it can move forward."
        )

    return (
        "A reviewer completed an additional review of your application and confirmed "
        "that we cannot approve it at this time."
    )


def _build_email_provider() -> EmailProvider | None:
    if not RESEND_API_KEY or not EMAIL_FROM:
        return None

    return ResendProvider(api_key=RESEND_API_KEY, email_from=EMAIL_FROM)


def _load_application_email_context(
    db: Session,
    *,
    application_id: str,
) -> ApplicationEmailContext:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError("Application not found for notification")

    applicant = db.query(User).filter(User.id == application.applicant_user_id).first()
    if not applicant:
        raise ValueError("Applicant user not found for notification")

    agent_outputs = (
        db.query(AgentOutput)
        .filter(AgentOutput.application_id == application.id)
        .order_by(AgentOutput.created_at.desc())
        .all()
    )
    decision_output = next(
        (output for output in agent_outputs if output.agent_name == "decision_summary"),
        None,
    )

    return ApplicationEmailContext(
        application=application,
        applicant=applicant,
        agent_outputs=agent_outputs,
        decision_output=decision_output,
    )


def _existing_sent_log(
    db: Session,
    *,
    application_id: str,
    email_type: str,
    manual_review_case_id: str | None = None,
) -> CommunicationLog | None:
    query = db.query(CommunicationLog).filter(
        CommunicationLog.application_id == application_id,
        CommunicationLog.template_key == email_type,
        CommunicationLog.status == "sent",
    )

    if manual_review_case_id:
        query = query.filter(CommunicationLog.manual_review_case_id == manual_review_case_id)
    else:
        query = query.filter(CommunicationLog.manual_review_case_id.is_(None))

    return query.order_by(CommunicationLog.created_at.desc()).first()


def generate_application_email(
    *,
    application: Application,
    applicant: User,
    agent_outputs: list[AgentOutput],
    email_type: str,
    reviewer_note: str | None = None,
    reviewer_decision: str | None = None,
) -> dict[str, str]:
    if email_type not in EMAIL_TYPES:
        raise ValueError(f"Unsupported email type '{email_type}'")

    decision_output = next(
        (output for output in agent_outputs if output.agent_name == "decision_summary"),
        None,
    )

    flags = _coerce_flags(decision_output.flags if decision_output else None)

    email_context = {
        "applicant": {
            "name": _applicant_display_name(applicant),
            "email": applicant.email,
        },
        "application": {
            "application_number": application.application_number,
            "requested_amount": application.requested_amount,
            "requested_term_months": application.requested_term_months,
            "status": application.status,
        },
        "email_type": email_type,
        "reviewer_decision": reviewer_decision,
        "reviewer_note": reviewer_note,
        "decision_summary": {
            "decision": decision_output.decision if decision_output else None,
            "reasoning": _applicant_safe_reasoning(
                decision_output=decision_output,
                fallback="The application has been reviewed.",
            ),
            "flags": flags,
        },
        "manual_review_summary": _manual_review_summary(
            final_decision=reviewer_decision or application.status,
            reviewer_note=reviewer_note,
        ),
    }

    email_metadata = {
        "application_id": application.id,
        "application_number": application.application_number,
        "email_type": email_type,
        "reviewer_decision": reviewer_decision,
        "agent_name": EMAIL_AGENT_PROMPT.agent_name,
        "model_provider": EMAIL_AGENT_PROMPT.model_provider,
        "model_name": EMAIL_AGENT_PROMPT.model_name,
        "prompt_version": EMAIL_AGENT_PROMPT.prompt_version,
    }

    trace_context = ensure_trace_context(
        seed=f"email:{application.id}:{email_type}",
        group_id=application.id,
    )

    with start_agent_observability(
        trace_name=EMAIL_AGENT_TRACE_NAME,
        trace_context=trace_context,
        metadata=email_metadata,
        input_payload=email_context,
    ) as observation:
        try:
            email_output = _run_structured_agent(
                prompt=EMAIL_AGENT_PROMPT,
                scoped_input=email_context,
                output_type=EmailAgentOutput,
            )
            email_output.pop("__runtime", None)
            structured_email = EmailAgentOutput.model_validate(email_output)
        except Exception as exc:
            observation.record_error(
                message=str(exc),
                data=email_metadata,
            )
            raise

        observation.record_output(
            output=structured_email.model_dump(),
            metadata=email_metadata,
        )

    return structured_email.model_dump()


def send_application_email(
    *,
    db: Session,
    application_id: str,
    to_email: str,
    subject: str,
    html_body: str,
    email_type: str,
    manual_review_case_id: str | None = None,
    metadata: dict | None = None,
) -> CommunicationLog:
    if email_type not in EMAIL_TYPES:
        raise ValueError(f"Unsupported email type '{email_type}'")

    log = CommunicationLog(
        application_id=application_id,
        manual_review_case_id=manual_review_case_id,
        recipient_email=to_email or "",
        template_key=email_type,
        subject=subject,
        body_text=html_body,
        status="pending",
        channel="email",
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(log)

    provider = _build_email_provider()

    if not to_email:
        log.status = "skipped"
        log.error_message = "Recipient email is missing"
        db.commit()
        db.refresh(log)
        return log

    if not provider:
        log.status = "skipped"
        log.error_message = "Email provider is not configured"
        db.commit()
        db.refresh(log)
        return log

    try:
        result = provider.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
        )
        log.status = "sent"
        log.provider_name = result.provider_name
        log.provider_message_id = result.provider_message_id
        log.sent_at = datetime.utcnow()
    except Exception as exc:
        log.status = "failed"
        log.provider_name = provider.provider_name
        log.error_message = f"Email delivery failed: {exc}"

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def send_automated_decision_notification(
    db: Session,
    *,
    application_id: str,
    decision: str,
) -> CommunicationLog | None:
    email_type = {
        "approved": "agent_final_approved",
        "rejected": "agent_final_rejected",
    }.get(decision)

    if not email_type:
        return None

    if _existing_sent_log(db, application_id=application_id, email_type=email_type):
        return None

    context = _load_application_email_context(db, application_id=application_id)

    email_payload = generate_application_email(
        application=context.application,
        applicant=context.applicant,
        agent_outputs=context.agent_outputs,
        email_type=email_type,
    )

    return send_application_email(
        db=db,
        application_id=context.application.id,
        to_email=context.applicant.email,
        subject=email_payload["subject"],
        html_body=email_payload["html_body"],
        email_type=email_type,
        metadata={
            "application_number": context.application.application_number,
            "decision": decision,
        },
    )


def send_manual_review_escalation_notification(
    db: Session,
    *,
    manual_review_case_id: str,
) -> CommunicationLog | None:
    case = db.query(ManualReviewCase).filter(ManualReviewCase.id == manual_review_case_id).first()

    if not case:
        raise ValueError("Manual review case not found for notification")

    email_type = "manual_review_escalated"

    if _existing_sent_log(
        db,
        application_id=case.application_id,
        email_type=email_type,
        manual_review_case_id=case.id,
    ):
        return None

    context = _load_application_email_context(db, application_id=case.application_id)

    email_payload = generate_application_email(
        application=context.application,
        applicant=context.applicant,
        agent_outputs=context.agent_outputs,
        email_type=email_type,
    )

    return send_application_email(
        db=db,
        application_id=context.application.id,
        to_email=context.applicant.email,
        subject=email_payload["subject"],
        html_body=email_payload["html_body"],
        email_type=email_type,
        manual_review_case_id=case.id,
        metadata={
            "application_number": context.application.application_number,
            "manual_review_case_id": case.id,
        },
    )


def send_manual_review_completed_notification(
    db: Session,
    *,
    manual_review_case_id: str,
) -> CommunicationLog | None:
    case = db.query(ManualReviewCase).filter(ManualReviewCase.id == manual_review_case_id).first()

    if not case:
        raise ValueError("Manual review case not found for notification")

    resolution_action = (
        db.query(ManualReviewAction)
        .filter(
            ManualReviewAction.manual_review_case_id == case.id,
            ManualReviewAction.new_decision.is_not(None),
        )
        .order_by(ManualReviewAction.created_at.desc())
        .first()
    )

    if not resolution_action or resolution_action.new_decision not in {"approved", "rejected"}:
        return None

    email_type = (
        "manual_review_final_approved"
        if resolution_action.new_decision == "approved"
        else "manual_review_final_rejected"
    )

    if _existing_sent_log(
        db,
        application_id=case.application_id,
        email_type=email_type,
        manual_review_case_id=case.id,
    ):
        return None

    context = _load_application_email_context(db, application_id=case.application_id)

    email_payload = generate_application_email(
        application=context.application,
        applicant=context.applicant,
        agent_outputs=context.agent_outputs,
        email_type=email_type,
        reviewer_note=resolution_action.note,
        reviewer_decision=resolution_action.new_decision,
    )

    return send_application_email(
        db=db,
        application_id=context.application.id,
        to_email=context.applicant.email,
        subject=email_payload["subject"],
        html_body=email_payload["html_body"],
        email_type=email_type,
        manual_review_case_id=case.id,
        metadata={
            "application_number": context.application.application_number,
            "manual_review_case_id": case.id,
            "decision": resolution_action.new_decision,
        },
    )