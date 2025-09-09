"""
Exceptions for consolidation operations.
"""


class ConsolidationError(Exception):
    """Base exception for consolidation errors."""
    pass


class DuplicateDeductionError(ConsolidationError):
    """Exception raised when duplicate deductions are detected."""
    
    def __init__(self, message: str, duplicates: dict = None):
        super().__init__(message)
        self.duplicates = duplicates or {}


class InconsistentDataError(ConsolidationError):
    """Exception raised when Form16 data is inconsistent."""
    pass


class ValidationTimeoutError(ConsolidationError):
    """Exception raised when validation takes too long."""
    pass