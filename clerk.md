The Clerk issue is now fixed and the live dashboard works.

Please harden the Terraform and GitHub Actions setup so this issue cannot return on future pushes/deployments.

Required permanent safeguards:

1. Terraform source of truth
- Ensure `CLERK_AUTHORIZED_PARTIES` is always managed by Terraform.
- Ensure `clerk-authorized-parties` Secret Manager secret always has an active enabled version.
- Do not allow Terraform apply to destroy all active versions.
- Keep these required origins as defaults/fallbacks:
  - http://localhost:3000
  - https://underlytics.vercel.app
  - https://underlytics-steve-mwangis-projects.vercel.app
  - https://underlytics-git-main-steve-mwangis-projects.vercel.app

2. Cloud Run binding
- Ensure backend Cloud Run always receives:
  `CLERK_AUTHORIZED_PARTIES`
  from the active `clerk-authorized-parties` secret.
- Keep a revision trigger env var so Cloud Run rolls forward when the secret version changes.

3. GitHub Actions protection
- Ensure backend deploy and terraform workflows do not override `clerk_authorized_parties` with stale or empty secrets.
- Prefer repo variable `CLERK_AUTHORIZED_PARTIES`.
- If the variable is missing, fallback to the required four-origin default list.
- Never fallback to localhost-only.

4. Validation step in CI/CD
Add a post-deploy verification step that checks:
- Secret Manager has an enabled latest version for `clerk-authorized-parties`
- latest secret value contains `https://underlytics.vercel.app`
- latest Cloud Run backend revision includes `CLERK_AUTHORIZED_PARTIES`
- backend service is ready

5. Documentation
Update README.md with:
- the required `CLERK_AUTHORIZED_PARTIES` value
- warning that it must not be changed to localhost-only
- note that Vercel production domains must remain included

Goal:
Future pushes, Terraform applies, and GitHub Actions deployments must not regress the Clerk authorized party configuration again.