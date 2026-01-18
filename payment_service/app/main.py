from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse

from .database import engine, SessionLocal
from .utils.errors import service_exception_handler, unhandled_exception_handler, ServiceError
from .utils.logging import setup_logging


setup_logging()
logger = logging.getLogger("payment_service")

# Prometheus metrics
payments_created_total = Counter("payments_created_total", "Total payments created")
payment_webhooks_total = Counter(
    "payment_webhooks_total",
    "Total webhook callbacks received",
    ["status"],
)
invalid_signature_total = Counter("invalid_signature_total", "Total invalid webhook signatures")
payment_status_transitions_total = Counter(
    "payment_status_transitions_total",
    "Total payment status transitions",
    ["from_status", "to_status"],
)
payment_latency = Histogram(
    "payment_creation_latency_seconds",
    "Payment creation latency",
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
webhook_latency = Histogram(
    "webhook_processing_latency_seconds",
    "Webhook processing latency",
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


def create_app() -> FastAPI:
    app = FastAPI(title="payment_service", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from .routers.payments import router as payments_router
    from .routers.webhooks import router as webhooks_router
    from .routers.internal import router as internal_router

    app.include_router(payments_router, prefix="/v1", tags=["payments"])
    app.include_router(webhooks_router, prefix="/v1", tags=["webhooks"])
    app.include_router(internal_router, prefix="/v1", tags=["internal"])

    # Exception handlers
    app.add_exception_handler(ServiceError, service_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Health checks
    @app.get("/health/live")
    async def health_live():
        """Liveness probe - process is alive"""
        return JSONResponse(content={"status": "ok"}, status_code=200)

    @app.get("/health/ready")
    async def health_ready():
        """Readiness probe - can serve traffic"""
        try:
            # Check database connection
            from sqlalchemy import text
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return JSONResponse(content={"status": "ready", "database": "ok"}, status_code=200)
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return JSONResponse(
                content={"status": "not_ready", "database": "error", "error": str(e)},
                status_code=503,
            )

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "payment_service",
            "version": "1.0.0",
            "status": "running",
        }

    logger.info("Payment service started")
    return app


app = create_app()
