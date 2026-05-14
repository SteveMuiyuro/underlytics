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
        lambda **kwargs: {
            "decision": "approved",
            "__runtime": {"model_name": "gpt-test", "model_provider": "openai"},
        },
    )

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert result["decision"] == "approved"
    assert result["__runtime"]["model_name"] == "gpt-test"


def test_run_structured_agent_dispatches_vertex(monkeypatch):
    prompt = make_prompt(provider="vertex_ai", model_name="gemini-test")

    monkeypatch.setattr(
        agent_runtime_service,
        "_run_vertex_structured_agent",
        lambda **kwargs: {
            "decision": "approved",
            "__runtime": {"model_name": "gemini-test", "model_provider": "vertex_ai"},
        },
    )

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert result["decision"] == "approved"
    assert result["__runtime"]["model_name"] == "gemini-test"


def test_run_structured_agent_falls_back_to_next_openai_model(monkeypatch):
    prompt = make_prompt(provider="openai", model_name="gpt-5.4")
    prompt = AgentPromptDefinition(
        agent_name=prompt.agent_name,
        role=prompt.role,
        model_provider=prompt.model_provider,
        model_name=prompt.model_name,
        prompt_version=prompt.prompt_version,
        allowed_decisions=prompt.allowed_decisions,
        system_prompt=prompt.system_prompt,
        fallback_model_names=("gpt-5.3", "gpt-5.2"),
    )

    attempted_models: list[str] = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.model = kwargs["model"]

    class FakeResult:
        def final_output_as(self, output_type, raise_if_incorrect_type=True):
            return output_type(
                score=0.8,
                confidence=0.9,
                decision="approved",
                flags=[],
                reasoning="fallback worked",
            )

    def fake_run_sync(agent, payload):
        attempted_models.append(agent.model)
        if agent.model == "gpt-5.4":
            raise RuntimeError("Model gpt-5.4 does not exist for this project")
        return FakeResult()

    monkeypatch.setattr(
        agent_runtime_service,
        "_is_test_or_deterministic_mode",
        lambda: False,
    )
    monkeypatch.setattr(agent_runtime_service, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(agent_runtime_service, "Agent", FakeAgent)
    monkeypatch.setattr(agent_runtime_service.Runner, "run_sync", fake_run_sync)

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert attempted_models == ["gpt-5.4", "gpt-5.3"]
    assert result["decision"] == "approved"
    assert result["__runtime"]["model_name"] == "gpt-5.3"


def test_run_structured_agent_tries_next_model_after_structured_output_failure(monkeypatch):
    prompt = make_prompt(provider="openai", model_name="gpt-5.4")
    prompt = AgentPromptDefinition(
        agent_name=prompt.agent_name,
        role=prompt.role,
        model_provider=prompt.model_provider,
        model_name=prompt.model_name,
        prompt_version=prompt.prompt_version,
        allowed_decisions=prompt.allowed_decisions,
        system_prompt=prompt.system_prompt,
        fallback_model_names=("gpt-5.3",),
    )

    attempted_models: list[str] = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.model = kwargs["model"]

    class InvalidStructuredResult:
        def final_output_as(self, output_type, raise_if_incorrect_type=True):
            raise RuntimeError("Invalid structured output: expected JSON object")

    class ValidStructuredResult:
        def final_output_as(self, output_type, raise_if_incorrect_type=True):
            return output_type(
                score=0.84,
                confidence=0.87,
                decision="approved",
                flags=[],
                reasoning="Fallback model returned valid structured output.",
            )

    def fake_run_sync(agent, payload):
        attempted_models.append(agent.model)
        if agent.model == "gpt-5.4":
            return InvalidStructuredResult()
        return ValidStructuredResult()

    monkeypatch.setattr(agent_runtime_service, "_is_test_or_deterministic_mode", lambda: False)
    monkeypatch.setattr(agent_runtime_service, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(agent_runtime_service, "Agent", FakeAgent)
    monkeypatch.setattr(agent_runtime_service.Runner, "run_sync", fake_run_sync)

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert attempted_models == ["gpt-5.4", "gpt-5.4", "gpt-5.4", "gpt-5.3"]
    assert result["decision"] == "approved"
    assert result["__runtime"]["model_name"] == "gpt-5.3"


def test_run_structured_agent_uses_deterministic_fallback_only_after_all_models_fail_schema(
    monkeypatch,
):
    prompt = make_prompt(provider="openai", model_name="gpt-5.4")
    prompt = AgentPromptDefinition(
        agent_name="decision_summary",
        role=prompt.role,
        model_provider=prompt.model_provider,
        model_name=prompt.model_name,
        prompt_version=prompt.prompt_version,
        allowed_decisions=("approved", "rejected", "manual_review"),
        system_prompt=prompt.system_prompt,
        fallback_model_names=("gpt-5.3",),
    )

    attempted_models: list[str] = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.model = kwargs["model"]

    class InvalidStructuredResult:
        def final_output_as(self, output_type, raise_if_incorrect_type=True):
            raise RuntimeError("JSON validation failed for structured output")

    def fake_run_sync(agent, payload):
        attempted_models.append(agent.model)
        return InvalidStructuredResult()

    monkeypatch.setattr(agent_runtime_service, "_is_test_or_deterministic_mode", lambda: False)
    monkeypatch.setattr(agent_runtime_service, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(agent_runtime_service, "Agent", FakeAgent)
    monkeypatch.setattr(agent_runtime_service.Runner, "run_sync", fake_run_sync)

    result = agent_runtime_service.run_structured_agent(
        prompt=prompt,
        scoped_input={"value": 1},
        output_type=EvaluationAgentOutput,
    )

    assert attempted_models == ["gpt-5.4", "gpt-5.4", "gpt-5.4", "gpt-5.3", "gpt-5.3", "gpt-5.3"]
    assert result["decision"] == "approved"
    assert result["__runtime"]["model_provider"] == "deterministic_fallback"
    assert result["__runtime"]["model_name"] == "decision_summary_fallback"


def test_run_structured_agent_raises_clear_error_when_openai_key_missing(monkeypatch):
    prompt = make_prompt(provider="openai", model_name="gpt-5.4")

    monkeypatch.setattr(agent_runtime_service, "_is_test_or_deterministic_mode", lambda: False)
    monkeypatch.setattr(agent_runtime_service, "OPENAI_API_KEY", None)

    try:
        agent_runtime_service.run_structured_agent(
            prompt=prompt,
            scoped_input={"value": 1},
            output_type=EvaluationAgentOutput,
        )
    except RuntimeError as exc:
        assert str(exc) == "OPENAI_API_KEY is required for OpenAI structured agent execution"
    else:
        raise AssertionError("Expected RuntimeError when OPENAI_API_KEY is missing")


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
