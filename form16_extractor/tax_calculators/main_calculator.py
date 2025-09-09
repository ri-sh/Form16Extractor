"""
Main tax calculator implementation.
"""

from typing import Dict, List, Optional
from decimal import Decimal
import time
from datetime import datetime

from .interfaces.calculator_interface import (
    ITaxCalculator, TaxCalculationInput, TaxCalculationResult, 
    TaxRegimeType, TaxSlabCalculation
)
from .interfaces.rule_provider_interface import ITaxRuleProvider
from .rules.json_rule_provider import JsonTaxRuleProvider
from ..utils.validation import ValidationError


class TaxCalculationError(Exception):
    """Exception raised during tax calculation."""
    pass


class MultiYearTaxCalculator(ITaxCalculator):
    """
    Main tax calculator with multi-year support.
    
    Calculates income tax based on Indian tax laws for different
    assessment years and regimes using configurable rule providers.
    """
    
    def __init__(self, rule_provider: Optional[ITaxRuleProvider] = None):
        """
        Initialize tax calculator.
        
        Args:
            rule_provider: Tax rule provider. If None, uses default JSON provider.
        """
        self.rule_provider = rule_provider or JsonTaxRuleProvider()
    
    def calculate_tax(self, input_data: TaxCalculationInput) -> TaxCalculationResult:
        """Calculate income tax for the given input."""
        # Validate input
        validation_errors = self.validate_input(input_data)
        if validation_errors:
            raise ValidationError(f"Invalid input: {'; '.join(validation_errors)}")
        
        try:
            # Get tax regime for calculation
            regime = self.rule_provider.get_tax_regime(
                input_data.assessment_year, 
                input_data.regime_type
            )
            
            # Calculate step by step
            total_income = self._calculate_total_income(input_data)
            total_deductions = self._calculate_total_deductions(input_data, regime)
            total_exemptions = self._calculate_total_exemptions(input_data)
            
            taxable_income = max(Decimal('0'), total_income - total_deductions - total_exemptions)
            
            # Calculate tax slab-wise
            slab_calculations = regime.calculate_slab_wise_tax(taxable_income, input_data.age_category)
            tax_before_rebate = sum(calc.tax_on_slab for calc in slab_calculations)
            
            # Apply rebate under Section 87A
            rebate_87a = regime.calculate_rebate_87a(tax_before_rebate, total_income)
            tax_after_rebate = max(Decimal('0'), tax_before_rebate - rebate_87a)
            
            # Calculate surcharge
            surcharge = regime.calculate_surcharge(tax_after_rebate, total_income)
            
            # Calculate health and education cess
            cess = self._calculate_cess(tax_after_rebate + surcharge)
            
            total_tax_liability = tax_after_rebate + surcharge + cess
            
            # Build result
            result = TaxCalculationResult(
                assessment_year=input_data.assessment_year,
                regime_type=input_data.regime_type,
                total_income=total_income,
                taxable_income=taxable_income,
                total_deductions=total_deductions,
                total_exemptions=total_exemptions,
                tax_before_rebate=tax_before_rebate,
                rebate_under_87a=rebate_87a,
                tax_after_rebate=tax_after_rebate,
                surcharge=surcharge,
                health_education_cess=cess,
                total_tax_liability=total_tax_liability,
                tds_deducted=input_data.tds_deducted,
                advance_tax_paid=input_data.advance_tax_paid,
                self_assessment_tax=input_data.self_assessment_tax,
                slab_calculations=slab_calculations
            )
            
            # Calculate marginal tax rate (disabled to avoid recursion)
            result.marginal_tax_rate = 0.0  # TODO: Fix marginal tax rate calculation
            
            return result
            
        except Exception as e:
            raise TaxCalculationError(f"Tax calculation failed: {str(e)}") from e
    
    def compare_regimes(
        self, 
        input_data: TaxCalculationInput
    ) -> Dict[TaxRegimeType, TaxCalculationResult]:
        """Calculate tax under both regimes for comparison."""
        results = {}
        
        for regime_type in [TaxRegimeType.OLD, TaxRegimeType.NEW]:
            if self.rule_provider.is_regime_supported(input_data.assessment_year, regime_type):
                regime_input = TaxCalculationInput(
                    assessment_year=input_data.assessment_year,
                    regime_type=regime_type,
                    age_category=input_data.age_category,
                    gross_salary=input_data.gross_salary,
                    other_income=input_data.other_income,
                    house_property_income=input_data.house_property_income,
                    standard_deduction=input_data.standard_deduction,
                    section_80c=input_data.section_80c if regime_type == TaxRegimeType.OLD else Decimal('0'),
                    section_80d=input_data.section_80d if regime_type == TaxRegimeType.OLD else Decimal('0'),
                    section_80ccd_1b=input_data.section_80ccd_1b if regime_type == TaxRegimeType.OLD else Decimal('0'),
                    other_deductions=input_data.other_deductions if regime_type == TaxRegimeType.OLD else {},
                    hra_exemption=input_data.hra_exemption if regime_type == TaxRegimeType.OLD else Decimal('0'),
                    lta_exemption=input_data.lta_exemption if regime_type == TaxRegimeType.OLD else Decimal('0'),
                    other_exemptions=input_data.other_exemptions if regime_type == TaxRegimeType.OLD else {},
                    house_property_loss=input_data.house_property_loss
                )
                
                try:
                    results[regime_type] = self.calculate_tax(regime_input)
                except Exception as e:
                    # Continue with other regime if one fails
                    print(f"Warning: {regime_type.value} regime calculation failed: {e}")
        
        # Add comparison data
        if TaxRegimeType.OLD in results and TaxRegimeType.NEW in results:
            old_tax = results[TaxRegimeType.OLD].total_tax_liability
            new_tax = results[TaxRegimeType.NEW].total_tax_liability
            
            results[TaxRegimeType.NEW].other_regime_tax = old_tax
            results[TaxRegimeType.NEW].regime_benefit = old_tax - new_tax
            
            results[TaxRegimeType.OLD].other_regime_tax = new_tax
            results[TaxRegimeType.OLD].regime_benefit = new_tax - old_tax
        
        return results
    
    def get_supported_assessment_years(self) -> List[str]:
        """Get list of supported assessment years."""
        return self.rule_provider.get_supported_years()
    
    def validate_input(self, input_data: TaxCalculationInput) -> List[str]:
        """Validate tax calculation input data."""
        errors = []
        
        # Check assessment year support
        if input_data.assessment_year not in self.get_supported_assessment_years():
            errors.append(f"Assessment year {input_data.assessment_year} not supported")
        
        # Check regime support
        if not self.rule_provider.is_regime_supported(
            input_data.assessment_year, 
            input_data.regime_type
        ):
            errors.append(
                f"Regime {input_data.regime_type.value} not supported for year {input_data.assessment_year}"
            )
        
        # Validate amounts
        if input_data.gross_salary < 0:
            errors.append("Gross salary cannot be negative")
        
        if input_data.other_income < 0:
            errors.append("Other income cannot be negative")
        
        # Validate deductions
        for deduction_type, amount in input_data.other_deductions.items():
            if amount < 0:
                errors.append(f"Deduction {deduction_type} cannot be negative")
        
        return errors
    
    def _calculate_total_income(self, input_data: TaxCalculationInput) -> Decimal:
        """Calculate total income from all sources."""
        return (
            input_data.gross_salary + 
            input_data.other_income + 
            input_data.house_property_income
        )
    
    def _calculate_total_deductions(self, input_data: TaxCalculationInput, regime) -> Decimal:
        """Calculate total deductions allowed under the regime."""
        total_deductions = Decimal('0')
        
        # Standard deduction (allowed in both regimes)
        if input_data.standard_deduction > 0:
            total_deductions += input_data.standard_deduction
        else:
            # Calculate standard deduction if not provided
            if hasattr(regime, 'calculate_standard_deduction'):
                total_deductions += regime.calculate_standard_deduction(input_data.gross_salary)
        
        # Regime-specific deductions
        if input_data.regime_type == TaxRegimeType.OLD:
            total_deductions += input_data.section_80c
            total_deductions += input_data.section_80d
            total_deductions += input_data.section_80ccd_1b
            
            # Add other deductions
            for amount in input_data.other_deductions.values():
                total_deductions += amount
        
        return total_deductions
    
    def _calculate_total_exemptions(self, input_data: TaxCalculationInput) -> Decimal:
        """Calculate total exemptions under Section 10."""
        total_exemptions = Decimal('0')
        
        if input_data.regime_type == TaxRegimeType.OLD:
            total_exemptions += input_data.hra_exemption
            total_exemptions += input_data.lta_exemption
            
            # Add other exemptions
            for amount in input_data.other_exemptions.values():
                total_exemptions += amount
        
        return total_exemptions
    
    def _calculate_cess(self, tax_plus_surcharge: Decimal) -> Decimal:
        """Calculate health and education cess."""
        cess_rate = Decimal('0.04')  # 4%
        return self._round_currency(tax_plus_surcharge * cess_rate)
    
    def _calculate_marginal_tax_rate(
        self, 
        input_data: TaxCalculationInput, 
        regime, 
        total_income: Decimal
    ) -> float:
        """Calculate marginal tax rate."""
        # Calculate tax for income + 1000
        test_input = TaxCalculationInput(
            assessment_year=input_data.assessment_year,
            regime_type=input_data.regime_type,
            age_category=input_data.age_category,
            gross_salary=input_data.gross_salary + Decimal('1000'),
            other_income=input_data.other_income,
            house_property_income=input_data.house_property_income,
            standard_deduction=input_data.standard_deduction,
            section_80c=input_data.section_80c,
            section_80d=input_data.section_80d,
            section_80ccd_1b=input_data.section_80ccd_1b,
            other_deductions=input_data.other_deductions,
            hra_exemption=input_data.hra_exemption,
            lta_exemption=input_data.lta_exemption,
            other_exemptions=input_data.other_exemptions,
            house_property_loss=input_data.house_property_loss
        )
        
        try:
            higher_tax_result = self.calculate_tax(test_input)
            original_result = self.calculate_tax(input_data)
            
            marginal_tax = higher_tax_result.total_tax_liability - original_result.total_tax_liability
            return float((marginal_tax / Decimal('1000')) * 100)
            
        except:
            return 0.0
    
    def _round_currency(self, amount: Decimal) -> Decimal:
        """Round amount to nearest rupee."""
        return amount.quantize(Decimal('1'))