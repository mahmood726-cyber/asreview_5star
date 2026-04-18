"""
FastAPI Application for ASReview 5-Star.

Provides a REST API for systematic review tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


def create_app(
    title: str = "ASReview 5-Star API",
    description: str = None,
    cors_origins: list = None
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Parameters
    ----------
    title : str
        API title for documentation.
    description : str
        API description for documentation.
    cors_origins : list
        List of allowed CORS origins. Use ["*"] for development.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.
    """
    if description is None:
        description = """
## ASReview 5-Star REST API

Enhanced systematic review tools including:

### Stopping Rules
- **Bayesian Stopping**: Posterior probability of achieving target recall
- **SPRT**: Sequential Probability Ratio Test for prevalence
- **SAFE**: Stop After First Estimate procedure

### Inter-Rater Reliability (IRR)
- **Cohen's Kappa**: Agreement between two raters
- **Fleiss' Kappa**: Agreement among multiple raters

### Meta-Analysis
- **Effect Pooling**: Fixed and random effects models
- **Egger's Test**: Publication bias detection
- **Begg's Test**: Rank correlation test for bias

### PRISMA
- **Statistics**: Flow diagram calculations
- **Flow Data**: Structured data for visualization

---
Built with FastAPI | ASReview Team
"""

    app = FastAPI(
        title=title,
        description=description,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS middleware
    if cors_origins is None:
        cors_origins = ["*"]  # Allow all for development

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    # Root endpoint
    @app.get("/", tags=["System"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "ASReview 5-Star API",
            "version": "0.1.0",
            "documentation": "/docs",
            "openapi": "/openapi.json",
            "endpoints": {
                "stopping": "/api/v1/stopping/",
                "irr": "/api/v1/irr/",
                "meta": "/api/v1/meta/",
                "prisma": "/api/v1/prisma/"
            }
        }

    return app


# Default application instance
app = create_app()


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """
    Run the API server.

    Parameters
    ----------
    host : str
        Host address to bind to.
    port : int
        Port number to listen on.
    reload : bool
        Enable auto-reload for development.
    """
    import uvicorn
    uvicorn.run(
        "asreview_5star.api.app:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server(reload=True)
