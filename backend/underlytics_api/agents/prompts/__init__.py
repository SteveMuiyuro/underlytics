from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.agents.prompts.decision_summary_prompt import PROMPT as DECISION_SUMMARY_PROMPT
from underlytics_api.agents.prompts.document_analysis_prompt import (
    PROMPT as DOCUMENT_ANALYSIS_PROMPT,
)
from underlytics_api.agents.prompts.email_agent_prompt import PROMPT as EMAIL_AGENT_PROMPT
from underlytics_api.agents.prompts.fraud_verification_prompt import (
    PROMPT as FRAUD_VERIFICATION_PROMPT,
)
from underlytics_api.agents.prompts.planner_prompt import PROMPT as PLANNER_PROMPT
from underlytics_api.agents.prompts.policy_retrieval_prompt import PROMPT as POLICY_RETRIEVAL_PROMPT
from underlytics_api.agents.prompts.risk_assessment_prompt import PROMPT as RISK_ASSESSMENT_PROMPT

PROMPT_REGISTRY: dict[str, AgentPromptDefinition] = {
    PLANNER_PROMPT.agent_name: PLANNER_PROMPT,
    DOCUMENT_ANALYSIS_PROMPT.agent_name: DOCUMENT_ANALYSIS_PROMPT,
    POLICY_RETRIEVAL_PROMPT.agent_name: POLICY_RETRIEVAL_PROMPT,
    RISK_ASSESSMENT_PROMPT.agent_name: RISK_ASSESSMENT_PROMPT,
    FRAUD_VERIFICATION_PROMPT.agent_name: FRAUD_VERIFICATION_PROMPT,
    DECISION_SUMMARY_PROMPT.agent_name: DECISION_SUMMARY_PROMPT,
    EMAIL_AGENT_PROMPT.agent_name: EMAIL_AGENT_PROMPT,
}
