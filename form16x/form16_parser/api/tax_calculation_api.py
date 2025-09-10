"""
Comprehensive Tax Calculation API

This module provides a clean, programmatic API for tax calculations that can be used
independently of the CLI. It serves as the main entry point for developers who want
to integrate tax calculations into their applications.

Example usage:
    ```python
    from form16x.form16_parser.api.tax_calculation_api import TaxCalculationAPI
    from decimal import Decimal
    
    # Initialize API
    api = TaxCalculationAPI()
    
    # Calculate tax from Form16 PDF
    result = api.calculate_tax_from_form16(
        form16_file="path/to/form16.pdf",
        assessment_year="2024-25",
        regime="both"
    )
    
    # Calculate tax from manual input
    result = api.calculate_tax_from_input(
        assessment_year="2024-25",
        gross_salary=Decimal("1200000"),
        bank_interest=Decimal("25000"),
        section_80c=Decimal("150000"),
        # ... other parameters
    )
    ```
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from decimal import Decimal
from enum import Enum

from ..extractors.enhanced_form16_extractor import EnhancedForm16Extractor, ProcessingLevel
from ..pdf.reader import RobustPDFProcessor
from ..integrators.data_mapper import Form16ToTaxMapper
from ..tax_calculators.comprehensive_calculator import (
    ComprehensiveTaxCalculator, ComprehensiveTaxCalculationInput
)
from ..tax_calculators.interfaces.calculator_interface import (
    TaxRegimeType, AgeCategory
)
from ..tax_calculators.rules.year_specific_rule_provider import YearSpecificTaxRuleProvider


class TaxRegime(str, Enum):
    """Tax regime options."""
    OLD = "old"
    NEW = "new"
    BOTH = "both"


class AgeCategoryEnum(str, Enum):
    """Age category options."""
    BELOW_60 = "below_60"
    SENIOR_60_TO_80 = "senior_60_to_80"
    SUPER_SENIOR_ABOVE_80 = "super_senior_above_80"


class TaxCalculationAPI:
    """
    Comprehensive Tax Calculation API for programmatic usage.
    
    This class provides a clean interface for tax calculations that can be used
    independently of the CLI. It handles both Form16-based calculations and 
    manual input calculations with proper error handling and validation.
    """

    def __init__(self):
        """Initialize the Tax Calculation API with required components."""
        self.extractor = EnhancedForm16Extractor(ProcessingLevel.ENHANCED)
        self.pdf_processor = RobustPDFProcessor()
        self.data_mapper = Form16ToTaxMapper()
        self.calculator = ComprehensiveTaxCalculator(YearSpecificTaxRuleProvider())

    def calculate_tax_from_form16(
        self,
        form16_file: Union[str, Path],
        assessment_year: Optional[str] = None,
        regime: TaxRegime = TaxRegime.BOTH,
        age_category: AgeCategoryEnum = AgeCategoryEnum.BELOW_60,
        bank_interest: Optional[Decimal] = None,
        other_income: Optional[Decimal] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate tax from Form16 PDF document.
        
        Args:
            form16_file: Path to Form16 PDF file
            assessment_year: Assessment year (e.g., '2024-25'). If None, extracted from Form16
            regime: Tax regime to calculate ('old', 'new', or 'both')
            age_category: Age category of taxpayer
            bank_interest: Bank interest income (overrides Form16 data if provided)
            other_income: Other income (overrides Form16 data if provided)
            verbose: Whether to enable verbose logging
            
        Returns:
            Dictionary containing tax calculation results:
            {
                'status': 'success' | 'error',
                'assessment_year': str,
                'regimes_calculated': List[str],
                'results': {
                    'old': {...} if calculated,
                    'new': {...} if calculated
                },
                'recommendation': str,
                'error_message': str if error occurred
            }
            
        Raises:
            FileNotFoundError: If Form16 file doesn't exist
            ValueError: If invalid parameters provided
        """
        try:
            # Validate inputs
            form16_path = Path(form16_file).expanduser()
            if not form16_path.exists():
                raise FileNotFoundError(f"Form16 file not found: {form16_file}")
            
            if not form16_path.suffix.lower() == '.pdf':
                raise ValueError(f"Only PDF files are supported, got: {form16_path.suffix}")
            
            # Extract Form16 data
            if verbose:
                print(f"Extracting data from Form16: {form16_path.name}")
            
            # First extract tables from PDF, then extract Form16 data from tables
            extraction_result = self.pdf_processor.extract_tables(form16_path)
            form16_result = self.extractor.extract_all(extraction_result.tables)
            
            if not form16_result:
                return {
                    'status': 'error',
                    'error_message': 'Failed to extract data from Form16 PDF'
                }
            
            # Determine assessment year
            if not assessment_year:
                assessment_year = self._extract_assessment_year(form16_result)
            
            # Extract other income from Form16 (with CLI overrides)
            extracted_other_income = self.data_mapper.extract_other_income_from_form16(
                form16_result, verbose
            )
            
            bank_interest_income = (
                bank_interest if bank_interest is not None 
                else extracted_other_income.get('bank_interest', Decimal('0'))
            )
            other_income_amount = (
                other_income if other_income is not None
                else extracted_other_income.get('other_income', Decimal('0'))
            )
            house_property_income = extracted_other_income.get('house_property', Decimal('0'))
            
            # Extract salary and deduction data
            salary_data, deductions_data = self._extract_form16_financial_data(form16_result)
            
            # Calculate tax for requested regimes
            results = {}
            regimes_to_calculate = self._determine_regimes_to_calculate(regime, assessment_year)
            
            for regime_name, regime_type in regimes_to_calculate:
                if verbose:
                    print(f"Calculating tax for {regime_name} regime")
                
                # Create comprehensive input
                comprehensive_input = ComprehensiveTaxCalculationInput(
                    assessment_year=assessment_year,
                    regime_type=regime_type,
                    age_category=self._convert_age_category(age_category),
                    gross_salary=salary_data['gross_salary'],
                    bank_interest_income=bank_interest_income,
                    other_income=other_income_amount,
                    house_property_income=house_property_income,
                    section_80c=deductions_data['section_80c'],
                    section_80ccd_1b=deductions_data['section_80ccd_1b'],
                    tds_deducted=salary_data['total_tds'],
                    basic_salary=salary_data['basic_salary'],
                    hra_received=salary_data['hra_received'],
                    rent_paid=salary_data['hra_received'] * Decimal('1.2'),
                    city_type="metro",  # Default
                    work_state="KA",  # Default
                    professional_tax_paid=Decimal('2500'),
                    lta_received=Decimal('50000'),
                    medical_reimbursement=Decimal('15000'),
                    perquisites_total=salary_data['perquisites'],
                )
                
                # Calculate tax
                tax_result = self.calculator.calculate_tax(comprehensive_input)
                
                # Format result
                tds_paid = salary_data['total_tds']
                balance = tds_paid - tax_result.total_tax_liability
                
                results[regime_name] = {
                    'taxable_income': float(tax_result.taxable_income),
                    'tax_liability': float(tax_result.total_tax_liability),
                    'tds_paid': float(tds_paid),
                    'balance': float(balance),
                    'status': 'refund_due' if balance > 0 else 'additional_payable',
                    'effective_tax_rate': float(
                        (tax_result.total_tax_liability / salary_data['gross_salary']) * 100
                        if salary_data['gross_salary'] > 0 else 0
                    ),
                    'detailed_calculation': {
                        'tax_before_rebate': float(tax_result.tax_before_rebate),
                        'surcharge': float(tax_result.surcharge),
                        'cess': float(tax_result.health_education_cess),
                        'rebate_87a': float(tax_result.rebate_under_87a),
                        'deductions_used': {
                            'section_80c': float(deductions_data['section_80c']),
                            'section_80ccd_1b': float(deductions_data['section_80ccd_1b']),
                            'total_deductions': float(tax_result.total_deductions)
                        }
                    }
                }
            
            # Determine recommendation
            recommendation = self._determine_recommendation(results)
            
            return {
                'status': 'success',
                'assessment_year': assessment_year,
                'regimes_calculated': list(results.keys()),
                'results': results,
                'recommendation': recommendation,
                'input_data': {
                    'gross_salary': float(salary_data['gross_salary']),
                    'bank_interest': float(bank_interest_income),
                    'other_income': float(other_income_amount),
                    'house_property': float(house_property_income),
                    'section_80c': float(deductions_data['section_80c']),
                    'section_80ccd_1b': float(deductions_data['section_80ccd_1b'])
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'assessment_year': assessment_year
            }

    def calculate_tax_from_input(
        self,
        assessment_year: str,
        gross_salary: Decimal,
        regime: TaxRegime = TaxRegime.BOTH,
        age_category: AgeCategoryEnum = AgeCategoryEnum.BELOW_60,
        bank_interest: Decimal = Decimal('0'),
        other_income: Decimal = Decimal('0'),
        house_property_income: Decimal = Decimal('0'),
        section_80c: Decimal = Decimal('0'),
        section_80ccd_1b: Decimal = Decimal('0'),
        tds_paid: Decimal = Decimal('0'),
        basic_salary: Optional[Decimal] = None,
        hra_received: Decimal = Decimal('0'),
        city_type: str = "metro",
        work_state: str = "KA",
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate tax from manual input parameters.
        
        Args:
            assessment_year: Assessment year (e.g., '2024-25')
            gross_salary: Total gross salary
            regime: Tax regime to calculate ('old', 'new', or 'both')
            age_category: Age category of taxpayer
            bank_interest: Bank interest income
            other_income: Other income
            house_property_income: Income from house property
            section_80c: Section 80C deductions
            section_80ccd_1b: Section 80CCD(1B) deductions  
            tds_paid: Total TDS paid
            basic_salary: Basic salary (estimated if not provided)
            hra_received: HRA received
            city_type: City type ('metro' or 'non_metro')
            work_state: Work state code
            verbose: Whether to enable verbose logging
            
        Returns:
            Dictionary containing tax calculation results (same format as calculate_tax_from_form16)
        """
        try:
            # Validate inputs
            if not assessment_year:
                raise ValueError("Assessment year is required")
            
            if gross_salary < 0:
                raise ValueError("Gross salary cannot be negative")
            
            # Estimate basic salary if not provided
            if basic_salary is None:
                basic_salary = gross_salary * Decimal('0.4')  # 40% estimate
            
            # Calculate tax for requested regimes
            results = {}
            regimes_to_calculate = self._determine_regimes_to_calculate(regime, assessment_year)
            
            for regime_name, regime_type in regimes_to_calculate:
                if verbose:
                    print(f"Calculating tax for {regime_name} regime")
                
                # Create comprehensive input
                comprehensive_input = ComprehensiveTaxCalculationInput(
                    assessment_year=assessment_year,
                    regime_type=regime_type,
                    age_category=self._convert_age_category(age_category),
                    gross_salary=gross_salary,
                    bank_interest_income=bank_interest,
                    other_income=other_income,
                    house_property_income=house_property_income,
                    section_80c=section_80c,
                    section_80ccd_1b=section_80ccd_1b,
                    tds_deducted=tds_paid,
                    basic_salary=basic_salary,
                    hra_received=hra_received,
                    rent_paid=hra_received * Decimal('1.2') if hra_received > 0 else Decimal('0'),
                    city_type=city_type,
                    work_state=work_state,
                    professional_tax_paid=Decimal('2500'),  # Default
                    lta_received=Decimal('50000'),  # Default
                    medical_reimbursement=Decimal('15000'),  # Default
                    perquisites_total=Decimal('0'),  # Default
                )
                
                # Calculate tax
                tax_result = self.calculator.calculate_tax(comprehensive_input)
                
                # Format result
                balance = tds_paid - tax_result.total_tax_liability
                
                results[regime_name] = {
                    'taxable_income': float(tax_result.taxable_income),
                    'tax_liability': float(tax_result.total_tax_liability),
                    'tds_paid': float(tds_paid),
                    'balance': float(balance),
                    'status': 'refund_due' if balance > 0 else 'additional_payable',
                    'effective_tax_rate': float(
                        (tax_result.total_tax_liability / gross_salary) * 100
                        if gross_salary > 0 else 0
                    ),
                    'detailed_calculation': {
                        'tax_before_rebate': float(tax_result.tax_before_rebate),
                        'surcharge': float(tax_result.surcharge),
                        'cess': float(tax_result.health_education_cess),
                        'rebate_87a': float(tax_result.rebate_under_87a),
                        'deductions_used': {
                            'section_80c': float(section_80c),
                            'section_80ccd_1b': float(section_80ccd_1b),
                            'total_deductions': float(tax_result.total_deductions)
                        }
                    }
                }
            
            # Determine recommendation
            recommendation = self._determine_recommendation(results)
            
            return {
                'status': 'success',
                'assessment_year': assessment_year,
                'regimes_calculated': list(results.keys()),
                'results': results,
                'recommendation': recommendation,
                'input_data': {
                    'gross_salary': float(gross_salary),
                    'bank_interest': float(bank_interest),
                    'other_income': float(other_income),
                    'house_property': float(house_property_income),
                    'section_80c': float(section_80c),
                    'section_80ccd_1b': float(section_80ccd_1b),
                    'tds_paid': float(tds_paid)
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'assessment_year': assessment_year
            }

    def get_supported_assessment_years(self) -> List[str]:
        """
        Get list of supported assessment years.
        
        Returns:
            List of supported assessment years
        """
        return [
            "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"
        ]

    def check_regime_support(self, assessment_year: str) -> Dict[str, bool]:
        """
        Check which tax regimes are supported for a given assessment year.
        
        Args:
            assessment_year: Assessment year to check
            
        Returns:
            Dictionary with regime support status:
            {'old': bool, 'new': bool}
        """
        try:
            old_supported = self.calculator.rule_provider.is_regime_supported(
                assessment_year, TaxRegimeType.OLD
            )
            new_supported = self.calculator.rule_provider.is_regime_supported(
                assessment_year, TaxRegimeType.NEW
            )
            
            return {
                'old': old_supported,
                'new': new_supported
            }
        except:
            return {
                'old': False,
                'new': False
            }

    def _extract_assessment_year(self, form16_result) -> str:
        """Extract assessment year from Form16 data."""
        # Try to extract from form16 metadata/financial year
        if hasattr(form16_result, 'metadata') and hasattr(form16_result.metadata, 'assessment_year'):
            return form16_result.metadata.assessment_year
        
        # Fallback to current assessment year
        return "2024-25"

    def _extract_form16_financial_data(self, form16_result) -> tuple:
        """Extract salary and deduction data from Form16."""
        # Extract salary data
        salary = getattr(form16_result, 'salary', None)
        gross_salary = Decimal(str(salary.gross_salary or 0)) if salary else Decimal('0')
        basic_salary = Decimal(str(salary.basic_salary or 0)) if salary else gross_salary * Decimal('0.4')
        
        # Extract perquisites
        perquisites = Decimal('0')
        if salary and hasattr(salary, 'perquisites_value') and salary.perquisites_value:
            perquisites = Decimal(str(salary.perquisites_value))
        
        # Estimate HRA (30% of gross salary if not available)
        hra_received = basic_salary * Decimal('0.3')
        
        # Extract TDS using the correct path from data mapper
        total_tds = Decimal('0')
        if (hasattr(form16_result, 'part_a') and 
            hasattr(form16_result.part_a, 'quarterly_tds_summary') and
            hasattr(form16_result.part_a.quarterly_tds_summary, 'total_tds') and
            form16_result.part_a.quarterly_tds_summary.total_tds.deducted is not None):
            total_tds = Decimal(str(form16_result.part_a.quarterly_tds_summary.total_tds.deducted))
        
        # Extract deductions using the correct path from data mapper
        deductions = None
        if hasattr(form16_result, 'part_b') and hasattr(form16_result.part_b, 'chapter_vi_a_deductions'):
            deductions = form16_result.part_b.chapter_vi_a_deductions
        
        section_80c = Decimal('0')
        section_80ccd_1b = Decimal('0')
        if deductions:
            if hasattr(deductions, 'section_80C') and deductions.section_80C.deductible_amount:
                section_80c = Decimal(str(deductions.section_80C.deductible_amount))
            if hasattr(deductions, 'section_80CCD_1B') and deductions.section_80CCD_1B.deductible_amount:
                section_80ccd_1b = Decimal(str(deductions.section_80CCD_1B.deductible_amount))
        
        salary_data = {
            'gross_salary': gross_salary,
            'basic_salary': basic_salary,
            'hra_received': hra_received,
            'perquisites': perquisites,
            'total_tds': total_tds
        }
        
        deductions_data = {
            'section_80c': section_80c,
            'section_80ccd_1b': section_80ccd_1b
        }
        
        return salary_data, deductions_data

    def _determine_regimes_to_calculate(self, regime: TaxRegime, assessment_year: str) -> List[tuple]:
        """Determine which regimes to calculate based on request and year support."""
        regimes = []
        
        regime_support = self.check_regime_support(assessment_year)
        
        if regime == TaxRegime.OLD and regime_support['old']:
            regimes.append(("old", TaxRegimeType.OLD))
        elif regime == TaxRegime.NEW and regime_support['new']:
            regimes.append(("new", TaxRegimeType.NEW))
        elif regime == TaxRegime.BOTH:
            if regime_support['old']:
                regimes.append(("old", TaxRegimeType.OLD))
            if regime_support['new']:
                regimes.append(("new", TaxRegimeType.NEW))
        
        return regimes

    def _convert_age_category(self, age_category: AgeCategoryEnum) -> AgeCategory:
        """Convert API age category to internal enum."""
        mapping = {
            AgeCategoryEnum.BELOW_60: AgeCategory.BELOW_60,
            AgeCategoryEnum.SENIOR_60_TO_80: AgeCategory.SENIOR_60_TO_80,
            AgeCategoryEnum.SUPER_SENIOR_ABOVE_80: AgeCategory.SUPER_SENIOR_ABOVE_80
        }
        return mapping[age_category]

    def _determine_recommendation(self, results: Dict[str, Any]) -> str:
        """Determine which regime is recommended based on calculation results."""
        if len(results) == 1:
            regime_name = list(results.keys())[0]
            return f"Only {regime_name} regime is available for this assessment year"
        
        if len(results) == 2:
            old_tax = results.get('old', {}).get('tax_liability', float('inf'))
            new_tax = results.get('new', {}).get('tax_liability', float('inf'))
            
            if old_tax < new_tax:
                savings = new_tax - old_tax
                return f"OLD regime recommended - saves ₹{savings:,.0f} annually"
            elif new_tax < old_tax:
                savings = old_tax - new_tax
                return f"NEW regime recommended - saves ₹{savings:,.0f} annually"
            else:
                return "Both regimes result in similar tax liability"
        
        return "Unable to determine recommendation"