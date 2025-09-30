from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.routers import pdf_parser
from app.exception_handlers import (
    custom_validation_exception_handler,
    pdf_parsing_error_handler,
    unsupported_bank_handler,
    file_processing_error_handler,
    http_exception_handler
)
from app.exceptions import (
    PDFParsingError,
    UnsupportedBankError,
    FileProcessingError
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="PDF Parser Service",
    description="Microservice for parsing bank PDFs and extracting transaction data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(PDFParsingError, pdf_parsing_error_handler)
app.add_exception_handler(UnsupportedBankError, unsupported_bank_handler)
app.add_exception_handler(FileProcessingError, file_processing_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(pdf_parser.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pdf-parser-service"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PDF Parser Service API", "version": "1.0.0"}

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("PDF Parser Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("PDF Parser Service shutting down...")
