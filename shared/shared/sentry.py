"""Sentry integration for all microservices.

Usage:
    from shared.sentry import init_sentry
    init_sentry("user_service")
"""

import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def init_sentry(service_name: str) -> None:
    """Initialize Sentry SDK. Reads DSN from SENTRY_DSN env var.

    Does nothing if SENTRY_DSN is not set, so safe to call in all environments.
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("ENVIRONMENT", "production"),
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        send_default_pii=True,
        server_name=service_name,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
    )
