#!/usr/bin/env python3

"""
Amount Parsing Mixin
=====================

Shared amount parsing utilities extracted from simple_extractor.py.
Contains the exact parsing logic for monetary values.
"""

import pandas as pd
from decimal import Decimal
from typing import Any, Optional
import re


class AmountParsingMixin:
    """Mixin providing amount parsing utilities from simple_extractor.py"""
    
    def _parse_amount(self, value: Any) -> Optional[Decimal]:
        """
        Parse amount value from cell (EXACT copy from simple_extractor.py)
        
        Handles various formats:
        - ₹50,000
        - Rs. 25000/-
        - 75000.00
        - Mixed text with numbers
        
        Args:
            value: Raw cell value from table
            
        Returns:
            Parsed amount as Decimal or None if invalid
        """
        
        if pd.isna(value):
            return None
        
        text = str(value).strip()
        
        # Skip if empty or non-numeric-looking
        if not text or len(text.replace(' ', '')) == 0:
            return None
        
        # Clean text
        clean_text = (text.replace(',', '').replace('₹', '')
                          .replace('Rs.', '').replace('/-', '').strip())
        
        # Skip if still contains letters (except lakh/crore)
        if any(c.isalpha() for c in clean_text.lower() if c not in 'lakhcroe'):
            return None
        
        try:
            amount = Decimal(clean_text)
            # Only return if it's a reasonable amount (> 0)
            return amount if amount > 0 else None
        except (ValueError, TypeError, Exception):
            # Try to extract just the numeric part
            numeric_match = re.search(r'(\d+(?:\.\d{2})?)', clean_text)
            if numeric_match:
                try:
                    amount = Decimal(numeric_match.group(1))
                    return amount if amount > 0 else None
                except (ValueError, TypeError):
                    pass
        
        return None
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """
        Convert value to Decimal safely (from simple_extractor.py)
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value or None if conversion fails
        """
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _format_amount(self, amount: Optional[Decimal]) -> str:
        """
        Format amount for display
        
        Args:
            amount: Decimal amount
            
        Returns:
            Formatted amount string
        """
        if amount is None or amount == 0:
            return "₹0"
        return f"₹{amount:,.2f}".rstrip('0').rstrip('.')
    
    def _parse_amount_with_multiplier(self, value: Any) -> Optional[Decimal]:
        """
        Parse amount with lakh/crore multipliers
        
        Handles formats like:
        - "5.2 Lakhs"
        - "1.5 Crore"
        - "25 Lakh"
        
        Args:
            value: Raw cell value
            
        Returns:
            Parsed amount as Decimal
        """
        if pd.isna(value):
            return None
        
        text = str(value).strip().lower()
        
        # Extract numeric part
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', text)
        if not numeric_match:
            return None
        
        base_amount = Decimal(numeric_match.group(1))
        
        # Apply multiplier
        if 'crore' in text:
            return base_amount * Decimal('10000000')  # 1 crore = 10 million
        elif 'lakh' in text:
            return base_amount * Decimal('100000')    # 1 lakh = 100k
        else:
            return base_amount
    
    def _is_reasonable_amount(self, amount: Decimal, min_value: Decimal = Decimal('0'), 
                             max_value: Decimal = Decimal('100000000')) -> bool:
        """
        Check if amount is within reasonable range
        
        Args:
            amount: Amount to validate
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value
            
        Returns:
            True if amount is reasonable
        """
        if amount is None:
            return False
        return min_value <= amount <= max_value
    
    def _extract_amounts_from_text(self, text: str) -> list[Decimal]:
        """
        Extract all numeric amounts from text
        
        Args:
            text: Text containing amounts
            
        Returns:
            List of extracted amounts
        """
        amounts = []
        
        # Pattern for amounts with currency symbols
        amount_patterns = [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d{2})?)',  # ₹50,000.00
            r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d{2})?)',  # Rs. 50,000.00
            r'(\d+(?:,\d+)*(?:\.\d{2})?)\s*/-',  # 50,000/-
            r'(\d+(?:,\d+)*(?:\.\d{2})?)',  # Plain numbers
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean_match = match.replace(',', '')
                try:
                    amount = Decimal(clean_match)
                    if amount > 0:
                        amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        return amounts