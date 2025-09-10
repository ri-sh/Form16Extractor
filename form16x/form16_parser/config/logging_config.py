#!/usr/bin/env python3
"""
Logging Configuration
====================

Structured logging setup for Form16 extractor.
Supports file and console output with proper formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from form16x.form16_parser.config.settings import get_settings


def setup_logging(log_level: Optional[str] = None, log_file: Optional[Path] = None):
    """
    Setup logging configuration based on settings
    
    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Override log file path
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    level = log_level or settings.logging.log_level
    file_path = log_file or settings.get_log_file_path()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = _get_formatter(settings)
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if settings.logging.enable_file_logging:
        file_handler = _create_file_handler(file_path, settings)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    
    # Set library loggers to WARNING to reduce noise
    logging.getLogger('camelot').setLevel(logging.WARNING)
    logging.getLogger('pdfplumber').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def _get_formatter(settings) -> logging.Formatter:
    """Create log formatter based on settings"""
    
    if settings.logging.enable_structured_logging:
        # Structured format for production
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    else:
        # Simple format for development
        if settings.logging.include_timestamp:
            format_string = "%(levelname)s: %(message)s"
        else:
            format_string = "%(levelname)s: %(message)s"
    
    return logging.Formatter(format_string)


def _create_file_handler(file_path: Path, settings) -> logging.Handler:
    """Create rotating file handler"""
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    max_bytes = settings.logging.max_log_file_size_mb * 1024 * 1024
    backup_count = 5  # Keep 5 backup files
    
    handler = logging.handlers.RotatingFileHandler(
        filename=file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    return handler


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_extraction_start(logger: logging.Logger, file_name: str):
    """Log extraction start with standard format"""
    logger.info(f"Starting extraction: {file_name}")


def log_extraction_success(logger: logging.Logger, file_name: str, 
                          processing_time: float, fields_extracted: int):
    """Log successful extraction with metrics"""
    logger.info(f"Extraction completed: {file_name} "
                f"({processing_time:.2f}s, {fields_extracted} fields)")


def log_extraction_error(logger: logging.Logger, file_name: str, error: Exception):
    """Log extraction error with details"""
    logger.error(f"Extraction failed: {file_name} - {type(error).__name__}: {error}")


def log_validation_warning(logger: logging.Logger, field_name: str, message: str):
    """Log validation warning with standard format"""
    logger.warning(f"Validation warning for {field_name}: {message}")


def log_performance_metrics(logger: logging.Logger, metrics: dict):
    """Log performance metrics in structured format"""
    logger.info("Performance metrics: " + 
                " | ".join(f"{k}={v}" for k, v in metrics.items()))


# Initialize logging on module import
def init_logging():
    """Initialize logging with default settings"""
    try:
        setup_logging()
    except Exception as e:
        # Fallback to basic console logging if setup fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s: %(message)s"
        )
        logging.getLogger(__name__).warning(f"Failed to setup advanced logging: {e}")


# Auto-initialize when module is imported
init_logging()