
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import text
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from app.api import analyses, auth, datasets, projects
from app.api.admin import router as admin_router
from app.api.audit_log import router as audit_logs_router
from app.api.health import router as health_router
from app.api.queue_dashboard import router as queue_dashboard_router
from app.config import settings
from app.db.session import engine, get_session, init_db
from app.logging_config import configure_logging
from app.services.bootstrap_admin import bootstrap_admin
from app.services.queue import AnalysisQueue
from app.services.storage import StorageService
from app.telemetry import init_telemetry


configure_logging(settings.environment)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------
    app.state.storage = StorageService(settings)
    await app.state.storage.initialize()

    # ---------------------------------------------------------
    # Analysis queue
    # ---------------------------------------------------------
    app.state.analysis_queue = None

    if settings.redis_enabled:
        app.state.analysis_queue = AnalysisQueue(settings)
        await app.state.analysis_queue.initialize()
        logger.info("analysis_queue_enabled")
    else:
        logger.info("analysis_queue_disabled")

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------
    await init_db()

    # ---------------------------------------------------------
    # LangGraph checkpointer
    # ---------------------------------------------------------
    #
    # SQLAlchemy may use:
    #   postgresql+asyncpg://...
    #   postgresql+psycopg://...
    #
    # Psycopg / LangGraph expects:
    #   postgresql://...
    #
    database_url = settings.database_url

    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )
    elif database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )

    checkpointer_context = AsyncPostgresSaver.from_conn_string(
        database_url
    )

    app.state.analysis_checkpointer = (
        await checkpointer_context.__aenter__()
    )

    # Create LangGraph checkpoint tables if needed.
    await app.state.analysis_checkpointer.setup()

    # ---------------------------------------------------------
    # Build analysis graph
    # ---------------------------------------------------------
    from app.graph.graph import build_analysis_graph

    app.state.analysis_graph = build_analysis_graph(
        checkpointer=app.state.analysis_checkpointer
    )

    # ---------------------------------------------------------
    # Bootstrap admin
    # ---------------------------------------------------------
    await bootstrap_admin()

    logger.info(
        "application_started",
        environment=settings.environment,
    )

    try:
        yield

    finally:
        # -----------------------------------------------------
        # Analysis queue
        # -----------------------------------------------------
        if app.state.analysis_queue is not None:
            await app.state.analysis_queue.close()

        # -----------------------------------------------------
        # LangGraph checkpointer
        # -----------------------------------------------------
        if hasattr(app.state, "analysis_checkpointer"):
            await checkpointer_context.__aexit__(
                None,
                None,
                None,
            )

        # -----------------------------------------------------
        # Storage
        # -----------------------------------------------------
        app.state.storage.close()

        # -----------------------------------------------------
        # Database
        # -----------------------------------------------------
        await engine.dispose()

        logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    description="Autonomous data science platform backend",
    version="0.1.0",
    lifespan=lifespan,
)

init_telemetry(app)


# ---------------------------------------------------------
# Security headers
# ---------------------------------------------------------
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"

    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    response.headers["Cache-Control"] = (
        "no-store"
        if request.url.path.startswith(
            f"{settings.api_prefix}/"
        )
        else "public, max-age=60"
    )

    return response


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API routers
# ---------------------------------------------------------
app.include_router(
    auth.router,
    prefix=settings.api_prefix,
)

app.include_router(
    admin_router,
    prefix=settings.api_prefix,
)

app.include_router(
    projects.router,
    prefix=settings.api_prefix,
)

app.include_router(
    datasets.router,
    prefix=settings.api_prefix,
)

app.include_router(
    analyses.router,
    prefix=settings.api_prefix,
)

app.include_router(
    health_router,
    prefix=settings.api_prefix,
)

app.include_router(
    audit_logs_router,
    prefix=settings.api_prefix,
)

app.include_router(
    queue_dashboard_router,
    prefix=settings.api_prefix,
)


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get(
    "/",
    include_in_schema=False,
)
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "docs": f"{settings.api_prefix}/docs",
    }


# ---------------------------------------------------------
# Liveness
# ---------------------------------------------------------
@app.get(
    f"{settings.api_prefix}/health/live",
    tags=["system"],
)
async def live() -> dict[str, str]:
    return {
        "status": "live",
        "version": "0.1.0",
    }


# ---------------------------------------------------------
# Readiness
# ---------------------------------------------------------
@app.get(
    f"{settings.api_prefix}/health/ready",
    tags=["system"],
)
async def ready(
    request: Request,
    session=Depends(get_session),
) -> dict[str, str]:
    try:
        # Database
        await session.execute(text("SELECT 1"))

        # Redis / analysis queue is optional
        if request.app.state.analysis_queue is not None:
            await request.app.state.analysis_queue.ping()

        # Storage
        await request.app.state.storage.ping()

    except Exception as exc:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="dependency_unavailable",
        ) from exc

    return {
        "status": "ready",
    }

