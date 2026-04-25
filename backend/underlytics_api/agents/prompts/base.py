from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPromptDefinition:
    agent_name: str
    role: str
    model_provider: str
    model_name: str
    prompt_version: str
    allowed_decisions: tuple[str, ...]
    system_prompt: str
    fallback_model_names: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    supports_mcp: bool = False
