"""
Section 89 Relief Calculator

Implements relief calculation for salary arrears under Section 89(1) of Income Tax Act.
This relief applies when an employee receives salary in arrears or advance in a financial year.
"""

from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from ..interfaces.calculator_interface import TaxRegimeType, TaxCalculationInput, TaxCalculationResult
from ..interfaces.rule_provider_interface import ITaxRuleProvider


class ReliefType(Enum):
    """Type of relief under Section 89."""
    ARREARS = "arrears"
    ADVANCE = "advance"


@dataclass
class ArrearDetails:
    """Details of salary arrears for a specific year."""
    assessment_year: str
    arrear_amount: Decimal
    year_of_receipt: str  # Year when arrears were actually received
    relief_type: ReliefType = ReliefType.ARREARS


@dataclass
class Section89ReliefCalculation:
    """Result of Section 89 relief calculation."""
    total_arrears: Decimal
    relief_amount: Decimal
    tax_without_arrears: Decimal
    tax_with_arrears: Decimal
    arrear_breakdown: List[Dict[str, any]]
    form_10e_data: Dict[str, any]


class Section89ReliefCalculator:
    """
    Calculator for Section 89 relief on salary arrears.
    
    Relief Calculation Method:
    1. Calculate tax for the year without arrears
    2. Calculate tax for the year with arrears included
    3. Calculate difference
    4. Calculate tax for each arrear year by spreading the arrears
    5. Relief = (Tax with arrears - Tax without arrears) - Sum of additional tax for arrear years
    """
    
    def __init__(self, rule_provider: ITaxRuleProvider):
        """Initialize with tax rule provider."""
        self.rule_provider = rule_provider
    
    def calculate_section_89_relief(
        self,
        base_calculation: TaxCalculationInput,
        arrear_details: List[ArrearDetails],
        current_assessment_year: str
    ) -> Section89ReliefCalculation:
        """
        Calculate Section 89 relief for salary arrears.
        
        Args:
            base_calculation: Base tax calculation input for current year
            arrear_details: List of arrear details for different years
            current_assessment_year: Assessment year when arrears are received
            
        Returns:
            Section89ReliefCalculation with relief amount and breakdown
        """
        total_arrears = sum(arrear.arrear_amount for arrear in arrear_details)
        
        # Step 1: Calculate tax without arrears (current year normal calculation)
        tax_without_arrears = self._calculate_tax_for_input(
            base_calculation, current_assessment_year
        )
        
        # Step 2: Calculate tax with arrears included in current year
        calculation_with_arrears = self._create_calculation_with_arrears(
            base_calculation, total_arrears
        )
        tax_with_arrears = self._calculate_tax_for_input(
            calculation_with_arrears, current_assessment_year
        )
        
        # Step 3: Calculate additional tax for each arrear year
        arrear_breakdown = []
        total_arrear_year_tax = Decimal('0')
        
        for arrear in arrear_details:
            # Create calculation for the arrear year with arrears included
            arrear_year_with_arrears = self._create_arrear_year_calculation(
                base_calculation, arrear
            )
            
            # Calculate tax for arrear year with arrears
            arrear_year_tax_with = self._calculate_tax_for_input(
                arrear_year_with_arrears, arrear.assessment_year
            )
            
            # Calculate tax for arrear year without arrears (base salary only)
            arrear_year_without_arrears = self._create_arrear_year_base_calculation(
                base_calculation, arrear.assessment_year
            )
            arrear_year_tax_without = self._calculate_tax_for_input(
                arrear_year_without_arrears, arrear.assessment_year
            )
            
            additional_tax = arrear_year_tax_with.total_tax_liability - arrear_year_tax_without.total_tax_liability
            total_arrear_year_tax += additional_tax
            
            arrear_breakdown.append({
                'assessment_year': arrear.assessment_year,
                'arrear_amount': float(arrear.arrear_amount),
                'tax_without_arrears': float(arrear_year_tax_without.total_tax_liability),
                'tax_with_arrears': float(arrear_year_tax_with.total_tax_liability),
                'additional_tax': float(additional_tax)
            })
        
        # Step 4: Calculate relief amount
        # Relief = (Tax with arrears - Tax without arrears) - Total additional tax for arrear years
        current_year_additional_tax = (
            tax_with_arrears.total_tax_liability - tax_without_arrears.total_tax_liability
        )
        relief_amount = max(Decimal('0'), current_year_additional_tax - total_arrear_year_tax)
        
        # Step 5: Generate Form 10E data
        form_10e_data = self._generate_form_10e_data(
            base_calculation, arrear_details, current_assessment_year,
            tax_without_arrears, tax_with_arrears, relief_amount
        )
        
        return Section89ReliefCalculation(
            total_arrears=total_arrears,
            relief_amount=relief_amount,
            tax_without_arrears=tax_without_arrears.total_tax_liability,
            tax_with_arrears=tax_with_arrears.total_tax_liability,
            arrear_breakdown=arrear_breakdown,
            form_10e_data=form_10e_data
        )
    
    def _calculate_tax_for_input(
        self, 
        tax_input: TaxCalculationInput, 
        assessment_year: str
    ) -> TaxCalculationResult:
        """Calculate tax for given input and assessment year."""
        from ..engines.tax_calculator import ComprehensiveTaxCalculator
        
        calculator = ComprehensiveTaxCalculator(self.rule_provider)
        return calculator.calculate_tax(tax_input, assessment_year)
    
    def _create_calculation_with_arrears(
        self,
        base_calculation: TaxCalculationInput,
        total_arrears: Decimal
    ) -> TaxCalculationInput:
        """Create tax calculation input with arrears added to current year income."""
        from copy import deepcopy
        
        calculation_with_arrears = deepcopy(base_calculation)
        calculation_with_arrears.gross_total_income += total_arrears
        
        # Also add to gross salary if it's salary arrears
        calculation_with_arrears.gross_salary += total_arrears
        
        return calculation_with_arrears
    
    def _create_arrear_year_calculation(
        self,
        base_calculation: TaxCalculationInput,
        arrear: ArrearDetails
    ) -> TaxCalculationInput:
        """Create calculation for arrear year with arrears included."""
        from copy import deepcopy
        
        # Create a representative calculation for the arrear year
        # This is simplified - in practice, you'd need historical salary data
        arrear_calculation = deepcopy(base_calculation)
        
        # Adjust income to represent typical income for that year + arrears
        # This is a simplification - actual implementation would need historical data
        base_income = base_calculation.gross_salary - arrear.arrear_amount
        arrear_calculation.gross_salary = base_income + arrear.arrear_amount
        arrear_calculation.gross_total_income = base_income + arrear.arrear_amount
        
        return arrear_calculation
    
    def _create_arrear_year_base_calculation(
        self,
        base_calculation: TaxCalculationInput,
        assessment_year: str
    ) -> TaxCalculationInput:
        """Create base calculation for arrear year without arrears."""
        from copy import deepcopy
        
        base_calc = deepcopy(base_calculation)
        # Remove any arrears from the calculation
        # This represents what the salary would have been in that year
        
        return base_calc
    
    def _generate_form_10e_data(
        self,
        base_calculation: TaxCalculationInput,
        arrear_details: List[ArrearDetails],
        current_assessment_year: str,
        tax_without_arrears: TaxCalculationResult,
        tax_with_arrears: TaxCalculationResult,
        relief_amount: Decimal
    ) -> Dict[str, any]:
        """Generate Form 10E data for filing with IT department."""
        return {
            'form_type': 'Form 10E',
            'assessment_year': current_assessment_year,
            'employee_details': {
                'pan': base_calculation.pan if hasattr(base_calculation, 'pan') else None,
                'name': base_calculation.employee_name if hasattr(base_calculation, 'employee_name') else None
            },
            'salary_arrears': [
                {
                    'arrear_year': arrear.assessment_year,
                    'amount': float(arrear.arrear_amount),
                    'nature': 'salary_arrears'
                }
                for arrear in arrear_details
            ],
            'tax_calculations': {
                'current_year_tax_without_arrears': float(tax_without_arrears.total_tax_liability),
                'current_year_tax_with_arrears': float(tax_with_arrears.total_tax_liability),
                'relief_claimed': float(relief_amount)
            },
            'computation_method': 'spread_back_method',
            'relief_section': '89(1)',
            'filing_required': relief_amount > 0
        }
    
    def validate_arrear_details(self, arrear_details: List[ArrearDetails]) -> List[str]:
        """Validate arrear details for correctness."""
        errors = []
        
        for i, arrear in enumerate(arrear_details):
            if arrear.arrear_amount <= 0:
                errors.append(f"Arrear {i+1}: Amount must be positive")
            
            if not arrear.assessment_year:
                errors.append(f"Arrear {i+1}: Assessment year is required")
            
            # Check if assessment year format is valid
            if not self._is_valid_assessment_year(arrear.assessment_year):
                errors.append(f"Arrear {i+1}: Invalid assessment year format")
        
        return errors
    
    def _is_valid_assessment_year(self, assessment_year: str) -> bool:
        """Check if assessment year format is valid (YYYY-YY)."""
        try:
            if '-' not in assessment_year:
                return False
            
            start_year, end_year_suffix = assessment_year.split('-')
            if len(start_year) != 4 or len(end_year_suffix) != 2:
                return False
            
            start_year_int = int(start_year)
            end_year_suffix_int = int(end_year_suffix)
            
            # Check if end year follows start year
            expected_end = (start_year_int + 1) % 100
            return end_year_suffix_int == expected_end
            
        except (ValueError, IndexError):
            return False


# Utility functions for easy integration
def calculate_salary_arrears_relief(
    base_salary_input: TaxCalculationInput,
    arrears_by_year: Dict[str, Decimal],
    current_assessment_year: str,
    rule_provider: ITaxRuleProvider
) -> Section89ReliefCalculation:
    """
    Convenience function to calculate Section 89 relief for salary arrears.
    
    Args:
        base_salary_input: Base salary calculation for current year
        arrears_by_year: Dictionary mapping assessment year to arrear amount
        current_assessment_year: Current assessment year
        rule_provider: Tax rule provider
        
    Returns:
        Section89ReliefCalculation with relief details
    """
    arrear_details = [
        ArrearDetails(
            assessment_year=year,
            arrear_amount=amount,
            year_of_receipt=current_assessment_year,
            relief_type=ReliefType.ARREARS
        )
        for year, amount in arrears_by_year.items()
    ]
    
    calculator = Section89ReliefCalculator(rule_provider)
    return calculator.calculate_section_89_relief(
        base_salary_input, arrear_details, current_assessment_year
    )