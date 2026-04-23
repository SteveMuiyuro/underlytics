Implement email notifications using Resend for the Underlytics backend.

## Environment variables
- RESEND_API_KEY
- EMAIL_FROM (e.g. decisions@mail.steveleesuppliers.co.ke)

---

## 1. Create communication_logs table

Fields:
- id
- application_id
- recipient_email
- subject
- body
- status (sent/failed)
- provider_message_id
- created_at

---

## 2. Create notification_service.py

Responsibilities:
- send email using Resend API
- accept:
    - to_email
    - subject
    - body
- return provider message id
- handle errors
- log result in communication_logs

---

## 3. Create email generation logic (agent-driven)

Create a function:
generate_application_email(application, agent_outputs, reviewer_note=None)

It should return:
- subject
- body (clear, professional, non-technical)

---

## 4. Email rules

### Case 1: Approved
Trigger when:
application.status == "approved"

Include:
- approval message
- key reasons
- next steps

---

### Case 2: Rejected
Trigger when:
application.status == "rejected"

Include:
- clear explanation
- main risk factors
- improvement guidance (optional)

---

### Case 3: Manual review (initial)
DO NOT send email

---

### Case 4: Manual review completed
Trigger when:
application.status changes from "manual_review" to final decision

Include:
- final decision
- reviewer note
- summary explanation

---

## 5. Trigger point

After workflow completes OR manual review is finalized:
- call notification_service.send_email()

---

## 6. Tone requirements

- professional
- clear
- empathetic (especially for rejection)
- concise
- no technical jargon

---

## 7. Future-proofing

Design notification_service with interface:

class EmailProvider:
    def send(...)

Implement ResendProvider first.

---

## 8. Do NOT use MCP

Email sending should be:
- deterministic backend service
- not an MCP tool