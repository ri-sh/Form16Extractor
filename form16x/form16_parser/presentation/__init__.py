"""
Presentation Layer - Display formatting and UI components.

This layer handles all display logic, formatting, and user interface concerns.
Business logic should never be mixed with presentation logic.
"""

from .formatters.tax_optimization_formatter import TaxOptimizationFormatter

__all__ = [
    'TaxOptimizationFormatter'
]