from __future__ import annotations

import hashlib
from contextlib import contextmanager
from typing import Any, Iterator

from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler

from app.config import Settings
from app.config import settings


class LangfuseService:
    def __init__(
        self,
        model_settings: Settings | None = None,
    ) -> None:
        model_settings = model_settings or settings

        self.enabled = model_settings.langfuse_is_configured
        self.client: Langfuse | None = None

        if self.enabled:
            self.client = Langfuse(
                public_key=model_settings.langfuse_public_key,
                secret_key=model_settings.langfuse_secret_key,
                base_url=model_settings.langfuse_host,
                tracing_enabled=True,
                environment=model_settings.environment,
            )

    @staticmethod
    def _parent_span_id(seed: str) -> str:
        """
        Generate a deterministic 16-character OpenTelemetry span ID.

        Langfuse requires a valid 16-hex-character parent span ID when
        supplying a deterministic trace ID.
        """
        return hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()[:16]

    def create_trace_id(
        self,
        analysis_id: str,
    ) -> str | None:
        if not self.enabled or self.client is None:
            return None

        return self.client.create_trace_id(
            seed=analysis_id,
        )

    @contextmanager
    def trace_context(
        self,
        *,
        name: str,
        analysis_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any | None]:
        """
        Create the active Langfuse root observation.

        Everything executed inside this context, including LangGraph
        and LangChain callbacks, becomes part of the same trace.
        """
        if not self.enabled or self.client is None:
            yield None
            return

        trace_id: str | None = None
        trace_context: dict[str, str] | None = None

        if analysis_id:
            trace_id = self.create_trace_id(analysis_id)

            if trace_id:
                trace_context = {
                    "trace_id": trace_id,
                    "parent_span_id": self._parent_span_id(
                        analysis_id
                    ),
                }

        with self.client.start_as_current_observation(
            as_type="span",
            name=name,
            trace_context=trace_context,
            metadata=metadata or {},
        ) as observation:

            with propagate_attributes(
                trace_name=name,
                metadata=metadata or {},
                environment=settings.environment,
            ):
                yield observation

    def callbacks(
        self,
    ) -> list[CallbackHandler]:
        """
        Create a fresh Langfuse LangChain callback handler.

        A fresh handler is used for each analysis execution so that
        concurrent analyses do not share callback state.
        """
        if not self.enabled or self.client is None:
            return []

        return [CallbackHandler()]

    def current_trace_id(self) -> str | None:
        if not self.enabled or self.client is None:
            return None

        return self.client.get_current_trace_id()

    def trace_url(
        self,
        trace_id: str | None = None,
    ) -> str | None:
        if not self.enabled or self.client is None:
            return None

        return self.client.get_trace_url(
            trace_id=trace_id,
        )

    def flush(self) -> None:
        if self.client is not None:
            self.client.flush()