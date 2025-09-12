"""
Tax Calculation Service - Business logic for comprehensive tax calculations.

This service handles all tax-related calculations including:
- Comprehensive tax calculation for both regimes
- Form16-based tax extraction and calculation
- Demo tax data generation
- Tax regime comparison and recommendations
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from pathlib import Path


class TaxCalculationService:
    """Service for handling comprehensive tax calculations."""
    
    def __init__(self):
        """Initialize the tax calculation service."""
        pass
    
    def calculate_comprehensive_tax(
        self, 
        form16_result: Any, 
        tax_args: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate comprehensive tax using extracted Form16 data.
        
        Args:
            form16_result: Extracted Form16 document data
            tax_args: Dictionary containing tax calculation arguments
                     (tax_regime, city_type, age_category, bank_interest, other_income)
        
        Returns:
            Dictionary containing tax calculation results or None if insufficient data
        """
        try:
            from form16x.form16_parser.tax_calculators.comprehensive_calculator import (
                ComprehensiveTaxCalculator, ComprehensiveTaxCalculationInput
            )
            from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import (
                TaxRegimeType, AgeCategory
            )
            from form16x.form16_parser.tax_calculators.rules.year_specific_rule_provider import (
                YearSpecificTaxRuleProvider
            )
            
            # Validate Form16 data availability
            if not hasattr(form16_result, 'salary') or not hasattr(form16_result, 'chapter_via_deductions'):
                if tax_args.get('verbose', False):
                    print("Warning: Insufficient Form16 data for tax calculation")
                return None
            
            # Extract financial data from Form16Document
            extraction_data = self._extract_financial_data(form16_result)
            
            # Parse command line arguments for tax calculation
            tax_regime = self._parse_tax_regime(tax_args.get('tax_regime', 'both'))
            city_type = tax_args.get('city_type', 'metro')
            age_category = self._parse_age_category(tax_args.get('age_category', 'below_60'))
            bank_interest = Decimal(str(tax_args.get('bank_interest', 0) or 0))
            other_income = Decimal(str(tax_args.get('other_income', 0) or 0))
            
            # Get assessment year from Form16 or use default
            assessment_year = self._extract_assessment_year_from_form16(form16_result)
            
            # Initialize tax calculator
            rule_provider = YearSpecificTaxRuleProvider()
            calculator = ComprehensiveTaxCalculator(rule_provider)
            
            # Prepare tax calculation input
            gross_salary = Decimal(str(extraction_data['gross_salary']))
            basic_salary = Decimal(str(extraction_data['section_17_1']))
            
            # Calculate HRA (if not explicitly provided, estimate based on basic salary)
            hra_received = gross_salary - basic_salary - Decimal(str(extraction_data['perquisites']))
            if hra_received < 0:
                hra_received = Decimal('0')
            
            # Create comprehensive input
            tax_input = ComprehensiveTaxCalculationInput(
                gross_salary=gross_salary,
                assessment_year=assessment_year,
                regime_type=tax_regime if tax_regime != TaxRegimeType.BOTH else TaxRegimeType.OLD,
                basic_salary=basic_salary,
                hra_received=hra_received,
                rent_paid=Decimal('0'),  # Not available in Form16
                city_type=city_type,
                other_income=other_income,
                bank_interest_income=bank_interest,
                section_80c=Decimal(str(extraction_data['section_80c'])),
                section_80ccd_1b=Decimal(str(extraction_data['section_80ccd_1b'])),
                age_category=age_category
            )
            
            # Calculate tax for specified regime(s)
            if tax_regime == TaxRegimeType.BOTH:
                # Calculate for old regime
                old_input = ComprehensiveTaxCalculationInput(
                    gross_salary=gross_salary,
                    assessment_year=assessment_year,
                    regime_type=TaxRegimeType.OLD,
                    basic_salary=basic_salary,
                    hra_received=hra_received,
                    rent_paid=Decimal('0'),
                    city_type=city_type,
                    other_income=other_income,
                    bank_interest_income=bank_interest,
                    section_80c=Decimal(str(extraction_data['section_80c'])),
                    section_80ccd_1b=Decimal(str(extraction_data['section_80ccd_1b'])),
                    age_category=age_category
                )
                # Calculate for new regime
                new_input = ComprehensiveTaxCalculationInput(
                    gross_salary=gross_salary,
                    assessment_year=assessment_year,
                    regime_type=TaxRegimeType.NEW,
                    basic_salary=basic_salary,
                    hra_received=hra_received,
                    rent_paid=Decimal('0'),
                    city_type=city_type,
                    other_income=other_income,
                    bank_interest_income=bank_interest,
                    section_80c=Decimal(str(extraction_data['section_80c'])),
                    section_80ccd_1b=Decimal(str(extraction_data['section_80ccd_1b'])),
                    age_category=age_category
                )
                old_result = calculator.calculate_tax(old_input)
                new_result = calculator.calculate_tax(new_input)
                results = {'old': old_result, 'new': new_result}
                comparison = calculator.compare_regimes(old_result, new_result)
            else:
                result = calculator.calculate_tax(tax_input)
                results = {tax_regime.value: result}
                comparison = {}
            
            # Build comprehensive result
            return self._build_tax_calculation_result(
                results, comparison, extraction_data, tax_input, tax_args
            )
            
        except Exception as e:
            if tax_args.get('verbose', False):
                print(f"Comprehensive tax calculation error: {str(e)}")
                print("Using simplified tax calculation...")
            
            # Fallback to simple tax calculation (not demo mode)
            return self._calculate_simple_tax(extraction_data, tax_args)
    
    def _calculate_simple_tax(self, extraction_data: Dict[str, Any], tax_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate tax using simple hardcoded rules (fallback when comprehensive calculator fails).
        
        Args:
            extraction_data: Financial data extracted from Form16
            tax_args: Tax calculation arguments
            
        Returns:
            Dictionary containing tax calculation results (without demo_mode flag)
        """
        from ..tax_calculators.simple_tax_calculator import SimpleTaxCalculator
        from decimal import Decimal
        
        calculator = SimpleTaxCalculator()
        
        # Extract data from Form16
        gross_salary = Decimal(str(extraction_data.get('gross_salary', 0)))
        section_80c = Decimal(str(extraction_data.get('section_80c', 0)))
        section_80ccd_1b = Decimal(str(extraction_data.get('section_80ccd_1b', 0)))
        tds_paid = Decimal(str(extraction_data.get('total_tds', 0)))
        
        # Calculate tax
        results = calculator.calculate_tax_both_regimes(
            gross_salary=gross_salary,
            section_80c=section_80c,
            section_80ccd_1b=section_80ccd_1b,
            tds_paid=tds_paid,
            assessment_year=tax_args.get('assessment_year', '2024-25')
        )
        
        # Add extraction data for display
        results['extraction_data'] = extraction_data
        
        return results
    
    def get_demo_tax_results(self, tax_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate demo tax calculation results for demonstration purposes.
        
        Args:
            tax_args: Dictionary containing tax calculation arguments
            
        Returns:
            Dictionary containing demo tax calculation results
        """
        # Return pre-calculated demo results
        return {
            'results': {
                'old': {
                    'tax_liability': 103723,
                    'taxable_income': 862724,
                    'tds_paid': 85000,
                    'balance': -18723,
                    'effective_tax_rate': 12.02
                },
                'new': {
                    'tax_liability': 78723,
                    'taxable_income': 862724,
                    'tds_paid': 85000,
                    'balance': 6277,
                    'effective_tax_rate': 9.13
                }
            },
            'comparison': {
                'savings_with_new': 25000,
                'recommended_regime': 'new'
            },
            'recommendation': 'NEW regime saves ₹25,000 annually',
            'demo_mode': True
        }
    
    def _generate_demo_tax_results_from_extraction(self, extraction_data: Dict[str, Any], tax_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate demo tax results based on actual extracted Form16 data.
        
        Args:
            extraction_data: Financial data extracted from Form16
            tax_args: Tax calculation arguments
            
        Returns:
            Dictionary containing realistic demo tax results
        """
        gross_salary = extraction_data.get('gross_salary', 800000)
        section_80c = extraction_data.get('section_80c', 15000)
        
        # Calculate realistic tax amounts based on actual salary
        taxable_income_old = gross_salary - 50000 - section_80c  # Standard deduction + 80C
        taxable_income_new = gross_salary - 50000  # Only standard deduction in new regime
        
        # Approximate tax calculation for demo
        # Old regime: Higher deductions but higher rates
        if taxable_income_old <= 250000:
            tax_old = 0
        elif taxable_income_old <= 500000:
            tax_old = (taxable_income_old - 250000) * 0.05
        elif taxable_income_old <= 1000000:
            tax_old = 12500 + (taxable_income_old - 500000) * 0.20
        else:
            tax_old = 112500 + (taxable_income_old - 1000000) * 0.30
            
        # New regime: Lower deductions but lower rates
        if taxable_income_new <= 300000:
            tax_new = 0
        elif taxable_income_new <= 600000:
            tax_new = (taxable_income_new - 300000) * 0.05
        elif taxable_income_new <= 900000:
            tax_new = 15000 + (taxable_income_new - 600000) * 0.10
        elif taxable_income_new <= 1200000:
            tax_new = 45000 + (taxable_income_new - 900000) * 0.15
        else:
            tax_new = 90000 + (taxable_income_new - 1200000) * 0.20
            
        # Add cess and round to nearest rupee
        tax_old = int(tax_old * 1.04)  # 4% cess
        tax_new = int(tax_new * 1.04)  # 4% cess
        
        return {
            'results': {
                'old': {
                    'gross_salary': gross_salary,
                    'taxable_income': taxable_income_old,
                    'tax_liability': tax_old,
                    'tds_paid': extraction_data.get('total_tds', 65000),
                    'balance': extraction_data.get('total_tds', 65000) - tax_old,
                    'effective_tax_rate': (tax_old / gross_salary * 100) if gross_salary > 0 else 0
                },
                'new': {
                    'gross_salary': gross_salary,
                    'taxable_income': taxable_income_new,
                    'tax_liability': tax_new,
                    'tds_paid': extraction_data.get('total_tds', 65000),
                    'balance': extraction_data.get('total_tds', 65000) - tax_new,
                    'effective_tax_rate': (tax_new / gross_salary * 100) if gross_salary > 0 else 0
                }
            },
            'comparison': {
                'savings_with_new': max(0, tax_old - tax_new),
                'recommended_regime': 'new' if tax_new < tax_old else 'old'
            },
            'extraction_data': extraction_data,
            'recommendation': f"{'NEW' if tax_new < tax_old else 'OLD'} regime saves ₹{abs(tax_old - tax_new):,.0f} annually",
            'demo_mode': True
        }
    
    def calculate_tax_with_consolidated_demo_data(self, consolidated_data: Dict[str, Any], tax_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate tax using consolidated demo data from multiple employers.
        
        Args:
            consolidated_data: Consolidated Form16 data from multiple employers
            tax_args: Tax calculation arguments
            
        Returns:
            Dictionary containing tax calculation results with proper consolidated values
        """
        # Extract totals from consolidated data
        summary = consolidated_data.get('consolidated_summary', {})
        total_gross = summary.get('total_gross_income', 2500000)
        total_tds = summary.get('total_tds_paid', 400000)  # 16% of 25L
        
        # Create financial data structure similar to regular extraction
        financial_data = {
            'employee_name': 'ASHISH MITTAL',
            'employee_pan': 'DEMO12345X', 
            'employer_name': 'MULTIPLE EMPLOYERS (CONSOLIDATED)',
            'gross_salary': total_gross,
            'section_17_1': total_gross * 0.85,  # 85% basic salary
            'perquisites': total_gross * 0.15,   # 15% perquisites
            'section_80c': 150000,               # Standard 80C deduction
            'section_80ccd_1b': 50000,           # NPS additional deduction
            'total_tds': total_tds
        }
        
        # Calculate tax for both regimes using realistic consolidated amounts
        return {
            'results': {
                'old': {
                    'gross_salary': total_gross,
                    'taxable_income': total_gross - 250000,  # Less deductions
                    'tax_liability': 675000,  # Higher tax for 25L salary
                    'tds_paid': total_tds,
                    'balance': total_tds - 675000,  # Likely refund
                    'effective_tax_rate': 27.0
                },
                'new': {
                    'gross_salary': total_gross,
                    'taxable_income': total_gross - 100000,  # Less deductions in new regime
                    'tax_liability': 600000,  # Lower tax in new regime
                    'tds_paid': total_tds,
                    'balance': total_tds - 600000,  # Better refund
                    'effective_tax_rate': 24.0
                }
            },
            'comparison': {
                'savings_with_new': 75000,  # Realistic savings for 25L salary
                'recommended_regime': 'new'
            },
            'financial_data': financial_data,
            'extraction_data': financial_data,  # Also add as extraction_data for display compatibility
            'recommendation': f'NEW regime saves ₹75,000 annually',
            'demo_mode': True
        }
    
    def _extract_financial_data(self, form16_result: Any) -> Dict[str, Any]:
        """
        Extract financial data from Form16 result for tax calculation.
        
        Args:
            form16_result: Extracted Form16 document data
            
        Returns:
            Dictionary containing extracted financial data
        """
        salary_data = form16_result.salary
        gross_salary = Decimal(str(salary_data.gross_salary or 0))
        basic_salary = Decimal(str(salary_data.basic_salary or 0))
        perquisites = Decimal(str(getattr(salary_data, 'perquisites_value', 0) or 0))
        
        # Extract deductions
        deductions = form16_result.chapter_via_deductions
        section_80c = Decimal(str(deductions.section_80c_total or 0))
        section_80ccd_1b = Decimal(str(deductions.section_80ccd_1b or 0))
        
        # Calculate total TDS from quarterly data
        total_tds = Decimal('0')
        if hasattr(form16_result, 'quarterly_tds') and form16_result.quarterly_tds:
            for quarter_data in form16_result.quarterly_tds:
                if hasattr(quarter_data, 'tax_deducted') and quarter_data.tax_deducted:
                    total_tds += Decimal(str(quarter_data.tax_deducted))
        
        return {
            'employee_name': getattr(form16_result.employee, 'name', 'N/A'),
            'employee_pan': getattr(form16_result.employee, 'pan', 'N/A'),
            'employer_name': getattr(form16_result.employer, 'name', 'N/A'),
            'gross_salary': float(gross_salary),
            'section_17_1': float(basic_salary),
            'perquisites': float(perquisites),
            'section_80c': float(section_80c),
            'section_80ccd_1b': float(section_80ccd_1b),
            'total_tds': float(total_tds),
        }
    
    def _parse_tax_regime(self, regime_str: str):
        """Parse tax regime string to enum value."""
        from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import TaxRegimeType
        
        regime_map = {
            'old': TaxRegimeType.OLD,
            'new': TaxRegimeType.NEW,
            'both': TaxRegimeType.BOTH
        }
        return regime_map.get(regime_str.lower(), TaxRegimeType.BOTH)
    
    def _parse_age_category(self, age_str: str):
        """Parse age category string to enum value."""
        from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import AgeCategory
        
        age_map = {
            'below_60': AgeCategory.BELOW_60,
            'senior_60_to_80': AgeCategory.SENIOR_60_TO_80,
            'super_senior_above_80': AgeCategory.SUPER_SENIOR_ABOVE_80
        }
        return age_map.get(age_str.lower(), AgeCategory.BELOW_60)
    
    def _extract_assessment_year_from_form16(self, form16_result: Any) -> str:
        """Extract assessment year from Form16 result."""
        if hasattr(form16_result, 'financial_year') and form16_result.financial_year:
            fy = form16_result.financial_year
            if isinstance(fy, str) and '-' in fy:
                start_year = fy.split('-')[0]
                return f"{int(start_year) + 1}-{str(int(start_year) + 2)[-2:]}"
        return "2024-25"  # Default fallback
    
    def _build_tax_calculation_result(
        self, 
        results: Dict[str, Any], 
        comparison: Dict[str, Any],
        extraction_data: Dict[str, Any],
        tax_input: Any,
        tax_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build comprehensive tax calculation result structure.
        
        Args:
            results: Tax calculation results for regimes
            comparison: Regime comparison data
            extraction_data: Extracted Form16 data
            tax_input: Tax calculation input parameters
            tax_args: Original tax calculation arguments
            
        Returns:
            Comprehensive tax calculation result dictionary
        """
        return {
            'results': results,
            'comparison': comparison,
            'extraction_data': extraction_data,
            'calculation_input': {
                'gross_salary': float(tax_input.gross_salary),
                'basic_salary': float(tax_input.basic_salary),
                'hra_received': float(tax_input.hra_received),
                'other_income': float(tax_input.other_income),
                'bank_interest': float(tax_input.bank_interest),
                'assessment_year': tax_input.assessment_year,
                'age_category': tax_input.age_category.value,
                'city_type': tax_input.city_type
            },
            'display_options': {
                'display_mode': tax_args.get('display_mode', 'colored'),
                'summary': tax_args.get('summary', False)
            }
        }