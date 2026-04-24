terraform {
  required_version = ">= 1.7.0"

  backend "gcs" {
    bucket = "underlytics-terraform-state"
    prefix = "infra/backend"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.31"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.31"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}