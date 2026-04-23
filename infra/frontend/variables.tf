variable "environment" {
  description = "Frontend deployment environment name."
  type        = string
  default     = "production"
}

variable "vercel_project_name" {
  description = "Human-readable Vercel project name."
  type        = string
  default     = "underlytics"
}

variable "vercel_project_id" {
  description = "Optional Vercel project ID reference."
  type        = string
  default     = ""
}

variable "vercel_org_id" {
  description = "Optional Vercel org/team ID reference."
  type        = string
  default     = ""
}

variable "frontend_domain" {
  description = "Optional primary frontend domain."
  type        = string
  default     = ""
}

variable "backend_api_base_url" {
  description = "Public backend API base URL consumed by the frontend."
  type        = string
  default     = ""
}

variable "clerk_publishable_key_reference" {
  description = "Optional reference describing where the frontend Clerk key is managed."
  type        = string
  default     = "GitHub/Vercel environment variable"
}
