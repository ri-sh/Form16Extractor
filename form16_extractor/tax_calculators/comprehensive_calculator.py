"""
Comprehensive Tax Calculator

Integrates all tax calculation components including:
- HRA exemption calculation
- LTA exemption calculation  
- Professional tax deduction
- Section 89 relief for arrears
- Perquisite valuation
- Gratuity exemption
- Year-specific rule handling
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass

from .interfaces.calculator_interface import (
    ITaxCalculator, TaxCalculationInput, TaxCalculationResult, 
    TaxRegimeType, AgeCategory
)
from .interfaces.rule_provider_interface import ITaxRuleProvider
from .main_calculator import MultiYearTaxCalculator
from .components.hra_calculator import HRACalculator, HRADetails, CityType
from .components.lta_calculator import LTACalculator
from .components.professional_tax import ProfessionalTaxCalculator, IndianState, get_state_from_code
from .components.section_89_relief import Section89ReliefCalculator, ArrearDetails
from .components.perquisite_calculator import PerquisiteCalculator
from .components.gratuity_calculator import GratuityCalculator, ServiceDetails, EmploymentType


@dataclass
class ComprehensiveTaxCalculationInput(TaxCalculationInput):
    """Extended input class with comprehensive tax calculation fields."""
    
    # HRA details
    hra_received: Decimal = Decimal('0')
    basic_salary: Decimal = Decimal('0')
    rent_paid: Decimal = Decimal('0')
    city_type: str = 'non_metro'  # 'metro' or 'non_metro'
    
    # LTA details
    lta_received: Decimal = Decimal('0')
    
    # Professional tax details
    work_state: str = ''  # State code like 'MH', 'KA'
    professional_tax_paid: Decimal = Decimal('0')
    
    # Section 89 relief details
    salary_arrears: Dict[str, Decimal] = None  # {year: amount}
    
    # Perquisite details
    perquisites_total: Decimal = Decimal('0')
    
    # Gratuity details
    gratuity_received: Decimal = Decimal('0')
    years_of_service: Decimal = Decimal('0')
    employment_type: str = 'covered_under_act'
    
    # Medical reimbursement
    medical_reimbursement: Decimal = Decimal('0')
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        super().__post_init__()
        if self.salary_arrears is None:
            self.salary_arrears = {}


class ComprehensiveTaxCalculationResult(TaxCalculationResult):
    """Extended result class with comprehensive calculation breakdown."""
    
    def __init__(self, base_result: TaxCalculationResult, **kwargs):
        """Initialize comprehensive result from base result."""
        # Copy all attributes from base result
        for attr in dir(base_result):
            if not attr.startswith('_') and hasattr(base_result, attr):
                setattr(self, attr, getattr(base_result, attr))
        
        # Add comprehensive calculation details
        self.hra_exemption: Decimal = kwargs.get('hra_exemption', Decimal('0'))
        self.lta_exemption: Decimal = kwargs.get('lta_exemption', Decimal('0'))
        self.professional_tax_deduction: Decimal = kwargs.get('professional_tax_deduction', Decimal('0'))
        self.section_89_relief: Decimal = kwargs.get('section_89_relief', Decimal('0'))
        self.gratuity_exemption: Decimal = kwargs.get('gratuity_exemption', Decimal('0'))
        self.medical_reimbursement_exemption: Decimal = kwargs.get('medical_reimbursement_exemption', Decimal('0'))
        self.total_additional_exemptions: Decimal = kwargs.get('total_additional_exemptions', Decimal('0'))
        
        # Detailed breakdown
        self.exemption_breakdown: Dict[str, Decimal] = kwargs.get('exemption_breakdown', {})
        self.optimization_suggestions: List[str] = kwargs.get('optimization_suggestions', [])


class ComprehensiveTaxCalculator(ITaxCalculator):
    """
    Comprehensive tax calculator integrating all components.
    
    This calculator combines:
    - Base tax calculation (MultiYearTaxCalculator)
    - HRA exemption calculation
    - LTA exemption calculation
    - Professional tax deduction
    - Section 89 relief for salary arrears
    - Perquisite valuation
    - Gratuity exemption
    - Medical reimbursement exemption
    """
    
    def __init__(self, rule_provider: Optional[ITaxRuleProvider] = None):
        """Initialize comprehensive tax calculator."""
        self.base_calculator = MultiYearTaxCalculator(rule_provider)
        self.rule_provider = self.base_calculator.rule_provider
        
        # Initialize component calculators
        self.hra_calculator = HRACalculator()
        self.lta_calculator = LTACalculator()
        self.professional_tax_calculator = ProfessionalTaxCalculator()
        self.section_89_calculator = Section89ReliefCalculator(self.rule_provider)
        self.perquisite_calculator = PerquisiteCalculator()
        self.gratuity_calculator = GratuityCalculator()
    
    def calculate_tax(self, input_data: ComprehensiveTaxCalculationInput) -> ComprehensiveTaxCalculationResult:
        """
        Calculate comprehensive tax with all components integrated.
        
        Process:
        1. Calculate exemptions and deductions from all components
        2. Adjust taxable income accordingly
        3. Perform base tax calculation
        4. Apply Section 89 relief if applicable
        5. Generate comprehensive result with breakdown
        """
        # Step 1: Calculate all exemptions and deductions
        exemptions = self._calculate_comprehensive_exemptions(input_data)
        deductions = self._calculate_comprehensive_deductions(input_data)
        
        # Step 2: Adjust input for base calculation
        adjusted_input = self._create_adjusted_input(input_data, exemptions, deductions)
        
        # Step 3: Perform base tax calculation
        base_result = self.base_calculator.calculate_tax(adjusted_input)
        
        # Step 4: Apply Section 89 relief if applicable
        section_89_relief = Decimal('0')
        if input_data.salary_arrears:
            section_89_relief = self._calculate_section_89_relief(input_data, adjusted_input)
        
        # Step 5: Create comprehensive result
        comprehensive_result = self._create_comprehensive_result(
            base_result, exemptions, deductions, section_89_relief, input_data
        )
        
        return comprehensive_result
    
    def _calculate_comprehensive_exemptions(self, input_data: ComprehensiveTaxCalculationInput) -> Dict[str, Decimal]:
        """Calculate all exemptions from various components."""
        exemptions = {}
        
        # HRA Exemption
        if input_data.hra_received > 0 and input_data.rent_paid > 0:
            city_type = CityType.METRO if input_data.city_type == 'metro' else CityType.NON_METRO
            hra_details = HRADetails(
                hra_received=input_data.hra_received,
                basic_salary=input_data.basic_salary,
                rent_paid=input_data.rent_paid,
                city_type=city_type
            )
            hra_calc = self.hra_calculator.calculate_hra_exemption(hra_details)
            exemptions['hra_exemption'] = hra_calc.exempt_hra
        
        # LTA Exemption (simplified - would need travel details for full calculation)
        if input_data.lta_received > 0:
            # For now, assume optimal utilization - in practice would need travel details
            exemptions['lta_exemption'] = min(input_data.lta_received, Decimal('50000'))
        
        # Gratuity Exemption
        if input_data.gratuity_received > 0:
            employment_type = EmploymentType.COVERED_UNDER_ACT  # Default
            if input_data.employment_type == 'government':
                employment_type = EmploymentType.GOVERNMENT
            elif input_data.employment_type == 'not_covered':
                employment_type = EmploymentType.NOT_COVERED_UNDER_ACT
            
            service_details = ServiceDetails(
                total_service_years=input_data.years_of_service,
                total_service_months=int(input_data.years_of_service * 12),
                last_drawn_salary=input_data.basic_salary
            )
            
            gratuity_calc = self.gratuity_calculator.calculate_gratuity_exemption(
                input_data.gratuity_received, service_details, employment_type
            )
            exemptions['gratuity_exemption'] = gratuity_calc.exempt_gratuity
        
        # Medical Reimbursement Exemption
        if input_data.medical_reimbursement > 0:
            # Medical reimbursement up to Rs.15,000 is exempt
            exemptions['medical_reimbursement_exemption'] = min(
                input_data.medical_reimbursement, Decimal('15000')
            )
        
        return exemptions
    
    def _calculate_comprehensive_deductions(self, input_data: ComprehensiveTaxCalculationInput) -> Dict[str, Decimal]:
        """Calculate all deductions from various components."""
        deductions = {}
        
        # Professional Tax Deduction
        if input_data.work_state and input_data.gross_salary > 0:
            state = get_state_from_code(input_data.work_state)
            if state:
                prof_calc = self.professional_tax_calculator.calculate_professional_tax(
                    input_data.gross_salary, state, input_data.professional_tax_paid
                )
                deductions['professional_tax'] = prof_calc.deduction_under_16
        
        return deductions
    
    def _create_adjusted_input(
        self, 
        original_input: ComprehensiveTaxCalculationInput,
        exemptions: Dict[str, Decimal],
        deductions: Dict[str, Decimal]
    ) -> TaxCalculationInput:
        """Create adjusted input for base calculation."""
        # Calculate total exemptions and deductions
        total_exemptions = sum(exemptions.values())
        total_section_16_deductions = sum(deductions.values())
        
        # Adjust gross salary for exemptions (these reduce taxable salary)
        adjusted_gross_salary = original_input.gross_salary - total_exemptions
        
        # Adjust gross total income (same as gross salary for our purposes)
        adjusted_gross_total_income = original_input.gross_salary + original_input.other_income - total_exemptions
        
        # Create adjusted input
        adjusted_input = TaxCalculationInput(
            assessment_year=original_input.assessment_year,
            regime_type=original_input.regime_type,
            age_category=original_input.age_category,
            gross_salary=adjusted_gross_salary,
            other_income=original_input.other_income,
            house_property_income=original_input.house_property_income,
            standard_deduction=original_input.standard_deduction + total_section_16_deductions,
            section_80c=original_input.section_80c + deductions.get('section_80c', Decimal('0')),
            section_80d=original_input.section_80d + deductions.get('section_80d', Decimal('0')),
            section_80ccd_1b=original_input.section_80ccd_1b + deductions.get('section_80ccd_1b', Decimal('0')),
            other_deductions=dict(original_input.other_deductions or {}, **{k: v for k, v in deductions.items() if k.startswith('other_')}),
            hra_exemption=original_input.hra_exemption + exemptions.get('hra_exemption', Decimal('0')),
            lta_exemption=original_input.lta_exemption + exemptions.get('lta_exemption', Decimal('0')),
            other_exemptions=dict(original_input.other_exemptions or {}, **{k: v for k, v in exemptions.items() if k.startswith('other_')}),
            house_property_loss=original_input.house_property_loss,
            tds_deducted=original_input.tds_deducted,
            advance_tax_paid=original_input.advance_tax_paid,
            self_assessment_tax=original_input.self_assessment_tax
        )
        
        return adjusted_input
    
    def _calculate_section_89_relief(
        self,
        input_data: ComprehensiveTaxCalculationInput,
        adjusted_input: TaxCalculationInput
    ) -> Decimal:
        """Calculate Section 89 relief for salary arrears."""
        try:
            arrear_details = [
                ArrearDetails(
                    assessment_year=year,
                    arrear_amount=amount,
                    year_of_receipt=input_data.assessment_year
                )
                for year, amount in input_data.salary_arrears.items()
            ]
            
            relief_calc = self.section_89_calculator.calculate_section_89_relief(
                adjusted_input, arrear_details, input_data.assessment_year
            )
            
            return relief_calc.relief_amount
            
        except Exception as e:
            # If Section 89 calculation fails, log and continue without relief
            print(f"Warning: Section 89 relief calculation failed: {e}")
            return Decimal('0')
    
    def _create_comprehensive_result(
        self,
        base_result: TaxCalculationResult,
        exemptions: Dict[str, Decimal],
        deductions: Dict[str, Decimal], 
        section_89_relief: Decimal,
        input_data: ComprehensiveTaxCalculationInput
    ) -> ComprehensiveTaxCalculationResult:
        """Create comprehensive result with all calculation details."""
        
        # Calculate total additional exemptions
        total_additional_exemptions = sum(exemptions.values())
        
        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(
            input_data, exemptions, deductions
        )
        
        # Adjust final tax liability for Section 89 relief
        final_tax_liability = max(Decimal('0'), base_result.total_tax_liability - section_89_relief)
        base_result.total_tax_liability = final_tax_liability
        
        # Create comprehensive result
        comprehensive_result = ComprehensiveTaxCalculationResult(
            base_result,
            hra_exemption=exemptions.get('hra_exemption', Decimal('0')),
            lta_exemption=exemptions.get('lta_exemption', Decimal('0')),
            professional_tax_deduction=deductions.get('professional_tax', Decimal('0')),
            section_89_relief=section_89_relief,
            gratuity_exemption=exemptions.get('gratuity_exemption', Decimal('0')),
            medical_reimbursement_exemption=exemptions.get('medical_reimbursement_exemption', Decimal('0')),
            total_additional_exemptions=total_additional_exemptions,
            exemption_breakdown=exemptions,
            optimization_suggestions=optimization_suggestions
        )
        
        return comprehensive_result
    
    def _generate_optimization_suggestions(
        self,
        input_data: ComprehensiveTaxCalculationInput,
        exemptions: Dict[str, Decimal],
        deductions: Dict[str, Decimal]
    ) -> List[str]:
        """Generate tax optimization suggestions."""
        suggestions = []
        
        # HRA optimization
        if input_data.hra_received > 0:
            hra_exemption = exemptions.get('hra_exemption', Decimal('0'))
            hra_utilization = float(hra_exemption / input_data.hra_received * 100) if input_data.hra_received > 0 else 0
            if hra_utilization < 80:
                suggestions.append(f"HRA utilization is {hra_utilization:.1f}%. Consider optimizing rent payments.")
        
        # LTA optimization
        if input_data.lta_received > 0:
            suggestions.append("Plan domestic travel to utilize LTA exemption benefits effectively.")
        
        # Professional tax
        if not input_data.work_state:
            suggestions.append("Provide work state information for professional tax calculation.")
        
        # Section 80C optimization
        if hasattr(input_data, 'section_80c') and input_data.section_80c < 150000:
            remaining = 150000 - input_data.section_80c
            suggestions.append(f"Consider additional Section 80C investments worth ₹{remaining:,.0f}.")
        
        return suggestions
    
    def validate_input(self, input_data: ComprehensiveTaxCalculationInput) -> List[str]:
        """Validate comprehensive tax calculation input."""
        errors = []
        
        # Basic validation
        base_errors = self.base_calculator.validate_input(input_data)
        errors.extend(base_errors)
        
        # HRA validation
        if input_data.hra_received > 0 and input_data.rent_paid == 0:
            errors.append("Cannot claim HRA exemption without rent payment")
        
        # Gratuity validation
        if input_data.gratuity_received > 0 and input_data.years_of_service <= 0:
            errors.append("Years of service required for gratuity exemption")
        
        return errors
    
    def compare_regimes(
        self, 
        input_data: ComprehensiveTaxCalculationInput, 
        assessment_year: Optional[str] = None
    ) -> Dict[str, ComprehensiveTaxCalculationResult]:
        """Compare tax calculation results between old and new regimes."""
        if assessment_year:
            input_data.assessment_year = assessment_year
        
        results = {}
        
        # Calculate for old regime
        old_input = input_data
        old_input.regime_type = TaxRegimeType.OLD
        results['old'] = self.calculate_tax(old_input)
        
        # Calculate for new regime  
        new_input = input_data
        new_input.regime_type = TaxRegimeType.NEW
        results['new'] = self.calculate_tax(new_input)
        
        return results
    
    def get_supported_assessment_years(self) -> List[str]:
        """Get list of supported assessment years."""
        return self.base_calculator.get_supported_assessment_years()