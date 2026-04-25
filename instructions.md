Please implement the following fixes and improvements.

## 1. New Application UI conditional fields

On:

https://underlytics.vercel.app/new-application

Update the form behavior:

### Employment status rule
If employment status is:

- self-employed
- unemployed

Then hide/remove the following field from the UI:

- Employer Name label
- Employer Name input

If employment status is employed, show Employer Name normally.

### Existing loan obligations rule
If Existing Loan Obligations is:

- 0
- empty
- not provided

Then hide/remove:

- Bank Name label/input
- Account Type label/select/input

Only show Bank Name and Account Type when Existing Loan Obligations is greater than 0.

Important:
- Preserve form submission
- Do not send irrelevant empty fields if hidden unless backend requires nullable values
- Keep validation aligned with visible fields
- Use shadcn/radix Select for selection fields
- Keep spacing/alignment polished

---

## 2. Agent workflow must become truly agentic

Review the current agent implementation.

The agents should not remain purely deterministic rule functions.

Implement a proper agentic workflow where:

- each agent has a system prompt
- each agent has a specific area of specialty
- each agent returns structured output
- each agent output passes guardrails validation
- agents remain independent workers
- planner orchestrates workers
- decision summary agent aggregates outputs

Required agents:

- Planner Agent
- Document Analysis Agent
- Policy Retrieval Agent
- Risk Assessment Agent
- Fraud Verification Agent
- Decision Summary Agent
- Email Agent

Each LLM-backed agent must have:

- system prompt
- input context
- structured output schema
- allowed decisions
- fallback behavior
- guardrail validation

Prompts should live in:

backend/underlytics_api/agents/prompts/

Do not collapse the workflow into one LLM call.

Do not remove deterministic guardrails.

Provider split:

- Planner Agent → Vertex AI `gemini-2.5-flash`
- Document Analysis Agent → Vertex AI `gemini-2.5-flash`
- Policy Retrieval Agent → Vertex AI `gemini-2.5-flash`
- Risk Assessment Agent → Vertex AI `gemini-2.5-flash`
- Fraud Verification Agent → Vertex AI `gemini-2.5-flash`
- Email Agent → Vertex AI `gemini-2.5-flash`
- Decision Summary Agent → OpenAI `gpt-5.4`, or `gpt-5.3` / `gpt-5.2` when the preferred model is unavailable

Gemini / Vertex AI should remain the primary path for planner and specialist worker execution, with deterministic fallback where needed.

Decision making should use a stronger OpenAI model than the email-generation path.

---

## 3. Email recipient bug

Currently, applicant decision emails are not being sent to the email address used during registration.

Please review and fix the email recipient resolution.

Expected behavior:

- email should be sent to the applicant email associated with the registered Clerk/backend user
- use the email captured during user registration / user sync
- do not send to a placeholder or missing field
- if applicant email is missing, log a clear failed/skipped communication record

Check:

- user sync logic
- application applicant_user_id relationship
- communication/email generation flow
- notification_service recipient selection
- manual review email flow
- approved/rejected automated email flow

Required result:

- approved email goes to applicant registration email
- rejected email goes to applicant registration email
- completed manual review email goes to applicant registration email
- communication_logs stores recipient_email correctly

Add or update tests for:

- applicant email is resolved from user record
- approved email uses applicant email
- rejected email uses applicant email
- manual review completed email uses applicant email
- missing applicant email is handled safely

---

## 4. Keep deployment safe

After changes:

- run frontend lint/typecheck/build
- run backend tests
- ensure deployment does not break Clerk auth
- ensure CORS and CLERK_AUTHORIZED_PARTIES remain unchanged
- do not regress the previous Clerk authorized parties fix

Please provide a summary of changed files and test results.
