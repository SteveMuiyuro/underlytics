import json
from datetime import datetime

from sqlalchemy.orm import Session

from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.agent_run import AgentRun
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.models.workflow_step_attempt import WorkflowStepAttempt
from underlytics_api.services.guardrail_service import (
    enforce_decision_guardrails,
    validate_agent_output,
)
from underlytics_api.services.orchestrator_service import get_ready_steps
from underlytics_api.services.tracing_service import (
    ensure_workflow_trace_context,
    start_guardrail_observability,
    start_step_observability,
    start_workflow_observability,
)

WORKER_AGENTS = [
    "document_analysis",
    "policy_retrieval",
    "risk_assessment",
    "fraud_verification",
    "decision_summary",
]


def _upsert_agent_output(
    db: Session,
    *,
    agent_run_id: str,
    application_id: str,
    agent_name: str,
    output: dict,
) -> None:
    existing = (
        db.query(AgentOutput)
        .filter(AgentOutput.agent_run_id == agent_run_id)
        .first()
    )

    payload = json.dumps(output)

    if existing:
        existing.output_json = payload
        existing.score = output.get("score")
        existing.confidence = output.get("confidence")
        existing.decision = output.get("decision")
        existing.flags = json.dumps(output.get("flags", []))
        existing.reasoning = output.get("reasoning")
        return

    db.add(
        AgentOutput(
            agent_run_id=agent_run_id,
            application_id=application_id,
            agent_name=agent_name,
            output_json=payload,
            score=output.get("score"),
            confidence=output.get("confidence"),
            decision=output.get("decision"),
            flags=json.dumps(output.get("flags", [])),
            reasoning=output.get("reasoning"),
        )
    )


def _compute_agent_output(
    db: Session,
    *,
    application: Application,
    agent_name: str,
    output_map: dict[str, dict],
    trace_core: str | None = None,
) -> dict:
    if agent_name == "document_analysis":
        documents = (
            db.query(ApplicationDocument)
            .filter(ApplicationDocument.application_id == application.id)
            .all()
        )

        uploaded_types = {doc.document_type for doc in documents}
        required_types = {"id_document", "payslip", "bank_statement"}
        missing_types = sorted(list(required_types - uploaded_types))
        all_required_present = len(missing_types) == 0

        return {
            "score": 0.9 if all_required_present else 0.35,
            "confidence": 0.95,
            "decision": "documents_complete" if all_required_present else "documents_missing",
            "flags": missing_types,
            "reasoning": (
                "All required documents are present."
                if all_required_present
                else f"Missing required documents: {', '.join(missing_types)}"
            ),
            "metrics": {
                "uploaded_count": len(documents),
                "uploaded_types": sorted(list(uploaded_types)),
                "missing_types": missing_types,
                "all_required_present": all_required_present,
            },
        }

    if agent_name == "policy_retrieval":
        product = (
            db.query(LoanProduct)
            .filter(LoanProduct.id == application.loan_product_id)
            .first()
        )

        amount_within_range = (
            product.min_amount <= application.requested_amount <= product.max_amount
            if product
            else False
        )
        term_within_range = (
            product.min_term_months
            <= application.requested_term_months
            <= product.max_term_months
            if product
            else False
        )

        flags = []
        if not amount_within_range:
            flags.append("amount_out_of_range")
        if not term_within_range:
            flags.append("term_out_of_range")

        policy_ok = amount_within_range and term_within_range

        return {
            "score": 0.88 if policy_ok else 0.25,
            "confidence": 0.9,
            "decision": "policy_match" if policy_ok else "policy_mismatch",
            "flags": flags,
            "reasoning": (
                "Application fits loan product policy."
                if policy_ok
                else "Application does not meet loan product policy limits."
            ),
            "metrics": {
                "loan_product_name": product.name if product else "Unknown",
                "min_amount": product.min_amount if product else None,
                "max_amount": product.max_amount if product else None,
                "min_term_months": product.min_term_months if product else None,
                "max_term_months": product.max_term_months if product else None,
                "amount_within_range": amount_within_range,
                "term_within_range": term_within_range,
            },
        }

    if agent_name == "risk_assessment":
        disposable_income = application.monthly_income - (
            application.monthly_expenses + application.existing_loan_obligations
        )

        dti_ratio = 0.0
        if application.monthly_income > 0:
            dti_ratio = (
                application.monthly_expenses + application.existing_loan_obligations
            ) / application.monthly_income

        if dti_ratio < 0.35 and disposable_income > 500:
            risk_band = "low"
            score = 0.85
        elif dti_ratio < 0.55 and disposable_income > 200:
            risk_band = "medium"
            score = 0.6
        else:
            risk_band = "high"
            score = 0.3

        return {
            "score": score,
            "confidence": 0.85,
            "decision": risk_band,
            "flags": ["high_dti"] if dti_ratio > 0.5 else [],
            "reasoning": (
                f"DTI ratio is {round(dti_ratio, 2)} and disposable income is {disposable_income}."
            ),
            "metrics": {
                "dti_ratio": round(dti_ratio, 2),
                "disposable_income": disposable_income,
            },
        }

    if agent_name == "fraud_verification":
        suspicious = False
        reasons = []

        if application.monthly_income <= 0:
            suspicious = True
            reasons.append("income_not_positive")

        if application.requested_amount > application.monthly_income * 20:
            suspicious = True
            reasons.append("requested_amount_extremely_high")

        return {
            "score": 0.2 if suspicious else 0.9,
            "confidence": 0.8,
            "decision": "suspicious" if suspicious else "clear",
            "flags": reasons,
            "reasoning": (
                "Potential fraud indicators found."
                if suspicious
                else "No fraud indicators detected."
            ),
            "metrics": {
                "suspicious": suspicious,
                "reasons": reasons,
            },
        }

    if agent_name == "decision_summary":
        document_output = output_map.get("document_analysis", {})
        policy_output = output_map.get("policy_retrieval", {})
        risk_output = output_map.get("risk_assessment", {})
        fraud_output = output_map.get("fraud_verification", {})

        document_ok = document_output.get("decision") == "documents_complete"
        policy_ok = policy_output.get("decision") == "policy_match"
        risk_decision = risk_output.get("decision")
        fraud_clear = fraud_output.get("decision") == "clear"

        if not document_ok:
            proposed_decision = "manual_review"
            score = 0.4
            flags = document_output.get("flags", [])
            reasoning = "Missing required documents requires manual review."
        elif not fraud_clear:
            proposed_decision = "manual_review"
            score = 0.35
            flags = fraud_output.get("flags", [])
            reasoning = "Fraud indicators require manual review."
        elif not policy_ok:
            proposed_decision = "rejected"
            score = 0.2
            flags = policy_output.get("flags", [])
            reasoning = "Application does not meet loan product policy."
        elif risk_decision == "low":
            proposed_decision = "approved"
            score = 0.9
            flags = []
            reasoning = "Application meets underwriting thresholds."
        elif risk_decision == "medium":
            proposed_decision = "manual_review"
            score = 0.55
            flags = risk_output.get("flags", [])
            reasoning = "Borderline risk requires reviewer decision."
        else:
            proposed_decision = "rejected"
            score = 0.25
            flags = risk_output.get("flags", [])
            reasoning = "High risk profile."

        guardrail_metadata = {
            "application_id": application.id,
            "agent_name": agent_name,
            "proposed_decision": proposed_decision,
        }

        if trace_core:
            guardrail_context = start_guardrail_observability(
                trace_core=trace_core,
                name="underwriting-decision-guardrail",
                metadata=guardrail_metadata,
            )
        else:
            guardrail_context = None

        if guardrail_context:
            with guardrail_context as observation:
                final_decision = enforce_decision_guardrails(
                    document_output=document_output,
                    policy_output=policy_output,
                    risk_output=risk_output,
                    fraud_output=fraud_output,
                    proposed_decision=proposed_decision,
                )
                observation.record_output(
                    output={
                        "proposed_decision": proposed_decision,
                        "final_decision": final_decision,
                    },
                    metadata={
                        **guardrail_metadata,
                        "guardrail_adjusted": final_decision != proposed_decision,
                    },
                )
        else:
            final_decision = enforce_decision_guardrails(
                document_output=document_output,
                policy_output=policy_output,
                risk_output=risk_output,
                fraud_output=fraud_output,
                proposed_decision=proposed_decision,
            )

        if final_decision != proposed_decision:
            flags = flags + [f"guardrail_adjusted_to_{final_decision}"]
            reasoning = (
                f"{reasoning} Final decision adjusted by hard guardrails to {final_decision}."
            )

        application.status = final_decision
        db.add(application)

        return {
            "score": score,
            "confidence": 0.88,
            "decision": final_decision,
            "flags": flags,
            "reasoning": reasoning,
            "inputs_used": {
                "document_analysis": document_output.get("decision"),
                "policy_retrieval": policy_output.get("decision"),
                "risk_assessment": risk_decision,
                "fraud_verification": fraud_output.get("decision"),
            },
        }

    raise ValueError(f"No execution logic defined for '{agent_name}'")


def _create_legacy_job(
    db: Session,
    application_id: str,
) -> tuple[UnderwritingJob, dict[str, AgentRun]]:
    job = UnderwritingJob(
        application_id=application_id,
        status="running",
        current_step="planner_initialized",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()

    runs_by_agent: dict[str, AgentRun] = {}
    for agent_name in WORKER_AGENTS:
        run = AgentRun(
            underwriting_job_id=job.id,
            application_id=application_id,
            agent_name=agent_name,
            status="pending",
        )
        db.add(run)
        db.flush()
        runs_by_agent[agent_name] = run

    return job, runs_by_agent


def _create_step_attempt(
    db: Session, step: WorkflowStep, *, trace_core: str | None = None
) -> WorkflowStepAttempt:
    previous_attempts = (
        db.query(WorkflowStepAttempt)
        .filter(WorkflowStepAttempt.workflow_step_id == step.id)
        .count()
    )
    attempt = WorkflowStepAttempt(
        workflow_step_id=step.id,
        attempt_number=previous_attempts + 1,
        executor_type="deterministic",
        status="running",
        trace_id=trace_core,
        started_at=datetime.utcnow(),
    )
    db.add(attempt)
    db.flush()
    return attempt


def _unblock_ready_steps(db: Session, workflow_plan_id: str) -> None:
    ready_steps = get_ready_steps(db, workflow_plan_id)
    for step in ready_steps:
        if step.status == "blocked":
            step.status = "pending"
            db.add(step)


def _ensure_manual_review_case(
    db: Session, *, application_id: str, workflow_plan_id: str, reason: str
) -> None:
    existing_case = (
        db.query(ManualReviewCase)
        .filter(
            ManualReviewCase.application_id == application_id,
            ManualReviewCase.workflow_plan_id == workflow_plan_id,
            ManualReviewCase.status == "open",
        )
        .first()
    )
    if existing_case:
        return

    db.add(
        ManualReviewCase(
            application_id=application_id,
            workflow_plan_id=workflow_plan_id,
            status="open",
            reason=reason,
        )
    )


def _execute_workflow_step(
    db: Session,
    *,
    step: WorkflowStep,
    output_map: dict[str, dict],
    legacy_run: AgentRun,
    trace_core: str | None = None,
) -> tuple[bool, dict | None]:
    application = db.query(Application).filter(Application.id == step.application_id).first()
    if not application:
        error_message = "Application not found"
        step.status = "failed"
        step.failed_at = datetime.utcnow()
        legacy_run.status = "failed"
        legacy_run.failed_at = datetime.utcnow()
        legacy_run.error_message = error_message
        db.add(step)
        db.add(legacy_run)
        db.commit()
        return False, None

    step.status = "running"
    step.started_at = datetime.utcnow()
    legacy_run.status = "running"
    legacy_run.started_at = datetime.utcnow()
    legacy_run.error_message = None
    db.add(step)
    db.add(legacy_run)
    attempt = _create_step_attempt(db, step, trace_core=trace_core)
    db.commit()

    step_metadata = {
        "application_id": step.application_id,
        "workflow_plan_id": step.workflow_plan_id,
        "workflow_step_id": step.id,
        "attempt_id": attempt.id,
        "worker_name": step.worker_name,
        "step_key": step.step_key,
        "executor_type": attempt.executor_type,
    }
    step_input = {
        "application_id": step.application_id,
        "input_context_json": step.input_context_json,
    }

    try:
        if trace_core:
            with start_step_observability(
                trace_core=trace_core,
                step_name=step.worker_name,
                metadata=step_metadata,
                input_payload=step_input,
            ) as observation:
                try:
                    output = _compute_agent_output(
                        db,
                        application=application,
                        agent_name=step.worker_name,
                        output_map=output_map,
                        trace_core=trace_core,
                    )
                    validate_agent_output(step.worker_name, output)
                    observation.record_output(
                        output=output,
                        metadata={**step_metadata, "status": "completed"},
                    )
                except Exception as exc:
                    observation.record_error(
                        message=str(exc),
                        data={
                            "workflow_step_id": step.id,
                            "attempt_id": attempt.id,
                        },
                    )
                    raise
        else:
            output = _compute_agent_output(
                db,
                application=application,
                agent_name=step.worker_name,
                output_map=output_map,
                trace_core=trace_core,
            )
            validate_agent_output(step.worker_name, output)

        _upsert_agent_output(
            db,
            agent_run_id=legacy_run.id,
            application_id=application.id,
            agent_name=step.worker_name,
            output=output,
        )

        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.decision = output.get("decision")

        attempt.status = "completed"
        attempt.completed_at = datetime.utcnow()

        legacy_run.status = "completed"
        legacy_run.completed_at = datetime.utcnow()
        legacy_run.error_message = None

        db.add(step)
        db.add(attempt)
        db.add(legacy_run)
        db.commit()
        db.refresh(step)
        return True, output
    except Exception as exc:
        error_message = str(exc)

        step.status = "failed"
        step.failed_at = datetime.utcnow()

        attempt.status = "failed"
        attempt.error_message = error_message
        attempt.completed_at = datetime.utcnow()

        legacy_run.status = "failed"
        legacy_run.failed_at = datetime.utcnow()
        legacy_run.error_message = error_message

        db.add(step)
        db.add(attempt)
        db.add(legacy_run)
        db.commit()
        db.refresh(step)
        return False, None


def run_workflow_plan(db: Session, plan: WorkflowPlan) -> UnderwritingJob:
    application = db.query(Application).filter(Application.id == plan.application_id).first()
    if not application:
        raise ValueError("Application not found")

    workflow_trace = ensure_workflow_trace_context(
        plan_id=plan.id,
        group_id=application.id,
    )
    plan.trace_id = workflow_trace.trace_core
    application.status = "in_progress"
    plan.status = "running"
    db.add(application)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    workflow_metadata = {
        "application_id": application.id,
        "application_number": application.application_number,
        "workflow_plan_id": plan.id,
        "planner_mode": plan.planner_mode,
        "plan_version": plan.plan_version,
    }
    workflow_input = {
        "application_id": application.id,
        "requested_amount": application.requested_amount,
        "requested_term_months": application.requested_term_months,
        "loan_product_id": application.loan_product_id,
    }

    with start_workflow_observability(
        workflow=workflow_trace,
        metadata=workflow_metadata,
        input_payload=workflow_input,
    ) as workflow_observation:
        legacy_job, runs_by_agent = _create_legacy_job(db, application.id)
        db.commit()
        db.refresh(plan)
        db.refresh(legacy_job)

        output_map: dict[str, dict] = {}
        failed = False

        while True:
            _unblock_ready_steps(db, plan.id)
            ready_steps = get_ready_steps(db, plan.id)
            if not ready_steps:
                break

            for step in ready_steps:
                legacy_job.current_step = step.step_key
                db.add(legacy_job)
                db.commit()

                success, output = _execute_workflow_step(
                    db,
                    step=step,
                    output_map=output_map,
                    legacy_run=runs_by_agent[step.worker_name],
                    trace_core=workflow_trace.trace_core,
                )
                if not success:
                    failed = True
                    break

                if output is not None:
                    output_map[step.worker_name] = output

            if failed:
                break

        refreshed_steps = (
            db.query(WorkflowStep)
            .filter(WorkflowStep.workflow_plan_id == plan.id)
            .order_by(WorkflowStep.priority.asc(), WorkflowStep.created_at.asc())
            .all()
        )

        if refreshed_steps and all(step.status == "completed" for step in refreshed_steps):
            final_decision = output_map.get("decision_summary", {}).get("decision")

            if final_decision == "manual_review":
                plan.status = "awaiting_review"
                _ensure_manual_review_case(
                    db,
                    application_id=application.id,
                    workflow_plan_id=plan.id,
                    reason=output_map.get("decision_summary", {}).get(
                        "reasoning", "Workflow escalated to manual review."
                    ),
                )
            else:
                plan.status = "completed"

            legacy_job.status = "completed"
            legacy_job.current_step = "workers_completed"
            legacy_job.completed_at = datetime.utcnow()
            workflow_observation.record_output(
                output={
                    "workflow_status": plan.status,
                    "final_decision": final_decision,
                },
                metadata={**workflow_metadata, "status": plan.status},
            )
        elif any(step.status == "failed" for step in refreshed_steps):
            plan.status = "failed"
            legacy_job.status = "failed"
            legacy_job.current_step = "worker_failed"
            legacy_job.failed_at = datetime.utcnow()
            workflow_observation.record_error(
                message="Workflow execution failed",
                data={**workflow_metadata, "status": plan.status},
            )
        else:
            plan.status = "running"
            legacy_job.status = "running"
            legacy_job.current_step = "workers_in_progress"
            workflow_observation.record_output(
                output={"workflow_status": plan.status},
                metadata={**workflow_metadata, "status": plan.status},
            )

        db.add(plan)
        db.add(legacy_job)
        db.commit()
        db.refresh(legacy_job)
        return legacy_job
