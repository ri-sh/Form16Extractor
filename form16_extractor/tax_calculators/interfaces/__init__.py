"""
Interfaces for tax calculation components.
"""

from .calculator_interface import ITaxCalculator, TaxCalculationInput, TaxCalculationResult
from .regime_interface import ITaxRegime
from .rule_provider_interface import ITaxRuleProvider

__all__ = [
    'ITaxCalculator',
    'TaxCalculationInput', 
    'TaxCalculationResult',
    'ITaxRegime',
    'ITaxRuleProvider'
]