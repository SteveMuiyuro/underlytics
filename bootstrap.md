# BOOTSTRAP.md

## Purpose

This document defines the baseline state of the GCP project before Terraform is applied.

Terraform will assume this state and provision all remaining infrastructure.

---

## Project

Project name:

underlytics

---

## Bootstrap status (already completed)

The following have already been completed manually:

- GCP project `underlytics` exists
- Billing is enabled
- A bootstrap identity with sufficient permissions is available
- The following APIs are already enabled:
  - serviceusage.googleapis.com
  - cloudresourcemanager.googleapis.com
  - iam.googleapis.com

Terraform MUST assume these already exist and must NOT attempt to recreate them.

---

## Architecture target

Terraform should provision infrastructure for the following architecture:

- Frontend: Cloud Storage + Cloud CDN
- API entry: API Gateway
- Backend: Cloud Run (Dockerized FastAPI)
- Async processing: Pub/Sub
- Database: Cloud SQL for PostgreSQL
- AI platform: Vertex AI (Gemini)
- Secrets: Secret Manager
- Registry: Artifact Registry
- CI/CD: GitHub Actions (OIDC / Workload Identity Federation)
- Observability: Cloud Logging + Cloud Monitoring

---

## API Gateway and backend access model

### Important

Do NOT attempt to use a `disable-auth` flag.

Instead, enforce public API access using Cloud Run IAM.

### Required behavior

- Cloud Run backend must allow unauthenticated access
- API Gateway must be publicly accessible
- API Gateway must not require API keys or IAM auth
- API Gateway forwards traffic to Cloud Run

### Required IAM binding

- role: roles/run.invoker
- member: allUsers

---

## APIs Terraform must enable

Terraform should enable the following APIs:

- run.googleapis.com
- artifactregistry.googleapis.com
- cloudbuild.googleapis.com
- apigateway.googleapis.com
- servicemanagement.googleapis.com
- servicecontrol.googleapis.com
- pubsub.googleapis.com
- aiplatform.googleapis.com
- secretmanager.googleapis.com
- sqladmin.googleapis.com
- storage.googleapis.com
- compute.googleapis.com
- iamcredentials.googleapis.com
- sts.googleapis.com
- logging.googleapis.com
- monitoring.googleapis.com
- servicenetworking.googleapis.com

---

## Core infrastructure Terraform must create

### Backend

- Cloud Run service for main API/backend
- Cloud Run service for worker processing

### Database

- Cloud SQL for PostgreSQL
- database instance
- database
- user configuration
- credentials stored in Secret Manager

### Queue / async processing

- Pub/Sub topics
- Pub/Sub subscriptions

### Frontend

- Cloud Storage bucket for static hosting
- Cloud CDN configuration

### API layer

- API Gateway routing to Cloud Run backend

### Secrets

Secret Manager entries for:
- database credentials
- Clerk keys
- Langfuse keys
- application secrets
- Vertex AI / Gemini configuration

### Registry and build

- Artifact Registry repository for backend images

### IAM and identities

- service accounts
- IAM bindings
- Workload Identity Pool
- Workload Identity Provider for GitHub Actions

---

## Service accounts to be created

- terraform-deployer
- underlytics-backend-sa
- underlytics-worker-sa

Optional:
- frontend-deployer-sa
- ci-test-sa

---

## CI/CD requirements

GitHub Actions must be included in the deployment design.

### Required workflows

#### Frontend CI
- install dependencies
- lint
- typecheck
- build

#### Backend CI
- install dependencies (uv)
- lint/format checks
- import validation
- unit tests
- workflow tests
- guardrail tests

#### Terraform CI
- terraform fmt -check
- terraform validate
- terraform plan

#### Deployment workflow
- authenticate to GCP using Workload Identity Federation
- run tests before deployment
- deploy only if tests pass

#### Optional integration tests
- health check backend
- create application
- verify workflow job creation
- verify worker execution

---

## GitHub Actions authentication

Use:

- GitHub OIDC
- Workload Identity Federation

Do NOT use service account keys in GitHub secrets.

Required GitHub permissions:

- contents: read
- id-token: write

---

## IAM expectations

The identity running Terraform must have permissions to:

- enable APIs
- manage IAM and service accounts
- deploy Cloud Run services
- manage Cloud SQL
- manage Pub/Sub
- manage Artifact Registry
- manage Secret Manager
- manage API Gateway
- manage Storage and CDN resources
- configure Workload Identity Federation

---

## Constraints

- Cloud Run is the primary backend compute platform
- Cloud SQL is the Aurora equivalent
- Pub/Sub is the SQS equivalent
- API must be publicly accessible (for now)
- Terraform must NOT attempt to create the project
- Terraform must assume bootstrap state already exists

---

## Deployment readiness

After this bootstrap state:

Codex will:
1. Dockerize the backend locally
2. Generate Terraform
3. Generate GitHub Actions workflows
4. Prepare the system for deployment

---

## Next step

Proceed with Codex Terraform generation using the provided Codex prompt.