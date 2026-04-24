import json
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.models.agent_evaluation import AgentEvaluation
from underlytics_api.models.application import Application
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.models.workflow_step_attempt import WorkflowStepAttempt
from underlytics_api.services.agent_evaluation_service import record_agent_evaluation


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_attempt(db: Session) -> tuple[WorkflowStep, WorkflowStepAttempt]:
    user = User(
        clerk_user_id="clerk-eval-user",
        role="applicant",
        email="eval@example.com",
        full_name="Eval Example",
    )
    product = LoanProduct(
        code="eval_product",
        name="Eval Product",
        description="Eval Product",
        min_amount=1000,
        max_amount=10000,
        min_term_months=3,
        max_term_months=24,
        is_active=True,
    )
    db.add_all([user, product])
    db.commit()
    db.refresh(user)
    db.refresh(product)

    application = Application(
        application_number="APP-EVAL-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=5000,
        requested_term_months=12,
        monthly_income=3000,
        monthly_expenses=800,
        existing_loan_obligations=200,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    plan = WorkflowPlan(
        application_id=application.id,
        plan_version="v1",
        planner_mode="agentic_vertex",
        status="running",
        summary="Eval",
        plan_json="{}",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    step = WorkflowStep(
        workflow_plan_id=plan.id,
        application_id=application.id,
        step_key="decision_summary",
        step_type="worker",
        worker_name="decision_summary",
        status="running",
        queue_name="underwriting",
        input_context_json="{}",
        priority=10,
    )
    db.add(step)
    db.commit()
    db.refresh(step)

    attempt = WorkflowStepAttempt(
        workflow_step_id=step.id,
        attempt_number=1,
        executor_type="autonomous_llm",
        status="completed",
        started_at=datetime.utcnow() - timedelta(seconds=2),
        completed_at=datetime.utcnow(),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return step, attempt


def test_record_agent_evaluation_captures_guardrail_adjustment_and_tool_counts():
    db = make_session()

    try:
        step, attempt = seed_attempt(db)
        prompt = AgentPromptDefinition(
            agent_name="decision_summary",
            role="Decision Summary Agent",
            model_provider="openai",
            model_name="gpt-5.4",
            prompt_version="v2",
            allowed_decisions=("approved", "rejected", "manual_review"),
            system_prompt="Prompt",
        )

        record_agent_evaluation(
            db,
            step=step,
            attempt=attempt,
            prompt=prompt,
            scoped_input={
                "input": {
                    "tool_evidence": [
                        {"status": "completed", "source": "fixture_public_registry"},
                        {"status": "skipped", "source": "internal_policy_catalog"},
                    ]
                }
            },
            output={
                "score": 0.8,
                "confidence": 0.9,
                "decision": "approved",
                "flags": ["guardrail_adjusted_to_manual_review"],
                "reasoning": "Reasoning text",
            },
            status="completed",
            schema_valid=True,
            final_decision="manual_review",
        )
        db.commit()

        stored = db.query(AgentEvaluation).one()
    finally:
        db.close()

    metadata = json.loads(stored.evaluation_json)
    assert stored.guardrail_adjusted is True
    assert stored.tool_evidence_count == 2
    assert stored.completed_tool_evidence_count == 1
    assert stored.final_decision == "manual_review"
    assert stored.latency_ms is not None
    assert metadata["tool_sources"] == [
        "fixture_public_registry",
        "internal_policy_catalog",
    ]
