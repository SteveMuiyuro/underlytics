# AGENT_SYSTEM.md

## Purpose

This document defines the architecture, behavior, and responsibilities of the Underlytics agent system.

It ensures Codex builds agents correctly using:
- LLM reasoning (Gemini via Vertex AI)
- structured outputs
- strict guardrails
- deterministic orchestration

---

## Core architecture

The system follows a **planner + worker (orchestrator-worker) architecture**.

This is a standard multi-agent pattern where:
- a planner decomposes tasks
- workers execute specialized subtasks
- results are aggregated into a final decision

This pattern improves scalability, specialization, and reliability in complex workflows :contentReference[oaicite:1]{index=1}.

---

## Agent roles

### 1. Planner Agent

Role:
- orchestrates the workflow
- decides which agents to run
- manages execution order
- tracks job state

Responsibilities:
- create job
- trigger workers
- monitor completion
- trigger final decision step

The planner acts as a **central coordinator**, routing tasks to specialized agents.

---

### 2. Worker Agents

Workers are **specialized evaluators**.

Each worker:
- receives scoped input
- performs a specific evaluation
- returns structured output
- does NOT make final decisions

Workers are stateless and focused.

---

## Current worker agents

### Document Analysis Worker

Purpose:
- check required documents

Outputs:
- decision: documents_missing / complete
- flags: missing documents
- reasoning

---

### Policy Retrieval Worker

Purpose:
- validate application against product policy

Outputs:
- decision: policy_match / mismatch
- reasoning
- flags

---

### Risk Assessment Worker

Purpose:
- evaluate financial risk

Inputs:
- income
- expenses
- obligations

Outputs:
- score
- decision: low / medium / high
- flags (e.g. high_dti)
- reasoning

---

### Fraud Verification Worker

Purpose:
- detect fraud indicators

Outputs:
- decision: clear / suspicious
- flags
- reasoning

---

### Decision Summary Worker

Purpose:
- aggregate all worker outputs
- determine final system decision

Outputs:
- decision: approved / rejected / manual_review
- score
- reasoning
- flags

---

## Output contract (MANDATORY)

All agents must return structured JSON:

```json
{
  "score": 0.82,
  "confidence": 0.91,
  "decision": "low_risk",
  "flags": ["high_dti"],
  "reasoning": "DTI ratio is high relative to income."
}