"""
Form16x - Professional Form16 Processing and Tax Calculation Library

A comprehensive Python library for extracting structured data from Indian Form16 
tax documents and performing accurate tax calculations.
"""

__version__ = "1.0.0"
__author__ = "Rishabh Roy"
__email__ = "rishabhroy.90@example.com"

# Import main components for easy access
from .form16_parser.api import TaxCalculationAPI, TaxRegime, AgeCategoryEnum
from .form16_parser.extractors.enhanced_form16_extractor import EnhancedForm16Extractor
from .form16_parser.models.form16_models import Form16Document

__all__ = [
    'TaxCalculationAPI',
    'TaxRegime', 
    'AgeCategoryEnum',
    'EnhancedForm16Extractor',
    'Form16Document'
]