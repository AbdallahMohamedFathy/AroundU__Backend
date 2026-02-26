import logging
import sys
from pythonjsonlogger import jsonlogger
from src.core.config import settings

def setup_logging():
    """Setup structured JSON logging."""
    logger = logging.getLogger()
    
    # Set log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Console handler with JSON formatting
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        logger.addHandler(logHandler)
    else:
        # Replace existing handlers if any (useful for reload)
        logger.handlers = [logHandler]

    # Special handling for uvicorn logs to use JSON
    logging.getLogger("uvicorn.access").handlers = [logHandler]
    logging.getLogger("uvicorn.error").handlers = [logHandler]

    return logger

# Initialize logger
logger = setup_logging()
