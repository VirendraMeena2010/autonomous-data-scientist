from __future__ import annotations

import os
from typing import Any

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings


def init_telemetry(app=None) -> None:
    sentry_dsn = os.getenv("SENTRY_DSN")

    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=float(
                os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
            ),
            profiles_sample_rate=float(
                os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
            ),
            environment=settings.environment,
            release=os.getenv("APP_VERSION", "0.1.0"),
        )

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not otlp_endpoint:
        return

    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.environment": settings.environment,
            "service.version": os.getenv("APP_VERSION", "0.1.0"),
        }
    )

    provider = TracerProvider(resource=resource)

    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=otlp_endpoint,
            )
        )
    )

    trace.set_tracer_provider(provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(
            engine=None,
            enable_commenter=True,
        )
