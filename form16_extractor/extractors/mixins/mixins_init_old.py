#!/usr/bin/env python3

"""
Mixins Module
=============

Shared behavior mixins for Form16 extraction components.
Contains utility methods extracted from simple_extractor.py.
"""

from .amount_parsing_mixin import AmountParsingMixin
from .validation_mixin import ValidationMixin
from .pattern_matching_mixin import PatternMatchingMixin
from .metadata_extraction_mixin import MetadataExtractionMixin

__all__ = [
    'AmountParsingMixin',
    'ValidationMixin', 
    'PatternMatchingMixin',
    'MetadataExtractionMixin'
]