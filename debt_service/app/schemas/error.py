from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Unified error response format"""
    error: str
    errorCode: str
    details: Optional[Dict[str, Any]] = None
