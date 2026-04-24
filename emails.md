# emails.md

## Purpose

This document defines how Codex must implement applicant email notifications for the Underlytics backend.

Underlytics must notify applicants using the email address they registered with. Email notifications are sent only after meaningful underwriting status changes.

The email system must use Resend, must log every send attempt, and must generate HTML-formatted applicant-facing emails.

---

# 1. Core Email Flow

Email notifications happen after the agentic underwriting workflow reaches a decision or requires manual review.

## Standard Agent-Completed Flow

If the application is fully handled by the agentic workflow and reaches a final decision, the applicant receives one email.

```text
Application Submitted
  ↓
Agentic Workflow Runs
  ↓
Final Decision: approved or rejected
  ↓
Send One Decision Email
```

## Manual Review Flow

If the workflow routes the application to manual review, the applicant receives two emails.

```text
Application Submitted
  ↓
Agentic Workflow Runs
  ↓
Decision Requires Manual Review
  ↓
Send Manual Review Escalation Email
  ↓
Human Reviewer Completes Review
  ↓
Final Decision: approved or rejected
  ↓
Send Final Decision Email
```

## Required Email Count Rules

- If agents complete the workflow with a final decision, send one email.
- If the application is escalated to manual review, send one email confirming escalation.
- After manual review is completed, send one final decision email.
- Manual review cases therefore result in two emails total.
- Do not send duplicate emails for the same status transition.

---

# 2. Email Recipient Source

The applicant email must come from the email address the user used to register or submit the application.

Codex must determine the recipient from the applicant or user record linked to the application.

If the recipient email is missing:

- Do not send the email.
- Log the communication as failed or skipped.
- Do not crash the underwriting workflow.
- Do not roll back the application decision.

---

# 3. Environment Variables

Required backend runtime environment variables:

```env
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=decisions@mail.steveleesuppliers.co.ke
```

Rules:

- These variables must only be used in the backend.
- Never expose these values to the frontend.
- Never log the Resend API key.
- If `RESEND_API_KEY` is missing, email sending must fail safely and log the failure.

---

# 4. Communication Logs

Create or preserve a `communication_logs` table.

## Required Fields

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

## Allowed Statuses

```text
pending
sent
failed
skipped
```

## Provider

```text
resend
```

## Logging Rules

Codex must log every email attempt.

The system must log:

- successful emails
- failed emails
- skipped emails caused by missing recipient email
- provider message ID when available
- safe error message when sending fails

The system must not log:

- API keys
- secrets
- raw provider credentials
- full internal traces
- sensitive applicant data beyond what is necessary for auditability

---

# 5. Notification Service

Create or preserve:

```text
backend/underlytics_api/services/notification_service.py
```

## Expected Function Shape

```python
def send_application_email(
    *,
    db,
    application_id: str,
    to_email: str,
    subject: str,
    html_body: str,
) -> CommunicationLog:
    ...
```

## Responsibilities

The Notification Service must:

- Accept recipient email, subject, and HTML body.
- Use the configured email provider.
- Send email through Resend.
- Create or update a communication log.
- Mark the communication as sent, failed, or skipped.
- Return the communication log record.
- Never crash the underwriting workflow if email sending fails.
- Never roll back an underwriting decision because email sending failed.
- Never expose raw provider errors to applicants.

---

# 6. Email Provider Interface

Create or preserve a provider abstraction.

```python
from typing import Protocol


class EmailProvider(Protocol):
    def send(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
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

## ResendProvider Responsibilities

The Resend provider must:

- Call the Resend API.
- Send HTML-formatted email.
- Return the provider message ID.
- Raise clear backend-safe errors on failure.
- Never log the API key.
- Never expose provider internals to applicants.

---

# 7. Email Generation Logic

Create or preserve an agent-driven email generation function.

```python
def generate_application_email(
    *,
    application,
    agent_outputs,
    email_type: str,
    reviewer_note: str | None = None,
    reviewer_decision: str | None = None,
) -> dict:
    ...
```

It must return:

```json
{
  "subject": "Your Underlytics application update",
  "html_body": "<html>...</html>"
}
```

## Rules

- The returned body must be HTML formatted.
- The content must be applicant-facing.
- The content must be clear, professional, and concise.
- The content must not include raw agent JSON.
- The content must not expose hidden reasoning.
- The content must not expose internal workflow logs.
- The content must not mention technical terms like guardrails, agent outputs, LLMs, traces, or retries.
- Reviewer notes must be rewritten into applicant-safe language.

The implementation may start deterministic, but it must be structured so it can later call the Email Agent through Gemini or Vertex AI.

---

# 8. HTML Email Requirements

All applicant emails must be HTML formatted.

Use a simple, compatible email layout.

Required qualities:

- clean HTML structure
- inline-friendly styling
- professional fintech tone
- readable on mobile and desktop
- no heavy JavaScript
- no frontend framework dependencies
- no external scripts

Recommended structure:

```html
<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif; color: #111827; background: #f8fafc; padding: 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0" role="presentation" style="background: #ffffff; border-radius: 12px; padding: 24px;">
            <tr>
              <td>
                <h1>Your Underlytics application update</h1>
                <p>Hello,</p>
                <p>...</p>
                <p>Regards,<br />The Underlytics Team</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
```

---

# 9. Email Types and Trigger Rules

## 9.1 Approved by Agentic Workflow

Trigger when:

```text
application.status == "approved"
```

and the application was not previously in manual review.

Send one final decision email.

The email should include:

- approval message
- concise reason for approval
- key positive factors
- next steps
- application reference number

Do not include:

- raw scores unless intentionally designed for applicants
- internal agent names unless presented in simple user-friendly language
- hidden reasoning

---

## 9.2 Rejected by Agentic Workflow

Trigger when:

```text
application.status == "rejected"
```

and the application was not previously in manual review.

Send one final decision email.

The email should include:

- clear rejection message
- main applicant-safe reason
- respectful tone
- optional improvement guidance
- application reference number

Avoid harsh language.

---

## 9.3 Escalated to Manual Review

Trigger when:

```text
application.status == "manual_review"
```

Send a manual review escalation email.

The email should confirm:

- the application has been received
- the automated review is complete
- the application requires manual review
- a reviewer will assess the application
- the applicant will receive another email after the review is complete
- application reference number

This is not a final decision email.

Do not say the application is approved or rejected.

---

## 9.4 Manual Review Completed: Approved

Trigger when application status changes from:

```text
manual_review → approved
```

Send a final decision email.

The email should include:

- approval message
- reviewer-safe summary
- next steps
- application reference number

Reviewer notes may be included only after being rewritten into applicant-safe wording.

---

## 9.5 Manual Review Completed: Rejected

Trigger when application status changes from:

```text
manual_review → rejected
```

Send a final decision email.

The email should include:

- clear rejection message
- reviewer-safe summary
- respectful explanation
- optional improvement guidance
- application reference number

Reviewer notes may be included only after being rewritten into applicant-safe wording.

---

# 10. Deduplication Rules

Codex must prevent duplicate emails.

Recommended approach:

- Check `communication_logs` before sending.
- Use `application_id` plus `email_type` or equivalent metadata if available.
- Do not resend the same notification for the same status transition.

Required email types:

```text
agent_final_approved
agent_final_rejected
manual_review_escalated
manual_review_final_approved
manual_review_final_rejected
```

If the existing table does not support `email_type`, Codex may add it if appropriate.

---

# 11. Trigger Points

Email sending should happen after these backend events:

## Agentic Workflow Completed

When the workflow completes and final status is:

```text
approved
rejected
manual_review
```

Send the appropriate email.

## Manual Review Finalized

When a reviewer changes the application from manual review to a final status:

```text
approved
rejected
```

Send the manual review final decision email.

---

# 12. Tone Requirements

All applicant emails must be:

- professional
- clear
- concise
- empathetic
- respectful
- non-technical
- applicant-friendly

Especially for rejection emails:

- Avoid blame.
- Avoid harsh wording.
- Explain the decision at a high level.
- Provide useful next steps where possible.

---

# 13. Manual Review Email Copy Guidance

## Manual Review Escalation Email Should Say

The application has been received and reviewed by the automated workflow, but it requires additional review by the Underlytics team before a final decision can be made.

## Manual Review Escalation Email Must Not Say

- The application is approved.
- The application is rejected.
- The applicant failed checks.
- The system detected fraud.
- The AI made a final decision.

---

# 14. Failure Handling

If email generation fails:

- Log the failure.
- Do not crash the workflow.
- Do not roll back the decision.

If email sending fails:

- Log the failed attempt.
- Store a safe error message.
- Do not expose the provider error to the applicant.
- Do not retry endlessly.

If applicant email is missing:

- Mark the communication as skipped or failed.
- Continue the workflow safely.

---

# 15. Testing Requirements

Add or preserve tests for:

- approved final decision email
- rejected final decision email
- manual review escalation email
- manual review final approval email
- manual review final rejection email
- no duplicate emails for the same status transition
- communication log created on successful send
- communication log created on failed send
- missing applicant email handled safely
- Resend provider mocked correctly
- HTML body generated for every email type
- email service does not crash underwriting workflow on provider failure

---

# 16. What Codex Must Not Do

Codex must not:

- Send emails from the frontend.
- Expose `RESEND_API_KEY` to the frontend.
- Send email directly from an LLM agent.
- Use MCP for email sending in v1.
- Skip communication logging.
- Send duplicate emails for the same status transition.
- Send a final approval or rejection email when the status is only `manual_review`.
- Use raw internal reasoning in applicant emails.
- Include raw JSON, traces, prompts, secrets, tokens, or system logs in emails.
- Crash the underwriting workflow because email failed.
- Roll back application decisions because email failed.
- Use plain text only; emails must be HTML formatted.

---

# 17. Implementation Order

Codex should implement in this order:

1. Confirm where applicant email is stored.
2. Create or update `communication_logs`.
3. Add email type support for deduplication if needed.
4. Create provider abstraction.
5. Implement `ResendProvider`.
6. Create `notification_service.py`.
7. Create deterministic HTML email generation logic.
8. Trigger email after agentic workflow final status.
9. Trigger manual review escalation email when status becomes `manual_review`.
10. Trigger manual review final decision email after reviewer completes review.
11. Add tests for all email cases.
12. Ensure secrets stay backend-only.

---

# 18. End Goal

Underlytics email notifications must give applicants clear, professional updates at the right time.

The expected behavior is:

- one email when the agentic workflow reaches a final approved or rejected decision
- one escalation email when manual review is required
- one final decision email after manual review is completed
- all emails are HTML formatted
- all sends are logged
- failures are handled safely
- secrets remain protected
