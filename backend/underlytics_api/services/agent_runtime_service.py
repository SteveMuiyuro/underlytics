from __future__ import annotations

import json
from typing import Any

from agents import Agent, ModelSettings, Runner
from pydantic import BaseModel

from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.core.config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT


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


def _run_openai_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    agent = Agent(
        name=prompt.role,
        instructions=prompt.system_prompt,
        model=prompt.model_name,
        model_settings=ModelSettings(
            temperature=0.15,
            max_tokens=1400,
        ),
        output_type=output_type,
    )
    result = Runner.run_sync(
        agent,
        _build_agent_payload(prompt=prompt, scoped_input=scoped_input),
    )
    output = result.final_output_as(output_type, raise_if_incorrect_type=True)
    return output.model_dump(exclude_none=True)


def _run_vertex_structured_agent(
    *,
    prompt: AgentPromptDefinition,
    scoped_input: dict[str, Any],
    output_type: type[BaseModel],
) -> dict[str, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required for Vertex AI agent execution. "
            "Install backend dependencies to enable Gemini runtime support."
        ) from exc

    if not GOOGLE_CLOUD_PROJECT:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Vertex AI agent execution")

    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )
    response = client.models.generate_content(
        model=prompt.model_name,
        contents=_build_agent_payload(prompt=prompt, scoped_input=scoped_input),
        config=types.GenerateContentConfig(
            system_instruction=prompt.system_prompt,
            temperature=0.15,
            max_output_tokens=1400,
            response_mime_type="application/json",
            response_schema=output_type,
        ),
    )

    parsed_output = getattr(response, "parsed", None)
    if parsed_output is not None:
        if isinstance(parsed_output, BaseModel):
            return parsed_output.model_dump(exclude_none=True)
        return output_type.model_validate(parsed_output).model_dump(exclude_none=True)

    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError(
            f"Vertex AI agent '{prompt.agent_name}' returned no structured output"
        )

    return output_type.model_validate_json(response_text).model_dump(exclude_none=True)


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

    raise ValueError(
        f"Unsupported model provider '{prompt.model_provider}' for '{prompt.agent_name}'"
    )
