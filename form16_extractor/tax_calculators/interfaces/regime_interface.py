"""
Interface for tax regime implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from decimal import Decimal
from dataclasses import dataclass

from .calculator_interface import TaxSlabCalculation, AgeCategory


@dataclass
class TaxSlab:
    """Tax slab definition."""
    
    from_amount: Decimal
    to_amount: Optional[Decimal]  # None for highest slab
    rate_percent: float
    
    def applies_to_amount(self, amount: Decimal) -> bool:
        """Check if this slab applies to the given amount."""
        if amount < self.from_amount:
            return False
        if self.to_amount is not None and amount > self.to_amount:
            return False
        return True


@dataclass
class RegimeSettings:
    """Settings for a tax regime."""
    
    # Basic settings
    standard_deduction: Decimal
    basic_exemption_limit: Dict[AgeCategory, Decimal]
    
    # Rebate settings
    rebate_limit: Decimal
    rebate_max_amount: Decimal
    
    # Surcharge settings
    surcharge_threshold_1: Decimal  # 50L
    surcharge_rate_1: float         # 10%
    surcharge_threshold_2: Decimal  # 1Cr
    surcharge_rate_2: float         # 15%
    surcharge_threshold_3: Optional[Decimal] = None  # 2Cr/5Cr
    surcharge_rate_3: Optional[float] = None         # 25%/37%
    
    # Cess
    health_education_cess_rate: float = 4.0
    
    # Deduction allowances
    allows_section_80c: bool = True
    allows_section_80d: bool = True
    allows_hra_exemption: bool = True
    allows_lta_exemption: bool = True


class ITaxRegime(ABC):
    """
    Interface for tax regime implementations.
    
    Defines the contract for different tax regimes (old/new)
    with their specific rules, slabs, and calculations.
    """
    
    @abstractmethod
    def get_tax_slabs(self, age_category: AgeCategory) -> List[TaxSlab]:
        """
        Get tax slabs for the regime based on age category.
        
        Args:
            age_category: Age category of the taxpayer
            
        Returns:
            List of applicable tax slabs
        """
        pass
    
    @abstractmethod
    def get_regime_settings(self) -> RegimeSettings:
        """
        Get regime-specific settings.
        
        Returns:
            RegimeSettings object with regime configuration
        """
        pass
    
    @abstractmethod
    def calculate_slab_wise_tax(
        self, 
        taxable_income: Decimal,
        age_category: AgeCategory
    ) -> List[TaxSlabCalculation]:
        """
        Calculate tax slab-wise for the given income.
        
        Args:
            taxable_income: Income after all deductions
            age_category: Age category of taxpayer
            
        Returns:
            List of TaxSlabCalculation objects
        """
        pass
    
    @abstractmethod
    def calculate_surcharge(
        self, 
        tax_before_surcharge: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """
        Calculate surcharge based on income level.
        
        Args:
            tax_before_surcharge: Tax amount before surcharge
            total_income: Total income for surcharge calculation
            
        Returns:
            Surcharge amount
        """
        pass
    
    @abstractmethod
    def calculate_rebate_87a(
        self, 
        tax_before_rebate: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """
        Calculate rebate under Section 87A.
        
        Args:
            tax_before_rebate: Tax before rebate calculation
            total_income: Total income for rebate eligibility
            
        Returns:
            Rebate amount
        """
        pass
    
    @abstractmethod
    def validate_deductions(
        self, 
        deductions: Dict[str, Decimal]
    ) -> List[str]:
        """
        Validate that deductions are allowed under this regime.
        
        Args:
            deductions: Dictionary of deduction types and amounts
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass