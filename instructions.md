Implement the project in this order:

1. bootstrap.md
Start with infrastructure and deployment assumptions first.
Use bootstrap.md to:
- respect the already completed GCP bootstrap state
- Dockerize the backend locally first
- generate Terraform for the remaining GCP infrastructure
- prepare GitHub Actions with automated testing
- configure Cloud Run, Cloud SQL, Pub/Sub, API Gateway, Artifact Registry, Secret Manager, Cloud Storage, Cloud CDN, and Workload Identity Federation

2. agents.md
After infrastructure planning, implement the agent system.
Use agents.md to:
- preserve the planner + worker architecture
- keep structured outputs
- enforce hard guardrails
- keep the workflow explainable
- prepare the system for Gemini on Vertex AI
- avoid collapsing the whole system into one LLM call

3. email.md
Implement email after the agent system is understood.
Use email.md to:
- send applicant emails after final decisions
- use Resend as the email provider
- generate email content from agent/reviewer context
- support approved, rejected, and completed manual review outcomes
- log communication events in the database

Important:
- Do not skip the order above
- Do not start with email before understanding the agent and workflow system
- Do not remove the current deterministic guardrails when introducing LLMs
- Keep the backend Docker and Cloud Run compatible from the start