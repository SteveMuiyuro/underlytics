from __future__ import annotations

import logging
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from functools import lru_cache
from hashlib import md5
from typing import Any

from agents import custom_span, flush_traces, guardrail_span, trace
from agents.tracing.spans import SpanError
from langfuse import Langfuse

from underlytics_api.core.config import (
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    OPENAI_API_KEY,
)

logger = logging.getLogger(__name__)

WORKFLOW_TRACE_NAME = "underlytics-underwriting-workflow"


@dataclass
class WorkflowTraceContext:
    trace_core: str
    openai_trace_id: str
    group_id: str


@dataclass
class ObservationContext:
    langfuse_observation: Any | None = None
    openai_span: Any | None = None

    def record_output(
        self,
        *,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
        status_message: str | None = None,
    ) -> None:
        if not self.langfuse_observation:
            return

        update_payload: dict[str, Any] = {}
        if output is not None:
            update_payload["output"] = output
        if metadata is not None:
            update_payload["metadata"] = metadata
        if status_message is not None:
            update_payload["status_message"] = status_message

        if update_payload:
            self.langfuse_observation.update(**update_payload)

    def record_error(
        self,
        *,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        if self.langfuse_observation:
            self.langfuse_observation.update(
                level="ERROR",
                status_message=message,
                output={"error": message, "data": data or {}},
            )

        if self.openai_span:
            self.openai_span.set_error(
                SpanError(message=message, data=data or None)
            )


def _langfuse_enabled() -> bool:
    return bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)


def _openai_tracing_enabled() -> bool:
    return bool(OPENAI_API_KEY)


@lru_cache(maxsize=1)
def _get_langfuse_client() -> Langfuse | None:
    if not _langfuse_enabled():
        return None

    return Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        base_url=LANGFUSE_HOST,
    )


def _build_trace_core(seed: str) -> str:
    return md5(seed.encode("utf-8"), usedforsecurity=False).hexdigest()


def _build_openai_trace_id(trace_core: str) -> str:
    return f"trace_{trace_core}"


def ensure_workflow_trace_context(*, plan_id: str, group_id: str) -> WorkflowTraceContext:
    trace_core = _build_trace_core(f"workflow_plan:{plan_id}")
    return WorkflowTraceContext(
        trace_core=trace_core,
        openai_trace_id=_build_openai_trace_id(trace_core),
        group_id=group_id,
    )


@contextmanager
def start_workflow_observability(
    *,
    workflow: WorkflowTraceContext,
    metadata: dict[str, Any],
    input_payload: dict[str, Any],
):
    langfuse_client = _get_langfuse_client()

    with ExitStack() as stack:
        if _openai_tracing_enabled():
            stack.enter_context(
                trace(
                    WORKFLOW_TRACE_NAME,
                    trace_id=workflow.openai_trace_id,
                    group_id=workflow.group_id,
                    metadata=metadata,
                )
            )

        langfuse_observation = None
        if langfuse_client:
            langfuse_observation = stack.enter_context(
                langfuse_client.start_as_current_observation(
                    name=WORKFLOW_TRACE_NAME,
                    as_type="span",
                    trace_context={"trace_id": workflow.trace_core},
                    input=input_payload,
                    metadata=metadata,
                )
            )

        try:
            yield ObservationContext(langfuse_observation=langfuse_observation)
        finally:
            if langfuse_client:
                try:
                    langfuse_client.flush()
                except Exception:
                    logger.exception("Failed to flush Langfuse traces")

            if _openai_tracing_enabled():
                try:
                    flush_traces()
                except Exception:
                    logger.exception("Failed to flush OpenAI traces")


@contextmanager
def start_step_observability(
    *,
    trace_core: str,
    step_name: str,
    metadata: dict[str, Any],
    input_payload: dict[str, Any],
):
    langfuse_client = _get_langfuse_client()

    with ExitStack() as stack:
        openai_span = None
        if _openai_tracing_enabled():
            openai_span = stack.enter_context(
                custom_span(
                    f"workflow_step:{step_name}",
                    data=metadata,
                )
            )

        langfuse_observation = None
        if langfuse_client:
            langfuse_observation = stack.enter_context(
                langfuse_client.start_as_current_observation(
                    name=f"workflow_step:{step_name}",
                    as_type="agent",
                    trace_context={"trace_id": trace_core},
                    input=input_payload,
                    metadata=metadata,
                )
            )

        yield ObservationContext(
            langfuse_observation=langfuse_observation,
            openai_span=openai_span,
        )


@contextmanager
def start_guardrail_observability(
    *,
    trace_core: str,
    name: str,
    metadata: dict[str, Any],
):
    langfuse_client = _get_langfuse_client()

    with ExitStack() as stack:
        openai_span = None
        if _openai_tracing_enabled():
            openai_span = stack.enter_context(guardrail_span(name))

        langfuse_observation = None
        if langfuse_client:
            langfuse_observation = stack.enter_context(
                langfuse_client.start_as_current_observation(
                    name=name,
                    as_type="guardrail",
                    trace_context={"trace_id": trace_core},
                    metadata=metadata,
                )
            )

        yield ObservationContext(
            langfuse_observation=langfuse_observation,
            openai_span=openai_span,
        )
