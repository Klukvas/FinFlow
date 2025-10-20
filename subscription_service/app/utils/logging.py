from __future__ import annotations

import logging
import os
from pythonjsonlogger import jsonlogger


def setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(levelname)s %(name)s %(message)s %(asctime)s %(trace_id)s %(user_id)s %(plan_code)s")
    handler.setFormatter(formatter)
    logger.handlers = [handler]


