#!/usr/bin/env python3
"""
Tests for Validation Utilities
===============================

Test coverage for validation utility functions.
"""

import unittest
from decimal import Decimal

from form16x.form16_parser.utils.validation import ValidationError


class TestValidationError(unittest.TestCase):
    """Test ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating validation error."""
        error = ValidationError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from Exception."""
        error = ValidationError("Test")
        self.assertIsInstance(error, Exception)
        self.assertTrue(issubclass(ValidationError, Exception))
    
    def test_validation_error_with_details(self):
        """Test ValidationError with detailed message."""
        details = "Field 'pan' is required but missing"
        error = ValidationError(details)
        self.assertEqual(str(error), details)
    
    def test_validation_error_empty_message(self):
        """Test ValidationError with empty message."""
        error = ValidationError("")
        self.assertEqual(str(error), "")
    
    def test_validation_error_none_message(self):
        """Test ValidationError with None message."""
        error = ValidationError(None)
        self.assertEqual(str(error), "None")


class TestValidationUtilities(unittest.TestCase):
    """Test validation utility functions if they exist."""
    
    def test_validation_module_imports(self):
        """Test that validation module imports correctly."""
        from form16x.form16_parser.utils import validation
        self.assertTrue(hasattr(validation, 'ValidationError'))
    
    def test_validation_error_usage_pattern(self):
        """Test typical usage pattern of ValidationError."""
        def validate_amount(amount):
            if amount is None:
                raise ValidationError("Amount cannot be None")
            if amount < 0:
                raise ValidationError("Amount cannot be negative")
            return True
        
        # Valid case
        self.assertTrue(validate_amount(Decimal('1000')))
        
        # Invalid cases
        with self.assertRaises(ValidationError) as cm:
            validate_amount(None)
        self.assertEqual(str(cm.exception), "Amount cannot be None")
        
        with self.assertRaises(ValidationError) as cm:
            validate_amount(-500)
        self.assertEqual(str(cm.exception), "Amount cannot be negative")


if __name__ == '__main__':
    unittest.main()