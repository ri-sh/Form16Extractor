"""
Interface definitions for tax calculation system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal


class TaxRegimeType(Enum):
    """Tax regime types."""
    OLD = "old"
    NEW = "new"
    BOTH = "both"


class AgeCategory(Enum):
    """Age categories for tax calculation."""
    BELOW_60 = "below_60"
    SENIOR_60_TO_80 = "senior_60_to_80"
    SUPER_SENIOR_ABOVE_80 = "super_senior_above_80"


@dataclass
class TaxCalculationInput:
    """Input data for tax calculation."""
    
    # Required fields first
    assessment_year: str
    regime_type: TaxRegimeType
    gross_salary: Decimal
    
    # Optional fields with defaults
    age_category: AgeCategory = AgeCategory.BELOW_60
    
    # Income from other sources (detailed breakdown)
    bank_interest_income: Decimal = Decimal('0')
    dividend_income: Decimal = Decimal('0')
    other_income: Decimal = Decimal('0')
    house_property_income: Decimal = Decimal('0')
    
    # Deductions (old regime)
    standard_deduction: Decimal = Decimal('0')
    section_80c: Decimal = Decimal('0')
    section_80d: Decimal = Decimal('0')
    section_80ccd_1b: Decimal = Decimal('0')
    other_deductions: Dict[str, Decimal] = None
    
    # Exemptions under Section 10
    hra_exemption: Decimal = Decimal('0')
    lta_exemption: Decimal = Decimal('0')
    other_exemptions: Dict[str, Decimal] = None
    
    # Previous year losses
    house_property_loss: Decimal = Decimal('0')
    
    # Tax payments
    tds_deducted: Decimal = Decimal('0')
    advance_tax_paid: Decimal = Decimal('0')
    self_assessment_tax: Decimal = Decimal('0')
    
    def __post_init__(self):
        if self.other_deductions is None:
            self.other_deductions = {}
        if self.other_exemptions is None:
            self.other_exemptions = {}


@dataclass
class TaxSlabCalculation:
    """Details of tax calculation for each slab."""
    
    slab_from: Decimal
    slab_to: Optional[Decimal]  # None for highest slab
    rate_percent: float
    taxable_amount_in_slab: Decimal
    tax_on_slab: Decimal


@dataclass
class TaxCalculationResult:
    """Result of tax calculation."""
    
    # Input summary
    assessment_year: str
    regime_type: TaxRegimeType
    
    # Income computation
    total_income: Decimal
    taxable_income: Decimal
    total_deductions: Decimal
    total_exemptions: Decimal
    
    # Tax computation
    tax_before_rebate: Decimal
    rebate_under_87a: Decimal
    tax_after_rebate: Decimal
    surcharge: Decimal
    health_education_cess: Decimal
    total_tax_liability: Decimal
    
    # Slab-wise breakdown
    slab_calculations: List[TaxSlabCalculation]
    
    # Tax payments and balance
    tds_deducted: Decimal = Decimal('0')
    advance_tax_paid: Decimal = Decimal('0')
    self_assessment_tax: Decimal = Decimal('0')
    total_taxes_paid: Decimal = Decimal('0')
    balance_tax_payable: Decimal = Decimal('0')  # Positive = payable, Negative = refundable
    
    # Comparison with other regime (if calculated)
    other_regime_tax: Optional[Decimal] = None
    regime_benefit: Optional[Decimal] = None
    
    # Additional details
    effective_tax_rate: float = 0.0
    marginal_tax_rate: float = 0.0
    
    # Validation
    calculation_warnings: List[str] = None
    
    def __post_init__(self):
        if self.calculation_warnings is None:
            self.calculation_warnings = []
        
        # Calculate effective tax rate
        if self.total_income > 0:
            self.effective_tax_rate = float(self.total_tax_liability / self.total_income) * 100
        
        # Calculate total taxes paid and balance
        self.total_taxes_paid = self.tds_deducted + self.advance_tax_paid + self.self_assessment_tax
        self.balance_tax_payable = self.total_tax_liability - self.total_taxes_paid


class ITaxCalculator(ABC):
    """
    Interface for tax calculation implementations.
    
    Defines the contract for calculating income tax based on
    Indian tax laws for different assessment years and regimes.
    """
    
    @abstractmethod
    def calculate_tax(
        self, 
        input_data: TaxCalculationInput
    ) -> TaxCalculationResult:
        """
        Calculate income tax for the given input.
        
        Args:
            input_data: Tax calculation input data
            
        Returns:
            TaxCalculationResult with detailed breakdown
            
        Raises:
            TaxCalculationError: If calculation fails
            ValidationError: If input data is invalid
        """
        pass
    
    @abstractmethod
    def compare_regimes(
        self, 
        input_data: TaxCalculationInput
    ) -> Dict[TaxRegimeType, TaxCalculationResult]:
        """
        Calculate tax under both regimes for comparison.
        
        Args:
            input_data: Tax calculation input data
            
        Returns:
            Dictionary mapping regime types to calculation results
        """
        pass
    
    @abstractmethod
    def get_supported_assessment_years(self) -> List[str]:
        """
        Get list of supported assessment years.
        
        Returns:
            List of assessment year strings (e.g., ['2024-25', '2025-26'])
        """
        pass
    
    @abstractmethod
    def validate_input(
        self, 
        input_data: TaxCalculationInput
    ) -> List[str]:
        """
        Validate tax calculation input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass