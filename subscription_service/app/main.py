from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .utils.errors import service_exception_handler, unhandled_exception_handler, ServiceError
from .utils.logging import setup_logging


setup_logging()
logger = logging.getLogger("subscription_service")


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

    return app


app = create_app()


