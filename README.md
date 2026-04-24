# Underlytics

Underlytics is an AI-powered loan underwriting platform that combines a Next.js frontend, a FastAPI backend, an agent-based underwriting workflow, and a cloud deployment pipeline. The product is designed to intake loan applications, orchestrate specialist underwriting agents, apply hard guardrails, surface explainable decisions, and support manual review when automation should not make the final call.

Live application: https://underlytics.vercel.app/

The current repository includes:

- a Clerk-protected frontend application for applicants, reviewers, and admins
- a FastAPI backend API with underwriting, workflow, manual review, and document endpoints
- a planner-plus-worker agent runtime with evaluation persistence
- Terraform and GitHub Actions workflows for backend infrastructure and frontend deployment

## Key Features

- Loan application intake with applicant profile, employment, banking, financial, and document submission flow
- AI-assisted underwriting using a planner plus specialist worker architecture
- Distinct worker agents for document analysis, policy retrieval, risk assessment, and fraud verification
- Explainable decision summaries with structured outputs, reasoning, scores, confidence, and flags
- Guardrails that enforce final decision safety after model output
- Manual review workflow for escalated cases
- Backend API for applications, documents, workflow status, manual review, users, and audit surfaces
- Frontend dashboard for applications, processing state, detail views, and manual review screens
- Evaluation persistence for agent decisions, latency, guardrail adjustments, and tool evidence usage
- CI/CD setup for backend verification, Terraform validation, Cloud Run deployment, and Vercel deployment

## Architecture Overview

### Frontend

The frontend is a Next.js App Router application in `frontend/` using React, TypeScript, Tailwind CSS, shadcn-style UI primitives, and Clerk authentication. It renders the public landing page, authenticated dashboards, application submission flow, processing screen, application detail pages, and manual review views. Frontend server helpers proxy authenticated requests to the backend with Clerk bearer tokens.

### Backend

The backend is a FastAPI application in `backend/underlytics_api/` backed by SQLAlchemy models and Alembic migrations. It exposes application, workflow, document, agent-output, evaluation, manual-review, and user-management routes. The backend also contains the orchestration runtime, guardrails, evaluation persistence, notification service, and a worker app for Pub/Sub-triggered workflow execution.

### Agent Workflow

Underlytics uses a Planner + Worker architecture defined in [AGENTS.md](./AGENTS.md). The planner orchestrates workflow execution. Specialist workers evaluate scoped evidence independently. A decision summary agent proposes an outcome. Deterministic guardrails then enforce the final underwriting decision. Worker outputs are structured, explainable, and stored for audit and review.

### Cloud Deployment Flow

The backend deployment targets Google Cloud and provisions Cloud Run, Pub/Sub, Cloud SQL, API Gateway, Secret Manager, Artifact Registry, and GitHub Workload Identity Federation. The frontend is deployed on Vercel, while Terraform in `infra/frontend` tracks frontend deployment metadata and integration references. GitHub Actions validates code, runs tests, applies Terraform, builds backend images, and deploys to production surfaces.

Current live frontend URL: https://underlytics.vercel.app/

## Architecture Diagrams

### Frontend Flow

```mermaid
flowchart LR
    user[User] --> browser[Browser]
    browser --> clerk[Clerk Authentication]
    browser --> frontend[Next.js Frontend App]
    frontend --> apiClient[Frontend API Client / Route Handlers]
    apiClient --> backend[FastAPI Backend API]
```

### Backend / Agent Flow

```mermaid
flowchart TD
    intake[Application + Documents] --> api[FastAPI Backend API]
    api --> planner[Planner Agent]
    planner --> workers[Worker Agents]
    workers --> structured[Structured Worker Outputs]
    structured --> summary[Decision Summary Agent]
    summary --> guardrails[Deterministic Guardrails]
    guardrails --> decision[Final Underwriting Decision]
    decision --> notify[Email / Notification Service]
    planner --> db[(Database / Persistence)]
    workers --> db
    summary --> db
    guardrails --> db
    notify --> db
```

### CI/CD Flow

```mermaid
flowchart TD
    gitpush[GitHub Push / PR] --> gha[GitHub Actions]
    gha --> backendci[Backend CI]
    gha --> frontendci[Frontend CI]
    gha --> tfbackend[Terraform Backend]
    gha --> tffrontend[Terraform Frontend]
    backendci --> backenddeploy[Backend Deploy Workflow]
    frontendci --> frontenddeploy[Frontend Deploy Workflow]
    backenddeploy --> cloud[Cloud Run / API Gateway / PubSub / Cloud SQL / Secrets]
    frontenddeploy --> vercel[Vercel Production Deployment]
```

## Tech Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- Clerk for authentication
- Lucide React icons
- shadcn-style component primitives

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- Python 3.12
- Uvicorn
- Python Multipart for file uploads

### AI / Agents

- OpenAI Agents SDK
- Google Gen AI SDK for Vertex AI
- Planner + Worker runtime with provider abstraction
- Vertex AI Gemini 2.5 for planner and specialist workers
- OpenAI GPT-5.4 for decision synthesis
- Evaluation persistence for audit and replay surfaces

### Infrastructure

- Terraform
- Google Cloud Run
- Google Cloud Pub/Sub
- Google Cloud SQL
- Google Artifact Registry
- Google Secret Manager
- Google API Gateway
- Vercel

### DevOps / Observability

- GitHub Actions
- Ruff
- Pytest
- ESLint
- TypeScript typecheck
- Langfuse tracing

## Repository Structure

```text
.
├── AGENTS.md
├── backend/
│   ├── alembic/
│   ├── scripts/
│   ├── tests/
│   ├── underlytics_api/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── mcp_fixtures/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── middleware.ts
│   └── package.json
├── infra/
│   ├── backend/
│   ├── frontend/
│   └── terraform/
└── .github/
    └── workflows/
```

Important directories and files:

- `AGENTS.md`: source of truth for the planner-plus-worker architecture and safety rules
- `backend/underlytics_api/api/`: FastAPI route definitions
- `backend/underlytics_api/services/`: orchestration, agent runtime, guardrails, notification, and workflow services
- `backend/underlytics_api/models/`: persistence models for applications, workflow state, agent outputs, evaluations, and manual review
- `backend/underlytics_api/agents/prompts/`: per-agent prompt definitions and model metadata
- `backend/alembic/`: database migration history
- `backend/tests/`: backend test suite
- `frontend/app/`: Next.js routes and page composition
- `frontend/components/`: UI and domain-specific components
- `frontend/lib/api/`: frontend API clients and route proxy helpers
- `infra/backend/`: primary backend Terraform scope for GCP
- `infra/frontend/`: frontend Terraform scope for deployment metadata and references
- `.github/workflows/`: CI, Terraform, and deployment workflows

## Local Development Setup

### Prerequisites

- Node.js 22 or newer
- npm
- Python 3.12
- `uv`
- SQLite for local default backend storage, or PostgreSQL if you override `DATABASE_URL`
- Clerk development credentials if you want authenticated flows
- OpenAI and Vertex credentials if you want live model execution locally
- Google Application Default Credentials locally if you want Vertex-backed agents to run outside test mode

### Environment Variables

Create local env files as needed:

- `frontend/.env.local`
- `backend/.env`

See the environment variable table below for the expected names.

### Frontend Setup

```bash
cd frontend
npm ci
npm run dev
```

### Backend Setup

```bash
cd backend
uv sync --dev
uv run alembic upgrade head
uv run uvicorn underlytics_api.main:app --reload
```

If you want live Vertex-backed planner and worker execution locally, authenticate Google Application Default Credentials first:

```bash
gcloud auth application-default login
```

Optional worker app for async workflow execution:

```bash
cd backend
uv run uvicorn underlytics_api.worker_app:app --reload --port 8001
```

### Run Tests

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
```

Backend:

```bash
cd backend
uv run ruff check .
uv run pytest
```

### Run the Full App Locally

1. Start the backend API.
2. Start the frontend app.
3. Sign in through Clerk.
4. Create or sync a backend user.
5. Submit a new application with the required documents.

## Environment Variables

The table below uses placeholders only.

| Variable | Scope | Required | Example Placeholder | Purpose |
| --- | --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Frontend | Yes | `http://localhost:8000` | Base URL for backend API access |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Frontend | Yes | `pk_test_xxx` | Clerk frontend authentication |
| `CLERK_SECRET_KEY` | Frontend deploy/runtime | Yes for Clerk production usage | `sk_test_xxx` | Clerk server-side auth integration |
| `CLERK_AUTHORIZED_PARTIES` | Frontend and backend | Recommended | `http://localhost:3000,https://underlytics.vercel.app` | Allowed origins / parties for Clerk tokens |
| `DATABASE_URL` | Backend | Yes | `postgresql://user:pass@host/db` | Primary backend database |
| `OPENAI_API_KEY` | Backend | Yes for live decision/email agents | `sk-...` | OpenAI model access |
| `GOOGLE_CLOUD_PROJECT` | Backend | Yes for live Vertex runtime | `my-gcp-project` | Vertex and Pub/Sub project selection |
| `GOOGLE_CLOUD_LOCATION` | Backend | Recommended | `us-central1` | Vertex runtime region |
| `VERTEX_LOCATION` | Backend / infra compatibility | Optional | `us-central1` | Backward-compatible Vertex location input |
| `PUBSUB_WORKFLOW_TOPIC` | Backend | Optional / required for async mode | `underwriting-workflows` | Pub/Sub topic name |
| `WORKFLOW_EXECUTION_MODE` | Backend | Optional | `sync` | Sync or Pub/Sub workflow execution |
| `RESEND_API_KEY` | Backend | Required for real email sending | `re_xxx` | Transactional email provider |
| `EMAIL_FROM` | Backend | Required for real email sending | `no-reply@example.com` | Sender address |
| `LANGFUSE_PUBLIC_KEY` | Backend | Optional but recommended | `pk-lf-xxx` | Langfuse tracing |
| `LANGFUSE_SECRET_KEY` | Backend | Optional but recommended | `sk-lf-xxx` | Langfuse tracing |
| `LANGFUSE_BASE_URL` | Backend | Optional | `https://cloud.langfuse.com` | Preferred Langfuse base URL |
| `LANGFUSE_HOST` | Backend / infra compatibility | Optional | `https://cloud.langfuse.com` | Backward-compatible Langfuse host alias |
| `ADMIN_BOOTSTRAP_SECRET` | Backend | Optional | `change-me` | Bootstrap first admin user |
| `CLERK_JWT_KEY` | Backend | Optional | `-----BEGIN PUBLIC KEY-----...` | Backend Clerk JWT verification |
| `CLERK_JWT_ISSUER` | Backend | Optional | `https://clerk.example.com` | Clerk issuer override |
| `CLERK_PUBLISHABLE_KEY` | Backend | Optional | `pk_test_xxx` | Backend fallback for issuer inference |
| `CORS_ALLOWED_ORIGINS` | Backend | Recommended | `http://localhost:3000,https://underlytics.vercel.app` | Backend CORS allowlist |

## Backend API Overview

Authentication notes:

- Most application-facing routes require a verified Clerk bearer token.
- Reviewer and admin routes enforce role checks in the backend.
- `GET /` and `GET /healthz` are public health routes.

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/` | API root health/info | Public |
| `GET` | `/healthz` | Health check | Public |
| `GET` | `/api/applications` | List applications visible to current actor | Clerk token required |
| `GET` | `/api/applications/stats` | Portfolio/application counts | Clerk token required |
| `GET` | `/api/applications/{application_number}` | Get one application | Clerk token required |
| `GET` | `/api/applications/{application_number}/workflow-status` | Processing/progress view for frontend polling | Clerk token required |
| `GET` | `/api/applications/{application_number}/evaluations` | Flat list of agent evaluation records | Clerk token required |
| `POST` | `/api/applications` | Create an application | Clerk token required |
| `POST` | `/api/documents/upload` | Upload or replace a required document | Clerk token required |
| `GET` | `/api/application-documents/{application_id}` | List uploaded documents for an application | Clerk token required |
| `GET` | `/api/workflow/applications/{application_number}/job` | Get latest underwriting job | Clerk token required |
| `GET` | `/api/workflow/jobs/{job_id}/agent-runs` | Get legacy agent run records for a workflow job | Clerk token required |
| `GET` | `/api/agent-outputs/applications/{application_id}` | Get stored agent outputs | Clerk token required |
| `GET` | `/api/loan-products` | List active loan products | Public in code today |
| `GET` | `/api/manual-review/cases` | List manual review cases | Reviewer/Admin required |
| `GET` | `/api/manual-review/cases/{case_id}` | Get one manual review case | Reviewer/Admin required |
| `POST` | `/api/manual-review/cases/{case_id}/actions` | Add manual review action or resolution | Reviewer/Admin required |
| `GET` | `/api/users/applicants` | List applicant users | Reviewer/Admin required |
| `GET` | `/api/users` | List all users | Admin required |
| `POST` | `/api/users/sync` | Sync Clerk identity into backend user table | Clerk token required |
| `POST` | `/api/users/bootstrap-admin` | Promote current synced user to admin via bootstrap secret | Clerk token required |
| `PATCH` | `/api/users/{user_id}/role` | Update a user role | Admin required |

## Agent System Overview

Underlytics uses a Planner + Worker architecture and deliberately avoids collapsing underwriting into a single model call.

Current agent identifiers:

- `planner`
- `document_analysis`
- `policy_retrieval`
- `risk_assessment`
- `fraud_verification`
- `decision_summary`
- `email_agent`

Core principles:

- The planner orchestrates workflow execution but must not approve or reject applications.
- Worker agents are scoped specialists and must not share hidden state.
- Workers must not make final approval decisions.
- The decision summary agent proposes a final outcome from worker outputs.
- Deterministic guardrails enforce the real final decision.
- Email generation is separate from email delivery.

Current provider split:

- Vertex AI Gemini 2.5 Flash for planner and specialist workers
- OpenAI GPT-5.4 for `decision_summary`
- OpenAI GPT-5.4 Mini for `email_agent`

The runtime also includes:

- per-agent prompt files
- structured output validation
- evaluation persistence
- prompt/model metadata capture
- staged MCP-style evidence inputs for selected workers

## Deployment

### Backend

Backend deployment is driven by:

- `.github/workflows/backend-ci.yml`
- `.github/workflows/backend-deploy.yml`
- `infra/backend/`

Current behavior:

- `Backend CI` runs on PRs and pushes to `main` affecting backend files
- `Backend Deploy` runs on pushes to `main` affecting backend or backend infra, or manually
- the deploy workflow validates prerequisites, runs backend verification, applies Terraform, builds and pushes the backend image, and deploys Cloud Run resources

Required GitHub repository variables and secrets referenced by the workflows include:

- Variables:
  - `GCP_PROJECT_ID`
  - `GCP_REGION`
  - `GCP_DB_REGION`
  - `GCP_WIF_PROVIDER`
  - `GCP_TERRAFORM_SERVICE_ACCOUNT`
  - `GITHUB_REPOSITORY_SLUG`
  - `CORS_ALLOWED_ORIGINS`
  - `VERTEX_LOCATION`
  - `VERTEX_MODEL`
- Secrets:
  - `TF_VAR_ADMIN_BOOTSTRAP_SECRET`
  - `TF_VAR_CLERK_JWT_KEY`
  - `TF_VAR_CLERK_JWT_ISSUER`
  - `TF_VAR_CLERK_PUBLISHABLE_KEY`
  - `TF_VAR_CLERK_SECRET_KEY`
  - `TF_VAR_CLERK_AUTHORIZED_PARTIES`
  - `TF_VAR_CLERK_WEBHOOK_SECRET`
  - `TF_VAR_LANGFUSE_PUBLIC_KEY`
  - `TF_VAR_LANGFUSE_SECRET_KEY`
  - `TF_VAR_LANGFUSE_HOST`
  - `TF_VAR_OPENAI_API_KEY`
  - `TF_VAR_RESEND_API_KEY`
  - `TF_VAR_EMAIL_FROM`

### Frontend

Frontend deployment is driven by:

- `.github/workflows/frontend-ci.yml`
- `.github/workflows/frontend-deploy.yml`
- `infra/frontend/`

Current behavior:

- `Frontend CI` runs on pushes, PRs, and manual dispatch
- `Frontend Deploy` runs after successful `Frontend CI` on `main`
- `Terraform Frontend` validates and plans the frontend Terraform scope
- Vercel CLI is used for production deployment

Required GitHub repository variables and secrets include:

- Variables:
  - `VERCEL_PROJECT_ID`
  - `VERCEL_ORG_ID`
  - `VERCEL_PROJECT_NAME`
  - `FRONTEND_DOMAIN`
  - `NEXT_PUBLIC_API_URL` or `BACKEND_API_BASE_URL`
  - `CLERK_PUBLISHABLE_KEY_REFERENCE`
- Secrets:
  - `VERCEL_TOKEN`

## Production Readiness

### Security Considerations

- Clerk bearer tokens are enforced in backend application routes
- backend access control distinguishes applicant, reviewer, and admin roles
- CORS is explicit rather than wildcard-based
- secrets are expected to be managed through Terraform + Secret Manager / Vercel envs

### Audit Logging and Traceability

- workflow state is persisted
- agent outputs are stored
- agent evaluations are stored
- prompt/model metadata is captured
- Langfuse tracing hooks are implemented

### Validation

- structured agent outputs are validated against strict schemas
- unsupported decisions fail validation
- guardrails enforce final approval safety
- document upload types are restricted to supported required documents

### Error Handling

- malformed or invalid agent outputs fail safely
- manual review exists for non-automatable or ambiguous cases
- document upload failures surface to the user path
- workflow failures are reflected in the processing UI

### Monitoring / Logging

- Langfuse is integrated
- OpenAI tracing hooks are present
- Cloud deployment workflows publish summaries

### Test Strategy

- backend unit and service tests cover:
  - guardrails
  - planner output handling
  - workflow status
  - notification flows
  - provider runtime dispatch
  - MCP evidence normalization
  - evaluation persistence
- frontend CI currently runs lint, typecheck, and build

### Failure Handling

- guardrails override unsafe automated approvals
- workflows can route to manual review
- email send failures do not roll back decision state
- async execution can run through Pub/Sub worker processing

### Future Scalability

- the architecture already separates planner, workers, summary, and notifications
- provider abstraction allows model changes without rewriting orchestration logic
- workflow execution mode supports sync now and Pub/Sub-backed async mode
- the repo is structured for more MCP-backed evidence sources later

## Current Project Status

### Implemented

- Clerk-protected frontend application
- applicant application intake flow
- required document submission during application creation
- application processing screen with real workflow polling
- application detail page with workflow, outputs, and submitted document inventory
- backend orchestration foundation with persisted workflow plans, steps, and attempts
- planner-plus-worker runtime with structured outputs
- decision-summary guardrails
- manual review queue and resolution flow
- notification service and communication logs
- agent evaluation persistence and read API
- Terraform for backend GCP stack and frontend metadata
- GitHub Actions CI and deployment workflows

### Partially Implemented

- MCP-style evidence inputs exist for `policy_retrieval` and `fraud_verification`, but the fraud source is currently fixture-backed rather than a true production intelligence integration
- async execution path exists through Pub/Sub and `worker_app`, but not every local workflow uses that path by default
- observability hooks exist, but production-grade tracing depends on environment configuration

### Pending / Incomplete

- a real production fraud / registry evidence integration
- broader production smoke testing against live Vertex + OpenAI credentials
- richer frontend visibility for evaluation records
- stronger migration and release discipline around all future model/runtime changes
- some infrastructure and repo artifacts still reflect active development rather than a finalized production baseline

## Roadmap

### Short-Term

- replace fixture-backed fraud evidence with a real trusted integration
- add a lightweight evaluation panel in the application detail UI
- run staging validation against live model credentials
- tighten production rollout checklists and smoke tests
- improve migration discipline for future schema changes

### Long-Term

- queue-backed resumable workflow execution at larger scale
- richer reviewer tooling and case analytics
- more external evidence sources through controlled MCP integrations
- stronger evaluation datasets and regression harnesses
- advanced portfolio analytics and operational dashboards

## Contributing / Development Rules

- Preserve the modular planner-plus-worker architecture.
- Do not collapse underwriting into a single monolithic LLM call.
- Keep worker outputs structured, scoped, explainable, and auditable.
- Keep deterministic guardrails in place for final decision enforcement.
- Do not let specialist workers make final approval decisions.
- Mark incomplete features honestly rather than presenting them as finished.
- When changing providers, prompts, or tools, preserve auditability and validation behavior.

## Quick Review Notes

This README intentionally reflects the repository as it exists today:

- it describes the hybrid agent runtime that is implemented in code
- it calls out fixture-backed fraud evidence as a current limitation
- it documents the real GitHub Actions workflows and Terraform layout
- it avoids claiming that every production concern is fully closed
