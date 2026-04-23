FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install uv \
    && uv export --frozen --no-dev --format requirements-txt > requirements.txt \
    && pip install -r requirements.txt

COPY underlytics_api ./underlytics_api
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

ENV PORT=8080

CMD ["python", "-m", "uvicorn", "underlytics_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
