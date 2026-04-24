# AGENTS.md

## Purpose

This document defines the architecture, behavior, and implementation rules for the Underlytics agent system.

Underlytics is an AI-powered loan underwriting platform. The agent system must be:

- explainable
- auditable
- deterministic where required
- modular
- production-ready
- safe under failure
- extensible to external tools (MCP) later

This document ensures Codex builds agents correctly and does not collapse the system into a single LLM call.

---

## Core Architecture

The system uses a **Planner + Worker (Orchestrator-Worker) architecture**.

Flow:

Application
→ Planner Agent
→ Independent Worker Agents
→ Structured Outputs
→ Decision Summary Agent
→ Guardrails
→ Final Decision
→ Email Agent
→ Notification Service

Key principles:

- Each worker operates independently
- Workers do NOT share hidden state
- Workers do NOT make final approval decisions
- The planner orchestrates, not decides
- Guardrails enforce correctness after LLM output

---

## Agent Roles

### 1. Planner Agent

Role:
- orchestrates workflow execution

Responsibilities:
- create job
- trigger worker agents
- track job state
- ensure required workers run
- trigger Decision Summary Agent
- handle retries/failures

Constraints:
- must NOT approve or reject applications
- must NOT bypass guardrails
- must NOT contain business logic decisions

---

### 2. Worker Agents

Workers are **specialized evaluators**.

Each worker:
- receives scoped input
- performs one task
- returns structured JSON
- is stateless
- can run independently (async-ready)

Workers must:
- NOT approve/reject applications
- NOT modify other worker outputs
- NOT assume other agents’ results unless explicitly passed

---

## Worker Agents

### Document Analysis Worker

Purpose:
- validate required documents

Inputs:
- uploaded documents
- required document list

Outputs:
- decision: documents_complete | documents_missing
- flags: missing documents
- reasoning
- score, confidence

Rules:
- missing documents → cannot approve
- unreadable documents → flag

---

### Policy Retrieval Worker

Purpose:
- validate against loan policy

Inputs:
- product
- requested amount
- term

Outputs:
- decision: policy_match | policy_mismatch
- flags
- reasoning
- score, confidence

Rules:
- mismatch → cannot approve
- missing policy → manual review

---

### Risk Assessment Worker

Purpose:
- evaluate affordability risk

Inputs:
- income
- expenses
- obligations
- requested loan

Outputs:
- decision: low | medium | high
- flags
- reasoning
- score, confidence

Rules:
- medium → manual review
- high → reject unless overridden by reviewer

---

### Fraud Verification Worker

Purpose:
- detect anomalies

Inputs:
- application data
- document metadata

Outputs:
- decision: clear | suspicious
- flags
- reasoning
- score, confidence

Rules:
- suspicious → no auto approval
- escalate to manual review

---

### Decision Summary Agent

Purpose:
- aggregate all worker outputs
- propose final decision

Inputs:
- all worker outputs

Outputs:
- decision: approved | rejected | manual_review
- score
- reasoning
- flags
- inputs_used

Rules:
- must NOT bypass guardrails
- must NOT override policy constraints
- must explain reasoning clearly

---

### Email Agent

Purpose:
- generate applicant-facing communication

Inputs:
- final decision
- worker outputs
- reviewer notes (if any)

Outputs:
- subject
- message body

Rules:
- professional tone
- no internal jargon
- no raw system data
- no hidden reasoning

Email sending is handled by Notification Service (NOT the agent).

---

## Output Contract (MANDATORY)

All agents must return:

```json
{
  "score": 0.82,
  "confidence": 0.91,
  "decision": "low",
  "flags": ["high_dti"],
  "reasoning": "DTI ratio is elevated."
}


## LLM Implementation Strategy

Primary LLM platform:
- Vertex AI

Primary model:
- Gemini

Implementation order:
1. Email Agent
2. Decision Summary Agent
3. Risk Assessment Worker
4. Policy Retrieval Worker
5. Document Analysis Worker
6. Fraud Verification Worker

Do NOT convert all agents to LLMs at once.

Each LLM-backed agent must:
- use the same structured output contract
- pass guardrail validation
- have fallback behavior
- log model name/version
- never directly approve without guardrails

---

## System Prompts

Each LLM-backed agent must have its own prompt file.

Recommended location:

```text
backend/underlytics_api/agents/prompts/

Add an agent processing experience after application submission.

Current flow:
- user submits application from /new-application
- backend creates application and workflow
- user is redirected to the application detail page

New desired flow:
- after the user submits the application, redirect them first to an intermediate processing screen
- route example: /applications/[applicationNumber]/processing
- show animated agent workflow progress
- after the final agent/decision completes, automatically redirect to /applications/[applicationNumber]

Processing screen behavior:
- show Planner Agent starting
- show worker agents appearing one by one:
  - Document Analysis
  - Policy Retrieval
  - Risk Assessment
  - Fraud Verification
  - Decision Summary
- each agent card should animate through states:
  - pending
  - running
  - completed
  - failed
- use existing backend workflow endpoints to poll status
- poll every 2–3 seconds
- when Decision Summary is completed and application status is final, redirect to the detail page
- if workflow fails, show a clear error state and a button to view application detail

Design:
- premium fintech / AI feel
- use shadcn/ui Card, Badge, Progress, Skeleton, Alert where appropriate
- subtle motion/animation, not childish
- make it feel like autonomous agents are independently processing the application
- preserve existing functionality

Important:
- do not fake completion if backend workflow is still running
- use real workflow/agent status from backend
- if backend currently completes too fast, still render a short minimum animation delay for better UX, but final state must be based on real backend result
- after completion redirect to the application detail page

Update create application flow:
- after successful submit, route to:
/applications/{application_number}/processing

Then processing page redirects to:
/applications/{application_number}

## Agent Processing UX

After application submission, the user should not be immediately sent to the detail page.

Flow:

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

Enhance the agent processing screen with a real progress bar and stage snippets.

Requirements:

1. Progress bar
- show a horizontal progress bar
- show numeric percentage completion
- calculate progress from real backend workflow state
- example:
  - Planner initialized = 10%
  - Document Analysis completed = 25%
  - Policy Retrieval completed = 40%
  - Risk Assessment completed = 55%
  - Fraud Verification completed = 70%
  - Decision Summary completed = 90%
  - Final redirect-ready state = 100%

2. Agent activity snippets
Show short, user-friendly snippets for each stage.

Examples:
- Planner: “Preparing your underwriting workflow…”
- Document Analysis: “Checking uploaded documents and required files…”
- Policy Retrieval: “Comparing your request against product rules…”
- Risk Assessment: “Reviewing income, expenses, and affordability…”
- Fraud Verification: “Checking for unusual application signals…”
- Decision Summary: “Combining all agent findings into a final recommendation…”

3. Live status behavior
Each agent card should show:
- agent name
- current status
- short snippet
- completion state
- optional reasoning once available

4. UX behavior
- use real backend status
- poll workflow status every 2–3 seconds
- do not fake final completion
- allow a minimum visible animation delay so the experience feels smooth
- redirect to detail page only when the final decision is ready

5. Design
Use shadcn/ui:
- Progress
- Card
- Badge
- Skeleton
- Alert
- Button if error occurs

Make the screen feel like autonomous AI agents are actively processing the loan application, but keep the tone professional and fintech-grade.


## Agent Processing Progress UX

The processing screen must show a progress bar with percentage completion.

Progress should be calculated from real workflow state.

Recommended progress mapping:

- Planner initialized: 10%
- Document Analysis completed: 25%
- Policy Retrieval completed: 40%
- Risk Assessment completed: 55%
- Fraud Verification completed: 70%
- Decision Summary completed: 90%
- Final redirect-ready state: 100%

Each stage should show a short applicant-friendly snippet:

- Planner: Preparing your underwriting workflow.
- Document Analysis: Checking uploaded documents and required files.
- Policy Retrieval: Comparing your request against product rules.
- Risk Assessment: Reviewing income, expenses, and affordability.
- Fraud Verification: Checking for unusual application signals.
- Decision Summary: Combining all agent findings into a final recommendation.

The UI must use real backend workflow status and must not fake final completion.