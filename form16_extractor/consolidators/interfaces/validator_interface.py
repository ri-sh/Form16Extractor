"""
Interface for consolidation validation components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

from ...models.form16_models import Form16Data
from ...utils.validation import ValidationResult


@dataclass
class ValidationContext:
    """Context information for validation operations."""
    
    financial_year: str
    assessment_year: str
    employee_pan: str
    validation_mode: str = "standard"
    
    # External data for cross-validation
    form26as_data: Dict[str, Any] = None
    previous_year_data: Dict[str, Any] = None


class IConsolidationValidator(ABC):
    """Interface for consolidation validation logic."""
    
    @abstractmethod
    def validate_employee_consistency(
        self, 
        form16_list: List[Form16Data],
        context: ValidationContext
    ) -> ValidationResult:
        """Validate that all Form16s belong to the same employee."""
        pass
    
    @abstractmethod
    def validate_financial_year_consistency(
        self, 
        form16_list: List[Form16Data],
        context: ValidationContext
    ) -> ValidationResult:
        """Validate that all Form16s are for the same financial year."""
        pass
    
    @abstractmethod
    def validate_salary_calculations(
        self, 
        form16_list: List[Form16Data],
        context: ValidationContext
    ) -> ValidationResult:
        """Validate salary calculation accuracy."""
        pass
    
    @abstractmethod
    def validate_tds_calculations(
        self, 
        form16_list: List[Form16Data],
        context: ValidationContext
    ) -> ValidationResult:
        """Validate TDS calculation accuracy."""
        pass
    
    @abstractmethod
    def validate_deduction_limits(
        self, 
        consolidated_deductions: Dict[str, float],
        context: ValidationContext
    ) -> ValidationResult:
        """Validate that deductions don't exceed statutory limits."""
        pass