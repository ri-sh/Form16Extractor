"""
Data mapper for converting Form16 data to tax calculation inputs.
"""

from typing import Dict, Optional
from decimal import Decimal

from ..models.form16_models import Form16Document
from ..tax_calculators.interfaces.calculator_interface import (
    TaxCalculationInput, TaxRegimeType, AgeCategory
)
from ..consolidators.multi_company_consolidator import ConsolidationResult


class Form16ToTaxMapper:
    """
    Maps Form16 data to tax calculation input format.
    
    Handles both single Form16 and consolidated multi-company data.
    """
    
    def __init__(self):
        """Initialize the data mapper."""
        pass
    
    def map_single_form16(
        self,
        form16_data: Form16Document,
        assessment_year: str,
        regime_type: TaxRegimeType = TaxRegimeType.NEW,
        age_category: AgeCategory = AgeCategory.BELOW_60
    ) -> TaxCalculationInput:
        """
        Map single Form16 data to tax calculation input.
        
        Args:
            form16_data: Form16 data object
            assessment_year: Assessment year for calculation
            regime_type: Tax regime to use
            age_category: Age category of taxpayer
            
        Returns:
            TaxCalculationInput object ready for calculation
        """
        part_b = form16_data.part_b
        
        # Extract basic income
        gross_salary = Decimal(str(part_b.gross_salary.total or 0))
        other_income_total = Decimal(str(part_b.other_income.total or 0))
        house_property_income = Decimal(str(part_b.other_income.income_from_house_property or 0))
        
        # Extract deductions (only for old regime)
        deductions = part_b.chapter_vi_a_deductions
        section_80c = Decimal(str(deductions.section_80C.deductible_amount or 0)) if regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80d = Decimal(str(deductions.section_80D.deductible_amount or 0)) if regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80ccd_1b = Decimal(str(deductions.section_80CCD_1B.deductible_amount or 0)) if regime_type == TaxRegimeType.OLD else Decimal('0')
        
        # Extract other deductions
        other_deductions = {}
        if regime_type == TaxRegimeType.OLD:
            if deductions.section_80CCD_1 and deductions.section_80CCD_1.deductible_amount:
                other_deductions['section_80ccd_1'] = Decimal(str(deductions.section_80CCD_1.deductible_amount))
            
            if deductions.section_80E and deductions.section_80E.deductible_amount:
                other_deductions['section_80e'] = Decimal(str(deductions.section_80E.deductible_amount))
            
            if deductions.section_80G and deductions.section_80G.deductible_amount:
                other_deductions['section_80g'] = Decimal(str(deductions.section_80G.deductible_amount))
            
            # Add more deduction sections as needed
            for attr_name in dir(deductions):
                if attr_name.startswith('section_') and not attr_name.endswith('_'):
                    section_obj = getattr(deductions, attr_name)
                    if hasattr(section_obj, 'deductible_amount') and section_obj.deductible_amount:
                        section_key = attr_name.lower()
                        if section_key not in ['section_80c', 'section_80d', 'section_80ccd_1b']:
                            other_deductions[section_key] = Decimal(str(section_obj.deductible_amount))
        
        # Extract exemptions (only for old regime)
        exemptions = part_b.allowances_exempt_under_section_10
        hra_exemption = Decimal(str(exemptions.house_rent_allowance or 0)) if regime_type == TaxRegimeType.OLD else Decimal('0')
        lta_exemption = Decimal(str(exemptions.leave_travel_allowance or 0)) if regime_type == TaxRegimeType.OLD else Decimal('0')
        
        other_exemptions = {}
        if regime_type == TaxRegimeType.OLD:
            if exemptions.gratuity:
                other_exemptions['gratuity'] = Decimal(str(exemptions.gratuity))
            if exemptions.commuted_pension:
                other_exemptions['commuted_pension'] = Decimal(str(exemptions.commuted_pension))
            if exemptions.cash_equivalent_of_leave:
                other_exemptions['leave_encashment'] = Decimal(str(exemptions.cash_equivalent_of_leave))
        
        # Extract TDS information
        tds_deducted = Decimal('0')
        if (hasattr(form16_data.part_a, 'quarterly_tds_summary') and
            hasattr(form16_data.part_a.quarterly_tds_summary, 'total_tds') and
            form16_data.part_a.quarterly_tds_summary.total_tds.deducted is not None):
            tds_deducted = Decimal(str(form16_data.part_a.quarterly_tds_summary.total_tds.deducted))

        return TaxCalculationInput(
            assessment_year=assessment_year,
            regime_type=regime_type,
            age_category=age_category,
            gross_salary=gross_salary,
            other_income=other_income_total - house_property_income,
            house_property_income=house_property_income,
            section_80c=section_80c,
            section_80d=section_80d,
            section_80ccd_1b=section_80ccd_1b,
            other_deductions=other_deductions,
            hra_exemption=hra_exemption,
            lta_exemption=lta_exemption,
            other_exemptions=other_exemptions,
            tds_deducted=tds_deducted
        )
    
    def map_consolidated_form16(
        self,
        consolidation_result: ConsolidationResult,
        regime_type: TaxRegimeType = TaxRegimeType.NEW,
        age_category: AgeCategory = AgeCategory.BELOW_60
    ) -> TaxCalculationInput:
        """
        Map consolidated Form16 data to tax calculation input.
        
        Args:
            consolidation_result: Result from multi-company consolidation
            regime_type: Tax regime to use
            age_category: Age category of taxpayer
            
        Returns:
            TaxCalculationInput object ready for calculation
        """
        # Use consolidated salary data
        gross_salary = consolidation_result.salary_data.total_gross_salary
        
        # Use consolidated deductions (with duplicate detection applied)
        deductions_data = consolidation_result.deductions_data
        section_80c = deductions_data.section_80c_total if regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80d = deductions_data.section_80d_total if regime_type == TaxRegimeType.OLD else Decimal('0')
        section_80ccd_1b = deductions_data.section_80ccd_1b_total if regime_type == TaxRegimeType.OLD else Decimal('0')
        
        # Map other consolidated deductions
        other_deductions = {}
        if regime_type == TaxRegimeType.OLD:
            for section, amount in deductions_data.other_deductions.items():
                other_deductions[section] = amount
        
        # Extract consolidated TDS
        total_tds = consolidation_result.tds_data.total_tds_deducted

        return TaxCalculationInput(
            assessment_year=consolidation_result.assessment_year,
            regime_type=regime_type,
            age_category=age_category,
            gross_salary=gross_salary,
            other_income=Decimal('0'),  # Consolidated data doesn't separate other income
            house_property_income=Decimal('0'),
            section_80c=section_80c,
            section_80d=section_80d,
            section_80ccd_1b=section_80ccd_1b,
            other_deductions=other_deductions,
            hra_exemption=Decimal('0'),  # Would need to be calculated separately
            lta_exemption=Decimal('0'),  # Would need to be calculated separately
            other_exemptions={},
            tds_deducted=total_tds
        )
    
    def determine_assessment_year(self, form16_data: Form16Document) -> str:
        """
        Determine assessment year from Form16 data.
        
        Args:
            form16_data: Form16 data object
            
        Returns:
            Assessment year string (e.g., '2024-25')
        """
        # Try to extract from form16 metadata if available
        if hasattr(form16_data, 'metadata') and hasattr(form16_data.metadata, 'assessment_year'):
            return form16_data.metadata.assessment_year
        
        # Fallback: assume current assessment year
        # In production, this would be more sophisticated
        return "2024-25"
    
    def suggest_regime_type(
        self, 
        form16_data: Form16Document,
        assessment_year: str
    ) -> TaxRegimeType:
        """
        Suggest optimal regime type based on Form16 data.
        
        Args:
            form16_data: Form16 data object
            assessment_year: Assessment year for calculation
            
        Returns:
            Suggested tax regime type
        """
        # Quick heuristic: if significant deductions exist, old regime might be better
        deductions = form16_data.part_b.chapter_vi_a_deductions
        total_deductions = Decimal('0')
        
        if deductions.section_80C and deductions.section_80C.deductible_amount:
            total_deductions += Decimal(str(deductions.section_80C.deductible_amount))
        
        if deductions.section_80D and deductions.section_80D.deductible_amount:
            total_deductions += Decimal(str(deductions.section_80D.deductible_amount))
        
        if deductions.section_80CCD_1B and deductions.section_80CCD_1B.deductible_amount:
            total_deductions += Decimal(str(deductions.section_80CCD_1B.deductible_amount))
        
        # If substantial deductions (>1L), suggest old regime for comparison
        if total_deductions > Decimal('100000'):
            return TaxRegimeType.OLD
        
        # Default to new regime (as per current tax policy)
        return TaxRegimeType.NEW
    
    def extract_employee_age_category(self, form16_data: Form16Document) -> AgeCategory:
        """
        Extract employee age category from Form16 data.
        
        Args:
            form16_data: Form16 data object
            
        Returns:
            Age category for tax calculation
        """
        # Form16 doesn't typically contain age information
        # In production, this would need to be provided separately
        # or derived from PAN/other sources
        
        # Default to below 60 for now
        return AgeCategory.BELOW_60
    
    def extract_other_income_from_form16(self, form16_data, verbose: bool = False) -> Dict[str, Decimal]:
        """
        Extract other income data from Form16 document.
        
        Attempts to extract bank interest, dividends, and other income sources
        from the Form16 data structure. Falls back to zero values if data is not available.
        
        Args:
            form16_data: Extracted Form16 data object
            verbose: Whether to log extraction details
            
        Returns:
            Dictionary with extracted other income values:
            - bank_interest: Bank interest income
            - other_income: Other income (excluding bank interest and house property)
            - house_property: House property income
        """
        extracted_income = {
            'bank_interest': Decimal('0'),
            'other_income': Decimal('0'),
            'house_property': Decimal('0')
        }
        
        try:
            # Try to extract from structured data if available
            if hasattr(form16_data, 'other_income'):
                other_income_data = form16_data.other_income
                
                # House property income
                if hasattr(other_income_data, 'income_from_house_property') and other_income_data.income_from_house_property:
                    extracted_income['house_property'] = Decimal(str(other_income_data.income_from_house_property))
                    if verbose:
                        print(f"DEBUG: Found house property income: {extracted_income['house_property']}")
                
                # Other sources (could include bank interest, dividends)
                if hasattr(other_income_data, 'income_from_other_sources') and other_income_data.income_from_other_sources:
                    total_other_sources = Decimal(str(other_income_data.income_from_other_sources))
                    
                    # For now, assume all "other sources" is bank interest
                    # In future, this could be enhanced to parse specific components
                    extracted_income['bank_interest'] = total_other_sources
                    extracted_income['other_income'] = Decimal('0')  # Remainder after bank interest
                    
                    if verbose:
                        print(f"DEBUG: Found income from other sources: {total_other_sources}")
                        print(f"DEBUG: Treating as bank interest income")
                
                # Total other income check
                if hasattr(other_income_data, 'total') and other_income_data.total:
                    total_other_income = Decimal(str(other_income_data.total))
                    
                    # If we have a total but haven't found specific breakdowns,
                    # allocate proportionally
                    if total_other_income > 0 and extracted_income['bank_interest'] == 0 and extracted_income['house_property'] == 0:
                        # Assume it's primarily bank interest for now
                        extracted_income['bank_interest'] = total_other_income
                        
                        if verbose:
                            print(f"DEBUG: Found total other income: {total_other_income}")
                            print(f"DEBUG: Allocated as bank interest (no specific breakdown available)")
            
            # Try alternative data structure paths
            elif hasattr(form16_data, 'income') and hasattr(form16_data.income, 'other_income'):
                alt_other_income = form16_data.income.other_income
                if alt_other_income:
                    extracted_income['other_income'] = Decimal(str(alt_other_income))
                    if verbose:
                        print(f"DEBUG: Found other income via alternative path: {extracted_income['other_income']}")
            
            if verbose and all(v == 0 for v in extracted_income.values()):
                print("DEBUG: No other income data found in Form16 document")
                
        except Exception as e:
            if verbose:
                print(f"DEBUG: Error extracting other income from Form16: {e}")
        
        return extracted_income