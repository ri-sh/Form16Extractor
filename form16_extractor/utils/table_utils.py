#!/usr/bin/env python3
"""
Table Processing Utilities
==========================

Utilities for preprocessing and normalizing Form16 tables.
Handles merged cells, empty rows/columns, and header normalization.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


class TablePreprocessor:
    """Preprocess and normalize Form16 tables"""
    
    @staticmethod
    def clean_table(table: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize table data
        
        Args:
            table: Raw DataFrame from PDF extraction
            
        Returns:
            Cleaned DataFrame
        """
        if table.empty:
            return table
        
        logger.debug(f"Cleaning table with shape {table.shape}")
        
        # Make a copy to avoid modifying original
        cleaned_table = table.copy()
        
        # Step 1: Remove completely empty rows and columns
        cleaned_table = TablePreprocessor.remove_empty_rows_cols(cleaned_table)
        
        # Step 2: Normalize cell values
        cleaned_table = TablePreprocessor.normalize_cell_values(cleaned_table)
        
        # Step 3: Handle merged cell artifacts
        cleaned_table = TablePreprocessor.handle_merged_cells(cleaned_table)
        
        # Step 4: Normalize column headers
        cleaned_table = TablePreprocessor.normalize_headers(cleaned_table)
        
        logger.debug(f"Table cleaned, new shape: {cleaned_table.shape}")
        
        return cleaned_table
    
    @staticmethod
    def remove_empty_rows_cols(table: pd.DataFrame) -> pd.DataFrame:
        """Remove completely empty rows and columns"""
        if table.empty:
            return table
        
        # Remove rows where all cells are empty/NaN
        table = table.dropna(how='all')
        
        # Remove columns where all cells are empty/NaN
        table = table.dropna(how='all', axis=1)
        
        # Reset index after removing rows
        table = table.reset_index(drop=True)
        
        return table
    
    @staticmethod
    def normalize_cell_values(table: pd.DataFrame) -> pd.DataFrame:
        """Normalize cell values (whitespace, NaN handling)"""
        if table.empty:
            return table
        
        def normalize_cell(cell):
            if pd.isna(cell):
                return None
            
            cell_str = str(cell).strip()
            
            # Convert common empty indicators to None
            if cell_str.lower() in ['nan', 'none', '', '-', 'nil', 'na']:
                return None
            
            # Normalize whitespace
            cell_str = re.sub(r'\s+', ' ', cell_str)
            
            return cell_str if cell_str else None
        
        # Apply normalization to all cells
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                table.iloc[row_idx, col_idx] = normalize_cell(table.iloc[row_idx, col_idx])
        
        return table
    
    @staticmethod
    def handle_merged_cells(table: pd.DataFrame) -> pd.DataFrame:
        """Handle artifacts from merged cells in PDF tables"""
        if table.empty or len(table) < 2:
            return table
        
        # Strategy 1: Fill down for merged cells (common in headers)
        table = TablePreprocessor._fill_merged_headers(table)
        
        # Strategy 2: Combine split text across rows
        table = TablePreprocessor._combine_split_text(table)
        
        return table
    
    @staticmethod
    def _fill_merged_headers(table: pd.DataFrame) -> pd.DataFrame:
        """Fill down merged header cells"""
        # Look for patterns where first column has value but subsequent columns are empty
        for row_idx in range(len(table) - 1):
            for col_idx in range(len(table.columns)):
                current_cell = table.iloc[row_idx, col_idx]
                next_cell = table.iloc[row_idx + 1, col_idx]
                
                # If current cell has content and next is empty, it might be merged
                if (current_cell and pd.notna(current_cell) and 
                    (not next_cell or pd.isna(next_cell))):
                    
                    # Check if the row below has content in other columns (indicating merge)
                    row_below_has_content = any(
                        table.iloc[row_idx + 1, c] and pd.notna(table.iloc[row_idx + 1, c])
                        for c in range(len(table.columns)) if c != col_idx
                    )
                    
                    if row_below_has_content:
                        table.iloc[row_idx + 1, col_idx] = current_cell
        
        return table
    
    @staticmethod
    def _combine_split_text(table: pd.DataFrame) -> pd.DataFrame:
        """Combine text that was split across rows"""
        rows_to_remove = []
        
        for row_idx in range(len(table) - 1):
            current_row_cells = [table.iloc[row_idx, c] for c in range(len(table.columns))]
            next_row_cells = [table.iloc[row_idx + 1, c] for c in range(len(table.columns))]
            
            # Check if next row looks like continuation of current row
            if TablePreprocessor._is_continuation_row(current_row_cells, next_row_cells):
                # Combine the rows
                for col_idx in range(len(table.columns)):
                    current_val = table.iloc[row_idx, col_idx]
                    next_val = table.iloc[row_idx + 1, col_idx]
                    
                    if current_val and next_val:
                        # Combine with space
                        table.iloc[row_idx, col_idx] = f"{current_val} {next_val}"
                    elif next_val and not current_val:
                        # Move next value to current
                        table.iloc[row_idx, col_idx] = next_val
                
                # Mark next row for removal
                rows_to_remove.append(row_idx + 1)
        
        # Remove combined rows
        if rows_to_remove:
            table = table.drop(table.index[rows_to_remove])
            table = table.reset_index(drop=True)
        
        return table
    
    @staticmethod
    def _is_continuation_row(current_row: List[Any], next_row: List[Any]) -> bool:
        """Check if next row is continuation of current row"""
        # Simple heuristic: if next row has fewer non-empty cells and
        # they appear to be continuations of text
        
        current_non_empty = sum(1 for cell in current_row if cell and pd.notna(cell))
        next_non_empty = sum(1 for cell in next_row if cell and pd.notna(cell))
        
        # Next row should have fewer cells
        if next_non_empty >= current_non_empty:
            return False
        
        # Check if next row cells look like continuations
        for i, (current, next_val) in enumerate(zip(current_row, next_row)):
            if next_val and pd.notna(next_val):
                next_str = str(next_val).strip()
                
                # If it starts with lowercase or doesn't look like a new field
                if (next_str and next_str[0].islower() or
                    len(next_str) < 10):  # Short fragments are likely continuations
                    return True
        
        return False
    
    @staticmethod
    def normalize_headers(table: pd.DataFrame) -> pd.DataFrame:
        """Normalize column headers for consistent access"""
        if table.empty:
            return table
        
        # If table has meaningful column names, normalize them
        if hasattr(table, 'columns') and not all(isinstance(col, int) for col in table.columns):
            new_columns = []
            for col in table.columns:
                normalized = TablePreprocessor._normalize_header_text(str(col))
                new_columns.append(normalized)
            
            table.columns = new_columns
        else:
            # Look for header row in first few rows
            header_row_idx = TablePreprocessor._find_header_row(table)
            if header_row_idx is not None:
                # Use this row as headers and remove it
                headers = [TablePreprocessor._normalize_header_text(str(cell)) 
                          for cell in table.iloc[header_row_idx]]
                
                # Ensure unique column names
                headers = TablePreprocessor._make_headers_unique(headers)
                
                table.columns = headers
                table = table.drop(table.index[header_row_idx]).reset_index(drop=True)
        
        return table
    
    @staticmethod
    def _find_header_row(table: pd.DataFrame) -> Optional[int]:
        """Find the row that contains column headers"""
        # Look in first 3 rows for header patterns
        for row_idx in range(min(3, len(table))):
            row = table.iloc[row_idx]
            
            # Check if this row looks like headers
            if TablePreprocessor._looks_like_header_row(row):
                return row_idx
        
        return None
    
    @staticmethod
    def _looks_like_header_row(row: pd.Series) -> bool:
        """Check if a row looks like column headers"""
        non_empty_cells = [cell for cell in row if cell and pd.notna(cell)]
        
        if len(non_empty_cells) < 2:
            return False
        
        # Check for header-like patterns
        header_indicators = [
            'sl.', 'sr.', 's.no', 'description', 'amount', 'particulars',
            'section', 'details', 'income', 'deduction', 'name', 'address',
            'quarter', 'period', 'tax', 'salary'
        ]
        
        header_count = 0
        for cell in non_empty_cells:
            cell_str = str(cell).lower()
            if any(indicator in cell_str for indicator in header_indicators):
                header_count += 1
        
        # If more than half the cells look like headers
        return header_count >= len(non_empty_cells) / 2
    
    @staticmethod
    def _normalize_header_text(header: str) -> str:
        """Normalize header text for consistent matching"""
        if not header or pd.isna(header):
            return "col"
        
        header_str = str(header).strip().lower()
        
        # Remove common prefixes
        header_str = re.sub(r'^(sl\.?\s*no\.?|s\.?\s*no\.?|sr\.?\s*no\.?)', 'sl_no', header_str)
        
        # Remove parentheses and their contents
        header_str = re.sub(r'\([^)]*\)', '', header_str)
        
        # Replace punctuation and spaces with underscores
        header_str = re.sub(r'[^\w]', '_', header_str)
        
        # Remove multiple underscores
        header_str = re.sub(r'_+', '_', header_str)
        
        # Remove leading/trailing underscores
        header_str = header_str.strip('_')
        
        return header_str or "col"
    
    @staticmethod
    def _make_headers_unique(headers: List[str]) -> List[str]:
        """Ensure header names are unique"""
        seen = set()
        unique_headers = []
        
        for header in headers:
            if header in seen:
                counter = 1
                new_header = f"{header}_{counter}"
                while new_header in seen:
                    counter += 1
                    new_header = f"{header}_{counter}"
                header = new_header
            
            seen.add(header)
            unique_headers.append(header)
        
        return unique_headers


class TableAnalyzer:
    """Analyze table structure and content"""
    
    @staticmethod
    def get_table_stats(table: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive statistics about table structure"""
        if table.empty:
            return {
                'rows': 0,
                'cols': 0,
                'empty_cells': 0,
                'numeric_cols': 0,
                'text_cols': 0,
                'has_headers': False
            }
        
        stats = {
            'rows': len(table),
            'cols': len(table.columns),
            'empty_cells': 0,
            'numeric_cols': 0,
            'text_cols': 0,
            'has_headers': False
        }
        
        # Count empty cells
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell = table.iloc[row_idx, col_idx]
                if not cell or pd.isna(cell):
                    stats['empty_cells'] += 1
        
        # Analyze column types
        for col_idx in range(len(table.columns)):
            if TableAnalyzer._is_numeric_column(table, col_idx):
                stats['numeric_cols'] += 1
            else:
                stats['text_cols'] += 1
        
        # Check if has headers
        if len(table) > 0:
            first_row = table.iloc[0]
            stats['has_headers'] = TablePreprocessor._looks_like_header_row(first_row)
        
        return stats
    
    @staticmethod
    def _is_numeric_column(table: pd.DataFrame, col_idx: int) -> bool:
        """Check if column contains primarily numeric data"""
        numeric_count = 0
        total_count = 0
        
        for row_idx in range(len(table)):
            cell = table.iloc[row_idx, col_idx]
            if cell and pd.notna(cell):
                total_count += 1
                if TableAnalyzer._is_numeric_value(str(cell)):
                    numeric_count += 1
        
        if total_count == 0:
            return False
        
        return (numeric_count / total_count) > 0.6
    
    @staticmethod
    def _is_numeric_value(value: str) -> bool:
        """Check if string represents numeric value"""
        if not value:
            return False
        
        # Remove common formatting
        clean_value = re.sub(r'[,\s₹Rs\.INR]', '', value.strip())
        
        try:
            float(clean_value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def find_data_boundaries(table: pd.DataFrame) -> Tuple[int, int, int, int]:
        """
        Find the actual data boundaries in table (excluding empty borders)
        
        Returns:
            (start_row, end_row, start_col, end_col) inclusive boundaries
        """
        if table.empty:
            return (0, 0, 0, 0)
        
        # Find first and last rows with data
        start_row = 0
        end_row = len(table) - 1
        
        # Find first row with data
        for row_idx in range(len(table)):
            if any(cell and pd.notna(cell) for cell in table.iloc[row_idx]):
                start_row = row_idx
                break
        
        # Find last row with data
        for row_idx in range(len(table) - 1, -1, -1):
            if any(cell and pd.notna(cell) for cell in table.iloc[row_idx]):
                end_row = row_idx
                break
        
        # Find first and last columns with data
        start_col = 0
        end_col = len(table.columns) - 1
        
        for col_idx in range(len(table.columns)):
            if any(table.iloc[row_idx, col_idx] and pd.notna(table.iloc[row_idx, col_idx]) 
                   for row_idx in range(len(table))):
                start_col = col_idx
                break
        
        for col_idx in range(len(table.columns) - 1, -1, -1):
            if any(table.iloc[row_idx, col_idx] and pd.notna(table.iloc[row_idx, col_idx])
                   for row_idx in range(len(table))):
                end_col = col_idx
                break
        
        return (start_row, end_row, start_col, end_col)


def preprocess_tables(tables: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Preprocess a list of tables with consistent cleaning
    
    Args:
        tables: List of raw DataFrames from PDF extraction
        
    Returns:
        List of cleaned DataFrames
    """
    logger.info(f"Preprocessing {len(tables)} tables")
    
    processed_tables = []
    
    for i, table in enumerate(tables):
        logger.debug(f"Processing table {i}")
        
        try:
            # Clean the table
            cleaned_table = TablePreprocessor.clean_table(table)
            
            # Skip if table becomes empty after cleaning
            if not cleaned_table.empty:
                processed_tables.append(cleaned_table)
            else:
                logger.debug(f"Table {i} became empty after cleaning, skipping")
                
        except Exception as e:
            logger.warning(f"Error processing table {i}: {e}")
            # Include original table if cleaning fails
            if not table.empty:
                processed_tables.append(table)
    
    logger.info(f"Preprocessing complete: {len(processed_tables)} tables retained")
    
    return processed_tables