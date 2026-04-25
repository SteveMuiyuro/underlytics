import json
from datetime import datetime

from sqlalchemy.orm import Session

from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.agent_run import AgentRun
from underlytics_api.models.application import Application
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.models.workflow_step_attempt import WorkflowStepAttempt
from underlytics_api.services.agent_evaluation_service import record_agent_evaluation
from underlytics_api.services.guardrail_service import (
    enforce_decision_guardrails,
    validate_agent_output,
)
from underlytics_api.services.notification_service import (
    send_automated_decision_notification,
    send_manual_review_escalation_notification,
)
from underlytics_api.services.orchestrator_service import get_ready_steps
from underlytics_api.services.tracing_service import (
    ensure_workflow_trace_context,
    start_guardrail_observability,
    start_step_observability,
    start_workflow_observability,
)
from underlytics_api.services.underwriting_agent_service import (
    execute_autonomous_underwriting_agent,
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
        executor_type="autonomous_llm",
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
) -> ManualReviewCase:
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
        return existing_case

    case = ManualReviewCase(
        application_id=application_id,
        workflow_plan_id=workflow_plan_id,
        status="open",
        reason=reason,
    )
    db.add(case)
    db.flush()
    return case


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

    try:
        execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name=step.worker_name,
            output_map=output_map,
        )
        step_metadata = {
            **step_metadata,
            "model_provider": execution.prompt.model_provider,
            "model_name": execution.prompt.model_name,
            "prompt_version": execution.prompt.prompt_version,
            "role": execution.prompt.role,
            "execution_mode": execution.execution_mode,
        }
        step_input = execution.scoped_input
        output = execution.output
        proposed_decision = output.get("decision")
        final_decision = proposed_decision

        if trace_core:
            with start_step_observability(
                trace_core=trace_core,
                step_name=step.worker_name,
                metadata=step_metadata,
                input_payload=step_input,
            ) as observation:
                try:
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
            validate_agent_output(step.worker_name, output)

        if step.worker_name == "decision_summary":
            guardrail_metadata = {
                "workflow_step_id": step.id,
                "attempt_id": attempt.id,
                "application_id": application.id,
                "proposed_decision": proposed_decision,
                "document_decision": output_map.get("document_analysis", {}).get("decision"),
                "policy_decision": output_map.get("policy_retrieval", {}).get("decision"),
                "risk_decision": output_map.get("risk_assessment", {}).get("decision"),
                "fraud_decision": output_map.get("fraud_verification", {}).get("decision"),
            }
            if trace_core:
                with start_guardrail_observability(
                    trace_core=trace_core,
                    name="decision_summary_guardrails",
                    metadata=guardrail_metadata,
                ) as observation:
                    try:
                        final_decision = enforce_decision_guardrails(
                            document_output=output_map.get("document_analysis", {}),
                            policy_output=output_map.get("policy_retrieval", {}),
                            risk_output=output_map.get("risk_assessment", {}),
                            fraud_output=output_map.get("fraud_verification", {}),
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
                    except Exception as exc:
                        observation.record_error(
                            message=str(exc),
                            data=guardrail_metadata,
                        )
                        raise
            else:
                final_decision = enforce_decision_guardrails(
                    document_output=output_map.get("document_analysis", {}),
                    policy_output=output_map.get("policy_retrieval", {}),
                    risk_output=output_map.get("risk_assessment", {}),
                    fraud_output=output_map.get("fraud_verification", {}),
                    proposed_decision=proposed_decision,
                )
            if final_decision != proposed_decision:
                output["flags"] = output.get("flags", []) + [
                    f"guardrail_adjusted_to_{final_decision}"
                ]
                output["reasoning"] = (
                    f'{output.get("reasoning", "").strip()} Final decision adjusted by hard '
                    f"guardrails to {final_decision}."
                ).strip()
                output["decision"] = final_decision

            application.status = output.get("decision")
            db.add(application)

        record_agent_evaluation(
            db,
            step=step,
            attempt=attempt,
            prompt=execution.prompt,
            scoped_input=step_input,
            output=output,
            status="completed",
            schema_valid=True,
            proposed_decision=proposed_decision,
            final_decision=final_decision,
        )

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

        record_agent_evaluation(
            db,
            step=step,
            attempt=attempt,
            prompt=locals().get("execution").prompt if "execution" in locals() else None,
            scoped_input=locals().get("step_input"),
            output=locals().get("output"),
            status="failed",
            schema_valid=False,
            proposed_decision=locals().get("proposed_decision"),
            final_decision=locals().get("final_decision"),
            error_message=error_message,
        )

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

        final_decision = output_map.get("decision_summary", {}).get("decision")

        manual_review_case: ManualReviewCase | None = None
        if refreshed_steps and all(step.status == "completed" for step in refreshed_steps):

            if final_decision == "manual_review":
                plan.status = "awaiting_review"
                manual_review_case = _ensure_manual_review_case(
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

        if final_decision in {"approved", "rejected"}:
            send_automated_decision_notification(
                db,
                application_id=application.id,
                decision=final_decision,
            )
            db.refresh(legacy_job)
        elif final_decision == "manual_review" and manual_review_case is not None:
            send_manual_review_escalation_notification(
                db,
                manual_review_case_id=manual_review_case.id,
            )
            db.refresh(legacy_job)

        return legacy_job
