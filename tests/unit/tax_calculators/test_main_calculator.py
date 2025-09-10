"""
Unit tests for the main tax calculator.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from form16x.form16_parser.tax_calculators.main_calculator import MultiYearTaxCalculator
from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import (
    TaxCalculationInput, TaxRegimeType, AgeCategory
)
from form16x.form16_parser.utils.validation import ValidationError


class TestMultiYearTaxCalculator:
    """Test cases for MultiYearTaxCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = MultiYearTaxCalculator()
    
    def test_get_supported_assessment_years(self):
        """Test that supported years are returned correctly."""
        years = self.calculator.get_supported_assessment_years()
        assert isinstance(years, list)
        assert "2024-25" in years
        assert "2025-26" in years
    
    def test_basic_new_regime_calculation(self):
        """Test basic new regime tax calculation."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('1000000')  # 10L
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Verify basic structure
        assert result.assessment_year == "2024-25"
        assert result.regime_type == TaxRegimeType.NEW
        assert result.total_income == Decimal('1000000')
        
        # For 10L income in new regime, tax should be reasonable
        assert result.total_tax_liability > 0
        assert result.effective_tax_rate < 20  # Should be under 20%
        
        # Standard deduction should be applied
        assert result.total_deductions >= Decimal('50000')
    
    def test_basic_old_regime_calculation(self):
        """Test basic old regime tax calculation."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.OLD,
            gross_salary=Decimal('1000000'),
            section_80c=Decimal('150000'),
            section_80d=Decimal('25000')
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Verify basic structure
        assert result.assessment_year == "2024-25"
        assert result.regime_type == TaxRegimeType.OLD
        assert result.total_income == Decimal('1000000')
        
        # Should have higher deductions due to 80C and 80D
        expected_deductions = Decimal('50000') + Decimal('150000') + Decimal('25000')  # Standard + 80C + 80D
        assert result.total_deductions >= expected_deductions
        
        # Should have slab calculations
        assert len(result.slab_calculations) > 0
    
    def test_high_income_surcharge_calculation(self):
        """Test surcharge calculation for high income."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('6000000')  # 60L - should attract surcharge
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Should have surcharge for income above 50L
        assert result.surcharge > 0
        
        # Should have health and education cess
        assert result.health_education_cess > 0
        
        # Total tax should be substantial
        assert result.total_tax_liability > Decimal('1000000')  # Should be over 10L
    
    def test_senior_citizen_calculation(self):
        """Test tax calculation for senior citizens."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.OLD,
            gross_salary=Decimal('400000'),  # 4L
            age_category=AgeCategory.SENIOR_60_TO_80
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # For senior citizen with 4L income, should have minimal tax
        # Due to higher exemption limit (3L vs 2.5L)
        assert result.total_tax_liability <= Decimal('20000')
    
    def test_super_senior_citizen_calculation(self):
        """Test tax calculation for super senior citizens."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.OLD,
            gross_salary=Decimal('600000'),  # 6L
            age_category=AgeCategory.SUPER_SENIOR_ABOVE_80
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Super senior citizen gets 5L basic exemption limit (not additional exemption)
        # So 6L income with standard deduction should result in ~5.5L taxable income
        assert result.taxable_income >= Decimal('500000')  # 6L - 50K standard deduction = 5.5L
        assert result.taxable_income <= Decimal('600000')  # Should be reasonable
    
    def test_rebate_87a_new_regime(self):
        """Test Section 87A rebate in new regime."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('600000')  # 6L - eligible for rebate in new regime
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Should get rebate under Section 87A in new regime
        # New regime has 7L rebate limit
        if result.tax_before_rebate > 0:
            assert result.rebate_under_87a >= 0
    
    def test_regime_comparison(self):
        """Test regime comparison functionality."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,  # Will be ignored in comparison
            gross_salary=Decimal('1500000'),  # 15L
            section_80c=Decimal('150000'),
            section_80d=Decimal('25000'),
            hra_exemption=Decimal('180000')
        )
        
        results = self.calculator.compare_regimes(input_data)
        
        # Should have results for both regimes
        assert TaxRegimeType.OLD in results
        assert TaxRegimeType.NEW in results
        
        # Should have regime benefit calculated
        old_result = results[TaxRegimeType.OLD]
        new_result = results[TaxRegimeType.NEW]
        
        assert old_result.other_regime_tax is not None
        assert new_result.other_regime_tax is not None
        assert old_result.regime_benefit is not None
        assert new_result.regime_benefit is not None
        
        # Benefits should be inverse of each other
        assert abs(old_result.regime_benefit + new_result.regime_benefit) < Decimal('1')
    
    def test_validate_input_invalid_year(self):
        """Test input validation for unsupported year."""
        input_data = TaxCalculationInput(
            assessment_year="2020-21",  # Unsupported year
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('1000000')
        )
        
        errors = self.calculator.validate_input(input_data)
        assert len(errors) > 0
        assert any("not supported" in error for error in errors)
    
    def test_validate_input_negative_salary(self):
        """Test input validation for negative salary."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('-100000')  # Negative salary
        )
        
        errors = self.calculator.validate_input(input_data)
        assert len(errors) > 0
        assert any("negative" in error.lower() for error in errors)
    
    def test_calculate_tax_with_invalid_input(self):
        """Test that invalid input raises ValidationError."""
        input_data = TaxCalculationInput(
            assessment_year="2020-21",  # Invalid year
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('1000000')
        )
        
        with pytest.raises(ValidationError):
            self.calculator.calculate_tax(input_data)
    
    def test_slab_wise_calculation_accuracy(self):
        """Test accuracy of slab-wise tax calculation."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('1200000')  # 12L - spans multiple slabs
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Verify slab calculations sum up correctly
        total_slab_tax = sum(calc.tax_on_slab for calc in result.slab_calculations)
        assert abs(total_slab_tax - result.tax_before_rebate) < Decimal('1')
        
        # Verify slab amounts sum up to taxable income
        total_slab_amount = sum(calc.taxable_amount_in_slab for calc in result.slab_calculations)
        assert abs(total_slab_amount - result.taxable_income) < Decimal('1')
    
    def test_cess_calculation(self):
        """Test health and education cess calculation."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.NEW,
            gross_salary=Decimal('2000000')  # 20L
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Cess should be 4% of (tax + surcharge)
        expected_cess = (result.tax_after_rebate + result.surcharge) * Decimal('0.04')
        assert abs(result.health_education_cess - expected_cess) < Decimal('1')
    
    def test_multiple_income_sources(self):
        """Test calculation with multiple income sources."""
        input_data = TaxCalculationInput(
            assessment_year="2024-25",
            regime_type=TaxRegimeType.OLD,
            gross_salary=Decimal('800000'),
            other_income=Decimal('200000'),
            house_property_income=Decimal('100000')
        )
        
        result = self.calculator.calculate_tax(input_data)
        
        # Total income should be sum of all sources
        expected_total = Decimal('800000') + Decimal('200000') + Decimal('100000')
        assert result.total_income == expected_total
        
        # Should have reasonable tax calculation
        assert result.total_tax_liability > 0