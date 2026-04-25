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

variable "frontend_bucket_name" {
  description = "Optional explicit bucket name for static frontend assets."
  type        = string
  default     = null
}

variable "enable_frontend_cdn" {
  description = "Whether to provision the Cloud Storage + Cloud CDN frontend skeleton."
  type        = bool
  default     = true
}

variable "admin_bootstrap_secret" {
  description = "Initial backend admin bootstrap secret."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_jwt_key" {
  description = "Optional Clerk JWT verification key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_jwt_issuer" {
  description = "Optional Clerk JWT issuer override."
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_publishable_key" {
  description = "Clerk publishable key used by backend auth fallback logic."
  type        = string
  sensitive   = true
  default     = ""
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
