"""
Display module for Form16 tax calculation results.

This module contains various display formatters and templates for
presenting tax calculation results in different formats.
"""

from .colored_templates import ColoredDisplayRenderer, ColoredDisplayTemplates
from .display_templates import (
    DisplayRenderer, SummaryDisplayRenderer, DetailedDisplayRenderer, 
    DefaultDisplayRenderer, DisplayTemplates
)

__all__ = [
    'ColoredDisplayRenderer', 'ColoredDisplayTemplates',
    'DisplayRenderer', 'SummaryDisplayRenderer', 'DetailedDisplayRenderer',
    'DefaultDisplayRenderer', 'DisplayTemplates'
]