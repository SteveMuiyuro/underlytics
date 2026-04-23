import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Prefer backend-local settings, then fill any missing shared auth settings from
# the frontend app's local env in this monorepo during development.
load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv(PROJECT_ROOT / "frontend" / ".env.local")


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    value = value.strip()
    return value or None

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./underlytics.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RESEND_API_KEY = _optional_env("RESEND_API_KEY")
EMAIL_FROM = _optional_env("EMAIL_FROM")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv(
    "LANGFUSE_BASE_URL",
    os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)
ADMIN_BOOTSTRAP_SECRET = os.getenv("ADMIN_BOOTSTRAP_SECRET")
CLERK_JWT_KEY = _optional_env("CLERK_JWT_KEY")
CLERK_JWT_ISSUER = _optional_env("CLERK_JWT_ISSUER")
CLERK_PUBLISHABLE_KEY = _optional_env("CLERK_PUBLISHABLE_KEY") or _optional_env(
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
)
GOOGLE_CLOUD_PROJECT = _optional_env("GOOGLE_CLOUD_PROJECT")
PUBSUB_WORKFLOW_TOPIC = _optional_env("PUBSUB_WORKFLOW_TOPIC")
WORKFLOW_EXECUTION_MODE = _optional_env("WORKFLOW_EXECUTION_MODE") or "sync"
CLERK_AUTHORIZED_PARTIES = [
    party.strip()
    for party in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",")
    if party.strip()
]
