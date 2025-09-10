"""
Income processing components for tax calculations.

Handles aggregation and processing of various income sources according to
Indian Income Tax Act provisions.
"""

from decimal import Decimal
from typing import Dict
from dataclasses import dataclass

from ..interfaces.calculator_interface import TaxCalculationInput


@dataclass
class ProcessedIncome:
    """
    Container for processed income data.
    
    Represents the complete income breakdown after processing all sources
    and applying relevant tax rules.
    """
    salary_income: Decimal
    other_sources_income: Decimal
    house_property_income: Decimal
    total_gross_income: Decimal
    
    # Detailed breakdown of other sources
    bank_interest: Decimal
    dividend_income: Decimal
    other_miscellaneous: Decimal


class IncomeProcessor:
    """
    Processes and aggregates income from various sources.
    
    Follows Single Responsibility Principle by focusing solely on income
    calculation and aggregation without handling deductions or tax computation.
    """
    
    def process_income(self, input_data: TaxCalculationInput) -> ProcessedIncome:
        """
        Process and aggregate all income sources.
        
        Args:
            input_data: Tax calculation input containing income details
            
        Returns:
            ProcessedIncome object with aggregated income breakdown
        """
        salary_income = input_data.gross_salary
        
        # Aggregate other sources income
        other_sources = (
            input_data.bank_interest_income + 
            input_data.dividend_income + 
            input_data.other_income
        )
        
        house_property = input_data.house_property_income
        
        total_gross = salary_income + other_sources + house_property
        
        return ProcessedIncome(
            salary_income=salary_income,
            other_sources_income=other_sources,
            house_property_income=house_property,
            total_gross_income=total_gross,
            bank_interest=input_data.bank_interest_income,
            dividend_income=input_data.dividend_income,
            other_miscellaneous=input_data.other_income
        )
    
    def get_total_income_for_rebate_calculation(self, processed_income: ProcessedIncome) -> Decimal:
        """
        Calculate total income for rebate eligibility under Section 87A.
        
        Args:
            processed_income: Processed income data
            
        Returns:
            Total income amount for rebate calculation
        """
        return processed_income.total_gross_income