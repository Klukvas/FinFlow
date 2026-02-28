from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    error: str
    errorCode: str
    details: Optional[Dict[str, Any]] = None
