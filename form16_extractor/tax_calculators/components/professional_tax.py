"""
Professional Tax Calculator

Implements professional tax calculation and deduction logic as per various state rules.
Professional tax is deductible under Section 16 of Income Tax Act.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class IndianState(Enum):
    """Indian states with professional tax."""
    ANDHRA_PRADESH = "AP"
    ASSAM = "AS"  
    BIHAR = "BR"
    GUJARAT = "GJ"
    KARNATAKA = "KA"
    KERALA = "KL"
    MADHYA_PRADESH = "MP"
    MAHARASHTRA = "MH"
    MANIPUR = "MN"
    MEGHALAYA = "ML"
    ODISHA = "OR"
    SIKKIM = "SK"
    TAMIL_NADU = "TN"
    TRIPURA = "TR"
    WEST_BENGAL = "WB"
    CHHATTISGARH = "CG"
    JHARKHAND = "JH"
    UTTARAKHAND = "UK"
    TELANGANA = "TS"


@dataclass
class ProfessionalTaxSlab:
    """Professional tax slab for a state."""
    min_salary: Decimal
    max_salary: Optional[Decimal]
    annual_tax: Decimal
    monthly_tax: Decimal


@dataclass
class ProfessionalTaxCalculation:
    """Result of professional tax calculation."""
    state: IndianState
    gross_monthly_salary: Decimal
    annual_professional_tax: Decimal
    monthly_professional_tax: Decimal
    applicable_slab: ProfessionalTaxSlab
    deduction_under_16: Decimal  # Amount deductible under Section 16


class ProfessionalTaxCalculator:
    """
    Calculator for professional tax as per various state rules.
    
    Professional tax is levied by state governments on individuals earning
    income from salary, profession, trade, calling or employment.
    """
    
    def __init__(self):
        """Initialize professional tax calculator with state-wise rates."""
        self.state_tax_slabs = self._initialize_state_tax_slabs()
    
    def _initialize_state_tax_slabs(self) -> Dict[IndianState, List[ProfessionalTaxSlab]]:
        """Initialize professional tax slabs for different states."""
        return {
            IndianState.MAHARASHTRA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), Decimal('50000'), Decimal('1800'), Decimal('150')),
                ProfessionalTaxSlab(Decimal('50000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.KARNATAKA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), Decimal('30000'), Decimal('1200'), Decimal('100')),
                ProfessionalTaxSlab(Decimal('30000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.TAMIL_NADU: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.GUJARAT: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('36000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('36000'), Decimal('50000'), Decimal('1800'), Decimal('150')),
                ProfessionalTaxSlab(Decimal('50000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.WEST_BENGAL: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('30000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('30000'), Decimal('50000'), Decimal('1500'), Decimal('125')),
                ProfessionalTaxSlab(Decimal('50000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.ANDHRA_PRADESH: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.TELANGANA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.KERALA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.ASSAM: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.BIHAR: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('25000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('25000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.MADHYA_PRADESH: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('25000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('25000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.ODISHA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.SIKKIM: [
                ProfessionalTaxSlab(Decimal('0'), None, Decimal('0'), Decimal('0')),  # No professional tax
            ],
            IndianState.MANIPUR: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.MEGHALAYA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.TRIPURA: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.CHHATTISGARH: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.JHARKHAND: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('25000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('25000'), None, Decimal('3000'), Decimal('250')),
            ],
            IndianState.UTTARAKHAND: [
                ProfessionalTaxSlab(Decimal('0'), Decimal('21000'), Decimal('0'), Decimal('0')),
                ProfessionalTaxSlab(Decimal('21000'), None, Decimal('3000'), Decimal('250')),
            ],
        }
    
    def calculate_professional_tax(
        self,
        gross_annual_salary: Decimal,
        state: IndianState,
        professional_tax_paid: Optional[Decimal] = None
    ) -> ProfessionalTaxCalculation:
        """
        Calculate professional tax for given salary and state.
        
        Args:
            gross_annual_salary: Gross annual salary
            state: State where professional tax is applicable
            professional_tax_paid: Actual professional tax paid (if available)
            
        Returns:
            ProfessionalTaxCalculation with calculated tax details
        """
        if state not in self.state_tax_slabs:
            # States without professional tax
            return ProfessionalTaxCalculation(
                state=state,
                gross_monthly_salary=gross_annual_salary / 12,
                annual_professional_tax=Decimal('0'),
                monthly_professional_tax=Decimal('0'),
                applicable_slab=ProfessionalTaxSlab(Decimal('0'), None, Decimal('0'), Decimal('0')),
                deduction_under_16=Decimal('0')
            )
        
        gross_monthly_salary = gross_annual_salary / 12
        applicable_slab = self._find_applicable_slab(gross_monthly_salary, state)
        
        # Use actual professional tax paid if provided, otherwise calculate
        if professional_tax_paid is not None:
            annual_professional_tax = professional_tax_paid
            monthly_professional_tax = professional_tax_paid / 12
        else:
            annual_professional_tax = applicable_slab.annual_tax
            monthly_professional_tax = applicable_slab.monthly_tax
        
        # Professional tax is fully deductible under Section 16
        deduction_under_16 = annual_professional_tax
        
        return ProfessionalTaxCalculation(
            state=state,
            gross_monthly_salary=gross_monthly_salary,
            annual_professional_tax=annual_professional_tax,
            monthly_professional_tax=monthly_professional_tax,
            applicable_slab=applicable_slab,
            deduction_under_16=deduction_under_16
        )
    
    def _find_applicable_slab(self, monthly_salary: Decimal, state: IndianState) -> ProfessionalTaxSlab:
        """Find applicable professional tax slab for given monthly salary."""
        slabs = self.state_tax_slabs[state]
        
        for slab in slabs:
            if monthly_salary >= slab.min_salary:
                if slab.max_salary is None or monthly_salary <= slab.max_salary:
                    return slab
        
        # Return highest slab if no match found
        return slabs[-1]
    
    def get_states_with_professional_tax(self) -> List[IndianState]:
        """Get list of states that levy professional tax."""
        return [
            state for state, slabs in self.state_tax_slabs.items()
            if slabs[0].annual_tax > 0 or len(slabs) > 1
        ]
    
    def get_max_professional_tax_by_state(self) -> Dict[IndianState, Decimal]:
        """Get maximum professional tax for each state."""
        max_tax = {}
        for state, slabs in self.state_tax_slabs.items():
            max_tax[state] = max(slab.annual_tax for slab in slabs)
        return max_tax
    
    def validate_professional_tax_deduction(
        self,
        professional_tax_claimed: Decimal,
        gross_annual_salary: Decimal,
        state: IndianState
    ) -> List[str]:
        """
        Validate professional tax deduction claimed.
        
        Args:
            professional_tax_claimed: Professional tax claimed as deduction
            gross_annual_salary: Gross annual salary
            state: State where professional tax applies
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if professional_tax_claimed < 0:
            errors.append("Professional tax cannot be negative")
            return errors
        
        if state not in self.state_tax_slabs:
            if professional_tax_claimed > 0:
                errors.append(f"State {state.value} does not levy professional tax")
            return errors
        
        # Calculate expected professional tax
        calculation = self.calculate_professional_tax(gross_annual_salary, state)
        max_allowable = calculation.annual_professional_tax
        
        # Allow for some variance (actual payment might be slightly different)
        variance_threshold = max(Decimal('100'), max_allowable * Decimal('0.05'))
        
        if professional_tax_claimed > max_allowable + variance_threshold:
            errors.append(
                f"Professional tax claimed ({professional_tax_claimed}) exceeds "
                f"maximum allowable for {state.value} ({max_allowable})"
            )
        
        return errors


# Utility functions for integration with main tax calculator
def calculate_section_16_professional_tax_deduction(
    gross_annual_salary: Decimal,
    state: IndianState,
    professional_tax_paid: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate professional tax deduction under Section 16.
    
    Args:
        gross_annual_salary: Gross annual salary
        state: State where professional tax applies
        professional_tax_paid: Actual professional tax paid
        
    Returns:
        Professional tax deduction amount
    """
    calculator = ProfessionalTaxCalculator()
    calculation = calculator.calculate_professional_tax(
        gross_annual_salary, state, professional_tax_paid
    )
    return calculation.deduction_under_16


def get_state_from_code(state_code: str) -> Optional[IndianState]:
    """Get IndianState enum from state code."""
    for state in IndianState:
        if state.value == state_code.upper():
            return state
    return None