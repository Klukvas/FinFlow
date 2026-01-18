from __future__ import annotations

import logging
import sys
from pythonjsonlogger import jsonlogger

from ..config import settings


def setup_logging():
    """Setup structured JSON logging"""
    logger = logging.getLogger()
    
    log_handler = logging.StreamHandler(sys.stdout)
    
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(settings.log_level)
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
