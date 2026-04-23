Continue from the current state. Do NOT restart or discard any existing work.

We are implementing a production-grade split deployment architecture:

- Frontend: Vercel
- Backend + workers: GCP (Cloud Run)
- Database: Cloud SQL (PostgreSQL)
- Queue/job processing: Pub/Sub
- AI platform: Vertex AI (Gemini)
- Secrets: Secret Manager
- Registry/build: Artifact Registry
- CI/CD auth: GitHub Actions with Workload Identity Federation

Important:
- Preserve all existing backend Docker, Terraform, and CI work
- Do NOT revert working infrastructure
- Do NOT treat frontend as a GCP static deployment target
- Frontend and backend must be cleanly separated in both infrastructure and CI/CD

---

## 1. Preserve completed work

The following MUST remain intact:

- backend Dockerfile and containerization
- backend health and worker entrypoints
- workflow dispatch system
- backend tests
- guardrail fixes
- existing Terraform scaffolding
- WIF provider and deployer service account
- Artifact Registry repo
- GitHub Actions workflows already created

Proceed from current state, not from scratch.

---

## 2. Terraform restructuring (MANDATORY)

Refactor Terraform into two explicit scopes:

infra/
  backend/
  frontend/

### Backend Terraform (primary, REQUIRED)

Must independently manage:

- GCP APIs
- Artifact Registry
- Cloud Run (API + workers)
- Cloud SQL PostgreSQL
- Pub/Sub
- API Gateway
- Secret Manager
- IAM roles and service accounts
- Workload Identity Federation

Backend Terraform must be fully deployable on its own.

---

### Frontend Terraform (REQUIRED but minimal)

Even though frontend is deployed on Vercel, frontend Terraform MUST exist for best practice.

Frontend Terraform should manage:

- future DNS/domain configuration (if needed)
- shared infrastructure hooks (if needed)
- environment configuration references

Do NOT:
- deploy frontend to GCP
- build bucket/CDN deployment logic
- couple frontend infra to backend infra

Goal:
Frontend Terraform exists for structure and future scalability, not active hosting.

---

## 3. GitHub Actions (MANDATORY split)

All pipelines must be separated and production-grade.

### Required workflows:

#### frontend-ci.yml (REQUIRED)
Runs on every push:
- install dependencies
- lint
- typecheck
- build

#### frontend-deploy.yml (REQUIRED)
- deploy to Vercel
- ONLY after CI passes
- use Vercel CLI or GitHub integration with required checks
- must NOT deploy if CI fails

---

#### backend-ci.yml
- uv install
- lint
- import checks
- unit tests
- workflow tests
- guardrail tests

---

#### terraform-backend.yml
- terraform fmt -check
- terraform validate
- terraform plan

---

#### backend-deploy.yml
- authenticate via Workload Identity Federation
- build Docker image
- push to Artifact Registry
- run Terraform apply
- deploy Cloud Run services

---

## 4. Backend deployment completion

Continue and complete:

1. configure Docker auth for Artifact Registry
2. build and push backend image
3. run full backend Terraform apply
4. wire GitHub Actions using:
   - WIF provider
   - terraform-deployer service account
5. verify end-to-end deployment

---

## 5. Public API behavior

Backend must be publicly accessible.

Do NOT use any fake `disable-auth` flag.

Instead:

- Cloud Run must allow unauthenticated access
- IAM binding:
  role: roles/run.invoker
  member: allUsers
- API Gateway must not require API keys

---

## 6. Secrets and environment configuration

Prepare for:

- database credentials
- Clerk keys
- RESEND_API_KEY
- EMAIL_FROM
- Langfuse keys
- Vertex AI / Gemini config

Use:
- Secret Manager for runtime
- GitHub secrets for CI

Use placeholders if needed.

---

## 7. Agent system rules

Use AGENT_SYSTEM.md strictly.

Maintain:

- planner + worker architecture
- structured outputs
- guardrails (must override LLM)
- explainable reasoning

Do NOT:
- collapse into a single LLM call
- remove guardrails
- return unstructured outputs

Prepare system for Gemini integration via Vertex AI.

---

## 8. Email workflow (REQUIRED)

Implement using Resend.

EMAIL_FROM:
decisions@mail.steveleesuppliers.co.ke

Build:

- communication_logs table
- notification_service.py
- provider abstraction (ResendProvider)

Send emails for:
- approved
- rejected
- completed manual review

Email content must be generated from:
- agent outputs
- reviewer notes (if applicable)

Do NOT use MCP for email.

---

## 9. Frontend deployment model (STRICT)

Frontend is deployed on Vercel.

Requirements:

- no Docker for frontend
- no GCP hosting for frontend
- GitHub Actions must control deploy
- Vercel deployment must be gated by CI

Frontend responsibilities:
- landing page
- auth (Clerk)
- application UI
- calling backend APIs

---

## 10. Final goal

End state must be:

- frontend deployed via Vercel with CI gating
- backend deployed via GCP Cloud Run
- Terraform cleanly separated into backend and frontend scopes
- GitHub Actions fully structured and enforced
- backend infra stable and reproducible
- agent system preserved and ready for LLM upgrade
- email workflow fully integrated


N/b:
Frontend environment variables must be configured in Vercel, not in GCP.

- All NEXT_PUBLIC_* variables belong to the frontend (Vercel)
- Backend secrets must be stored in GCP Secret Manager and GitHub secrets

Do not expose backend secrets to the frontend.

Ensure frontend code only uses safe public environment variables.

Proceed from current state and implement the above structure cleanly.