"""Logging configuration for AIpp Opener."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


DEFAULT_LOG_DIR = Path.home() / ".local" / "state" / "aipp_opener"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "aipp_opener.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_LOG_BACKUP_COUNT = 3


class LoggerConfig:
    """Centralized logging configuration."""

    _initialized = False
    _loggers: dict[str, logging.Logger] = {}

    @classmethod
    def setup(
        cls,
        log_level: int = DEFAULT_LOG_LEVEL,
        log_file: Optional[Path] = None,
        console_output: bool = True,
        file_output: bool = True,
    ) -> None:
        """
        Set up logging configuration.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            log_file: Path to log file.
            console_output: Enable console output.
            file_output: Enable file output.
        """
        if cls._initialized:
            return

        log_file = log_file or DEFAULT_LOG_FILE

        # Create log directory
        if file_output:
            log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler with rotation
        if file_output:
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=DEFAULT_LOG_MAX_BYTES,
                    backupCount=DEFAULT_LOG_BACKUP_COUNT,
                )
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except (PermissionError, OSError) as e:
                # If we can't write to log file, fall back to console only
                print(f"Warning: Could not create log file: {e}", file=sys.stderr)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name: Logger name (usually __name__).

        Returns:
            Configured logger instance.
        """
        if not cls._initialized:
            # Auto-setup with defaults if not initialized
            cls.setup()

        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Configured logger instance.
    """
    return LoggerConfig.get_logger(name)


# Module-level logger for common usage
logger = get_logger(__name__)
