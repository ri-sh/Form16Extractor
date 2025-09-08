#!/usr/bin/env python3
"""
Amount Extractor - Specialized Component
=======================================

Implements contextual amount extraction for salary components.
Handles multiple currency formats and column-aware detection.

Key Features:
- Multi-format parsing: ₹5,00,000, Rs. 500000, 5L
- Context-aware column selection
- Indian currency format support  
- Validation and confidence scoring
- Cross-column amount correlation
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
from decimal import Decimal, InvalidOperation


class AmountExtractor:
    """
    Contextual amount extractor for Form16 salary tables
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Currency patterns for Indian formats
        self.currency_patterns = [
            # Standard formats with symbols
            re.compile(r'₹\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE),
            re.compile(r'Rs\.?\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE),
            re.compile(r'INR\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE),
            
            # Amount with trailing currency
            re.compile(r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:INR|Rs\.?|/-)', re.IGNORECASE),
            
            # Lakhs and crores
            re.compile(r'([0-9.]+)\s*lakhs?', re.IGNORECASE),
            re.compile(r'([0-9.]+)\s*L', re.IGNORECASE),
            re.compile(r'([0-9.]+)\s*crores?', re.IGNORECASE),
            re.compile(r'([0-9.]+)\s*Cr', re.IGNORECASE),
            
            # Plain numbers without commas (most common case)
            re.compile(r'\b([0-9]+(?:\.[0-9]{1,2})?)\b'),
            
            # Indian comma format (e.g., 1,23,456.78)
            re.compile(r'\b([0-9]{1,3}(?:,[0-9]{2})*,[0-9]{3}(?:\.[0-9]{2})?)\b'),
            
            # International comma format (e.g., 123,456.78)
            re.compile(r'\b([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{2})?)\b'),
        ]
        
        # Amount validation ranges for different salary components
        self.amount_ranges = {
            'basic_salary': (50000, 15000000),
            'hra_received': (20000, 8000000),
            'transport_allowance': (1200, 100000),
            'medical_allowance': (1000, 200000),
            'special_allowance': (5000, 5000000),
            'gross_salary': (100000, 25000000),
            'total_allowances': (50000, 15000000),
            'perquisites_value': (10000, 5000000),
        }
    
    def extract_amount(self, cell_value: str, component_hint: Optional[str] = None) -> Optional[float]:
        """
        Extract amount from a cell value with validation
        
        Args:
            cell_value: String value from table cell
            component_hint: Hint about expected salary component type
            
        Returns:
            Extracted amount as float, or None if not found/invalid
        """
        if not cell_value or pd.isna(cell_value):
            return None
        
        cell_str = str(cell_value).strip()
        if not cell_str or cell_str.lower() in ['nan', 'none', '', '-', '0']:
            return None
        
        # Try each pattern
        for pattern in self.currency_patterns:
            match = pattern.search(cell_str)
            if match:
                amount_str = match.group(1)
                amount = self._parse_amount_string(amount_str, pattern)
                
                if amount is not None and self._validate_amount(amount, component_hint):
                    return amount
        
        return None
    
    def extract_amounts_from_row(self, row: pd.Series, component_hint: Optional[str] = None) -> List[Tuple[int, float]]:
        """
        Extract all valid amounts from a table row
        
        Args:
            row: DataFrame row
            component_hint: Expected salary component type
            
        Returns:
            List of (column_index, amount) tuples
        """
        amounts = []
        
        for col_idx, cell_value in enumerate(row):
            amount = self.extract_amount(cell_value, component_hint)
            if amount:
                amounts.append((col_idx, amount))
        
        return amounts
    
    def extract_amounts_from_column(self, column: pd.Series, component_hint: Optional[str] = None) -> List[Tuple[int, float]]:
        """
        Extract all valid amounts from a table column
        
        Args:
            column: DataFrame column
            component_hint: Expected salary component type
            
        Returns:
            List of (row_index, amount) tuples
        """
        amounts = []
        
        for row_idx, cell_value in enumerate(column):
            amount = self.extract_amount(cell_value, component_hint)
            if amount:
                amounts.append((row_idx, amount))
        
        return amounts
    
    def find_best_amount(self, table: pd.DataFrame, row_label: str, 
                        component_hint: Optional[str] = None) -> Optional[float]:
        """
        Find the best amount for a given row label in the table
        
        Args:
            table: DataFrame containing salary data
            row_label: Row label to search for
            component_hint: Expected salary component type
            
        Returns:
            Best matching amount, or None
        """
        # Find rows matching the label
        matching_rows = []
        for idx, row in table.iterrows():
            for cell_value in row:
                if self._label_matches(str(cell_value), row_label):
                    matching_rows.append(idx)
                    break
        
        if not matching_rows:
            return None
        
        # Extract amounts from matching rows
        all_amounts = []
        for row_idx in matching_rows:
            row = table.iloc[row_idx]
            amounts = self.extract_amounts_from_row(row, component_hint)
            all_amounts.extend([amount for _, amount in amounts])
        
        if not all_amounts:
            return None
        
        # Return the highest valid amount (typically the most complete value)
        return max(all_amounts)
    
    def _parse_amount_string(self, amount_str: str, pattern: re.Pattern) -> Optional[float]:
        """Parse amount string to float value"""
        try:
            # Handle lakhs and crores
            if 'lakh' in pattern.pattern.lower() or ' L' in pattern.pattern:
                return float(amount_str.replace(',', '')) * 100000
            elif 'crore' in pattern.pattern.lower() or ' Cr' in pattern.pattern:
                return float(amount_str.replace(',', '')) * 10000000
            else:
                # Standard number parsing
                clean_amount = amount_str.replace(',', '')
                return float(clean_amount)
        except (ValueError, InvalidOperation):
            return None
    
    def _validate_amount(self, amount: float, component_hint: Optional[str] = None) -> bool:
        """Validate amount is reasonable for the component type"""
        if amount is None or amount < 0:
            return False
            
        # Allow zero for perquisites (common case)
        if amount == 0.0:
            return True
        
        # Basic sanity check - amounts should be reasonable
        if amount > 50000000:  # 5 crores max
            return False
        if amount < 10:  # 10 rupees min
            return False
        
        # Component-specific validation
        if component_hint and component_hint in self.amount_ranges:
            min_val, max_val = self.amount_ranges[component_hint]
            return min_val <= amount <= max_val
        
        return True
    
    def _label_matches(self, cell_value: str, target_label: str) -> bool:
        """Check if cell value matches the target label"""
        cell_clean = cell_value.lower().strip()
        target_clean = target_label.lower().strip()
        
        # Exact match
        if target_clean in cell_clean:
            return True
        
        # Fuzzy matching for common variations
        variations = {
            'basic salary': ['basic', 'basic pay', 'salary basic'],
            'hra': ['house rent allowance', 'hra received', 'house rent'],
            'transport allowance': ['transport', 'conveyance', 'travel allowance'],
            'medical allowance': ['medical', 'medical reimbursement'],
            'special allowance': ['special', 'spl allowance', 'other allowances'],
            'gross salary': ['gross', 'total salary', 'gross total'],
        }
        
        for key, synonyms in variations.items():
            if key == target_clean:
                return any(synonym in cell_clean for synonym in synonyms)
        
        return False