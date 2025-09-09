"""
Integration components for connecting Form16 data to tax calculations.
"""

from .form16_tax_integrator import Form16TaxIntegrator
from .data_mapper import Form16ToTaxMapper

__all__ = [
    'Form16TaxIntegrator',
    'Form16ToTaxMapper'
]