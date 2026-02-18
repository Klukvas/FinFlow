from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .utils.errors import service_exception_handler, unhandled_exception_handler, ServiceError
from .utils.logging import setup_logging


setup_logging()
logger = logging.getLogger("subscription_service")

p95_entitlements = Histogram(
    "subscription_entitlements_latency_seconds",
    "Latency for /v1/entitlements",
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
cache_hits = Counter("subscription_entitlements_cache_hits_total", "Cache hit count for entitlements")
subs_changes = Counter("subscription_changes_total", "Number of subscription changes")


def create_app() -> FastAPI:
    app = FastAPI(title="subscription_service")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers will be included later when implemented
    from .routers.plans import router as plans_router
    from .routers.subscriptions import router as subs_router
    from .routers.entitlements import router as ents_router
    from .routers.features import router as features_router
    from .routers.internal import router as internal_router
    from .routers.admin_plans import router as admin_plans_router
    from .routers.consent import router as consent_router

    app.include_router(plans_router, prefix="/v1", tags=["plans"])
    app.include_router(subs_router, prefix="/v1", tags=["subscriptions"])
    app.include_router(ents_router, prefix="/v1", tags=["entitlements"])
    app.include_router(features_router, prefix="/v1", tags=["features"])
    app.include_router(internal_router, prefix="/v1", tags=["internal"])
    app.include_router(admin_plans_router, prefix="/v1", tags=["admin"])
    app.include_router(consent_router, prefix="/v1", tags=["consent"])

    app.add_exception_handler(ServiceError, service_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()


