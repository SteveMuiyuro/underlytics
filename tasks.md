# TASKS.md

## Project
Underlytics is a loan underwriting platform moving from deterministic worker execution toward real agentic orchestration.

Current stack:
- Frontend: Next.js, TypeScript, Tailwind, shadcn/ui, Clerk
- Backend: FastAPI, SQLAlchemy, SQLite for dev
- Auth: Clerk in frontend, backend auth still needs to be enforced
- Current workflow: synchronous, in-process worker execution with persisted runs and outputs
- Target workflow: planner + orchestrator + autonomous workers + hard guardrails + human review
- Target model platform: Vertex AI Gemini for planner and specialist workers, OpenAI for decision synthesis

---

## Current reality
The current implementation already has useful foundations, but it is not yet an agentic orchestration system.

What exists today:
- Clerk-protected frontend routes
- backend user sync
- applications, loan products, documents, workflow, and agent-output endpoints
- underwriting job, agent run, and agent output persistence
- deterministic workers for:
  - document_analysis
  - policy_retrieval
  - risk_assessment
  - fraud_verification
  - decision_summary
- hard guardrails for output validation and final decision enforcement

What is still missing for real orchestration:
- backend authentication and authorization enforcement
- a true planner that produces a run plan instead of a fixed worker list
- resumable workflow state
- dependency-aware execution
- retries and reruns after new documents arrive
- queue-backed async execution
- reviewer queue and override flow
- evaluation and prompt versioning

---

## Core architecture rules
These rules should remain true as development continues:

1. Do not collapse the system into one monolithic underwriting function.
2. Keep planner logic separate from worker execution.
3. Keep worker outputs structured, explainable, and auditable.
4. Keep deterministic guardrails in place even after LLM integration.
5. LLMs may assist reasoning, but they must not bypass policy or safety rules.
6. Maintain support for human-in-the-loop review and overrides.
7. Keep orchestration state in the database so runs are observable and recoverable.
8. Prefer incremental migration from the current implementation over a rewrite.
9. Keep the agent runtime provider-agnostic.
10. Add MCP only where external evidence materially improves a specialist worker.

---

## Structured agent output contract
Every agent output should follow this contract:

```json
{
  "score": 0.82,
  "confidence": 0.91,
  "decision": "low_risk",
  "flags": ["high_dti"],
  "reasoning": "DTI ratio is within acceptable range and disposable income is strong."
}
```

Required invariants:
- output must validate against a strict schema
- unsupported decisions must fail safely
- malformed outputs must default to manual review or worker failure
- final approval must still pass hard guardrails

This contract should remain the standard for both deterministic and LLM-backed workers.

---

## Target orchestration architecture

### Runtime flow
1. Applicant submits or updates an application.
2. Planner builds a workflow plan based on application state and available documents.
3. Orchestrator materializes workflow steps and dependencies.
4. Eligible steps are queued for execution.
5. Workers execute with typed context and produce structured outputs.
6. Guardrails validate each output and enforce allowed transitions.
7. If escalation is required, the application enters manual review.
8. If all required steps succeed, the final decision is persisted and communicated.

### Planner responsibilities
The planner should be responsible for:
- deciding which steps are required for this application
- setting execution order and dependencies
- choosing the correct provider-backed worker path
- routing to manual review when prerequisites are missing
- generating a concise planner summary for the UI and audit trail

### Orchestrator responsibilities
The orchestrator should be responsible for:
- creating workflow steps from the planner output
- tracking step state transitions
- dispatching ready steps
- handling retries and reruns
- resuming the workflow after external events such as document uploads or reviewer actions
- emitting traces, audit events, and notifications

### Worker responsibilities
Each worker should:
- receive typed context only for its domain
- return structured output only
- avoid mutating final workflow state directly unless explicitly allowed
- fail loudly on invalid context or malformed output

---

## Core gaps to fix before LLM rollout
These are the current blockers to agentic orchestration and should come before prompt and model work.

### 1. Backend auth and authorization
Current backend endpoints trust caller-supplied IDs too much.

Required fixes:
- validate backend identity from Clerk or trusted backend token
- enforce application ownership for applicant actions
- enforce reviewer role for reviewer actions
- remove role escalation from open user-sync inputs

### 2. Workflow state redesign
Current workflow state is too thin for real orchestration.

Required fixes:
- separate workflow execution state from final application decision state
- add explicit step lifecycle states
- add dependency tracking
- support pending, blocked, running, completed, failed, cancelled, awaiting_review, and retried states

### 3. Document-driven reruns
Today the workflow can finish before required documents are uploaded.

Required fixes:
- block final decision when required documents are absent
- rerun or resume relevant steps when documents are uploaded or replaced
- mark superseded outputs when a rerun invalidates prior reasoning

### 4. Idempotency and retries
The system needs safe re-entry.

Required fixes:
- idempotent application submission
- idempotent job and step creation
- retry policy per step
- attempt history per step

### 5. Migrations
Schema evolution needs to stop depending on implicit table creation.

Required fixes:
- add Alembic
- create baseline migration
- define a migration workflow for future orchestration models

---

## Proposed v1 data model additions
The exact table names can change, but this is the shape the system needs.

### workflow_plans
Represents the planner output for one underwriting run.

Suggested fields:
- `id`
- `application_id`
- `plan_version`
- `planner_mode`
- `status`
- `summary`
- `plan_json`
- `trace_id`
- `created_at`
- `updated_at`

### workflow_steps
Represents one executable step in the plan.

Suggested fields:
- `id`
- `workflow_plan_id`
- `application_id`
- `step_key`
- `step_type`
- `worker_name`
- `status`
- `queue_name`
- `input_context_json`
- `output_schema_version`
- `decision`
- `priority`
- `created_at`
- `updated_at`
- `started_at`
- `completed_at`
- `failed_at`

### workflow_step_dependencies
Defines the DAG between steps.

Suggested fields:
- `id`
- `workflow_step_id`
- `depends_on_step_id`

### workflow_step_attempts
Tracks retries and execution attempts.

Suggested fields:
- `id`
- `workflow_step_id`
- `attempt_number`
- `executor_type`
- `model_name`
- `status`
- `error_message`
- `trace_id`
- `started_at`
- `completed_at`

### manual_review_cases
Represents reviewer work items.

Suggested fields:
- `id`
- `application_id`
- `workflow_plan_id`
- `status`
- `reason`
- `assigned_reviewer_user_id`
- `created_at`
- `resolved_at`

### manual_review_actions
Tracks reviewer decisions and overrides.

Suggested fields:
- `id`
- `manual_review_case_id`
- `reviewer_user_id`
- `action`
- `note`
- `old_decision`
- `new_decision`
- `created_at`

### communication_logs
Stores outbound communication and delivery status.

Suggested fields:
- `id`
- `application_id`
- `event_type`
- `channel`
- `template_key`
- `status`
- `payload_json`
- `sent_at`
- `created_at`

### Optional audit_events
Useful for long-term production governance.

Suggested fields:
- `id`
- `application_id`
- `actor_type`
- `actor_id`
- `event_type`
- `event_json`
- `created_at`

---

## Worker design by phase

### Deterministic workers first
These should remain mostly deterministic:
- policy_retrieval
- fraud_verification
- guardrail enforcement

### Hybrid workers
These can combine deterministic checks with model-assisted reasoning:
- decision_summary
- document_analysis once OCR or extraction is introduced

### Later LLM candidates
These should only become LLM-heavy if the business case is clear:
- risk_assessment
- policy_retrieval over a real policy corpus

Recommendation:
- first LLM rollout should be `decision_summary`
- second LLM rollout can be `document_analysis` if document extraction becomes complex
- keep `risk_assessment` largely deterministic in early versions

---

## Evaluation and safety requirements
This is missing from the current implementation plan and should be treated as mandatory.

Required work:
- underwriting fixtures for replayable scenarios
- expected outputs for deterministic workers
- schema validation tests for all workers
- guardrail regression tests
- prompt version tracking
- model version tracking
- approval/rejection/manual-review golden-path tests

Deliverables:
- evaluation dataset directory
- worker regression tests
- prompt and model version metadata
- replay script for historical workflows

---

## Tracing and observability
Tracing is still important, but it should wrap the orchestration layer rather than lead the architecture.

### Goal
Introduce full observability for planning, orchestration, worker execution, retries, and reviewer actions.

### Requirements
- use Langfuse for workflow-level tracing
- keep tracing provider-agnostic so Vertex and future model providers fit cleanly
- capture:
  - application submission
  - planner start and completion
  - step creation
  - step dispatch
  - worker start and completion
  - worker output validation
  - retries
  - manual review escalation and resolution
  - document uploads and reruns
  - final decision generation
  - outbound communications

### Deliverables
- tracing utility layer
- trace ids linked to plans, steps, and attempts
- spans for planner, orchestrator, and workers
- error traces for failures and retries

---

## Prompt system
Prompt work should begin only after worker boundaries and context contracts are stable.

### Goal
Prepare LLM-backed workers with versioned, testable prompt modules.

### Requirements
Create modular prompt files or prompt builders for:
- planner
- document analysis
- policy retrieval
- risk assessment
- fraud verification
- decision summary

Each prompt should define:
- role
- task
- available context
- disallowed assumptions
- required output schema
- guardrail expectations
- escalation rules
- examples where useful

### Deliverables
- prompt directory
- one prompt module per agent
- prompt version metadata
- structured output instructions aligned to the output contract

---

## Vertex AI integration

### Goal
Introduce Gemini into selected worker paths without weakening safety guarantees.

### Requirements
- use Vertex AI as the primary model platform
- start with one worker path only
- keep deterministic validation after every model call
- support fallback to deterministic/manual-review behavior if model calls fail
- persist model name, prompt version, and attempt metadata

### Recommended rollout
1. `decision_summary`
2. `document_analysis` if document extraction is added
3. consider `policy_retrieval` later only if policy retrieval becomes genuinely unstructured

### Deliverables
- Vertex AI client setup
- model invocation abstraction
- worker execution path that can call Gemini
- fallback behavior on timeout, malformed output, and low confidence

---

## Manual review capability
Manual review is a core underwriting feature, not a later polish item.

### Goal
Support reviewer intervention for escalated or overridden applications.

### Requirements
- add reviewer actions:
  - approve
  - reject
  - request_more_info
- require reviewer note on override
- record reviewer actions in DB
- allow reassignment and resolution tracking
- surface manual review state clearly in frontend

### Deliverables
- reviewer action endpoints
- reviewer queue model
- reviewer UI controls
- audit logging for overrides

---

## Workflow visibility in frontend
The current frontend already shows useful data, but it should evolve to reflect orchestration rather than raw rows.

### Goal
Improve the application detail view so users can understand plan state, worker status, and escalation clearly.

### Requirements
- show planner summary
- show workflow stages and dependencies
- show timestamps per step and attempt
- show retries and failures
- show clearer reasoning and flags
- show manual review state and reviewer actions
- show rerun/superseded outputs when documents change

### Deliverables
- improved workflow UI
- human-friendly labels
- grouped workflow stages
- planner summary panel

---

## Document handling
Document handling needs to support underwriting state changes, not just file storage.

### Goal
Make uploads production-ready and orchestration-aware.

### Requirements
- validate file types and sizes
- add document replacement behavior
- add upload status transitions
- classify required vs optional documents
- trigger plan recomputation or targeted reruns after upload
- prepare storage abstraction for later GCS migration

### Deliverables
- backend validation rules
- improved frontend upload UX
- storage abstraction layer
- rerun trigger logic after document changes

---

## Communication layer

### Goal
Send applicant-facing notifications based on workflow events and final decisions.

### Requirements
- send notification after final decision
- later support:
  - approved email
  - rejected email
  - manual review email
  - request-more-info email
- store communication logs in DB

### Deliverables
- notification service module
- communication log model and endpoint
- frontend communication section backed by real data

---

## Async execution
Async execution is a core architecture milestone and should happen before broad LLM rollout.

### Goal
Move from in-process execution to queue-backed orchestration.

### Requirements
- preserve planner + worker separation
- move execution off the request path
- keep database-driven workflow state as source of truth
- support retries, backoff, and dead-letter handling
- keep the task runner replaceable so local dev and cloud deployment can differ

### Deliverables
- execution abstraction
- queue or background task runner interface
- local dev runner
- later integration path for Pub/Sub or equivalent

---

## Recommended implementation order
This order is intentionally different from the earlier version because the system needs orchestration foundations before more model sophistication.

1. Enforce backend auth and authorization
2. Add Alembic migrations
3. Redesign workflow state for planner, steps, dependencies, and attempts
4. Fix document-driven reruns and resumability
5. Add async execution abstraction
6. Add tracing around planner, orchestrator, and workers
7. Add manual review queue and reviewer actions
8. Add evaluation harness and regression tests
9. Add prompt modules and prompt versioning
10. Integrate Gemini for one selected worker path
11. Improve workflow visibility in frontend
12. Add communication layer
13. Harden document storage and cloud migration path

---

## Immediate next milestone
The best next milestone for this repo is:

### Milestone: Orchestration foundation v1
Scope:
- backend auth enforcement
- Alembic baseline
- workflow plan, step, dependency, and attempt models
- planner output persisted as plan JSON
- orchestrator service that dispatches ready steps
- document upload rerun trigger
- manual review case model

Exit criteria:
- submitting an application creates a workflow plan, not an immediate final decision
- missing documents block approval correctly
- uploading a required document can resume the workflow
- workflow state is visible and recoverable from the database

---

## Important notes for Codex
- Do not remove the planner/worker separation
- Do not bypass guardrails when adding LLMs
- Keep outputs structured and explainable
- Prefer incremental changes over full rewrites
- Keep the architecture ready for GCP deployment and Dockerization
- Maintain compatibility with current routes where practical, but allow internal workflow refactors when necessary
- Treat evaluation, replayability, and auditability as first-class requirements
