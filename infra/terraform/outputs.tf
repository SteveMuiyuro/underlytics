output "project_id" {
  value = var.project_id
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.backend.id
}

output "backend_cloud_run_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "worker_cloud_run_url" {
  value = google_cloud_run_v2_service.worker.uri
}

output "api_gateway_url" {
  value = "https://${google_api_gateway_gateway.backend.default_hostname}"
}

output "frontend_cdn_ip" {
  value = var.enable_frontend_cdn ? google_compute_global_address.frontend[0].address : null
}

output "github_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "terraform_deployer_service_account" {
  value = google_service_account.terraform_deployer.email
}
