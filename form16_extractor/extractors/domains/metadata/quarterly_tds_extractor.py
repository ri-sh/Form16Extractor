#!/usr/bin/env python3

"""
Quarterly TDS Extractor Component
==================================

Component for extracting quarterly TDS data from Form16 tables.
Contains EXACT logic from simple_extractor._extract_quarterly_tds_data().

This component fixes the TDS amount assignment issues.
"""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

from form16_extractor.extractors.base.abstract_field_extractor import AbstractFieldExtractor
from form16_extractor.models.form16_models import TaxDeductionQuarterly
from form16_extractor.pdf.table_classifier import TableType


class QuarterlyTdsExtractorComponent(AbstractFieldExtractor):
    """
    Component for extracting quarterly TDS data.
    
    EXACT implementation from simple_extractor._extract_quarterly_tds_data()
    to fix TDS amount assignment issues in modular extractor.
    """
    
    def __init__(self):
        super().__init__()
    
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Get TDS tables (EXACT from simple_extractor.py)
        
        Args:
            tables_by_type: Classified tables
            
        Returns:
            List of TDS table_info dicts
        """
        # ROOT CAUSE FIX: TDS data is primarily in HEADER_METADATA tables!
        return (tables_by_type.get(TableType.HEADER_METADATA, []) +
                tables_by_type.get(TableType.PART_B_SALARY_DETAILS, []) +
                tables_by_type.get(TableType.PART_A_SUMMARY, []) +
                tables_by_type.get(TableType.PART_B_EMPLOYER_EMPLOYEE, []) +
                tables_by_type.get(TableType.VERIFICATION_SECTION, []))
    
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> List[TaxDeductionQuarterly]:
        """
        Extract TDS using EXACT logic from simple_extractor._extract_quarterly_tds_data()
        
        Args:
            tables: List of TDS table_info dicts
            
        Returns:
            List of quarterly TDS records
        """
        
        quarterly_data = []
        
        for table_info in tables:
            table = table_info['table']
            
            # First, find the header row with "Quarter(s)" to understand table structure
            header_row_idx = None
            for i in range(len(table)):
                for j in range(len(table.columns)):
                    cell_value = str(table.iloc[i, j]).lower()
                    if 'quarter(s)' in cell_value or 'quarters' in cell_value:
                        header_row_idx = i
                        break
                if header_row_idx is not None:
                    break
            
            if header_row_idx is None:
                continue  # No quarterly data structure found in this table
            
            # Analyze header row to identify column positions - enhanced approach from older codebase
            header_columns = {}
            if header_row_idx is not None:
                for j in range(len(table.columns)):
                    header_text = str(table.iloc[header_row_idx, j]).lower()
                    
                    # Try to identify column purposes
                    if 'quarter' in header_text and 'quarter' not in header_columns:
                        header_columns['quarter'] = j
                    elif ('receipt' in header_text and 'number' in header_text) and 'receipt' not in header_columns:
                        header_columns['receipt'] = j
                    elif ('amount paid' in header_text or 'amount paid/credited' in header_text) and 'amount_paid' not in header_columns:
                        header_columns['amount_paid'] = j
                    elif ('tax deducted' in header_text or 'amount of tax deducted' in header_text) and 'tax_deducted' not in header_columns:
                        header_columns['tax_deducted'] = j
                    elif ('tax deposited' in header_text or 'tax deposited / remitted' in header_text or 'amount of tax deposited' in header_text) and 'tax_deposited' not in header_columns:
                        header_columns['tax_deposited'] = j
            
            # Extract quarterly data from subsequent rows - enhanced approach from older codebase
            for i in range(header_row_idx + 1, len(table)):
                # Get the whole row as text to search for quarter indicators
                row_text = ' '.join([str(table.iloc[i, j]) for j in range(len(table.columns))]).upper()
                
                # Check if this row contains quarter data (Q1, Q2, Q3, Q4)
                quarter_match = None
                for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                    if quarter in row_text:
                        quarter_match = quarter
                        break
                
                # Also check specific quarter cell if column is identified
                if not quarter_match and 'quarter' in header_columns:
                    quarter_cell = str(table.iloc[i, header_columns['quarter']]).upper()
                    for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                        if quarter in quarter_cell:
                            quarter_match = quarter
                            break
                
                if quarter_match:
                    tds_record = TaxDeductionQuarterly(quarter=quarter_match)
                    
                    # Enhanced receipt number extraction (working PDF fix)
                    if 'receipt' in header_columns:
                        receipt_value = str(table.iloc[i, header_columns['receipt']]).strip()
                        if receipt_value and self._is_valid_receipt_number(receipt_value):
                            tds_record.receipt_number = receipt_value.upper()
                    else:
                        # Scan row for receipt pattern if no column mapping
                        for j in range(len(table.columns)):
                            cell_value = str(table.iloc[i, j]).strip()
                            
                            # PDF receipt pattern: Uppercase alphanumeric like ABCD1234
                            if (cell_value and 'nan' not in cell_value.lower() and 
                                6 <= len(cell_value) <= 15 and 
                                cell_value.isalnum() and 
                                any(c.isalpha() for c in cell_value) and
                                cell_value.isupper() and cell_value != quarter_match):
                                tds_record.receipt_number = cell_value
                                break
                    
                    # Extract amounts from the row - CRITICAL LOGIC FROM simple_extractor.py
                    amounts_found = 0
                    
                    # Try column-based extraction first
                    if 'amount_paid' in header_columns:
                        amount_paid = self._parse_amount(table.iloc[i, header_columns['amount_paid']])
                        if amount_paid and amount_paid > 0:
                            tds_record.amount_paid = amount_paid
                            amounts_found += 1
                    
                    if 'tax_deducted' in header_columns:
                        tax_deducted = self._parse_amount(table.iloc[i, header_columns['tax_deducted']])
                        if tax_deducted and tax_deducted > 0:
                            tds_record.tax_deducted = tax_deducted
                            amounts_found += 1
                    
                    if 'tax_deposited' in header_columns:
                        tax_deposited = self._parse_amount(table.iloc[i, header_columns['tax_deposited']])
                        if tax_deposited and tax_deposited > 0:
                            tds_record.tax_deposited = tax_deposited
                            amounts_found += 1
                    
                    # If column mapping didn't work, scan the row for amounts (EXACT from simple_extractor)
                    if amounts_found == 0:
                        row_amounts = []
                        for j in range(len(table.columns)):
                            amount = self._parse_amount(table.iloc[i, j])
                            if amount and amount > 0:
                                row_amounts.append(amount)
                        
                        # CRITICAL: Assign amounts based on position and context (EXACT from simple_extractor)
                        if len(row_amounts) >= 1:
                            tds_record.tax_deducted = row_amounts[0]  # First amount is usually tax deducted
                        if len(row_amounts) >= 2:
                            tds_record.tax_deposited = row_amounts[1]  # Second amount is usually tax deposited
                            amounts_found += 1
                        if len(row_amounts) >= 3:
                            tds_record.amount_paid = row_amounts[-1]  # Last amount might be total amount paid
                    
                    # Only add if we have at least tax deducted amount
                    if tds_record.tax_deducted and tds_record.tax_deducted > 0:
                        quarterly_data.append(tds_record)
        
        return quarterly_data
    
    def create_model(self, data: List[TaxDeductionQuarterly]) -> List[TaxDeductionQuarterly]:
        """
        Return quarterly TDS records as-is
        
        Args:
            data: List of TaxDeductionQuarterly records
            
        Returns:
            Same list of records
        """
        return data if data else []
    
    def get_strategy_name(self) -> str:
        """Return strategy name for metadata"""
        return "enhanced_pattern_matching"
    
    def calculate_confidence(self, data: List[TaxDeductionQuarterly], tables: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence for TDS extraction
        
        Args:
            data: Extracted TDS records
            tables: Tables used
            
        Returns:
            Confidence score
        """
        if not data:
            return 0.2
        
        # Higher confidence for more quarters extracted
        confidence = min(0.95, 0.7 + len(data) * 0.05)
        
        # Bonus for records with receipt numbers
        records_with_receipts = sum(1 for record in data if record.receipt_number)
        if records_with_receipts > 0:
            confidence = min(1.0, confidence + 0.05)
        
        return confidence
    
    # ===============================
    # HELPER METHODS
    # ===============================
    
    def _is_valid_receipt_number(self, text: str) -> bool:
        """Check if text is a valid receipt number"""
        if not text or len(text) < 6:
            return False
        
        text = text.strip().upper()
        
        # Must be alphanumeric
        if not text.isalnum():
            return False
        
        # Should have both letters and numbers (or all letters for some formats)
        has_letters = any(c.isalpha() for c in text)
        
        # Avoid common words
        avoid_words = ['QUARTER', 'TOTAL', 'AMOUNT', 'RECEIPT', 'NUMBER']
        if text in avoid_words:
            return False
        
        return has_letters and len(text) <= 15