# Underlytics Refactor: Implement Pydantic Structured Outputs for Agents and Guardrails

## Objective

Refactor the Underlytics AI underwriting system so that all agents and guardrails use strongly typed Pydantic structured outputs instead of loose JSON dictionaries.

The goal is to improve reliability, validation, type safety, observability, frontend/backend consistency, and safer downstream processing.

This must be implemented as a safe compatibility-focused refactor that does not break existing functionality.

---

# Critical Requirement: Do Not Break Existing Functionality

This is not a rewrite.

Codex must preserve:

- Existing API contracts
- Existing frontend behavior
- Existing workflow orchestration
- Existing database behavior
- Existing authentication flow
- Existing event streaming behavior
- Existing tests
- Existing route names
- Existing environment variable names
- Existing public response fields

The application must continue functioning exactly as before from the user perspective.

---

# Mandatory Test Execution Requirement

Codex must run the full test suite after implementation and must not mark the task as complete until all relevant checks pass.

After making changes, Codex must run backend checks such as:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If the project has a frontend, Codex must also run the frontend checks from the frontend directory, such as:

```bash
npm run lint
npm run typecheck
npm run build
```

If the exact commands differ in this repository, Codex must inspect:

- `pyproject.toml`
- `package.json`
- GitHub Actions workflows
- Existing README instructions

Then use the correct project-specific test and validation commands.

Codex must report:

- Which commands were run
- Which commands passed
- Any failures encountered
- What was fixed
- Any checks that could not be run and why

The task is not complete unless:

- Existing tests pass
- New tests pass
- Linting passes
- Type checks pass
- Frontend build still succeeds where applicable

Codex must not only add tests. It must execute them and confirm the implementation does not break the project.

---

# Required Implementation Strategy

## 1. Inspect Existing Architecture First

Before changing anything, inspect:

- All agent implementations
- All guardrail implementations
- Orchestration flow
- API response shapes
- Frontend expectations
- Database models
- SSE/event streaming logic
- Existing tests
- Existing CI/CD workflows

Identify:

- Where raw JSON is currently returned
- Where downstream systems rely on dictionary keys
- Which response fields are required by frontend rendering
- Which tests currently protect the existing behavior

Do not change field names unnecessarily.

---

# Refactor Rules

## Safe Refactor Principles

Codex must:

- Make small incremental changes
- Convert one agent at a time
- Avoid large rewrites
- Preserve current behavior
- Preserve response shape compatibility
- Add compatibility adapters where needed
- Prefer additive changes before removals
- Keep deterministic business logic outside LLM outputs
- Avoid unrelated cleanup or styling changes
- Avoid modifying files unrelated to this refactor

---

# Pydantic Migration Requirements

## Replace Loose JSON With Typed Models

Current anti-pattern example:

```python
return {
    "risk_score": 82,
    "decision": "manual_review",
    "reason": "High DTI",
}
```

Target pattern:

```python
from typing import Literal
from pydantic import BaseModel, Field


class RiskAssessmentOutput(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    decision: Literal["approved", "rejected", "manual_review"]
    reason: str


return RiskAssessmentOutput(
    risk_score=82,
    decision="manual_review",
    reason="High DTI",
)
```

Where API or frontend code still expects dictionaries, convert using:

```python
risk_result.model_dump()
```

---

# Required Folder Structure

If not already present, introduce a dedicated schema layer.

Suggested structure:

```text
backend/app/schemas/
    agents/
    guardrails/
    api/
```

Example files:

```text
backend/app/schemas/agents/document_analysis.py
backend/app/schemas/agents/risk_assessment.py
backend/app/schemas/agents/fraud_detection.py
backend/app/schemas/agents/policy_validation.py
backend/app/schemas/guardrails/decision_guardrail.py
backend/app/schemas/api/underwriting.py
```

Use the existing project structure if it already has a better convention. Do not force a new structure if it would break imports or create unnecessary churn.

---

# Required Pydantic Models

The exact fields should be aligned with the existing project’s current outputs. Preserve current field names wherever possible.

## Document Analysis Agent

Create structured outputs for:

- Extracted applicant information
- Income analysis
- Employment verification
- Missing documents
- Confidence scores

Example:

```python
from pydantic import BaseModel, Field


class EmploymentInfo(BaseModel):
    employer_name: str | None = None
    employment_status: str | None = None
    monthly_income: float | None = Field(default=None, ge=0)
    years_employed: float | None = Field(default=None, ge=0)


class DocumentAnalysisOutput(BaseModel):
    applicant_name: str | None = None
    employment: EmploymentInfo | None = None
    missing_documents: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    summary: str
```

---

## Risk Assessment Agent

Create structured outputs for:

- Risk score
- Debt-to-income ratio
- Affordability classification
- Risk factors
- Recommended decision
- Reasoning

Example:

```python
from typing import Literal
from pydantic import BaseModel, Field


class RiskAssessmentOutput(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    debt_to_income_ratio: float | None = Field(default=None, ge=0)
    affordability: Literal["low", "medium", "high"]
    risk_factors: list[str] = Field(default_factory=list)
    recommended_decision: Literal["approved", "manual_review", "rejected"]
    reasoning: str
```

---

## Fraud Detection Agent

Create structured outputs for:

- Fraud status
- Fraud signals
- Identity match score
- Recommendation
- Explanation

Example:

```python
from typing import Literal
from pydantic import BaseModel, Field


class FraudDetectionOutput(BaseModel):
    fraud_detected: bool
    fraud_signals: list[str] = Field(default_factory=list)
    identity_match_score: float = Field(ge=0, le=1)
    recommendation: Literal["clear", "manual_review", "block"]
    explanation: str
```

---

## Policy Validation Agent

Create structured outputs for:

- Policy pass/fail status
- Violated rules
- Manual review triggers
- Recommendation
- Explanation

Example:

```python
from typing import Literal
from pydantic import BaseModel, Field


class PolicyValidationOutput(BaseModel):
    policy_passed: bool
    violated_rules: list[str] = Field(default_factory=list)
    manual_review_triggers: list[str] = Field(default_factory=list)
    recommendation: Literal["approved", "manual_review", "rejected"]
    explanation: str
```

---

## Final Underwriting Decision

Create a structured output for the final decision summary.

Example:

```python
from typing import Literal
from pydantic import BaseModel, Field


class UnderwritingDecisionOutput(BaseModel):
    application_id: str
    final_decision: Literal["approved", "manual_review", "rejected"]
    confidence: float = Field(ge=0, le=1)
    summary: str
    contributing_factors: list[str] = Field(default_factory=list)
    risk_score: int = Field(ge=0, le=100)
    guardrail_overrides: list[str] = Field(default_factory=list)
```

---

# Guardrail Refactor Requirements

Guardrails must also use Pydantic models.

Example:

```python
from typing import Literal
from pydantic import BaseModel, Field


class GuardrailResult(BaseModel):
    allowed: bool
    original_decision: Literal["approved", "manual_review", "rejected"] | None = None
    final_decision: Literal["approved", "manual_review", "rejected"]
    violations: list[str] = Field(default_factory=list)
    escalation_required: bool
    explanation: str
```

---

# Deterministic Logic Rules

LLMs must never directly decide approval or rejection without deterministic validation.

Guardrails must validate:

- Affordability thresholds
- Policy limits
- Fraud thresholds
- Required documents
- Missing or inconsistent applicant information
- Risk score thresholds
- Manual review triggers

Guardrails must override unsafe LLM outputs.

The final approval logic must remain deterministic Python logic.

---

# OpenAI / LLM Structured Output Integration

Where supported, use structured outputs directly.

Preferred pattern:

```python
response = client.responses.parse(
    model="gpt-5",
    input=prompt,
    text_format=RiskAssessmentOutput,
)
```

Or use the equivalent structured-output feature for the current SDK already used in the project.

Avoid:

- `json.loads()` for LLM output where structured outputs are supported
- Manual dictionary parsing
- Regex extraction
- Unsafe parsing logic
- Trusting unvalidated LLM output

If the current SDK does not support direct Pydantic parsing, then parse the model response and immediately validate it with the appropriate Pydantic model before downstream use.

---

# Validation Requirements

Every agent response must:

- Validate through Pydantic
- Fail safely on invalid output
- Log validation failures
- Return controlled fallback behavior
- Avoid passing invalid data to downstream services

Example:

```python
from pydantic import ValidationError


try:
    result = RiskAssessmentOutput.model_validate(data)
except ValidationError:
    logger.exception("Invalid risk assessment output")
    return RiskAssessmentOutput(
        risk_score=100,
        debt_to_income_ratio=None,
        affordability="high",
        risk_factors=["Invalid AI output"],
        recommended_decision="manual_review",
        reasoning="The risk assessment output could not be validated, so the application requires manual review.",
    )
```

---

# Fallback Rules

If an agent output fails validation:

- Do not crash the full underwriting workflow
- Do not approve the application
- Prefer `manual_review`
- Log the error
- Include enough context for debugging without exposing sensitive data
- Continue the workflow safely where possible

---

# Backward Compatibility Requirement

This is mandatory.

If frontend or downstream systems expect JSON:

- Convert models using `.model_dump()`
- Preserve current response fields
- Preserve current naming conventions
- Preserve current nesting where possible
- Preserve SSE event payload shapes where possible

Example:

```python
return risk_result.model_dump()
```

Do not break:

- Existing frontend rendering
- Existing API consumers
- Existing database writes
- Existing SSE streams
- Existing audit log formatting

If a new Pydantic model has cleaner internal names but the frontend expects older names, add a compatibility mapping layer.

---

# API Layer Requirements

FastAPI endpoints should use typed response models where practical.

Example:

```python
@router.post(
    "/underwrite",
    response_model=UnderwritingDecisionOutput,
)
async def underwrite_application():
    ...
```

Only introduce response models if they do not break existing response behavior.

If current endpoints return a wider compatibility object, create a response model that matches the existing API shape instead of forcing a new shape.

---

# Frontend Compatibility Rules

The frontend must continue functioning without modification wherever possible.

Do not:

- Rename fields unnecessarily
- Change payload nesting unnecessarily
- Remove fields currently rendered by the UI
- Break TypeScript types
- Break SSE parsing
- Break dashboard cards, decision summaries, or application detail pages

If needed:

- Add temporary compatibility mapping layers
- Update frontend types only where necessary
- Ensure existing UI still renders correctly

---

# Database Compatibility Rules

Do not change database schema unless absolutely necessary.

Do not:

- Rename columns
- Drop columns
- Change enum values
- Change persisted JSON shape unless compatibility is maintained
- Introduce migrations unless required

If structured outputs are stored as JSON, store `.model_dump()` output and preserve existing keys.

---

# Logging & Observability

Enhance observability using structured logging.

Required logging points:

- Agent validation failures
- Guardrail overrides
- Fallback behavior
- Schema mismatch issues
- Final decision synthesis
- Manual review escalation

Example:

```python
logger.info(
    "guardrail_override",
    extra={
        "original_decision": "approved",
        "final_decision": "manual_review",
        "reason": "Affordability threshold exceeded",
    },
)
```

Do not log sensitive applicant data unnecessarily.

---

# Testing Requirements

Codex must add tests and run tests.

Before refactoring:

- Run existing backend tests
- Note the baseline result

After refactoring:

- Run all existing backend tests
- Run all new backend tests
- Run linting
- Run formatting check
- Run frontend checks if the project has a frontend

---

# Required Test Coverage

Add tests for the new Pydantic structured outputs.

## Agent Validation Tests

Test valid agent output:

```python
def test_risk_assessment_output_validation():
    ...
```

## Invalid Output Tests

Test invalid output fails safely:

```python
def test_invalid_agent_output_falls_back_to_manual_review():
    ...
```

## Guardrail Tests

Test guardrail overrides unsafe approval:

```python
def test_guardrail_overrides_unsafe_approval():
    ...
```

## API Compatibility Tests

Test API response shape remains compatible:

```python
def test_underwriting_api_response_shape_unchanged():
    ...
```

## Serialization Tests

Test `.model_dump()` output works as expected:

```python
def test_structured_output_serializes_to_expected_shape():
    ...
```

---

# Commands Codex Must Run

Codex must determine the correct commands for this repo.

At minimum, try backend commands such as:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If frontend exists, run from the frontend directory:

```bash
npm run lint
npm run typecheck
npm run build
```

If the repo uses different commands, inspect project files and use the correct ones.

---

# CI/CD Requirements

Codex must ensure:

- Backend tests pass
- New tests pass
- Ruff passes
- Formatting check passes
- Frontend lint passes where applicable
- Frontend typecheck passes where applicable
- Frontend build passes where applicable
- No circular imports are introduced
- GitHub Actions should still pass

---

# Migration Strategy

## Phase 1: Baseline

- Inspect current architecture
- Run current tests
- Record current behavior and response shapes

## Phase 2: Schema Introduction

- Add Pydantic models
- Do not change runtime behavior yet
- Add serialization tests

## Phase 3: Agent Refactor

- Convert one agent at a time
- Validate output through Pydantic
- Preserve `.model_dump()` compatibility where needed

## Phase 4: Guardrail Refactor

- Convert guardrails to Pydantic models
- Keep deterministic override logic
- Add guardrail tests

## Phase 5: API Compatibility

- Add FastAPI response models where safe
- Preserve existing API response shape
- Add API regression tests

## Phase 6: Frontend Verification

- Confirm frontend types still match API responses
- Run lint, typecheck, and build

## Phase 7: Final Validation

- Run all backend tests
- Run all frontend checks
- Fix regressions
- Report final command results

---

# Important Anti-Patterns To Avoid

Do not:

- Rewrite the architecture
- Change unrelated files
- Rename APIs unnecessarily
- Rename environment variables
- Change authentication behavior
- Change frontend payload shapes unnecessarily
- Remove existing fields
- Replace deterministic rules with AI decisions
- Use raw JSON parsing if structured outputs are available
- Introduce large unreviewable commits
- Mark the task complete without running tests
- Claim tests pass without running them

---

# Completion Criteria

The task is only complete when:

- Existing functionality still works
- Existing tests pass
- New tests pass
- Agents use Pydantic structured outputs
- Guardrails use Pydantic structured outputs
- Validation failures are safely handled
- API compatibility is preserved
- Frontend still renders correctly
- Backend linting passes
- Formatting check passes
- Frontend lint/typecheck/build pass where applicable
- No regressions are introduced
- Codex reports the exact commands executed and their results

---

# Final Deliverables

Codex should produce:

1. Pydantic schema files
2. Refactored agent implementations
3. Refactored guardrail implementations
4. Updated API response models where safe
5. Validation handling and safe fallbacks
6. Regression tests
7. Structured logging improvements
8. Minimal compatibility adapters if needed
9. Summary of all modified files
10. Exact test/check commands run and their results

---

# Final Instruction To Codex

Implement Pydantic structured outputs for Underlytics agents and guardrails as a safe compatibility-focused refactor.

Do not break existing behavior.

Do not change user-facing API shapes unless absolutely necessary.

Run all relevant backend and frontend tests/checks after implementation.

Do not mark the task complete until all tests and checks pass, or clearly explain any command that could not be run and why.