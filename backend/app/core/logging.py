import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(settings.log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    ))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


app_logger = _build_logger("app")
agent_logger = _build_logger("agent")
trace_logger = _build_logger("trace")
llm_logger = _build_logger("llm")