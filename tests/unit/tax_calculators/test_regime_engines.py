"""
Unit tests for tax regime engines.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from form16x.form16_parser.tax_calculators.engines.old_regime import OldTaxRegime
from form16x.form16_parser.tax_calculators.engines.new_regime import NewTaxRegime
from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import AgeCategory


class TestOldTaxRegime:
    """Test cases for OldTaxRegime."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock config for old regime
        self.config = {
            "assessment_year": "2024-25",
            "regime_type": "old",
            "basic_settings": {
                "standard_deduction": 50000,
                "basic_exemption_limits": {
                    "below_60": 250000,
                    "senior_60_to_80": 300000,
                    "super_senior_above_80": 500000
                }
            },
            "tax_slabs": {
                "below_60": [
                    {"from": 0, "to": 250000, "rate": 0.0},
                    {"from": 250000, "to": 500000, "rate": 5.0},
                    {"from": 500000, "to": 1000000, "rate": 20.0},
                    {"from": 1000000, "to": None, "rate": 30.0}
                ]
            },
            "surcharge": {
                "threshold_1": 5000000,
                "rate_1": 10.0,
                "threshold_2": 10000000,
                "rate_2": 15.0,
                "threshold_3": 20000000,
                "rate_3": 25.0,
                "threshold_4": 50000000,
                "rate_4": 37.0
            },
            "rebate_87a": {
                "income_limit": 500000,
                "max_rebate": 12500
            },
            "cess": {
                "health_education_cess_rate": 4.0
            },
            "deduction_limits": {
                "section_80c": 150000,
                "section_80d": 25000,
                "section_80ccd_1b": 50000
            },
            "allowed_deductions": [
                "section_80c", "section_80d", "section_80ccd_1b"
            ],
            "allowed_exemptions": [
                "hra", "lta"
            ]
        }
        self.regime = OldTaxRegime(self.config)
    
    def test_get_tax_slabs(self):
        """Test tax slab retrieval."""
        slabs = self.regime.get_tax_slabs(AgeCategory.BELOW_60)
        
        assert len(slabs) == 4
        assert slabs[0].from_amount == Decimal('0')
        assert slabs[0].rate_percent == 0.0
        assert slabs[1].rate_percent == 5.0
        assert slabs[2].rate_percent == 20.0
        assert slabs[3].rate_percent == 30.0
        assert slabs[3].to_amount is None  # Highest slab
    
    def test_calculate_slab_wise_tax(self):
        """Test slab-wise tax calculation."""
        taxable_income = Decimal('800000')  # 8L
        calculations = self.regime.calculate_slab_wise_tax(
            taxable_income, AgeCategory.BELOW_60
        )
        
        # Should span 3 slabs: 0%, 5%, 20%
        assert len(calculations) == 3
        
        # First slab: 0 to 2.5L at 0%
        assert calculations[0].taxable_amount_in_slab == Decimal('250000')
        assert calculations[0].tax_on_slab == Decimal('0')
        
        # Second slab: 2.5L to 5L at 5%
        assert calculations[1].taxable_amount_in_slab == Decimal('250000')
        assert calculations[1].tax_on_slab == Decimal('12500')
        
        # Third slab: 5L to 8L at 20%
        assert calculations[2].taxable_amount_in_slab == Decimal('300000')
        assert calculations[2].tax_on_slab == Decimal('60000')
        
        # Total tax should be 0 + 12500 + 60000 = 72500
        total_tax = sum(calc.tax_on_slab for calc in calculations)
        assert total_tax == Decimal('72500')
    
    def test_calculate_surcharge_no_surcharge(self):
        """Test surcharge calculation for income below threshold."""
        tax_before_surcharge = Decimal('100000')
        total_income = Decimal('3000000')  # 30L - below 50L threshold
        
        surcharge = self.regime.calculate_surcharge(tax_before_surcharge, total_income)
        assert surcharge == Decimal('0')
    
    def test_calculate_surcharge_10_percent(self):
        """Test 10% surcharge calculation."""
        tax_before_surcharge = Decimal('500000')
        total_income = Decimal('6000000')  # 60L - 10% surcharge bracket
        
        surcharge = self.regime.calculate_surcharge(tax_before_surcharge, total_income)
        expected = tax_before_surcharge * Decimal('0.10')
        assert abs(surcharge - expected) < Decimal('1')
    
    def test_calculate_rebate_87a_eligible(self):
        """Test Section 87A rebate for eligible income."""
        tax_before_rebate = Decimal('10000')
        total_income = Decimal('400000')  # 4L - eligible for rebate
        
        rebate = self.regime.calculate_rebate_87a(tax_before_rebate, total_income)
        assert rebate == tax_before_rebate  # Full tax as rebate
    
    def test_calculate_rebate_87a_capped(self):
        """Test Section 87A rebate capping."""
        tax_before_rebate = Decimal('20000')  # More than max rebate
        total_income = Decimal('450000')  # 4.5L - eligible for rebate
        
        rebate = self.regime.calculate_rebate_87a(tax_before_rebate, total_income)
        assert rebate == Decimal('12500')  # Capped at max rebate
    
    def test_calculate_rebate_87a_ineligible(self):
        """Test Section 87A rebate for ineligible income."""
        tax_before_rebate = Decimal('50000')
        total_income = Decimal('600000')  # 6L - above rebate limit
        
        rebate = self.regime.calculate_rebate_87a(tax_before_rebate, total_income)
        assert rebate == Decimal('0')
    
    def test_validate_deductions_within_limits(self):
        """Test deduction validation within limits."""
        deductions = {
            "section_80c": Decimal('100000'),
            "section_80d": Decimal('20000')
        }
        
        errors = self.regime.validate_deductions(deductions)
        assert len(errors) == 0
    
    def test_validate_deductions_exceeds_limit(self):
        """Test deduction validation exceeding limits."""
        deductions = {
            "section_80c": Decimal('200000'),  # Exceeds 1.5L limit
            "section_80d": Decimal('30000')    # Exceeds 25K limit
        }
        
        errors = self.regime.validate_deductions(deductions)
        assert len(errors) >= 2  # Should have errors for both sections
        assert any("80c" in error.lower() for error in errors)
        assert any("80d" in error.lower() for error in errors)
    
    def test_calculate_hra_exemption(self):
        """Test HRA exemption calculation."""
        hra_received = Decimal('300000')
        basic_salary = Decimal('600000')
        rent_paid = Decimal('360000')
        
        # Metro city calculation
        exemption_metro = self.regime.calculate_hra_exemption(
            hra_received, basic_salary, rent_paid, is_metro_city=True
        )
        
        # Non-metro city calculation
        exemption_non_metro = self.regime.calculate_hra_exemption(
            hra_received, basic_salary, rent_paid, is_metro_city=False
        )
        
        # Metro should have higher exemption (50% vs 40%)
        assert exemption_metro >= exemption_non_metro
        
        # Should not exceed HRA received
        assert exemption_metro <= hra_received
        assert exemption_non_metro <= hra_received


class TestNewTaxRegime:
    """Test cases for NewTaxRegime."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock config for new regime
        self.config = {
            "assessment_year": "2024-25",
            "regime_type": "new",
            "basic_settings": {
                "standard_deduction": 50000,
                "basic_exemption_limits": {
                    "below_60": 300000,
                    "senior_60_to_80": 300000,
                    "super_senior_above_80": 500000
                }
            },
            "tax_slabs": {
                "below_60": [
                    {"from": 0, "to": 300000, "rate": 0.0},
                    {"from": 300000, "to": 700000, "rate": 5.0},
                    {"from": 700000, "to": 1000000, "rate": 10.0},
                    {"from": 1000000, "to": 1200000, "rate": 15.0},
                    {"from": 1200000, "to": 1500000, "rate": 20.0},
                    {"from": 1500000, "to": None, "rate": 30.0}
                ]
            },
            "surcharge": {
                "threshold_1": 5000000,
                "rate_1": 10.0,
                "threshold_2": 10000000,
                "rate_2": 15.0,
                "threshold_3": 20000000,
                "rate_3": 25.0
            },
            "rebate_87a": {
                "income_limit": 700000,
                "max_rebate": 25000
            },
            "cess": {
                "health_education_cess_rate": 4.0
            },
            "allowed_deductions": [
                "standard_deduction"
            ],
            "allowed_exemptions": [
                "gratuity", "leave_encashment"
            ],
            "restricted_deductions": [
                "section_80c", "section_80d", "hra"
            ]
        }
        self.regime = NewTaxRegime(self.config)
    
    def test_get_tax_slabs_new_regime(self):
        """Test new regime tax slabs."""
        slabs = self.regime.get_tax_slabs(AgeCategory.BELOW_60)
        
        assert len(slabs) == 6  # More slabs in new regime
        assert slabs[0].from_amount == Decimal('0')
        assert slabs[0].to_amount == Decimal('300000')  # Higher exemption
        assert slabs[1].rate_percent == 5.0
        assert slabs[2].rate_percent == 10.0
        assert slabs[3].rate_percent == 15.0
        assert slabs[4].rate_percent == 20.0
        assert slabs[5].rate_percent == 30.0
    
    def test_calculate_slab_wise_tax_new_regime(self):
        """Test slab-wise tax calculation for new regime."""
        taxable_income = Decimal('1100000')  # 11L
        calculations = self.regime.calculate_slab_wise_tax(
            taxable_income, AgeCategory.BELOW_60
        )
        
        # Should span 4 slabs: 0%, 5%, 10%, 15%
        assert len(calculations) == 4
        
        # Verify amounts and rates
        assert calculations[0].tax_on_slab == Decimal('0')  # 0-3L at 0%
        assert calculations[1].rate_percent == 5.0  # 3-7L at 5%
        assert calculations[2].rate_percent == 10.0  # 7-10L at 10%
        assert calculations[3].rate_percent == 15.0  # 10-11L at 15%
    
    def test_validate_deductions_restricted(self):
        """Test that restricted deductions are not allowed."""
        deductions = {
            "section_80c": Decimal('100000'),
            "hra": Decimal('50000')
        }
        
        errors = self.regime.validate_deductions(deductions)
        assert len(errors) >= 2  # Should have errors for restricted deductions
        assert any("80c" in error for error in errors)
        assert any("hra" in error for error in errors)
    
    def test_is_exemption_allowed(self):
        """Test exemption allowance check."""
        assert self.regime.is_exemption_allowed("gratuity") == True
        assert self.regime.is_exemption_allowed("leave_encashment") == True
        assert self.regime.is_exemption_allowed("hra") == False  # Not in allowed list
    
    def test_get_tax_benefit_vs_old_regime(self):
        """Test tax benefit calculation against old regime."""
        total_income = Decimal('1500000')
        old_regime_tax = Decimal('150000')
        new_regime_tax = Decimal('135000')
        
        benefit = self.regime.get_tax_benefit_vs_old_regime(
            total_income, old_regime_tax, new_regime_tax
        )
        
        assert benefit['absolute_benefit'] == Decimal('15000')
        assert benefit['recommended_regime'] == 'new'
        assert benefit['old_regime_tax'] == old_regime_tax
        assert benefit['new_regime_tax'] == new_regime_tax
    
    def test_rebate_87a_higher_limit_new_regime(self):
        """Test that new regime has higher rebate limit."""
        tax_before_rebate = Decimal('20000')
        total_income = Decimal('650000')  # 6.5L - eligible in new regime only
        
        rebate = self.regime.calculate_rebate_87a(tax_before_rebate, total_income)
        assert rebate == tax_before_rebate  # Should get full rebate in new regime