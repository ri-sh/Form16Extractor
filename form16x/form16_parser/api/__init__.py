"""
Form16 Extractor API Package

This package provides clean, programmatic APIs for tax calculations and Form16 processing
that can be used independently of the CLI interface.

Main Components:
- TaxCalculationAPI: Comprehensive API for tax calculations from Form16 or manual input
- TaxRegime, AgeCategoryEnum: Enums for API parameters

Example usage:
    ```python
    from form16x.form16_parser.api import TaxCalculationAPI, TaxRegime
    from decimal import Decimal
    
    # Initialize API
    api = TaxCalculationAPI()
    
    # Calculate from Form16
    result = api.calculate_tax_from_form16(
        form16_file="path/to/form16.pdf",
        regime=TaxRegime.BOTH
    )
    
    # Calculate from manual input
    result = api.calculate_tax_from_input(
        assessment_year="2024-25",
        gross_salary=Decimal("1200000"),
        section_80c=Decimal("150000")
    )
    ```
"""

from .tax_calculation_api import TaxCalculationAPI, TaxRegime, AgeCategoryEnum

__all__ = [
    'TaxCalculationAPI',
    'TaxRegime', 
    'AgeCategoryEnum'
]