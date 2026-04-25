variable "project_id" {
  description = "Existing GCP project ID created during manual bootstrap."
  type        = string
}

variable "project_name" {
  description = "Display name used for resource naming context."
  type        = string
  default     = "underlytics"
}

variable "region" {
  description = "Primary GCP region for Cloud Run, Artifact Registry, and API Gateway."
  type        = string
  default     = "us-central1"
}

variable "db_region" {
  description = "Region for Cloud SQL."
  type        = string
  default     = "us-central1"
}

variable "db_tier" {
  description = "Cloud SQL machine tier."
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "underlytics"
}

variable "db_user" {
  description = "PostgreSQL user name."
  type        = string
  default     = "underlytics_app"
}

variable "github_repository" {
  description = "GitHub repository in owner/name form for Workload Identity Federation."
  type        = string
}

variable "image_tag" {
  description = "Container image tag to deploy to Cloud Run services."
  type        = string
  default     = "latest"
}

variable "admin_bootstrap_secret" {
  description = "Initial backend admin bootstrap secret."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_jwt_key" {
  description = "Optional Clerk JWT PEM public key. Leave empty to use Clerk JWKS issuer verification."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_jwt_issuer" {
  description = "Clerk JWT issuer root URL. Must not be the JWKS endpoint."
  type        = string
  sensitive   = true
  default     = "https://primary-grouse-65.clerk.accounts.dev"

  validation {
    condition = (
      trimspace(nonsensitive(var.clerk_jwt_issuer)) != "" &&
      startswith(nonsensitive(var.clerk_jwt_issuer), "https://") &&
      !strcontains(nonsensitive(var.clerk_jwt_issuer), "/.well-known/jwks.json")
    )
    error_message = "clerk_jwt_issuer must be a non-empty issuer root URL, for example https://primary-grouse-65.clerk.accounts.dev, not the JWKS URL."
  }
}

variable "clerk_publishable_key" {
  description = "Clerk publishable key used by backend auth fallback logic."
  type        = string
  sensitive   = true
  default     = "pk_test_cHJpbWFyeS1ncm91c2UtNjUuY2xlcmsuYWNjb3VudHMuZGV2JA"

  validation {
    condition = (
      startswith(nonsensitive(var.clerk_publishable_key), "pk_test_") ||
      startswith(nonsensitive(var.clerk_publishable_key), "pk_live_")
    )
    error_message = "clerk_publishable_key must start with pk_test_ or pk_live_."
  }
}

variable "clerk_secret_key" {
  description = "Optional Clerk secret key reserved for future runtime integration."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_authorized_parties" {
  description = "Comma-separated Clerk authorized parties for backend token validation."
  type        = string
  sensitive   = true
  default     = "http://localhost:3000,https://underlytics.vercel.app,https://underlytics-steve-mwangis-projects.vercel.app,https://underlytics-git-main-steve-mwangis-projects.vercel.app"

  validation {
    condition = trimspace(nonsensitive(var.clerk_authorized_parties)) != "" && length(setsubtract(
      toset([
        "http://localhost:3000",
        "https://underlytics.vercel.app",
        "https://underlytics-steve-mwangis-projects.vercel.app",
        "https://underlytics-git-main-steve-mwangis-projects.vercel.app",
      ]),
      toset([
        for party in split(",", nonsensitive(var.clerk_authorized_parties)) : trimspace(party)
        if trimspace(party) != ""
      ])
    )) == 0
    error_message = "clerk_authorized_parties must include the required localhost and Vercel Clerk origins."
  }
}

variable "clerk_webhook_secret" {
  description = "Optional Clerk webhook secret reserved for future webhook verification."
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_public_key" {
  description = "Optional Langfuse public key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Optional Langfuse secret key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_host" {
  description = "Optional Langfuse host override."
  type        = string
  default     = "https://cloud.langfuse.com"
}

variable "openai_api_key" {
  description = "Optional OpenAI API key for future model providers."
  type        = string
  sensitive   = true
  default     = ""
}

variable "resend_api_key" {
  description = "Optional Resend API key reserved for outbound email integration."
  type        = string
  sensitive   = true
  default     = ""
}

variable "email_from" {
  description = "Optional default sender address for transactional email."
  type        = string
  default     = ""
}

variable "vertex_location" {
  description = "Vertex AI region."
  type        = string
  default     = "us-central1"
}

variable "vertex_model" {
  description = "Default Vertex AI Gemini model identifier."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "cors_allowed_origins" {
  description = "Comma-separated frontend origins allowed by backend CORS."
  type        = string
  default     = "http://localhost:3000,http://127.0.0.1:3000,https://underlytics.vercel.app"
}