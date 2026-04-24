provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {
  project_id = var.project_id
}

locals {
  service_apis = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "apigateway.googleapis.com",
    "servicemanagement.googleapis.com",
    "servicecontrol.googleapis.com",
    "pubsub.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  artifact_repository_id = "underlytics-images"
  backend_image          = "${var.region}-docker.pkg.dev/${var.project_id}/${local.artifact_repository_id}/underlytics-api:${var.image_tag}"
  worker_image           = local.backend_image

  project_roles = {
    terraform_deployer = [
      "roles/serviceusage.serviceUsageAdmin",
      "roles/resourcemanager.projectIamAdmin",
      "roles/iam.serviceAccountAdmin",
      "roles/iam.serviceAccountUser",
      "roles/iam.workloadIdentityPoolAdmin",
      "roles/run.admin",
      "roles/cloudsql.admin",
      "roles/pubsub.admin",
      "roles/artifactregistry.admin",
      "roles/secretmanager.admin",
      "roles/apigateway.admin",
      "roles/storage.admin",
      "roles/compute.admin",
      "roles/logging.admin",
      "roles/monitoring.editor",
    ]
    backend = [
      "roles/cloudsql.client",
      "roles/pubsub.publisher",
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
      "roles/aiplatform.user",
    ]
    worker = [
      "roles/cloudsql.client",
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
      "roles/aiplatform.user",
    ]
  }

  secret_values = {
    "admin-bootstrap-secret"   = var.admin_bootstrap_secret
    "clerk-jwt-key"            = var.clerk_jwt_key
    "clerk-jwt-issuer"         = var.clerk_jwt_issuer
    "clerk-publishable-key"    = var.clerk_publishable_key
    "clerk-secret-key"         = var.clerk_secret_key
    "clerk-authorized-parties" = var.clerk_authorized_parties
    "clerk-webhook-secret"     = var.clerk_webhook_secret
    "langfuse-public-key"      = var.langfuse_public_key
    "langfuse-secret-key"      = var.langfuse_secret_key
    "langfuse-host"            = var.langfuse_host
    "openai-api-key"           = var.openai_api_key
    "resend-api-key"           = var.resend_api_key
    "email-from"               = var.email_from
    "vertex-project-id"        = var.project_id
    "vertex-location"          = var.vertex_location
    "vertex-model"             = var.vertex_model
  }

  secret_value_presence = {
    "admin-bootstrap-secret"   = trimspace(nonsensitive(var.admin_bootstrap_secret)) != ""
    "clerk-jwt-key"            = trimspace(nonsensitive(var.clerk_jwt_key)) != ""
    "clerk-jwt-issuer"         = trimspace(nonsensitive(var.clerk_jwt_issuer)) != ""
    "clerk-publishable-key"    = trimspace(nonsensitive(var.clerk_publishable_key)) != ""
    "clerk-secret-key"         = trimspace(nonsensitive(var.clerk_secret_key)) != ""
    "clerk-authorized-parties" = trimspace(nonsensitive(var.clerk_authorized_parties)) != ""
    "clerk-webhook-secret"     = trimspace(nonsensitive(var.clerk_webhook_secret)) != ""
    "langfuse-public-key"      = trimspace(nonsensitive(var.langfuse_public_key)) != ""
    "langfuse-secret-key"      = trimspace(nonsensitive(var.langfuse_secret_key)) != ""
    "langfuse-host"            = trimspace(var.langfuse_host) != ""
    "openai-api-key"           = trimspace(nonsensitive(var.openai_api_key)) != ""
    "resend-api-key"           = trimspace(nonsensitive(var.resend_api_key)) != ""
    "email-from"               = trimspace(var.email_from) != ""
    "vertex-project-id"        = trimspace(var.project_id) != ""
    "vertex-location"          = trimspace(var.vertex_location) != ""
    "vertex-model"             = trimspace(var.vertex_model) != ""
  }

  configured_secret_names = toset([
    for key, is_present in local.secret_value_presence : key
    if is_present
  ])

  gateway_openapi_document = templatefile("${path.module}/templates/api-gateway-openapi.yaml.tftpl", {
    gateway_backend_url = local.gateway_backend_url
  })
  gateway_openapi_document_base64 = base64encode(local.gateway_openapi_document)
  gateway_api_config_id_prefix    = "cfg-${substr(md5(local.gateway_openapi_document), 0, 8)}-"

  backend_secret_envs = {
    "ADMIN_BOOTSTRAP_SECRET"   = "admin-bootstrap-secret"
    "CLERK_JWT_KEY"            = "clerk-jwt-key"
    "CLERK_JWT_ISSUER"         = "clerk-jwt-issuer"
    "CLERK_PUBLISHABLE_KEY"    = "clerk-publishable-key"
    "CLERK_AUTHORIZED_PARTIES" = "clerk-authorized-parties"
    "LANGFUSE_PUBLIC_KEY"      = "langfuse-public-key"
    "LANGFUSE_SECRET_KEY"      = "langfuse-secret-key"
    "LANGFUSE_HOST"            = "langfuse-host"
    "OPENAI_API_KEY"           = "openai-api-key"
  }

  worker_secret_envs = {
    "LANGFUSE_PUBLIC_KEY" = "langfuse-public-key"
    "LANGFUSE_SECRET_KEY" = "langfuse-secret-key"
    "LANGFUSE_HOST"       = "langfuse-host"
    "OPENAI_API_KEY"      = "openai-api-key"
  }

  gateway_backend_url = trimsuffix(google_cloud_run_v2_service.backend.uri, "/")
}

resource "google_project_service" "enabled" {
  for_each           = local.service_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "terraform_deployer" {
  account_id   = "terraform-deployer"
  display_name = "Underlytics Terraform Deployer"
}

resource "google_service_account" "underlytics_backend" {
  account_id   = "underlytics-backend-sa"
  display_name = "Underlytics Backend Cloud Run Service Account"
}

resource "google_service_account" "underlytics_worker" {
  account_id   = "underlytics-worker-sa"
  display_name = "Underlytics Worker Cloud Run Service Account"
}

resource "google_project_iam_member" "terraform_deployer_roles" {
  for_each = toset(local.project_roles.terraform_deployer)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

resource "google_project_iam_member" "backend_roles" {
  for_each = toset(local.project_roles.backend)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.underlytics_backend.email}"
}

resource "google_project_iam_member" "worker_roles" {
  for_each = toset(local.project_roles.worker)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.underlytics_worker.email}"
}

resource "google_artifact_registry_repository" "backend" {
  provider      = google-beta
  location      = var.region
  repository_id = local.artifact_repository_id
  description   = "Container images for Underlytics backend and worker services"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic" "underwriting_workflows" {
  name = "underwriting-workflows"

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic" "underwriting_events" {
  name = "underwriting-events"

  depends_on = [google_project_service.enabled]
}

resource "random_password" "database_password" {
  length           = 24
  special          = true
  override_special = "_%@"
}

resource "google_sql_database_instance" "postgres" {
  name                = "underlytics-postgres"
  database_version    = "POSTGRES_15"
  region              = var.db_region
  deletion_protection = false

  settings {
    tier = var.db_tier

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled = true
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_sql_database" "application" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "application" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.database_password.result
}

resource "google_secret_manager_secret" "app" {
  for_each = merge(
    {
      "db-user"      = ""
      "db-password"  = ""
      "db-name"      = ""
      "database-url" = ""
    },
    local.secret_values
  )

  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "database_user" {
  secret      = google_secret_manager_secret.app["db-user"].id
  secret_data = var.db_user
}

resource "google_secret_manager_secret_version" "database_password" {
  secret      = google_secret_manager_secret.app["db-password"].id
  secret_data = random_password.database_password.result
}

resource "google_secret_manager_secret_version" "database_name" {
  secret      = google_secret_manager_secret.app["db-name"].id
  secret_data = var.db_name
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.app["database-url"].id
  secret_data = "postgresql+psycopg2://${urlencode(var.db_user)}:${urlencode(random_password.database_password.result)}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_secret_manager_secret_version" "configured" {
  for_each = local.configured_secret_names

  secret      = google_secret_manager_secret.app[each.key].id
  secret_data = local.secret_values[each.key]
}

resource "google_secret_manager_secret_iam_member" "backend_access" {
  for_each = google_secret_manager_secret.app

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.underlytics_backend.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_access" {
  for_each = google_secret_manager_secret.app

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.underlytics_worker.email}"
}

resource "google_cloud_run_v2_service" "backend" {
  provider = google-beta
  name     = "underlytics-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.underlytics_backend.email

    volumes {
      name = "cloudsql"

      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image = local.backend_image

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app["database-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "UNDERLYTICS_DATABASE_URL_SECRET_VERSION"
        value = google_secret_manager_secret_version.database_url.version
      }

      dynamic "env" {
        for_each = {
          for env_name, secret_name in local.backend_secret_envs : env_name => secret_name
          if contains(local.configured_secret_names, secret_name)
        }

        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app[env.value].secret_id
              version = "latest"
            }
          }
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.vertex_location
      }

      env {
        name  = "VERTEX_LOCATION"
        value = var.vertex_location
      }

      env {
        name  = "VERTEX_MODEL"
        value = var.vertex_model
      }

      env {
        name  = "PUBSUB_WORKFLOW_TOPIC"
        value = google_pubsub_topic.underwriting_workflows.name
      }

      env {
        name  = "WORKFLOW_EXECUTION_MODE"
        value = "pubsub"
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = var.cors_allowed_origins
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.backend,
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_version.configured,
    google_secret_manager_secret_iam_member.backend_access,
  ]
}

resource "google_cloud_run_v2_service" "worker" {
  provider = google-beta
  name     = "underlytics-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.underlytics_worker.email

    volumes {
      name = "cloudsql"

      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image   = local.worker_image
      command = ["python", "-m", "uvicorn"]
      args    = ["underlytics_api.worker_app:app", "--host", "0.0.0.0", "--port", "8080"]

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app["database-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "UNDERLYTICS_DATABASE_URL_SECRET_VERSION"
        value = google_secret_manager_secret_version.database_url.version
      }

      dynamic "env" {
        for_each = {
          for env_name, secret_name in local.worker_secret_envs : env_name => secret_name
          if contains(local.configured_secret_names, secret_name)
        }

        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app[env.value].secret_id
              version = "latest"
            }
          }
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.vertex_location
      }

      env {
        name  = "VERTEX_LOCATION"
        value = var.vertex_location
      }

      env {
        name  = "VERTEX_MODEL"
        value = var.vertex_model
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.backend,
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_version.configured,
    google_secret_manager_secret_iam_member.worker_access,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "backend_public_invoker" {
  provider = google-beta
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "worker_push_invoker" {
  provider = google-beta
  name     = google_cloud_run_v2_service.worker.name
  location = google_cloud_run_v2_service.worker.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.underlytics_worker.email}"
}

resource "google_service_account_iam_member" "pubsub_worker_token_creator" {
  service_account_id = google_service_account.underlytics_worker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "worker_push" {
  name  = "underwriting-workflows-worker-push"
  topic = google_pubsub_topic.underwriting_workflows.name

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.worker.uri}/pubsub/workflows"

    oidc_token {
      service_account_email = google_service_account.underlytics_worker.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }

  ack_deadline_seconds = 30

  depends_on = [
    google_cloud_run_v2_service.worker,
    google_cloud_run_v2_service_iam_member.worker_push_invoker,
    google_service_account_iam_member.pubsub_worker_token_creator,
  ]
}

resource "google_api_gateway_api" "backend" {
  provider     = google-beta
  api_id       = "underlytics-api"
  display_name = "Underlytics API"

  depends_on = [google_project_service.enabled]
}

resource "google_api_gateway_api_config" "backend" {
  provider             = google-beta
  api                  = google_api_gateway_api.backend.api_id
  api_config_id_prefix = local.gateway_api_config_id_prefix
  display_name         = "Underlytics backend API config"

  openapi_documents {
    document {
      path     = "openapi.yaml"
      contents = local.gateway_openapi_document_base64
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "backend" {
  provider     = google-beta
  gateway_id   = "underlytics-gateway"
  api_config   = google_api_gateway_api_config.backend.id
  display_name = "Underlytics public API gateway"
  region       = var.region
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "underlytics-github-pool"
  display_name              = "Underlytics GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_actions_wif" {
  service_account_id = google_service_account.terraform_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}
