"""
Logger Utility

Provides structured logging for the application.

Features
--------
• colored console logs
• file logs
• module-level loggers
• stack trace support
"""

import logging
import sys
from pathlib import Path

from src.config.settings import config

# ---------------------------------------------------------
# Log Directory
# ---------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

ERROR_LOG = LOG_DIR / "error.log"
COMBINED_LOG = LOG_DIR / "combined.log"


# ---------------------------------------------------------
# Console Formatter (colored)
# ---------------------------------------------------------

class ColorFormatter(logging.Formatter):

    COLORS = {
        "DEBUG": "\033[37m",
        "INFO": "\033[36m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }

    RESET = "\033[0m"

    def format(self, record):

        color = self.COLORS.get(record.levelname, "")

        message = super().format(record)

        return f"{color}{message}{self.RESET}"


# ---------------------------------------------------------
# Base Logger Setup
# ---------------------------------------------------------

def setup_logger():

    logger = logging.getLogger("maantra")

    if logger.handlers:
        return logger

    level = getattr(logging, config.app.log_level.upper(), logging.INFO)

    logger.setLevel(level)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    formatter = logging.Formatter(log_format)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(log_format))

    # Error File Handler
    error_file_handler = logging.FileHandler(ERROR_LOG)
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # Combined File Handler
    combined_handler = logging.FileHandler(COMBINED_LOG)
    combined_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(combined_handler)

    return logger


# Global logger
logger = setup_logger()


# ---------------------------------------------------------
# Module Logger
# ---------------------------------------------------------

def get_logger(module_name: str):

    return logger.getChild(module_name)