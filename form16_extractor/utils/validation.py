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


# Note: Standalone validate_pan() and validate_tan() functions previously here
# were unused - validation is done by individual extractors using their own methods