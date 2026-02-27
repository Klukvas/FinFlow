from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.exceptions import (
    InsufficientDataError,
    LLMServiceError,
    LLMRateLimitError,
    FeatureNotAvailableError,
    QuotaExhaustedError,
)
from app.routers import analysis
from app.services.cache_service import close_redis

import logging
import time
import uuid

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms:.1f}ms"
            )
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"error={e} duration={duration_ms:.1f}ms"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Assistant Service starting up...")
    yield
    logger.info("AI Assistant Service shutting down...")
    await close_redis()


app = FastAPI(
    title="AI Assistant Service",
    description="AI-powered financial analysis service for FinFlow",
    version="1.0.0",
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    lifespan=lifespan,
)


# Exception handlers
async def _json_error(status_code: int, detail: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=detail)


@app.exception_handler(InsufficientDataError)
async def insufficient_data_handler(request: Request, exc: InsufficientDataError):
    return await _json_error(exc.status_code, exc.detail)


@app.exception_handler(LLMServiceError)
async def llm_service_handler(request: Request, exc: LLMServiceError):
    return await _json_error(exc.status_code, exc.detail)


@app.exception_handler(LLMRateLimitError)
async def llm_rate_limit_handler(request: Request, exc: LLMRateLimitError):
    return await _json_error(exc.status_code, exc.detail)


@app.exception_handler(FeatureNotAvailableError)
async def feature_not_available_handler(request: Request, exc: FeatureNotAvailableError):
    return await _json_error(exc.status_code, exc.detail)


@app.exception_handler(QuotaExhaustedError)
async def quota_exhausted_handler(request: Request, exc: QuotaExhaustedError):
    response = await _json_error(exc.status_code, exc.detail)
    response.headers["Retry-After"] = str(exc.detail.get("retry_after", 60))
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "errorCode": "VALIDATION_ERROR", "details": str(exc)},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "errorCode": "HTTP_ERROR"},
    )


# Middleware (registered in reverse order: last registered runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-Id"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Router
app.include_router(analysis.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-assistant-service"}
