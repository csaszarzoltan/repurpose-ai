"""RepurposeAI - AI-powered content repurposing tool."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.formats import router as formats_router
from app.api.health import router as health_router
from app.api.repurpose import router as repurpose_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RepurposeAI",
        description="AI-powered content repurposing tool",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
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

    return app


app = create_app()
