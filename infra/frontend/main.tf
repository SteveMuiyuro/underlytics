resource "terraform_data" "frontend_context" {
  input = {
    environment                     = var.environment
    vercel_project_name             = var.vercel_project_name
    vercel_project_id               = var.vercel_project_id
    vercel_org_id                   = var.vercel_org_id
    frontend_domain                 = var.frontend_domain
    backend_api_base_url            = var.backend_api_base_url
    clerk_publishable_key_reference = var.clerk_publishable_key_reference
  }
}
