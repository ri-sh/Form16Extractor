"""
Main integrator for Form16 data and tax calculations.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..models.form16_models import Form16Document
from ..consolidators.multi_company_consolidator import MultiCompanyForm16Consolidator, ConsolidationResult
from ..tax_calculators.main_calculator import MultiYearTaxCalculator
from ..tax_calculators.interfaces.calculator_interface import TaxRegimeType, TaxCalculationResult, AgeCategory
from .data_mapper import Form16ToTaxMapper


@dataclass
class IntegratedTaxResult:
    """Result of integrated Form16 tax calculation."""
    
    # Source information
    source_type: str  # "single" or "consolidated"
    employee_pan: str
    assessment_year: str
    
    # Tax calculation results
    recommended_regime: TaxRegimeType
    old_regime_result: Optional[TaxCalculationResult]
    new_regime_result: Optional[TaxCalculationResult]
    
    # Consolidation data (if applicable)
    consolidation_result: Optional[ConsolidationResult]
    
    # Summary
    optimal_tax_amount: float
    tax_savings: float  # Savings by choosing optimal regime
    
    # Validation and warnings
    calculation_warnings: List[str]
    consolidation_warnings: List[str]


class Form16TaxIntegrator:
    """
    Main integrator that connects Form16 extraction with tax calculation.
    
    Provides high-level APIs for:
    1. Single Form16 tax calculation
    2. Multi-company Form16 consolidation and tax calculation
    3. Regime comparison and optimization
    """
    
    def __init__(self):
        """Initialize the integrator."""
        self.consolidator = MultiCompanyForm16Consolidator()
        self.calculator = MultiYearTaxCalculator()
        self.mapper = Form16ToTaxMapper()
    
    def calculate_tax_single_form16(
        self,
        form16_data: Form16Document,
        assessment_year: Optional[str] = None,
        age_category: AgeCategory = AgeCategory.BELOW_60,
        compare_regimes: bool = True
    ) -> IntegratedTaxResult:
        """
        Calculate tax for a single Form16.
        
        Args:
            form16_data: Form16 data object
            assessment_year: Assessment year (auto-detected if None)
            age_category: Employee age category
            compare_regimes: Whether to compare both tax regimes
            
        Returns:
            IntegratedTaxResult with calculation details
        """
        # Determine assessment year if not provided
        if assessment_year is None:
            assessment_year = self.mapper.determine_assessment_year(form16_data)
        
        # Get employee PAN
        employee_pan = form16_data.part_a.employee.pan
        
        # Suggest optimal regime
        suggested_regime = self.mapper.suggest_regime_type(form16_data, assessment_year)
        
        calculation_results = {}
        warnings = []
        
        if compare_regimes:
            # Calculate for both regimes
            for regime in [TaxRegimeType.OLD, TaxRegimeType.NEW]:
                try:
                    tax_input = self.mapper.map_single_form16(
                        form16_data, assessment_year, regime, age_category
                    )
                    calculation_results[regime] = self.calculator.calculate_tax(tax_input)
                except Exception as e:
                    warnings.append(f"Failed to calculate {regime.value} regime: {str(e)}")
        else:
            # Calculate only suggested regime
            try:
                tax_input = self.mapper.map_single_form16(
                    form16_data, assessment_year, suggested_regime, age_category
                )
                calculation_results[suggested_regime] = self.calculator.calculate_tax(tax_input)
            except Exception as e:
                warnings.append(f"Failed to calculate {suggested_regime.value} regime: {str(e)}")
        
        # Determine optimal regime and savings
        recommended_regime, optimal_tax, savings = self._determine_optimal_regime(calculation_results)
        
        return IntegratedTaxResult(
            source_type="single",
            employee_pan=employee_pan,
            assessment_year=assessment_year,
            recommended_regime=recommended_regime,
            old_regime_result=calculation_results.get(TaxRegimeType.OLD),
            new_regime_result=calculation_results.get(TaxRegimeType.NEW),
            consolidation_result=None,
            optimal_tax_amount=float(optimal_tax),
            tax_savings=float(savings),
            calculation_warnings=warnings,
            consolidation_warnings=[]
        )
    
    def calculate_tax_multi_company(
        self,
        form16_list: List[Form16Document],
        age_category: AgeCategory = AgeCategory.BELOW_60,
        compare_regimes: bool = True
    ) -> IntegratedTaxResult:
        """
        Calculate tax for multiple Form16s (multi-company scenario).
        
        Args:
            form16_list: List of Form16 data objects
            age_category: Employee age category
            compare_regimes: Whether to compare both tax regimes
            
        Returns:
            IntegratedTaxResult with consolidated calculation details
        """
        # First consolidate the Form16s
        consolidation_result = self.consolidator.consolidate_form16s(form16_list)
        
        calculation_results = {}
        warnings = []
        
        if compare_regimes:
            # Calculate for both regimes using consolidated data
            for regime in [TaxRegimeType.OLD, TaxRegimeType.NEW]:
                try:
                    tax_input = self.mapper.map_consolidated_form16(
                        consolidation_result, regime, age_category
                    )
                    calculation_results[regime] = self.calculator.calculate_tax(tax_input)
                except Exception as e:
                    warnings.append(f"Failed to calculate {regime.value} regime: {str(e)}")
        else:
            # Use new regime as default for consolidated calculations
            try:
                tax_input = self.mapper.map_consolidated_form16(
                    consolidation_result, TaxRegimeType.NEW, age_category
                )
                calculation_results[TaxRegimeType.NEW] = self.calculator.calculate_tax(tax_input)
            except Exception as e:
                warnings.append(f"Failed to calculate new regime: {str(e)}")
        
        # Determine optimal regime and savings
        recommended_regime, optimal_tax, savings = self._determine_optimal_regime(calculation_results)
        
        # Extract consolidation warnings
        consolidation_warnings = [w.message for w in consolidation_result.warnings]
        
        return IntegratedTaxResult(
            source_type="consolidated",
            employee_pan=consolidation_result.employee_pan,
            assessment_year=consolidation_result.assessment_year,
            recommended_regime=recommended_regime,
            old_regime_result=calculation_results.get(TaxRegimeType.OLD),
            new_regime_result=calculation_results.get(TaxRegimeType.NEW),
            consolidation_result=consolidation_result,
            optimal_tax_amount=float(optimal_tax),
            tax_savings=float(savings),
            calculation_warnings=warnings,
            consolidation_warnings=consolidation_warnings
        )
    
    def get_tax_optimization_suggestions(
        self,
        result: IntegratedTaxResult
    ) -> List[str]:
        """
        Generate tax optimization suggestions based on calculation results.
        
        Args:
            result: Integrated tax result
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Regime comparison suggestion
        if result.old_regime_result and result.new_regime_result:
            old_tax = result.old_regime_result.total_tax_liability
            new_tax = result.new_regime_result.total_tax_liability
            
            if old_tax < new_tax:
                savings = float(new_tax - old_tax)
                suggestions.append(
                    f"Consider opting for old tax regime to save ₹{savings:,.0f}"
                )
            elif new_tax < old_tax:
                savings = float(old_tax - new_tax)
                suggestions.append(
                    f"New tax regime is optimal, saving ₹{savings:,.0f} over old regime"
                )
        
        # Deduction optimization (old regime)
        if result.old_regime_result:
            old_result = result.old_regime_result
            
            # Section 80C optimization
            section_80c_used = 0  # Would need to extract from input
            section_80c_limit = 150000
            if section_80c_used < section_80c_limit:
                remaining = section_80c_limit - section_80c_used
                potential_savings = remaining * 0.3  # Assuming 30% tax bracket
                suggestions.append(
                    f"Invest ₹{remaining:,.0f} more in 80C to potentially save ₹{potential_savings:,.0f}"
                )
        
        # Multi-company specific suggestions
        if result.consolidation_result:
            if result.consolidation_result.warnings:
                suggestions.append(
                    "Review Form16s for potential duplicate deductions across employers"
                )
        
        return suggestions
    
    def _determine_optimal_regime(
        self, 
        calculation_results: Dict[TaxRegimeType, TaxCalculationResult]
    ) -> Tuple[TaxRegimeType, float, float]:
        """
        Determine optimal tax regime and calculate savings.
        
        Args:
            calculation_results: Dictionary of regime calculation results
            
        Returns:
            Tuple of (optimal_regime, optimal_tax_amount, savings)
        """
        if not calculation_results:
            return TaxRegimeType.NEW, 0.0, 0.0
        
        # If only one regime calculated, use that
        if len(calculation_results) == 1:
            regime = list(calculation_results.keys())[0]
            tax_amount = float(calculation_results[regime].total_tax_liability)
            return regime, tax_amount, 0.0
        
        # Compare both regimes
        old_tax = float(calculation_results[TaxRegimeType.OLD].total_tax_liability) if TaxRegimeType.OLD in calculation_results else float('inf')
        new_tax = float(calculation_results[TaxRegimeType.NEW].total_tax_liability) if TaxRegimeType.NEW in calculation_results else float('inf')
        
        if old_tax <= new_tax:
            return TaxRegimeType.OLD, old_tax, new_tax - old_tax
        else:
            return TaxRegimeType.NEW, new_tax, old_tax - new_tax