"""
Unit tests for TaxCalculatorInterface and related enums.

Tests the interface definitions, enum values, and type safety
without breaking existing functionality.
"""

import unittest
from unittest.mock import Mock

from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import (
    ITaxCalculator, TaxRegimeType, AgeCategory
)


class TestTaxCalculatorInterface(unittest.TestCase):
    """Test cases for TaxCalculatorInterface and related enums."""
    
    def test_tax_regime_type_enum_values(self):
        """Test that TaxRegimeType enum has all required values."""
        # Verify all expected values exist
        self.assertEqual(TaxRegimeType.OLD.value, "old")
        self.assertEqual(TaxRegimeType.NEW.value, "new")
        self.assertEqual(TaxRegimeType.BOTH.value, "both")
        
        # Verify we can iterate over all values
        expected_values = {"old", "new", "both"}
        actual_values = {regime.value for regime in TaxRegimeType}
        self.assertEqual(actual_values, expected_values)
    
    def test_tax_regime_type_both_exists(self):
        """Test that the BOTH enum value exists (this was the bug we fixed)."""
        # This test ensures the bug fix for missing BOTH value is preserved
        both_regime = TaxRegimeType.BOTH
        self.assertEqual(both_regime.value, "both")
        
        # Test that BOTH can be used in comparisons
        self.assertTrue(both_regime == TaxRegimeType.BOTH)
        self.assertFalse(both_regime == TaxRegimeType.OLD)
        self.assertFalse(both_regime == TaxRegimeType.NEW)
    
    def test_age_category_enum_values(self):
        """Test that AgeCategory enum has all required values."""
        expected_values = {
            AgeCategory.BELOW_60.value,
            AgeCategory.SENIOR_60_TO_80.value,
            AgeCategory.SUPER_SENIOR_ABOVE_80.value
        }
        
        # Verify enum values are reasonable
        self.assertIn("below_60", expected_values)
        self.assertIn("senior", AgeCategory.SENIOR_60_TO_80.value)
        self.assertIn("super_senior", AgeCategory.SUPER_SENIOR_ABOVE_80.value)
    
    # Note: CityType enum not present in current interface, removing test
    
    def test_tax_calculator_interface_is_abstract(self):
        """Test that ITaxCalculator cannot be instantiated directly."""
        # This should raise TypeError because it's an abstract class
        with self.assertRaises(TypeError):
            ITaxCalculator()
    
    def test_tax_calculator_interface_abstract_methods(self):
        """Test that interface defines required abstract methods."""
        # Check that the required methods are defined
        abstract_methods = ITaxCalculator.__abstractmethods__
        expected_methods = {'calculate_tax', 'compare_regimes', 'get_supported_assessment_years', 'validate_input'}
        
        self.assertTrue(expected_methods.issubset(abstract_methods))
    
    def test_enum_string_representation(self):
        """Test string representation of enum values."""
        # Test that enum values can be converted to strings properly
        self.assertEqual(str(TaxRegimeType.OLD.value), "old")
        self.assertEqual(str(TaxRegimeType.NEW.value), "new")
        self.assertEqual(str(TaxRegimeType.BOTH.value), "both")
    
    def test_enum_comparison_with_strings(self):
        """Test that enum values can be compared with strings."""
        # This is important for backwards compatibility
        self.assertEqual(TaxRegimeType.OLD.value, "old")
        self.assertEqual(TaxRegimeType.NEW.value, "new")
        self.assertEqual(TaxRegimeType.BOTH.value, "both")
        
        # Test inequality
        self.assertNotEqual(TaxRegimeType.OLD.value, "new")
        self.assertNotEqual(TaxRegimeType.NEW.value, "both")
    
    def test_enum_membership_testing(self):
        """Test membership testing with enum values."""
        valid_regimes = [regime.value for regime in TaxRegimeType]
        
        self.assertIn("old", valid_regimes)
        self.assertIn("new", valid_regimes)
        self.assertIn("both", valid_regimes)
        self.assertNotIn("invalid", valid_regimes)
    
    def test_tax_regime_type_from_string(self):
        """Test creating enum instances from string values."""
        # Test that we can create enum instances from their string values
        old_regime = TaxRegimeType("old")
        new_regime = TaxRegimeType("new")
        both_regime = TaxRegimeType("both")
        
        self.assertEqual(old_regime, TaxRegimeType.OLD)
        self.assertEqual(new_regime, TaxRegimeType.NEW)
        self.assertEqual(both_regime, TaxRegimeType.BOTH)
    
    def test_invalid_enum_value_handling(self):
        """Test handling of invalid enum values."""
        with self.assertRaises(ValueError):
            TaxRegimeType("invalid_regime")
        
        with self.assertRaises(ValueError):
            AgeCategory("invalid_age")
        
        # CityType test removed as enum not present in current interface
    
    def test_enum_uniqueness(self):
        """Test that all enum values are unique."""
        # TaxRegimeType uniqueness
        regime_values = [regime.value for regime in TaxRegimeType]
        self.assertEqual(len(regime_values), len(set(regime_values)))
        
        # AgeCategory uniqueness
        age_values = [age.value for age in AgeCategory]
        self.assertEqual(len(age_values), len(set(age_values)))
        
        # CityType uniqueness test removed as enum not present
    
    def test_concrete_implementation_requirements(self):
        """Test that concrete implementations must implement all abstract methods."""
        # Create a mock concrete implementation
        class ConcreteTaxCalculator(ITaxCalculator):
            def calculate_tax(self, input_data):
                return Mock(total_tax_liability=1000)
            
            def compare_regimes(self, input_data):
                return {TaxRegimeType.OLD: Mock(), TaxRegimeType.NEW: Mock()}
            
            def get_supported_assessment_years(self):
                return ["2024-25"]
            
            def validate_input(self, input_data):
                return []
        
        # This should work without raising an error
        calculator = ConcreteTaxCalculator()
        years = calculator.get_supported_assessment_years()
        self.assertEqual(years, ["2024-25"])
    
    def test_incomplete_implementation_fails(self):
        """Test that incomplete implementations cannot be instantiated."""
        # Define an incomplete implementation
        class IncompleteTaxCalculator(ITaxCalculator):
            pass  # Missing all abstract methods
        
        # This should raise TypeError
        with self.assertRaises(TypeError):
            IncompleteTaxCalculator()


if __name__ == '__main__':
    unittest.main()