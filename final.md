Please create a full production-ready `README.md` for this project.

Before writing, read and use the existing project context from:

*.md files
- existing frontend files
- existing backend files
- existing Terraform/GitHub Actions workflow files

The README should be clear enough for a new engineer, recruiter, investor, or technical reviewer to understand the project.

Include the following sections:

1. Project title and summary
   - Explain what Underlytics is.
   - Describe it as an AI-powered loan underwriting platform.
   - Mention that it uses a frontend, backend API, agent-based underwriting workflow, and cloud deployment pipeline.

2. Key features
   - Loan application intake
   - AI-assisted underwriting
   - Planner and worker agent architecture
   - Explainable decision summaries
   - Guardrails and auditability
   - Backend API
   - Frontend dashboard
   - CI/CD deployment setup

3. Architecture overview
   - Explain the frontend architecture.
   - Explain the backend architecture.
   - Explain the agent workflow.
   - Explain the cloud deployment flow.

4. Architecture diagrams
   Add Mermaid diagrams directly inside the README.

   Include one diagram for the frontend flow:
   - User
   - Browser
   - Frontend app
   - Authentication if present
   - API client
   - Backend API

   Include one diagram for the backend flow:
   - Backend API
   - Planner agent
   - Worker agents
   - Structured outputs
   - Decision summary agent
   - Guardrails
   - Final underwriting decision
   - Email/notification service
   - Database or persistence layer if present

   Include one diagram for CI/CD:
   - GitHub push
   - GitHub Actions
   - Backend CI
   - Terraform workflow
   - Deployment workflow
   - Cloud resources

5. Tech stack
   Separate frontend, backend, AI/agents, infrastructure, and DevOps.

6. Repository structure
   Show the folder structure and explain the purpose of important directories and files.

7. Local development setup
   Include:
   - prerequisites
   - environment variables
   - frontend setup
   - backend setup
   - how to run tests
   - how to run the app locally

8. Environment variables
   Create a clean table of required variables.
   Do not include real secrets.
   Use placeholder values only.

9. Backend API overview
   Document the main API routes found in the codebase.
   Include method, path, purpose, and authentication requirement if applicable.

10. Agent system overview
   Explain the Planner + Worker architecture from `AGENTS.md`.
   Make it clear that workers must remain independent and must not make final approval decisions.

11. Deployment
   Explain the production deployment process based on the current GitHub Actions and Terraform files.
   Mention what triggers CI, Terraform, and deployment.
   Include any required GitHub variables and secrets.

12. Production readiness
   Include:
   - security considerations
   - audit logging
   - validation
   - error handling
   - monitoring/logging
   - test strategy
   - failure handling
   - future scalability

13. Current project status
   Based on the existing files, summarize what is already implemented and what still needs to be completed.
   Be honest and do not claim features are complete if they are not implemented.

14. Roadmap
   Include short-term and long-term improvements.

15. Contributing / development rules
   Mention that changes should preserve the modular agent architecture and avoid collapsing the system into a single LLM call.

Important instructions:

- Do not invent fake features.
- If something is not implemented, mark it as planned or pending.
- Use professional production-grade language.
- Make the README polished and GitHub-ready.
- Use Mermaid diagrams that render correctly on GitHub.
- Do not expose secrets.
- Keep explanations clear and structured.
- Update or create only the `README.md` file unless a supporting file is absolutely necessary.
- After writing the README, run a quick review for broken Mermaid syntax, inaccurate claims, and missing setup instructions.