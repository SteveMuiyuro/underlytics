from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.schemas.agent_execution import EvaluationAgentOutput
from underlytics_api.services import agent_runtime_service


def make_prompt(*, provider: str, model_name: str = "test-model") -> AgentPromptDefinition:
    return AgentPromptDefinition(
        agent_name="test_agent",
        role="Test Agent",
        model_provider=provider,
        model_name=model_name,
        prompt_version="v1",
        allowed_decisions=("approved",),
        system_prompt="Return valid JSON.",
    )


def test_run_structured_agent_dispatches_openai(monkeypatch):
    prompt = make_prompt(provider="openai", model_name="gpt-test")

    monkeypatch.setattr(
        agent_runtime_service,
        "_run_openai_structured_agent",
        lambda **kwargs: {"decision": "approved"},
    )

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert result["decision"] == "approved"


def test_run_structured_agent_dispatches_vertex(monkeypatch):
    prompt = make_prompt(provider="vertex_ai", model_name="gemini-test")

    monkeypatch.setattr(
        agent_runtime_service,
        "_run_vertex_structured_agent",
        lambda **kwargs: {"decision": "approved"},
    )

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert result["decision"] == "approved"


def test_run_structured_agent_rejects_unknown_provider():
    prompt = make_prompt(provider="unknown_provider")

    try:
        agent_runtime_service.run_structured_agent(
            prompt=prompt,
            scoped_input={"value": 1},
            output_type=EvaluationAgentOutput,
        )
    except ValueError as exc:
        assert "Unsupported model provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported provider")
