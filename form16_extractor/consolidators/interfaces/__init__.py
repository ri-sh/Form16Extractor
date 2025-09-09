"""
Interfaces for consolidation components.
"""

from .consolidator_interface import IForm16Consolidator, ConsolidationConfig
from .validator_interface import IConsolidationValidator

__all__ = [
    'IForm16Consolidator',
    'ConsolidationConfig', 
    'IConsolidationValidator'
]