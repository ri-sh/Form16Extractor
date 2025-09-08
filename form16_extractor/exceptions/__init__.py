"""
Form16 Extractor Exceptions
==========================

Custom exception classes for Form16 extraction with error codes and severity levels.
"""

# Import all exceptions from core_exceptions module
from .core_exceptions import (
    ErrorSeverity,
    ErrorCodes,
    Form16ExtractionError,
    PDFProcessingError,
    TableClassificationError,
    FieldExtractionError,
    DataValidationError,
    ComponentInitializationError,
    ExtractionTimeoutError
)

def create_recovery_suggestions(error):
    """Create recovery suggestions based on error type and context"""
    return ["Contact support with error details"]

# Export all exception classes and enums for easy importing
__all__ = [
    'ErrorSeverity',
    'ErrorCodes', 
    'Form16ExtractionError',
    'PDFProcessingError',
    'TableClassificationError',
    'FieldExtractionError',
    'DataValidationError',
    'ComponentInitializationError',
    'ExtractionTimeoutError',
    'create_recovery_suggestions'
]