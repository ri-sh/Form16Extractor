"""
Deduction processing components for tax calculations.

Handles calculation of various deductions according to Indian Income Tax Act,
including automatic computation of interest deductions under Sections 80TTA and 80TTB.
"""

from decimal import Decimal
from typing import Dict
from dataclasses import dataclass

from ..interfaces.calculator_interface import TaxCalculationInput, TaxRegimeType, AgeCategory
from .income_processor import ProcessedIncome


@dataclass
class ProcessedDeductions:
    """
    Container for processed deduction data.
    
    Represents all applicable deductions after processing and validation
    according to tax regime and eligibility rules.
    """
    standard_deduction: Decimal
    section_80c_total: Decimal
    section_80d_total: Decimal
    section_80ccd_1b: Decimal
    interest_deductions: Decimal  # 80TTA/80TTB combined
    other_deductions: Decimal
    total_deductions: Decimal
    
    # Detailed breakdown of interest deductions
    section_80tta: Decimal = Decimal('0')  # Non-senior citizens
    section_80ttb: Decimal = Decimal('0')  # Senior citizens


class InterestDeductionCalculator:
    """
    Calculates interest-based deductions under Sections 80TTA and 80TTB.
    
    Follows Interface Segregation Principle by providing specific functionality
    for interest deduction calculations.
    """
    
    def calculate_interest_deductions(
        self, 
        bank_interest: Decimal, 
        age_category: AgeCategory,
        regime_type: TaxRegimeType
    ) -> Dict[str, Decimal]:
        """
        Calculate applicable interest deductions based on age and regime.
        
        Args:
            bank_interest: Total bank interest income
            age_category: Taxpayer's age category
            regime_type: Tax regime (old/new)
            
        Returns:
            Dictionary with applicable deduction sections and amounts
        """
        deductions = {'section_80tta': Decimal('0'), 'section_80ttb': Decimal('0')}
        
        # Interest deductions only available in old regime
        if regime_type != TaxRegimeType.OLD or bank_interest <= 0:
            return deductions
        
        if age_category in [AgeCategory.SENIOR_60_TO_80, AgeCategory.SUPER_SENIOR_ABOVE_80]:
            # Section 80TTB for senior citizens - up to Rs. 50,000
            deductions['section_80ttb'] = min(bank_interest, Decimal('50000'))
        else:
            # Section 80TTA for non-senior citizens - up to Rs. 10,000
            deductions['section_80tta'] = min(bank_interest, Decimal('10000'))
        
        return deductions


class DeductionProcessor:
    """
    Main deduction processor coordinating all deduction calculations.
    
    Orchestrates various deduction calculators while maintaining separation
    of concerns for different deduction types.
    """
    
    def __init__(self):
        self.interest_calculator = InterestDeductionCalculator()
    
    def process_deductions(
        self, 
        input_data: TaxCalculationInput, 
        processed_income: ProcessedIncome
    ) -> ProcessedDeductions:
        """
        Process and calculate all applicable deductions.
        
        Args:
            input_data: Tax calculation input data
            processed_income: Processed income information
            
        Returns:
            ProcessedDeductions object with all calculated deductions
        """
        # Standard deduction
        standard_ded = input_data.standard_deduction
        
        # Investment deductions (old regime only)
        section_80c = input_data.section_80c if input_data.regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80d = input_data.section_80d if input_data.regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80ccd_1b = input_data.section_80ccd_1b
        
        # Calculate interest deductions automatically
        interest_deductions = self.interest_calculator.calculate_interest_deductions(
            processed_income.bank_interest,
            input_data.age_category,
            input_data.regime_type
        )
        
        total_interest_ded = interest_deductions['section_80tta'] + interest_deductions['section_80ttb']
        
        # Other deductions from input
        other_deductions_total = Decimal('0')
        if input_data.other_deductions:
            other_deductions_total = sum(input_data.other_deductions.values())
        
        # Calculate total deductions
        total_deductions = (
            standard_ded + section_80c + section_80d + section_80ccd_1b + 
            total_interest_ded + other_deductions_total
        )
        
        return ProcessedDeductions(
            standard_deduction=standard_ded,
            section_80c_total=section_80c,
            section_80d_total=section_80d,
            section_80ccd_1b=section_80ccd_1b,
            interest_deductions=total_interest_ded,
            other_deductions=other_deductions_total,
            total_deductions=total_deductions,
            section_80tta=interest_deductions['section_80tta'],
            section_80ttb=interest_deductions['section_80ttb']
        )