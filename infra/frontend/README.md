# Underlytics Frontend Terraform

This directory is the minimal Terraform scope for the frontend deployment shape.

The frontend is deployed on Vercel, not GCP. This scope exists to preserve a
clean infrastructure split and to hold future frontend-oriented references such
as domains, environment metadata, and shared integration hooks.

## What it manages

- frontend deployment metadata
- Vercel project references
- optional domain and DNS reference inputs
- backend API base URL references for frontend environments

## What it does not manage

- frontend hosting on GCP
- buckets, CDN, or Cloud Run for the frontend
- backend infrastructure

## Usage

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Fill in the Vercel and domain reference values you want to track.
3. Run:

```bash
terraform init
terraform plan
terraform apply
```
