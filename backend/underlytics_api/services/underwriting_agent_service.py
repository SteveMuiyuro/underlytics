from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from underlytics_api.agents.prompts import PROMPT_REGISTRY
from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.schemas.agent_execution import EvaluationAgentOutput
from underlytics_api.services.agent_runtime_service import run_structured_agent
from underlytics_api.services.mcp_evidence_service import build_mcp_tool_evidence


@dataclass(frozen=True)
class AutonomousAgentExecution:
    output: dict[str, Any]
    prompt: AgentPromptDefinition
    scoped_input: dict[str, Any]
    execution_mode: str


def get_agent_prompt_definition(agent_name: str) -> AgentPromptDefinition:
    prompt = PROMPT_REGISTRY.get(agent_name)
    if not prompt:
        raise ValueError(f"No prompt definition registered for '{agent_name}'")
    return prompt


def build_autonomous_agent_input(
    db: Session,
    *,
    application: Application,
    agent_name: str,
    output_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if agent_name == "document_analysis":
        documents = (
            db.query(ApplicationDocument)
            .filter(ApplicationDocument.application_id == application.id)
            .all()
        )
        required_document_types = ["id_document", "payslip", "bank_statement"]
        return {
            "application": {
                "id": application.id,
                "application_number": application.application_number,
            },
            "required_document_types": required_document_types,
            "uploaded_documents": [
                {
                    "document_type": document.document_type,
                    "file_name": document.file_name,
                    "upload_status": document.upload_status,
                    "is_required": document.is_required,
                    "mime_type": document.mime_type,
                    "file_size_bytes": document.file_size_bytes,
                }
                for document in documents
            ],
        }

    if agent_name == "policy_retrieval":
        product = (
            db.query(LoanProduct)
            .filter(LoanProduct.id == application.loan_product_id)
            .first()
        )
        return {
            "application": {
                "id": application.id,
                "application_number": application.application_number,
                "requested_amount": application.requested_amount,
                "requested_term_months": application.requested_term_months,
                "employment_status": application.employment_status,
                "employer_name": application.employer_name,
            },
            "loan_product": {
                "id": product.id if product else None,
                "code": product.code if product else None,
                "name": product.name if product else None,
                "min_amount": product.min_amount if product else None,
                "max_amount": product.max_amount if product else None,
                "min_term_months": product.min_term_months if product else None,
                "max_term_months": product.max_term_months if product else None,
                "is_active": product.is_active if product else None,
            },
            "tool_evidence": build_mcp_tool_evidence(
                db,
                application=application,
                agent_name=agent_name,
            ),
        }

    if agent_name == "risk_assessment":
        return {
            "application": {
                "id": application.id,
                "application_number": application.application_number,
                "requested_amount": application.requested_amount,
                "requested_term_months": application.requested_term_months,
            },
            "financials": {
                "monthly_income": application.monthly_income,
                "monthly_expenses": application.monthly_expenses,
                "existing_loan_obligations": application.existing_loan_obligations,
            },
        }

    if agent_name == "fraud_verification":
        applicant = db.query(User).filter(User.id == application.applicant_user_id).first()
        documents = (
            db.query(ApplicationDocument)
            .filter(ApplicationDocument.application_id == application.id)
            .all()
        )
        return {
            "application": {
                "id": application.id,
                "application_number": application.application_number,
                "requested_amount": application.requested_amount,
                "requested_term_months": application.requested_term_months,
                "monthly_income": application.monthly_income,
            },
            "applicant": {
                "id": applicant.id if applicant else None,
                "email": applicant.email if applicant else None,
                "full_name": applicant.full_name if applicant else None,
                "phone_number": application.phone_number
                or (applicant.phone_number if applicant else None),
            },
            "document_metadata": [
                {
                    "document_type": document.document_type,
                    "upload_status": document.upload_status,
                    "mime_type": document.mime_type,
                    "file_size_bytes": document.file_size_bytes,
                }
                for document in documents
            ],
            "tool_evidence": build_mcp_tool_evidence(
                db,
                application=application,
                agent_name=agent_name,
            ),
        }

    if agent_name == "decision_summary":
        return {
            "application": {
                "id": application.id,
                "application_number": application.application_number,
                "requested_amount": application.requested_amount,
                "requested_term_months": application.requested_term_months,
            },
            "worker_outputs": {
                "document_analysis": output_map.get("document_analysis"),
                "policy_retrieval": output_map.get("policy_retrieval"),
                "risk_assessment": output_map.get("risk_assessment"),
                "fraud_verification": output_map.get("fraud_verification"),
            },
        }

    raise ValueError(f"No scoped input builder defined for '{agent_name}'")


def _run_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    return run_structured_agent(
        prompt=prompt,
        scoped_input=scoped_input,
        output_type=output_type,
    )


def _extract_runtime_metadata(
    output: dict[str, Any],
    *,
    prompt: AgentPromptDefinition,
) -> dict[str, Any]:
    runtime_metadata = output.pop("__runtime", {}) if output else {}
    return {
        "model_provider": runtime_metadata.get("model_provider", prompt.model_provider),
        "model_name": runtime_metadata.get("model_name", prompt.model_name),
    }


def execute_autonomous_underwriting_agent(
    db: Session,
    *,
    application: Application,
    agent_name: str,
    output_map: dict[str, dict[str, Any]],
) -> AutonomousAgentExecution:
    prompt = get_agent_prompt_definition(agent_name)
    scoped_input = build_autonomous_agent_input(
        db,
        application=application,
        agent_name=agent_name,
        output_map=output_map,
    )
    output = _run_structured_agent(
        prompt=prompt,
        scoped_input=scoped_input,
        output_type=EvaluationAgentOutput,
    )
    runtime_metadata = _extract_runtime_metadata(output, prompt=prompt)
    output["agent_metadata"] = {
        "agent_name": prompt.agent_name,
        "role": prompt.role,
        "model_provider": runtime_metadata["model_provider"],
        "model_name": runtime_metadata["model_name"],
        "prompt_version": prompt.prompt_version,
        "supports_mcp": prompt.supports_mcp,
        "allowed_tools": list(prompt.allowed_tools),
        "fallback_model_names": list(prompt.fallback_model_names),
        "execution_mode": "autonomous_llm",
    }
    return AutonomousAgentExecution(
        output=output,
        prompt=prompt,
        scoped_input={
            "agent_name": prompt.agent_name,
            "role": prompt.role,
            "model_provider": runtime_metadata["model_provider"],
            "model_name": runtime_metadata["model_name"],
            "prompt_version": prompt.prompt_version,
            "supports_mcp": prompt.supports_mcp,
            "allowed_tools": list(prompt.allowed_tools),
            "fallback_model_names": list(prompt.fallback_model_names),
            "allowed_decisions": list(prompt.allowed_decisions),
            "system_prompt": prompt.system_prompt,
            "input": scoped_input,
        },
        execution_mode="autonomous_llm",
    )


def prompt_registry_snapshot() -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for agent_name, prompt in PROMPT_REGISTRY.items():
        prompt_dict = asdict(prompt)
        prompt_dict["allowed_decisions"] = list(prompt.allowed_decisions)
        prompt_dict["fallback_model_names"] = list(prompt.fallback_model_names)
        prompt_dict["allowed_tools"] = list(prompt.allowed_tools)
        snapshot[agent_name] = prompt_dict

    return snapshot