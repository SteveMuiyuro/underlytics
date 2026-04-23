Here are the deployment details:

1. GCP project ID
The project ID is:
underlytics

Use `underlytics` as the actual Google Cloud project ID, not just the display name.

2. Continue deployment wiring
Proceed with the next deployment wiring step using this project ID.

3. GitHub repository slug
Make sure you have created the .gitignore file in both the frontend and backend or the root folders to exclude sensitive files and local environment configurations.
The repo slug is SteveMuiyuro/underlytics.git.
For now, structure the Terraform and GitHub Actions so the repo slug can be passed in as a variable.

4. Secrets
Structure the setup so the following secrets can be injected through GitHub Actions secrets and/or GCP Secret Manager: (check .env inside the backend folder for the values)
- admin bootstrap secret=
- Clerk publishable key=
- Clerk secret key=
- Clerk webhook secret if needed=
- any app environment secrets=
- later: Langfuse keys
- later: Resend API key
- later: EMAIL_FROM
- later: Vertex/Gemini related config if needed

Do not block the implementation on actual secret values. Use placeholders and variable wiring.

5. Frontend deployment caveat
You are correct that the current Clerk-based Next.js app is not yet a true static export.
Because of that, do not finalize frontend deployment to Cloud Storage + Cloud CDN yet.

For now:
- keep the frontend bucket/CDN skeleton if already provisioned
- treat frontend deployment as pending
- prioritize backend, IAM, Workload Identity Federation, Terraform, and GitHub Actions
- keep frontend deployment configurable

6. Frontend deployment recommendation
Unless the frontend is explicitly refactored into a true static export, plan for the frontend to be deployed on Cloud Run as well.
If you want to preserve the original bucket/CDN architecture, then first confirm whether the frontend will be converted to static export.

7. Next step
Proceed with:
- Workload Identity Federation
- GitHub Actions wiring
- Terraform completion
- backend deploy pipeline
- secrets wiring with placeholders