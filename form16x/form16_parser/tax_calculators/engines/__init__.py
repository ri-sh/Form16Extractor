"""
Tax calculation engines for different regimes.
"""

from .old_regime import OldTaxRegime
from .new_regime import NewTaxRegime

__all__ = [
    'OldTaxRegime',
    'NewTaxRegime'
]