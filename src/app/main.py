"""RepurposeAI - AI-powered content repurposing tool."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_keys import router as api_keys_router
from app.api.auth import router as auth_router
from app.api.batch import router as batch_router
from app.api.formats import router as formats_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.repurpose import router as repurpose_router
from app.api.subscription import router as subscription_router
from app.api.webhook import router as webhook_router
from app.api.workflows import router as workflows_router
from app.constants import APP_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — start/stop background services."""
    # Startup
    from app.services.scheduler import WorkflowScheduler
    from app.services.workflow_store import WORKFLOWS_DB

    scheduler = WorkflowScheduler(store={"workflows": WORKFLOWS_DB}, poll_interval=60)
    app.state.scheduler = scheduler

    yield

    # Shutdown
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        await scheduler.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RepurposeAI",
        description="AI-powered content repurposing tool",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(repurpose_router)
    app.include_router(formats_router)
    app.include_router(subscription_router)
    app.include_router(webhook_router)
    app.include_router(auth_router)
    app.include_router(api_keys_router)
    app.include_router(workflows_router)
    app.include_router(batch_router)
    app.include_router(jobs_router)

    return app


app = create_app()
