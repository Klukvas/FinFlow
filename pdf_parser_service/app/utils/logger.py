import logging
import sys
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(settings.log_format)
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    return logger
