output "frontend_environment" {
  value = terraform_data.frontend_context.input.environment
}

output "vercel_project_name" {
  value = terraform_data.frontend_context.input.vercel_project_name
}

output "frontend_domain" {
  value = terraform_data.frontend_context.input.frontend_domain
}

output "backend_api_base_url" {
  value = terraform_data.frontend_context.input.backend_api_base_url
}
