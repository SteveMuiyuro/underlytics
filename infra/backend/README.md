# Underlytics Backend Terraform

This directory is the primary Terraform scope for the GCP backend stack.

## What it creates

- Artifact Registry for backend and worker images
- Cloud Run backend service
- Cloud Run worker service
- Pub/Sub topics and push subscription
- Cloud SQL for PostgreSQL
- Secret Manager secrets and initial versions
- API Gateway pointing at the backend Cloud Run service
- Workload Identity Federation for GitHub Actions

## Frontend boundary

The frontend is now treated as a Vercel deployment target and is intentionally
excluded from this Terraform scope. GCP frontend bucket/CDN resources are not
managed here.

## Required inputs

- `project_id`: use `underlytics`, which `git.md` confirmed as the real GCP project ID.
- `github_repository`: the GitHub repository in `owner/name` form used by Workload Identity Federation. The confirmed value is `SteveMuiyuro/underlytics` without the `.git` suffix.
- Initial secret values for anything you already have available, especially Clerk and the bootstrap admin secret.

The Terraform variables and GitHub Actions workflows are intentionally parameterized so the repository slug can be overridden later with a GitHub repository variable if needed.

## Usage

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Set the real `project_id` and `github_repository`.
3. Provide any initial secret values you already have.
4. Run:

```bash
terraform init
terraform plan
terraform apply
```

## Deploy flow

The GitHub Actions deployment workflow uses a two-phase apply:

1. A targeted Terraform apply creates the required APIs and Artifact Registry repository.
2. GitHub Actions builds and pushes the backend image.
3. Terraform performs the full apply so Cloud Run, API Gateway, Pub/Sub, Cloud SQL, and the rest of the stack are created against a real image tag.
