#!/usr/bin/env python3
"""
Tests for AmountParsingMixin
============================

Test coverage for amount parsing utilities used across extractors.
"""

import unittest
import pandas as pd
from decimal import Decimal

from form16_extractor.extractors.mixins.amount_parsing_mixin import AmountParsingMixin


class TestAmountParsingMixin(unittest.TestCase):
    """Test AmountParsingMixin functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mixin = AmountParsingMixin()
    
    def test_parse_amount_currency_symbols(self):
        """Test parsing amounts with currency symbols."""
        # Test with rupee symbol
        result = self.mixin._parse_amount("₹50,000")
        self.assertEqual(result, Decimal('50000'))
        
        # Test with Rs.
        result = self.mixin._parse_amount("Rs. 25000/-")
        self.assertEqual(result, Decimal('25000'))
        
        # Test plain number
        result = self.mixin._parse_amount("75000.00")
        self.assertEqual(result, Decimal('75000.00'))
    
    def test_parse_amount_invalid_values(self):
        """Test parsing with invalid values."""
        # Test None
        result = self.mixin._parse_amount(None)
        self.assertIsNone(result)
        
        # Test NaN
        result = self.mixin._parse_amount(pd.NA)
        self.assertIsNone(result)
        
        # Test empty string
        result = self.mixin._parse_amount("")
        self.assertIsNone(result)
        
        # Test text with letters
        result = self.mixin._parse_amount("salary amount")
        self.assertIsNone(result)
        
        # Test negative/zero
        result = self.mixin._parse_amount("0")
        self.assertIsNone(result)
    
    def test_parse_amount_with_text(self):
        """Test parsing amounts embedded in text."""
        # The _parse_amount method filters out text with letters, 
        # so these should return None
        result = self.mixin._parse_amount("Amount: 12345.50")
        self.assertIsNone(result)
        
        # However, currency symbols and numbers should work
        result = self.mixin._parse_amount("₹1,50,000")
        self.assertEqual(result, Decimal('150000'))
    
    def test_to_decimal_conversion(self):
        """Test safe decimal conversion."""
        # Valid conversions
        self.assertEqual(self.mixin._to_decimal("123.45"), Decimal('123.45'))
        self.assertEqual(self.mixin._to_decimal(123), Decimal('123'))
        self.assertEqual(self.mixin._to_decimal(Decimal('456.78')), Decimal('456.78'))
        
        # Invalid conversions
        self.assertIsNone(self.mixin._to_decimal(None))
        
        # The actual implementation doesn't catch conversion errors, 
        # so this will raise an exception
        with self.assertRaises(Exception):
            self.mixin._to_decimal("invalid")
    
    def test_format_amount_display(self):
        """Test amount formatting for display."""
        # Regular amount
        result = self.mixin._format_amount(Decimal('12345.67'))
        self.assertEqual(result, "₹12,345.67")
        
        # Zero amount
        result = self.mixin._format_amount(Decimal('0'))
        self.assertEqual(result, "₹0")
        
        # None amount
        result = self.mixin._format_amount(None)
        self.assertEqual(result, "₹0")
        
        # Whole number (should remove trailing zeros)
        result = self.mixin._format_amount(Decimal('1000.00'))
        self.assertEqual(result, "₹1,000")
    
    def test_parse_amount_with_multiplier(self):
        """Test parsing amounts with lakh/crore multipliers."""
        # Lakhs
        result = self.mixin._parse_amount_with_multiplier("5.2 Lakhs")
        self.assertEqual(result, Decimal('520000'))
        
        result = self.mixin._parse_amount_with_multiplier("25 Lakh")
        self.assertEqual(result, Decimal('2500000'))
        
        # Crores
        result = self.mixin._parse_amount_with_multiplier("1.5 Crore")
        self.assertEqual(result, Decimal('15000000'))
        
        # Without multiplier
        result = self.mixin._parse_amount_with_multiplier("50000")
        self.assertEqual(result, Decimal('50000'))
        
        # Invalid input
        result = self.mixin._parse_amount_with_multiplier("invalid")
        self.assertIsNone(result)
        
        result = self.mixin._parse_amount_with_multiplier(None)
        self.assertIsNone(result)
    
    def test_is_reasonable_amount(self):
        """Test amount validation."""
        # Valid amounts
        self.assertTrue(self.mixin._is_reasonable_amount(Decimal('50000')))
        self.assertTrue(self.mixin._is_reasonable_amount(Decimal('1000000')))
        
        # Invalid amounts
        self.assertFalse(self.mixin._is_reasonable_amount(None))
        self.assertFalse(self.mixin._is_reasonable_amount(Decimal('-1000')))
        self.assertFalse(self.mixin._is_reasonable_amount(Decimal('200000000')))  # Too high
        
        # Custom range
        self.assertTrue(self.mixin._is_reasonable_amount(
            Decimal('5000'), 
            min_value=Decimal('1000'), 
            max_value=Decimal('10000')
        ))
        
        self.assertFalse(self.mixin._is_reasonable_amount(
            Decimal('15000'), 
            min_value=Decimal('1000'), 
            max_value=Decimal('10000')
        ))
    
    def test_extract_amounts_from_text(self):
        """Test extracting multiple amounts from text."""
        text = "Salary ₹50,000 and bonus Rs. 10,000/- total 60000"
        amounts = self.mixin._extract_amounts_from_text(text)
        
        # Should extract all numeric amounts
        self.assertIn(Decimal('50000'), amounts)
        self.assertIn(Decimal('10000'), amounts)  
        self.assertIn(Decimal('60000'), amounts)
        
        # Test with no amounts
        amounts = self.mixin._extract_amounts_from_text("No amounts here")
        self.assertEqual(amounts, [])
        
        # Test with decimal amounts
        text = "Amount is ₹12,345.50 and fee 100.25"
        amounts = self.mixin._extract_amounts_from_text(text)
        self.assertIn(Decimal('12345.50'), amounts)
        self.assertIn(Decimal('100.25'), amounts)


if __name__ == '__main__':
    unittest.main()