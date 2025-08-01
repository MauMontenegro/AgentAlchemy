import logging
import sys
from typing import Optional
from .config import settings

def setup_logging(level: Optional[str] = None) -> None:
    """Configure application logging"""
    log_level = level or ("DEBUG" if settings.debug else "INFO")
    
    # Root logger configuration
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log', mode='a') if settings.debug else logging.NullHandler()
        ]
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

# Initialize logging on import
setup_logging()

# Backward compatibility
logger = get_logger("SAIP Logger")