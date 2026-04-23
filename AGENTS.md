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