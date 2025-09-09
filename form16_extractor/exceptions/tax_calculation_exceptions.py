"""
Exceptions for tax calculation operations.
"""


class TaxCalculationError(Exception):
    """Base exception for tax calculation errors."""
    pass


class UnsupportedYearError(TaxCalculationError):
    """Exception raised when assessment year is not supported."""
    pass


class UnsupportedRegimeError(TaxCalculationError):
    """Exception raised when regime is not supported for the given year."""
    pass


class InvalidTaxConfigError(TaxCalculationError):
    """Exception raised when tax configuration is invalid."""
    pass


class DeductionLimitExceededError(TaxCalculationError):
    """Exception raised when deduction exceeds statutory limits."""
    
    def __init__(self, message: str, section: str = None, limit: float = None, claimed: float = None):
        super().__init__(message)
        self.section = section
        self.limit = limit
        self.claimed = claimed