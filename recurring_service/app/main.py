from fastapi import FastAPI
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

logger = get_logger(__name__)


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
app.include_router(recurring_router)
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
