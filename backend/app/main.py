"""
FastAPI Main Application
Entry point for the Enterprise RAG Platform API.
Implements multi-tenant isolation and OpenTelemetry instrumentation.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.telemetry.otel import telemetry_manager, shutdown_telemetry
from app.api import query_routes, upload_routes, dashboard_routes

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for application startup and shutdown."""
    # Startup
    logger.info("🚀 Enterprise RAG Platform starting...")
    telemetry_manager  # Initialize telemetry
    yield
    # Shutdown
    logger.info("🛑 Enterprise RAG Platform shutting down...")
    shutdown_telemetry()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade RAG platform with observability and multi-tenancy",
    lifespan=lifespan,
)

# ==================== CORS Middleware ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Multi-Tenant Dependency ====================
async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract tenant ID from request header (required for multi-tenancy)."""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-ID header")
    return x_tenant_id


async def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from request header."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    return x_user_id


# ==================== Health Check ====================
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    """Welcome endpoint."""
    return {
        "message": "Enterprise RAG Platform",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }


# ==================== Error Handlers ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with telemetry."""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions with telemetry."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# ==================== Include Routes ====================
app.include_router(
    query_routes.router,
    prefix=f"{settings.API_V1_STR}/query",
    tags=["Query"],
)

app.include_router(
    upload_routes.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["Documents"],
)

app.include_router(
    dashboard_routes.router,
    prefix=f"{settings.API_V1_STR}/dashboard",
    tags=["Dashboard"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
