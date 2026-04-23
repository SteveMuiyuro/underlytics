from __future__ import annotations

import json
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session

from underlytics_api.core.config import EMAIL_FROM, RESEND_API_KEY
from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.application import Application
from underlytics_api.models.communication_log import CommunicationLog
from underlytics_api.models.manual_review_action import ManualReviewAction
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.user import User
from underlytics_api.services.providers.resend_provider import (
    EmailDeliveryResult,
    ResendProvider,
)


class EmailProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
    ) -> EmailDeliveryResult: ...


def _coerce_flags(raw_flags: str | None) -> list[str]:
    if not raw_flags:
        return []

    try:
        decoded = json.loads(raw_flags)
    except json.JSONDecodeError:
        return [raw_flags]

    if not isinstance(decoded, list):
        return []

    return [str(flag) for flag in decoded if flag]


def _get_email_provider() -> EmailProvider | None:
    if not RESEND_API_KEY or not EMAIL_FROM:
        return None

    return ResendProvider(api_key=RESEND_API_KEY, email_from=EMAIL_FROM)


def _load_application_context(
    db: Session,
    *,
    application_id: str,
) -> tuple[Application, User, AgentOutput | None]:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError("Application not found for notification")

    applicant = db.query(User).filter(User.id == application.applicant_user_id).first()
    if not applicant:
        raise ValueError("Applicant user not found for notification")

    decision_output = (
        db.query(AgentOutput)
        .filter(
            AgentOutput.application_id == application.id,
            AgentOutput.agent_name == "decision_summary",
        )
        .order_by(AgentOutput.created_at.desc())
        .first()
    )

    return application, applicant, decision_output


def _existing_sent_log(
    db: Session,
    *,
    application_id: str,
    template_key: str,
    manual_review_case_id: str | None = None,
) -> CommunicationLog | None:
    query = db.query(CommunicationLog).filter(
        CommunicationLog.application_id == application_id,
        CommunicationLog.template_key == template_key,
        CommunicationLog.status == "sent",
    )
    if manual_review_case_id:
        query = query.filter(CommunicationLog.manual_review_case_id == manual_review_case_id)
    else:
        query = query.filter(CommunicationLog.manual_review_case_id.is_(None))

    return query.order_by(CommunicationLog.created_at.desc()).first()


def _create_log(
    *,
    application_id: str,
    manual_review_case_id: str | None,
    recipient_email: str,
    template_key: str,
    subject: str,
    body_text: str,
    metadata: dict,
) -> CommunicationLog:
    return CommunicationLog(
        application_id=application_id,
        manual_review_case_id=manual_review_case_id,
        recipient_email=recipient_email,
        template_key=template_key,
        subject=subject,
        body_text=body_text,
        metadata_json=json.dumps(metadata),
        status="pending",
    )


def _deliver_log(
    db: Session,
    *,
    log: CommunicationLog,
) -> CommunicationLog:
    provider = _get_email_provider()
    if not log.recipient_email:
        log.status = "skipped"
        log.error_message = "Recipient email is missing"
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    if not provider:
        log.status = "skipped"
        log.error_message = "Email provider is not configured"
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    try:
        result = provider.send_email(
            to_email=log.recipient_email,
            subject=log.subject,
            body_text=log.body_text,
        )
        log.status = "sent"
        log.provider_name = result.provider_name
        log.provider_message_id = result.provider_message_id
        log.sent_at = datetime.utcnow()
    except Exception as exc:
        log.status = "failed"
        log.provider_name = provider.provider_name
        log.error_message = str(exc)

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
    if decision not in {"approved", "rejected"}:
        return None

    if _existing_sent_log(
        db,
        application_id=application_id,
        template_key=f"application_{decision}",
    ):
        return None

    application, applicant, decision_output = _load_application_context(
        db,
        application_id=application_id,
    )
    flags = _coerce_flags(decision_output.flags if decision_output else None)
    subject = f"Underlytics application {application.application_number}: {decision.title()}"
    body_text = "\n".join(
        [
            f"Hello {applicant.full_name},",
            "",
            f"Your application {application.application_number} has been {decision}.",
            f"Requested amount: {application.requested_amount}",
            f"Requested term: {application.requested_term_months} month(s)",
            "",
            "Decision reasoning:",
            decision_output.reasoning
            if decision_output and decision_output.reasoning
            else "No additional reasoning was recorded.",
            "",
            "Flags considered:",
            ", ".join(flags) if flags else "None",
        ]
    )
    log = _create_log(
        application_id=application.id,
        manual_review_case_id=None,
        recipient_email=applicant.email,
        template_key=f"application_{decision}",
        subject=subject,
        body_text=body_text,
        metadata={
            "decision": decision,
            "application_number": application.application_number,
        },
    )
    return _deliver_log(db, log=log)


def send_manual_review_completed_notification(
    db: Session,
    *,
    manual_review_case_id: str,
) -> CommunicationLog | None:
    case = db.query(ManualReviewCase).filter(ManualReviewCase.id == manual_review_case_id).first()
    if not case:
        raise ValueError("Manual review case not found for notification")

    if _existing_sent_log(
        db,
        application_id=case.application_id,
        template_key="manual_review_completed",
        manual_review_case_id=case.id,
    ):
        return None

    application, applicant, decision_output = _load_application_context(
        db,
        application_id=case.application_id,
    )
    resolution_action = (
        db.query(ManualReviewAction)
        .filter(
            ManualReviewAction.manual_review_case_id == case.id,
            ManualReviewAction.new_decision.is_not(None),
        )
        .order_by(ManualReviewAction.created_at.desc())
        .first()
    )
    final_decision = resolution_action.new_decision if resolution_action else application.status
    reviewer_note = resolution_action.note if resolution_action else "No reviewer note recorded."
    flags = _coerce_flags(decision_output.flags if decision_output else None)

    subject = (
        f"Underlytics application {application.application_number}: Manual review completed"
    )
    body_text = "\n".join(
        [
            f"Hello {applicant.full_name},",
            "",
            f"Manual review for application {application.application_number} is complete.",
            f"Final decision: {final_decision}",
            "",
            "Reviewer note:",
            reviewer_note,
            "",
            "Supporting agent reasoning:",
            decision_output.reasoning
            if decision_output and decision_output.reasoning
            else "No additional reasoning was recorded.",
            "",
            "Flags considered:",
            ", ".join(flags) if flags else "None",
        ]
    )
    log = _create_log(
        application_id=application.id,
        manual_review_case_id=case.id,
        recipient_email=applicant.email,
        template_key="manual_review_completed",
        subject=subject,
        body_text=body_text,
        metadata={
            "decision": final_decision,
            "application_number": application.application_number,
            "manual_review_case_id": case.id,
        },
    )
    return _deliver_log(db, log=log)
