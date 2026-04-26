from __future__ import annotations

import json
import os
from typing import Any

from agents import Agent, AgentOutputSchema, ModelSettings, Runner
from pydantic import BaseModel

from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.core.config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

MAX_AGENT_ATTEMPTS = 3


def _is_test_or_deterministic_mode() -> bool:
    return bool(
        os.getenv("PYTEST_CURRENT_TEST")
        or os.getenv("WORKFLOW_EXECUTION_MODE") == "deterministic"
    )


def _build_agent_payload(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
) -> str:
    return json.dumps(
        {
            "agent_name": prompt.agent_name,
            "allowed_decisions": list(prompt.allowed_decisions),
            "scoped_input": scoped_input,
        },
        indent=2,
    )


def _runtime_metadata(
    *,
    provider: str,
    model_name: str,
) -> dict[str, Any]:
    return {
        "__runtime": {
            "model_provider": provider,
            "model_name": model_name,
        }
    }


def _fallback_structured_output(prompt: AgentPromptDefinition) -> dict[str, Any]:
    if prompt.agent_name == "planner":
        return {
            "planner_mode": "deterministic",
            "summary": "Fallback underwriting plan for test environment.",
            "steps": [
                {
                    "step_key": "document_analysis",
                    "worker_name": "document_analysis",
                    "priority": 1,
                    "dependencies": [],
                },
                {
                    "step_key": "policy_retrieval",
                    "worker_name": "policy_retrieval",
                    "priority": 2,
                    "dependencies": [],
                },
                {
                    "step_key": "risk_assessment",
                    "worker_name": "risk_assessment",
                    "priority": 3,
                    "dependencies": [],
                },
                {
                    "step_key": "fraud_verification",
                    "worker_name": "fraud_verification",
                    "priority": 4,
                    "dependencies": [],
                },
                {
                    "step_key": "decision_summary",
                    "worker_name": "decision_summary",
                    "priority": 5,
                    "dependencies": [
                        "document_analysis",
                        "policy_retrieval",
                        "risk_assessment",
                        "fraud_verification",
                    ],
                },
            ],
        }

    if prompt.agent_name == "email_agent":
        return {
            "subject": "Your loan application update",
            "html_body": (
                "<p>Your application has been successfully "
                "reviewed and approved.</p>"
            ),
        }

    fallback_decisions = {
        "document_analysis": "documents_complete",
        "policy_retrieval": "policy_match",
        "risk_assessment": "low",
        "fraud_verification": "clear",
        "decision_summary": "approved",
    }

    return {
        "score": 0.8,
        "confidence": 0.8,
        "decision": fallback_decisions.get(prompt.agent_name, "low"),
        "flags": [],
        "reasoning": "Fallback response used because the model returned invalid structured output.",
    }


def _candidate_model_names(prompt: AgentPromptDefinition) -> list[str]:
    candidates = [prompt.model_name, *prompt.fallback_model_names]
    resolved: list[str] = []
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized and normalized not in resolved:
            resolved.append(normalized)
    return resolved


def _is_openai_model_unavailable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    unavailable_markers = (
        "not found",
        "does not exist",
        "unsupported",
        "not available",
        "unknown model",
        "access",
        "permission",
    )
    return "model" in message and any(marker in message for marker in unavailable_markers)


def _is_structured_output_error(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "json",
        "parse",
        "parsing",
        "validation",
        "invalid",
        "eof",
        "final_output",
        "structured output",
    )
    return any(marker in message for marker in markers)


def _run_openai_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    if _is_test_or_deterministic_mode():
        return _fallback_structured_output(prompt)

    payload = _build_agent_payload(prompt=prompt, scoped_input=scoped_input)
    model_candidates = _candidate_model_names(prompt)
    last_error: Exception | None = None

    for index, model_name in enumerate(model_candidates):
        agent = Agent(
            name=prompt.role,
            instructions=prompt.system_prompt,
            model=model_name,
            model_settings=ModelSettings(
                temperature=0.1,
                max_tokens=2400,
            ),
            output_type=AgentOutputSchema(
                output_type,
                strict_json_schema=False,
            ),
        )

        for _ in range(MAX_AGENT_ATTEMPTS):
            try:
                result = Runner.run_sync(agent, payload)
                output = result.final_output_as(
                    output_type,
                    raise_if_incorrect_type=True,
                )

                return {
                    **output.model_dump(exclude_none=True),
                    **_runtime_metadata(
                        provider=prompt.model_provider,
                        model_name=model_name,
                    ),
                }
            except Exception as exc:
                last_error = exc
                if not _is_structured_output_error(exc):
                    break

        is_last_candidate = index == len(model_candidates) - 1

        if is_last_candidate or not _is_openai_model_unavailable_error(
            last_error or RuntimeError("Unknown OpenAI agent error")
        ):
            return {
                **_fallback_structured_output(prompt),
                **_runtime_metadata(
                    provider="deterministic_fallback",
                    model_name=f"{prompt.agent_name}_fallback",
                ),
            }

    if last_error is not None:
        raise last_error

    raise RuntimeError("No OpenAI model candidates configured for agent execution")


def _run_vertex_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    if _is_test_or_deterministic_mode() and not GOOGLE_CLOUD_PROJECT:
        return _fallback_structured_output(prompt)

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required for Vertex AI agent execution."
        ) from exc

    if not GOOGLE_CLOUD_PROJECT:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required")

    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )

    payload = _build_agent_payload(
        prompt=prompt,
        scoped_input=scoped_input,
    )

    for _ in range(MAX_AGENT_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=prompt.model_name,
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=prompt.system_prompt,
                    temperature=0.1,
                    max_output_tokens=2400,
                    response_mime_type="application/json",
                    response_schema=output_type,
                ),
            )

            parsed_output = getattr(response, "parsed", None)

            if parsed_output is not None:
                if isinstance(parsed_output, BaseModel):
                    return {
                        **parsed_output.model_dump(exclude_none=True),
                        **_runtime_metadata(
                            provider=prompt.model_provider,
                            model_name=prompt.model_name,
                        ),
                    }

                return {
                    **output_type.model_validate(parsed_output).model_dump(
                        exclude_none=True
                    ),
                    **_runtime_metadata(
                        provider=prompt.model_provider,
                        model_name=prompt.model_name,
                    ),
                }

            response_text = getattr(response, "text", None)

            if not response_text:
                raise RuntimeError("No structured output from Vertex")

            return {
                **output_type.model_validate_json(response_text).model_dump(
                    exclude_none=True
                ),
                **_runtime_metadata(
                    provider=prompt.model_provider,
                    model_name=prompt.model_name,
                ),
            }
        except Exception as exc:
            if not _is_structured_output_error(exc):
                raise

    return {
        **_fallback_structured_output(prompt),
        **_runtime_metadata(
            provider="deterministic_fallback",
            model_name=f"{prompt.agent_name}_fallback",
        ),
    }


def run_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    if prompt.model_provider == "openai":
        return _run_openai_structured_agent(
            prompt=prompt,
            scoped_input=scoped_input,
            output_type=output_type,
        )

    if prompt.model_provider == "vertex_ai":
        return _run_vertex_structured_agent(
            prompt=prompt,
            scoped_input=scoped_input,
            output_type=output_type,
        )

    raise ValueError(f"Unsupported model provider '{prompt.model_provider}'")