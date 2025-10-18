from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import recurring_router, internal_router
from app.services.scheduler_service import scheduler_service
from app.exception_handlers import (
    recurring_payment_not_found_handler,
    invalid_schedule_config_handler,
    payment_execution_error_handler,
    http_exception_handler,
    general_exception_handler
)
from app.exceptions import (
    RecurringPaymentNotFoundError,
    InvalidScheduleConfigError,
    PaymentExecutionError
)
from fastapi import HTTPException
from app.utils.logger import get_logger
import time
import uuid

logger = get_logger(__name__)
# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract user ID from request if available
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Set request context
        from logging_utils import set_request_context
        set_request_context(request_id, user_id, "recurring_service")
        
        # Log request start
        start_time = time.time()
        logger.log_api_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=0,  # Will be updated after response
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.log_api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error response
            logger.error(
                f"API request failed: {request.method} {request.url.path} - {str(e)}",
                category="api",
                operation="api_request_error",
                method=request.method,
                endpoint=str(request.url.path),
                duration_ms=duration_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=request_id
            )
            
            raise




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting Recurring Payments Service")
    
    # Создать таблицы в базе данных
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Запустить встроенный шедулер
    scheduler_service.start()
    logger.info("Built-in scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Recurring Payments Service")
    scheduler_service.stop()
    logger.info("Built-in scheduler stopped")


# Создать приложение FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Сервис для управления повторяющимися платежами",
    lifespan=lifespan
)

# Настроить CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Добавить обработчики исключений
app.add_exception_handler(RecurringPaymentNotFoundError, recurring_payment_not_found_handler)
app.add_exception_handler(InvalidScheduleConfigError, invalid_schedule_config_handler)
app.add_exception_handler(PaymentExecutionError, payment_execution_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Подключить роутеры
# Add middleware
app.add_middleware(RequestLoggingMiddleware)

app.include_router(recurring_router)
# Add middleware
app.add_middleware(RequestLoggingMiddleware)

app.include_router(internal_router)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Recurring Payments Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "recurring-payments",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
