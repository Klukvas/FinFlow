from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import currency

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(currency.router)

@app.get("/")
async def root():
    return {
        "message": "Currency Service API",
        "version": settings.api_version,
        "status": "running"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass
