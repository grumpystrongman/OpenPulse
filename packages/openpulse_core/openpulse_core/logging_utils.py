from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger


def configure_logging(service_name: str, level: str = "INFO") -> None:
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    logger.info("logging_configured", extra={"service": service_name})


def log_event(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    logger.info(event, extra={"event": event, **kwargs})
