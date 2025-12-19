"""Logger configuration for the Researcher system.

This module configures loguru for consistent logging across the system.
"""

import sys
from pathlib import Path

from loguru import logger


def configure_logger(
    level: str = "INFO",
    log_file: str | Path | None = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """Configure the logger with specified settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional). If None, only logs to console.
        rotation: When to rotate log file (e.g., "10 MB", "1 day")
        retention: How long to keep old log files (e.g., "7 days")

    Example:
        >>> configure_logger(level="DEBUG", log_file="./logs/researcher.log")
    """
    # Remove default logger
    logger.remove()

    # Add console logger with color
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )

    # Add file logger if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

        logger.info(f"Logging to file: {log_path}")


def get_logger(name: str):
    """Get a logger instance with a specific name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("Hello from my module")
    """
    return logger.bind(name=name)


# Configure default logger (INFO level, console only)
configure_logger(level="INFO")
