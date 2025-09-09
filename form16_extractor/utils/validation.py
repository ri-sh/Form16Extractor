"""
Validation utilities for Form16 processing.
"""

from typing import Any, List, Dict, Optional
from dataclasses import dataclass


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class ValidationWarning(Exception):
    """Exception raised for validation warnings."""
    pass


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class BaseValidator:
    """Base class for all validators."""
    
    def validate(self, data: Any) -> ValidationResult:
        """Validate the given data."""
        raise NotImplementedError("Subclasses must implement validate method")
    
    def _create_result(self, errors: List[str] = None, warnings: List[str] = None) -> ValidationResult:
        """Helper to create validation result."""
        errors = errors or []
        warnings = warnings or []
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


def validate_pan(pan: str) -> bool:
    """Validate PAN format (AAAAA9999A)."""
    if not pan or len(pan) != 10:
        return False
    
    # First 5 characters should be letters
    if not pan[:5].isalpha():
        return False
    
    # Next 4 should be digits
    if not pan[5:9].isdigit():
        return False
    
    # Last character should be letter
    if not pan[9].isalpha():
        return False
    
    return True


def validate_tan(tan: str) -> bool:
    """Validate TAN format (AAAA99999A)."""
    if not tan or len(tan) != 10:
        return False
    
    # First 4 characters should be letters
    if not tan[:4].isalpha():
        return False
    
    # Next 5 should be digits
    if not tan[4:9].isdigit():
        return False
    
    # Last character should be letter
    if not tan[9].isalpha():
        return False
    
    return True