# AGENTS.md

## Purpose

This document defines the architecture, behavior, implementation rules, and UX requirements for the Underlytics agent system.

Underlytics is an AI-powered loan underwriting platform. The system must be explainable, auditable, modular, safe under failure, deterministic where required, and ready for future LLM and MCP expansion.

Codex must preserve the planner-worker architecture and must not collapse the system into a single LLM call.

---

# 1. Core Architecture

Underlytics uses a Planner + Worker architecture.

```text
Application
  ↓
Planner Agent
  ↓
Independent Worker Agents
  ↓
Structured Outputs
  ↓
Decision Summary Agent
  ↓
Guardrails
  ↓
Final Decision
  ↓
Email Agent
  ↓
Notification Service
```

## Core Rules

Codex must preserve these rules:

- The Planner Agent orchestrates workflow execution.
- Worker Agents perform isolated specialist checks.
- Worker Agents do not share hidden state.
- Worker Agents do not make final approval or rejection decisions.
- The Decision Summary Agent proposes a decision.
- Guardrails enforce the final decision.
- Email Agent generates applicant-facing content only.
- Notification Service sends emails.
- LLM output must never directly approve an application without guardrail validation.

---

# Provider Architecture

Underlytics should use a provider-agnostic agent runtime.

Target provider split:

- `planner` → Vertex AI `gemini-2.5-flash`
- `document_analysis` → Vertex AI `gemini-2.5-flash`
- `policy_retrieval` → Vertex AI `gemini-2.5-flash`
- `risk_assessment` → Vertex AI `gemini-2.5-flash`
- `fraud_verification` → Vertex AI `gemini-2.5-flash`
- `decision_summary` → OpenAI `gpt-5.4`
- `email_agent` → Vertex AI `gemini-2.5-flash-lite` or OpenAI `gpt-5.4-mini`

Rules:

- Keep the runtime provider-agnostic so models can be swapped without rewriting workflow logic.
- Use Vertex AI as the default platform for orchestration and specialist workers.
- Use OpenAI for the Decision Summary Agent unless evaluation data shows a clearly better alternative.
- Do not let model-provider choice alter the output contract, guardrails, or audit trail.
- Do not silently fall back to deterministic agent reasoning once a live agent path is enabled.
- If an agent call fails, retry within policy or route to manual review / workflow failure.

# 2. Required Agent Identifiers

Use these stable identifiers everywhere:

```text
planner
document_analysis
policy_retrieval
risk_assessment
fraud_verification
decision_summary
email_agent
```

These identifiers must be consistent across:

- database records
- API responses
- frontend processing UI
- logs
- Langfuse traces
- workflow status endpoint

---

# 3. Agent Roles

## 3.1 Planner Agent

The Planner Agent is responsible for orchestration only.

### Responsibilities

- Create underwriting jobs.
- Trigger required worker agents.
- Track workflow state.
- Track retries and failures.
- Ensure all required workers run.
- Trigger the Decision Summary Agent.
- Store workflow status for frontend polling.

### Must Not Do

- Approve applications.
- Reject applications.
- Bypass guardrails.
- Contain final decision logic.
- Replace specialist workers.

---

## 3.2 Worker Agents

Worker Agents are specialized evaluators.

Each worker must:

- Receive scoped input.
- Perform one task.
- Return structured JSON.
- Store its output.
- Be stateless.
- Support async execution later.

Worker Agents must not:

- Approve or reject applications directly.
- Modify other worker outputs.
- Depend on hidden in-memory state.
- Assume other workers’ results unless explicitly passed.

---

# 4. Worker Definitions

## 4.1 Document Analysis Worker

### Purpose

Validate required documents.

### Inputs

- Uploaded documents.
- Required document list.

### Allowed Decisions

```text
documents_complete
documents_missing
```

### Rules

- Missing documents must prevent approval.
- Unreadable documents must be flagged.
- Missing or unreadable documents should route to manual review.

---

## 4.2 Policy Retrieval Worker

### Purpose

Validate the application against loan product policy.

### Inputs

- Loan product.
- Requested amount.
- Requested term.

### Allowed Decisions

```text
policy_match
policy_mismatch
```

### Rules

- Policy mismatch must prevent approval.
- Missing policy should route to manual review.
- Policy uncertainty must lower confidence.

---

## 4.3 Risk Assessment Worker

### Purpose

Evaluate affordability risk.

### Inputs

- Income.
- Expenses.
- Existing obligations.
- Requested loan amount.
- Requested loan term.

### Allowed Decisions

```text
low
medium
high
```

### Rules

- Low risk may proceed if other checks pass.
- Medium risk must route to manual review.
- High risk should normally reject unless manually overridden by a reviewer.

---

## 4.4 Fraud Verification Worker

### Purpose

Detect anomalies and suspicious signals.

### Inputs

- Application data.
- Applicant profile.
- Document metadata.

### Allowed Decisions

```text
clear
suspicious
```

### Rules

- Suspicious cases must not auto-approve.
- Suspicious cases should route to manual review.
- Uncertainty must lower confidence.

---

## 4.5 Decision Summary Agent

### Purpose

Aggregate worker outputs and propose a final decision.

### Inputs

- Application data.
- Document Analysis output.
- Policy Retrieval output.
- Risk Assessment output.
- Fraud Verification output.

### Allowed Decisions

```text
approved
rejected
manual_review
```

### Rules

- The decision is proposed only.
- Guardrails enforce the final outcome.
- The agent must explain reasoning clearly.
- The agent must not override hard policy constraints.
- The agent must not approve if required workers failed.

---

## 4.6 Email Agent

### Purpose

Generate applicant-facing communication.

### Inputs

- Final decision.
- Worker outputs.
- Applicant details.
- Reviewer note, if available.
- Reviewer decision, if available.

### Outputs

```json
{
  "subject": "Your Underlytics application update",
  "body": "Clear applicant-facing message..."
}
```

### Rules

- Email Agent generates content only.
- Email Agent must not send emails.
- Notification Service sends emails.
- Do not expose internal jargon, raw system data, hidden reasoning, prompts, or raw JSON.
- Reviewer notes must be rewritten into applicant-safe wording.

---

# 5. Mandatory Agent Output Contract

All evaluation agents must return valid JSON using this shape:

```json
{
  "score": 0.82,
  "confidence": 0.91,
  "decision": "low",
  "flags": ["high_dti"],
  "reasoning": "DTI ratio is elevated."
}
```

## Validation Rules

- `score` must be a number between 0 and 1.
- `confidence` must be a number between 0 and 1.
- `decision` must match the allowed decisions for that agent.
- `flags` must be an array of strings.
- `reasoning` must be present and concise.
- Invalid output must fail validation.
- Malformed output must route to manual review or workflow failure handling.

---

# 6. Guardrails

Guardrails must run after every agent output.

## Hard Guardrails

- Missing documents → no approval.
- Policy mismatch → no approval.
- Fraud suspicious → no approval.
- Medium risk → manual review.
- High risk → reject or manual review.
- Malformed output → manual review or failure.
- Unknown decision → manual review.
- Low confidence → manual review.
- Required worker failure → no approval.

Guardrails always override LLM output.

---

# 7. LLM Implementation Strategy

The target architecture is hybrid.

Primary orchestration platform:

```text
Vertex AI
```

Primary worker model family:

```text
Gemini 2.5
```

Decision synthesis model:

```text
OpenAI gpt-5.4
```

## Runtime Requirements

Each live agent path must:

- Use the same structured output contract.
- Pass guardrail validation.
- Log provider, model name, and model version when available.
- Log prompt version.
- Fail safely without silent deterministic substitution.
- Never directly approve applications without guardrails.

## Implementation Order

Codex should implement the hybrid architecture in this order:

1. Add a provider-agnostic agent runtime abstraction.
2. Move `planner` to Vertex AI.
3. Move `document_analysis`, `policy_retrieval`, `risk_assessment`, and `fraud_verification` to Vertex AI.
4. Move `decision_summary` to OpenAI `gpt-5.4`.
5. Keep guardrails deterministic and provider-independent.
6. Decide the `email_agent` provider after evaluation results.
7. Add MCP-backed workers only after the core runtime and evaluation harness are stable.

---

# 8. Prompt Files

Each LLM-backed agent must have a dedicated prompt file.

Recommended location:

```text
backend/underlytics_api/agents/prompts/
```

Required files:

```text
planner_prompt.py
document_analysis_prompt.py
policy_retrieval_prompt.py
risk_assessment_prompt.py
fraud_verification_prompt.py
decision_summary_prompt.py
email_agent_prompt.py
```

Each prompt must define:

- role
- task
- inputs
- constraints
- allowed decisions
- output schema
- failure behavior
- escalation rules
- what the agent must not do

Prompts must instruct agents to:

- return valid JSON only
- avoid guessing
- lower confidence when uncertain
- escalate uncertainty to manual review
- never expose internal system details

## Prompt Requirements

Each prompt file must also declare:

- `provider`
- `model`
- `prompt_version`
- `allowed_tools`
- `supports_mcp`

Prompt instructions must clearly distinguish:

- deterministic input features supplied by the system
- tool-fetched evidence supplied through MCP
- facts the agent is not allowed to invent

Prompts must tell agents to prefer provided policy inputs and computed features over free-form reasoning.

## Decision Reference Pack

Agents must not make underwriting decisions from prompt text alone.

Every worker should receive a governed decision reference pack made up of:

- typed application data
- deterministic derived metrics
- product and policy constraints
- explicit escalation thresholds
- any approved MCP evidence for that worker

Examples:

- `risk_assessment` should receive derived affordability metrics such as DTI, disposable income, and repayment ratio.
- `policy_retrieval` should receive product rules, caps, exclusions, and versioned policy references.
- `document_analysis` should receive required-document matrices and document metadata.
- `fraud_verification` should receive normalized anomaly signals, not raw unsupported guesses.

Agents interpret the reference pack. They do not invent the reference pack.

## Evaluation Requirements

Underlytics must maintain evaluation metrics before broad rollout.

Minimum tracked metrics:

- worker schema-valid output rate
- guardrail override rate
- manual-review precision and recall
- decision agreement with human reviewers
- confidence calibration
- latency per agent
- cost per application
- reasoning completeness / citation quality where applicable

Worker-specific metrics:

- `document_analysis`: missing-document recall, unreadable-document precision
- `policy_retrieval`: policy mismatch precision/recall, policy citation correctness
- `risk_assessment`: agreement with gold affordability band, calibration by score bucket
- `fraud_verification`: suspicious-case recall, false escalation rate
- `decision_summary`: agreement with adjudicated outcome, illegal-approval rate
- `email_agent`: factual consistency, tone compliance, sensitive-data leakage rate

---

# 9. Workflow Status Endpoint

Codex must expose a structured workflow status endpoint for frontend polling.

## Required Endpoint

```http
GET /api/applications/{application_number}/workflow-status
```

## Example Response

```json
{
  "application_number": "APP-001",
  "status": "processing",
  "progress": 55,
  "current_stage": "risk_assessment",
  "agents": [
    {
      "name": "planner",
      "label": "Planner Agent",
      "status": "completed",
      "snippet": "Preparing your underwriting workflow."
    },
    {
      "name": "document_analysis",
      "label": "Document Analysis",
      "status": "completed",
      "snippet": "Checking uploaded documents and required files."
    },
    {
      "name": "policy_retrieval",
      "label": "Policy Retrieval",
      "status": "completed",
      "snippet": "Comparing your request against product rules."
    },
    {
      "name": "risk_assessment",
      "label": "Risk Assessment",
      "status": "running",
      "snippet": "Reviewing income, expenses, and affordability."
    },
    {
      "name": "fraud_verification",
      "label": "Fraud Verification",
      "status": "pending",
      "snippet": "Checking for unusual application signals."
    },
    {
      "name": "decision_summary",
      "label": "Decision Summary",
      "status": "pending",
      "snippet": "Combining all agent findings into a final recommendation."
    }
  ]
}
```

## Allowed Workflow Statuses

```text
processing
completed
failed
```

## Allowed Agent Statuses

```text
pending
running
completed
failed
```

---

# 10. Agent Processing UX

After application submission, the user must not be sent immediately to the application detail page.

## Required Flow

```text
Submit Application
  ↓
Processing Page
  ↓
Animated Planner + Worker Agent Progress
  ↓
Final Decision
  ↓
Application Detail Page
```

## Required Route

```text
/applications/{application_number}/processing
```

After completion, redirect to:

```text
/applications/{application_number}
```

## Update Create Application Flow

After successful application submission, redirect to:

```text
/applications/{application_number}/processing
```

The processing page then redirects to:

```text
/applications/{application_number}
```

---

# 11. Processing Screen Requirements

The processing screen must:

- Poll workflow status every 2 to 3 seconds.
- Use the real backend workflow status endpoint.
- Show Planner and Worker Agent cards.
- Show pending, running, completed, and failed states.
- Show a horizontal progress bar.
- Show numeric percentage completion.
- Show applicant-friendly stage snippets.
- Show optional reasoning once available.
- Redirect only when the final decision is ready.
- Show a clear error state if workflow fails.
- Provide a button to view application detail if workflow fails.

The UI must not fake final completion.

A short minimum animation delay is allowed only to make fast workflows feel smooth, but final state must always come from the backend.

---

# 12. Progress Mapping

Progress must be calculated from real workflow state.

Use this recommended mapping:

```text
Planner initialized: 10%
Document Analysis completed: 25%
Policy Retrieval completed: 40%
Risk Assessment completed: 55%
Fraud Verification completed: 70%
Decision Summary completed: 90%
Final redirect-ready state: 100%
```

## Stage Snippets

Use these applicant-friendly snippets:

```text
Planner: Preparing your underwriting workflow.
Document Analysis: Checking uploaded documents and required files.
Policy Retrieval: Comparing your request against product rules.
Risk Assessment: Reviewing income, expenses, and affordability.
Fraud Verification: Checking for unusual application signals.
Decision Summary: Combining all agent findings into a final recommendation.
```

---

# 13. Frontend Design Requirements

Use shadcn/ui where appropriate:

- Card
- Badge
- Progress
- Skeleton
- Alert
- Button

Design direction:

- premium fintech / AI feel
- subtle motion
- professional tone
- not childish
- autonomous agents should feel active and independent
- preserve existing functionality
- responsive on desktop and mobile

---

# 14. Application Detail Page Layout Improvements

Codex must improve the layout and alignment of the application detail page.

Target page:

```text
/applications/APP-001
```

Focus areas:

- Planner Workflow section.
- Planner Job card.
- Worker result cards.
- Completed status badges.
- Score, confidence, and decision layout.

## Planner Job Card Requirements

The Planner Job card must be visually balanced.

Current issues:

- Retries, Started, and Updated stat boxes are squeezed.
- Completed status and completed workers badges take space away from metadata.
- Card content does not align cleanly.

Required improvements:

- Give Retries, Started, and Updated enough space.
- Move Completed and completed workers badges after the stat boxes, or redesign the layout so all elements align cleanly.
- Use responsive wrapping where needed.
- Prevent metadata from becoming cramped.
- Keep the existing visual style.

## Worker Card Requirements

Worker result cards must be readable and aligned.

Current issues:

- Score, Confidence, and Decision boxes are too narrow.
- Decision text wraps awkwardly.
- Completed badges are not consistently aligned.
- Some content appears squeezed.

Required improvements:

- Give Score, Confidence, and Decision enough width.
- Avoid text clipping.
- Ensure decision values are readable.
- Align Completed badges consistently inside card headers.
- Prevent badges from overflowing or overlapping.
- Use responsive card layouts.
- Preserve the existing design style, colors, rounded cards, and badges.

---

# 15. Email Workflow

Email flow:

```text
Final Decision or Completed Manual Review
  ↓
Email Agent generates applicant-facing message
  ↓
Notification Service sends via Resend
  ↓
Communication Log stores result
```

## Required Environment Variables

```env
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=decisions@mail.steveleesuppliers.co.ke
```

These are backend runtime secrets and must never be exposed to the frontend.

---

# 16. Communication Logs

Create or preserve a `communication_logs` table.

Required fields:

```text
id
application_id
recipient_email
subject
body
status
provider
provider_message_id
error_message
sent_at
created_at
updated_at
```

Allowed statuses:

```text
pending
sent
failed
```

Provider:

```text
resend
```

---

# 17. Notification Service

Create or preserve:

```text
backend/underlytics_api/services/notification_service.py
```

Expected function shape:

```python
def send_application_email(
    *,
    db,
    application_id: str,
    to_email: str,
    subject: str,
    body: str,
) -> CommunicationLog:
    ...
```

## Responsibilities

The Notification Service must:

- Accept recipient, subject, and body.
- Call the email provider.
- Create a communication log.
- Mark email as sent or failed.
- Never crash the underwriting workflow if email fails.
- Never roll back underwriting decisions because email failed.
- Never expose raw provider errors to applicants.

---

# 18. Email Provider Interface

Create or preserve a provider abstraction.

```python
from typing import Protocol


class EmailProvider(Protocol):
    def send(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
    ) -> str:
        ...
```

Implement:

```text
ResendProvider
```

Recommended file:

```text
backend/underlytics_api/services/providers/resend_provider.py
```

The Resend provider must:

- Call the Resend API.
- Return the provider message ID.
- Raise clear errors on failure.
- Never log API keys.

---

# 19. Email Generation

Create or preserve:

```python
def generate_application_email(
    *,
    application,
    agent_outputs,
    reviewer_note: str | None = None,
    reviewer_decision: str | None = None,
) -> dict:
    ...
```

Return:

```json
{
  "subject": "Your Underlytics application update",
  "body": "Clear applicant-facing message..."
}
```

This may start deterministic but must be structured so it can later call the Email Agent through Gemini.

---

# 20. Email Cases

## Approved

Trigger when:

```text
application.status == "approved"
```

Include:

- approval message
- concise reason for approval
- key positive factors
- next steps

## Rejected

Trigger when:

```text
application.status == "rejected"
```

Include:

- clear explanation
- main reason or risk factor
- respectful tone
- optional improvement guidance

Avoid harsh language.

## Manual Review Initial State

Trigger when:

```text
application.status == "manual_review"
```

Do not send final decision email.

Manual review is not final.

## Manual Review Completed

Trigger when application status changes from:

```text
manual_review → approved
manual_review → rejected
```

Include:

- final decision
- reviewer note
- summary explanation
- next steps

Reviewer note must be converted into applicant-safe wording.

---

# 21. Applicant Email Source

The system must determine recipient email from the applicant or user record.

If recipient email is missing:

- Do not send email.
- Log skipped or failed communication if appropriate.
- Do not crash the workflow.

---

# 22. Manual Review

Manual review is a first-class workflow.

Manual review is triggered by:

- missing documents
- policy uncertainty
- fraud suspicion
- medium risk
- high risk
- low confidence
- malformed output
- human escalation

Reviewer must provide:

- final decision
- reviewer note

After manual review completion:

- Email Agent generates applicant-facing message.
- Notification Service sends email.
- Communication Log stores result.

---

# 23. MCP Strategy

MCP is a staged capability, not a default dependency.

Do not use MCP for:

- email sending
- final decision synthesis
- unrestricted planner research

## Initial MCP Policy

The first MCP rollout should stay on free or keyless tooling where possible.

Preferred initial MCPs:

- internal policy / product knowledgebase MCP
- read-only filesystem or document MCP for internal policy artifacts
- browser / Playwright MCP against trusted public sources
- public business-registry lookups where no paid API is required

These can usually be introduced without paid API keys.

## MCP Candidates by Agent

Good early MCP candidates:

- `policy_retrieval`
- `fraud_verification`

Possible later MCP candidates:

- `document_analysis`
- `risk_assessment`

Agents that should not directly use MCP in normal operation:

- `decision_summary`
- `email_agent`

Planner MCP use should be limited to orchestration metadata, not substantive underwriting evidence.

## MCP Rules

- Tools must be read-only at first.
- Tool outputs are supporting evidence only.
- MCP evidence must be normalized into worker inputs before final synthesis.
- External data must not directly approve or reject applications.
- Browser tools should only access trusted sources.
- Every tool call must be logged with source and timestamp.
- Paid MCP/API integrations must be explicitly approved before implementation.

## Likely Paid Integrations Later

These usually require API keys or commercial contracts:

- credit bureau data
- KYC / identity verification
- sanctions / PEP screening
- bank statement enrichment
- device intelligence
- commercial fraud feeds

Codex must call out these requirements before implementation.

---

# 24. Tracing

Use Langfuse to trace the full underwriting workflow.

Trace:

- planner start and end
- each worker start and end
- model name and version
- prompt version
- input summary
- output summary
- guardrail result
- final decision
- email generation
- email send result

Do not log:

- secrets
- API keys
- full raw uploaded documents
- full Clerk tokens
- sensitive applicant data unless redacted

OpenAI tracing may be used later for experiments, but Langfuse is the primary workflow tracing layer.

---

# 25. Testing Requirements

Add or preserve tests for:

- workflow status endpoint
- progress calculation
- processing route behavior
- approved email generation
- rejected email generation
- manual review completed email generation
- no final email for initial manual review
- communication log created on success
- communication log created on failure
- missing applicant email handled safely
- Resend provider mocked correctly
- guardrails overriding LLM output
- malformed agent output handling
- failed worker handling
- application detail page layout responsiveness

---

# 26. Failure Handling

If an agent fails:

- Mark that agent as failed.
- Store error message.
- Retry if policy allows.
- Escalate to manual review or workflow failure.
- Never approve blindly.

If LLM output is malformed:

- Fail validation.
- Retry if allowed.
- Otherwise route to manual review.

If required workers fail:

- Decision Summary Agent must not approve.

If email sending fails:

- Log failure.
- Do not expose raw provider error to applicant.
- Do not roll back the underwriting decision.

---

# 27. What Codex Must Not Do

Codex must not:

- Collapse the workflow into one LLM call.
- Remove planner and worker separation.
- Remove guardrails.
- Allow LLM output to directly approve applications.
- Return unstructured text as the primary agent output.
- Use MCP everywhere by default.
- Use MCP for email sending in v1.
- Let `decision_summary` fetch outside evidence directly in normal operation.
- Send email directly from an LLM agent.
- Expose prompts, secrets, tokens, raw JSON, or raw internal logs to users.
- Remove manual review flow.
- Fake final workflow completion in the UI.
- Break existing authentication.
- Break existing backend integration.
- Redesign the whole UI unnecessarily.
- Remove deterministic guardrails or governed policy inputs.

---

# 28. Implementation Order

Codex should implement in this order:

1. Keep the planner-worker workflow and deterministic guardrails intact.
2. Confirm workflow status persistence and processing-page UX.
3. Add prompt files, provider metadata, and prompt versioning.
4. Add a provider-agnostic runtime abstraction.
5. Move planner and specialist workers to Vertex AI.
6. Move `decision_summary` to OpenAI `gpt-5.4`.
7. Preserve Notification Service ownership of email sending.
8. Add evaluation datasets, regression checks, and guardrail reporting.
9. Add Langfuse tracing for provider/model/tool metadata.
10. Add MCP abstraction later only when justified by evaluation results.
11. Start MCP with `policy_retrieval` and `fraud_verification` using free or keyless sources first.

---

# 29. End Goal

The Underlytics system should become a hybrid AI underwriting engine that is:

- planner-orchestrated
- worker-specialized
- independently executable
- LLM-assisted
- deterministic where safety matters
- explainable to users
- auditable for reviewers
- applicant-friendly
- safe under failure
- production-ready
