#!/usr/bin/env python3
"""
Table Structure Analyzer - Specialized Component
==============================================

Analyzes Form16 table structures to identify salary component layouts.
Handles various table formats and structures commonly found in Form16 documents.

Key Features:
- Row-based vs column-based layout detection
- Header pattern recognition  
- Multi-column amount detection
- Table type classification
- Structure-aware extraction strategies
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from .amount_extractor import AmountExtractor


class TableStructureAnalyzer:
    """
    Analyzes table structures for optimal salary extraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.amount_extractor = AmountExtractor()
        
        # Common salary component labels
        self.salary_labels = {
            'basic_salary': [
                'basic salary', 'basic pay', 'salary basic', 'basic',
                'basic sal', 'salary (basic)'
            ],
            'hra_received': [
                'hra', 'house rent allowance', 'hra received', 'house rent',
                'h.r.a', 'rent allowance'
            ],
            'transport_allowance': [
                'transport allowance', 'conveyance allowance', 'transport',
                'conveyance', 'travel allowance', 'ta'
            ],
            'medical_allowance': [
                'medical allowance', 'medical', 'medical reimbursement',
                'medical reimb', 'health allowance'
            ],
            'special_allowance': [
                'special allowance', 'special', 'spl allowance', 'other allowances',
                'misc allowance', 'special pay'
            ],
            'total_allowances': [
                'total allowances', 'allowances total', 'total allowance',
                'allowances', 'total other allowances'
            ],
            'gross_salary': [
                'gross salary', 'gross total', 'total salary', 'gross',
                'salary total', 'gross sal'
            ],
            'perquisites_value': [
                'perquisites', 'perquisite', 'perqs', 'benefits',
                'perquisites value', 'perq value'
            ]
        }
    
    def analyze_table_structure(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze table structure and determine best extraction strategy
        
        Args:
            table: DataFrame to analyze
            
        Returns:
            Dictionary with structure analysis results
        """
        analysis = {
            'table_shape': table.shape,
            'layout_type': self._detect_layout_type(table),
            'amount_columns': self._identify_amount_columns(table),
            'label_column': self._identify_label_column(table),
            'header_rows': self._identify_header_rows(table),
            'data_rows': self._identify_data_rows(table),
            'extraction_strategy': 'row_based'  # Default
        }
        
        # Determine best extraction strategy based on structure
        if analysis['layout_type'] == 'column_based':
            analysis['extraction_strategy'] = 'column_based'
        elif len(analysis['amount_columns']) > 2:
            analysis['extraction_strategy'] = 'multi_column'
        else:
            analysis['extraction_strategy'] = 'row_based'
        
        self.logger.debug(f"Table structure: {analysis['table_shape']}, "
                         f"strategy: {analysis['extraction_strategy']}")
        
        return analysis
    
    def extract_salary_components_by_structure(self, table: pd.DataFrame) -> Dict[str, float]:
        """
        Extract salary components using structure-aware analysis
        
        Args:
            table: DataFrame containing salary data
            
        Returns:
            Dictionary of extracted salary components
        """
        # TASK A1.1: First try semantic Section 17(1) extraction
        semantic_results = self._extract_section_17_1_semantic(table)
        if semantic_results.get('gross_salary', 0) > 0:
            self.logger.debug(f"Semantic Section 17(1) extraction successful: ₹{semantic_results['gross_salary']:,.2f}")
            return semantic_results
        
        # Fallback to original structure-based extraction
        structure = self.analyze_table_structure(table)
        strategy = structure['extraction_strategy']
        
        if strategy == 'column_based':
            return self._extract_column_based(table, structure)
        elif strategy == 'multi_column':
            return self._extract_multi_column(table, structure)
        else:
            return self._extract_row_based(table, structure)
    
    def _detect_layout_type(self, table: pd.DataFrame) -> str:
        """Detect if table is row-based or column-based layout"""
        rows, cols = table.shape
        
        # Column-based: more columns than rows, or wide format
        if cols > rows and cols > 4:
            return 'column_based'
        
        # Row-based: more rows than columns, or tall format
        if rows > cols:
            return 'row_based'
        
        # Square-ish tables - analyze content
        label_in_first_col = self._count_labels_in_column(table.iloc[:, 0])
        label_in_first_row = self._count_labels_in_row(table.iloc[0, :])
        
        if label_in_first_col > label_in_first_row:
            return 'row_based'
        else:
            return 'column_based'
    
    def _identify_amount_columns(self, table: pd.DataFrame) -> List[int]:
        """Identify columns that primarily contain amounts"""
        amount_columns = []
        
        for col_idx in range(table.shape[1]):
            column = table.iloc[:, col_idx]
            amount_count = 0
            total_cells = 0
            
            for cell_value in column:
                if pd.notna(cell_value) and str(cell_value).strip():
                    total_cells += 1
                    if self.amount_extractor.extract_amount(str(cell_value)):
                        amount_count += 1
            
            # Column is amount column if >50% of non-empty cells are amounts
            if total_cells > 0 and (amount_count / total_cells) > 0.5:
                amount_columns.append(col_idx)
        
        return amount_columns
    
    def _identify_label_column(self, table: pd.DataFrame) -> Optional[int]:
        """Identify the column that contains salary component labels"""
        best_col = None
        best_score = 0
        
        for col_idx in range(table.shape[1]):
            column = table.iloc[:, col_idx]
            score = self._count_labels_in_column(column)
            
            if score > best_score:
                best_score = score
                best_col = col_idx
        
        return best_col if best_score > 0 else None
    
    def _identify_header_rows(self, table: pd.DataFrame) -> List[int]:
        """Identify rows that contain headers"""
        header_rows = []
        
        for row_idx in range(min(3, table.shape[0])):  # Check first 3 rows
            row = table.iloc[row_idx, :]
            if self._is_header_row(row):
                header_rows.append(row_idx)
        
        return header_rows
    
    def _identify_data_rows(self, table: pd.DataFrame) -> List[int]:
        """Identify rows that contain actual data"""
        data_rows = []
        header_rows = self._identify_header_rows(table)
        
        for row_idx in range(table.shape[0]):
            if row_idx not in header_rows:
                row = table.iloc[row_idx, :]
                if self._has_meaningful_data(row):
                    data_rows.append(row_idx)
        
        return data_rows
    
    def _extract_row_based(self, table: pd.DataFrame, structure: Dict) -> Dict[str, float]:
        """Extract using row-based strategy"""
        results = {}
        
        for component, labels in self.salary_labels.items():
            for label in labels:
                amount = self.amount_extractor.find_best_amount(table, label, component)
                if amount:
                    results[component] = amount
                    break
        
        return results
    
    def _extract_column_based(self, table: pd.DataFrame, structure: Dict) -> Dict[str, float]:
        """Extract using column-based strategy"""
        results = {}
        
        # In column-based tables, first row often contains labels
        if table.shape[0] > 0:
            labels_row = table.iloc[0, :]
            
            # Match labels to components
            for col_idx, label_cell in enumerate(labels_row):
                if pd.isna(label_cell):
                    continue
                    
                label_str = str(label_cell).lower().strip()
                
                # Find matching component
                for component, labels in self.salary_labels.items():
                    if any(label in label_str for label in labels):
                        # Extract amount from this column
                        column = table.iloc[1:, col_idx]  # Skip header row
                        amounts = self.amount_extractor.extract_amounts_from_column(column, component)
                        if amounts:
                            results[component] = amounts[0][1]  # Take first valid amount
                        break
        
        return results
    
    def _extract_multi_column(self, table: pd.DataFrame, structure: Dict) -> Dict[str, float]:
        """Extract using multi-column strategy"""
        results = {}
        amount_columns = structure['amount_columns']
        
        for component, labels in self.salary_labels.items():
            best_amount = None
            
            for label in labels:
                # Search for this label in the table
                for row_idx in range(table.shape[0]):
                    row = table.iloc[row_idx, :]
                    
                    # Check if any cell in this row contains the label
                    label_found = False
                    for cell_value in row:
                        if self.amount_extractor._label_matches(str(cell_value), label):
                            label_found = True
                            break
                    
                    if label_found:
                        # Look for amounts in amount columns for this row
                        for col_idx in amount_columns:
                            if col_idx < table.shape[1]:
                                cell_value = table.iloc[row_idx, col_idx]
                                amount = self.amount_extractor.extract_amount(str(cell_value), component)
                                if amount and (not best_amount or amount > best_amount):
                                    best_amount = amount
            
            if best_amount:
                results[component] = best_amount
        
        return results
    
    def _extract_section_17_1_semantic(self, table: pd.DataFrame) -> Dict[str, float]:
        """
        TASK A1.1: Semantic extraction for Section 17(1) salary components
        
        This method specifically looks for Section 17(1) patterns and extracts
        the adjacent column values, addressing the universal field mapping issues.
        
        Args:
            table: DataFrame containing salary data
            
        Returns:
            Dictionary with semantic extraction results
        """
        results = {}
        
        # Section 17(1) patterns - comprehensive list for all Form16 types
        section_17_1_patterns = [
            'salary as per provisions contained in section 17(1)',
            'provisions contained in section 17(1)',
            'salary as per provisions of section 17(1)',
            'section 17(1)',
            '17(1)',
            'salary under section 17(1)',
            'gross salary under section 17(1)',
            'salary section 17(1)',
            '17(1) salary',
            'section 17(1) salary',
            'salary (section 17(1))',
            '17(1) - salary',
            'under section 17(1)'
        ]
        
        # Section 17(2) patterns - to avoid confusion
        section_17_2_patterns = [
            'value of perquisites under section 17(2)',
            'perquisites under section 17(2)',
            'section 17(2)',
            '17(2)',
            'section 17(2) perquisites',
            '17(2) perquisites',
            'perquisites section 17(2)',
            'perquisites (section 17(2))'
        ]
        
        try:
            # Search for Section 17(1) rows
            section_17_1_amount = self._find_section_amount(table, section_17_1_patterns, "Section 17(1)")
            if section_17_1_amount:
                results['gross_salary'] = section_17_1_amount
                # For Form16, Section 17(1) is typically the gross salary
                results['basic_salary'] = section_17_1_amount  # Use as basic salary too
                self.logger.info(f"Found Section 17(1) salary: ₹{section_17_1_amount:,.2f}")
            
            # Search for Section 17(2) rows (perquisites)
            section_17_2_amount = self._find_section_amount(table, section_17_2_patterns, "Section 17(2)")
            if section_17_2_amount:
                results['perquisites_value'] = section_17_2_amount
                self.logger.info(f"Found Section 17(2) perquisites: ₹{section_17_2_amount:,.2f}")
            else:
                # If no Section 17(2) found, perquisites are likely 0
                results['perquisites_value'] = 0.0
                self.logger.debug("No Section 17(2) perquisites found - setting to 0.0")
            
        except Exception as e:
            self.logger.error(f"Error in semantic Section 17(1) extraction: {e}")
            return {}
        
        return results
    
    def _find_section_amount(self, table: pd.DataFrame, patterns: List[str], section_name: str) -> Optional[float]:
        """
        Find amount for specific section patterns using semantic row detection
        
        Args:
            table: DataFrame to search
            patterns: List of patterns to match
            section_name: Name for logging
            
        Returns:
            Amount found or None
        """
        try:
            self.logger.debug(f"=== SEARCHING FOR {section_name} ===")
            self.logger.debug(f"Table shape: {table.shape}")
            self.logger.debug(f"Patterns to search: {patterns}")
            
            patterns_found = []
            
            # Search all cells for pattern matches
            for row_idx, row in table.iterrows():
                for col_idx, cell_value in enumerate(row):
                    if pd.isna(cell_value):
                        continue
                    
                    cell_str = str(cell_value).lower().strip()
                    
                    # Check if any pattern matches
                    for pattern in patterns:
                        if pattern.lower() in cell_str:
                            patterns_found.append((pattern, row_idx, col_idx, cell_str))
                            self.logger.debug(f"Found {section_name} pattern '{pattern}' in cell ({row_idx}, {col_idx}): '{cell_str}'")
                            
                            # Extract amount from adjacent columns in same row
                            amount = self._extract_adjacent_amount(table, row_idx, col_idx, section_name)
                            if amount:
                                self.logger.info(f"Successfully extracted {section_name}: ₹{amount:,.2f}")
                                return amount
                            else:
                                self.logger.debug(f"No amount found adjacent to pattern at ({row_idx}, {col_idx})")
            
            if patterns_found:
                self.logger.debug(f"Found {len(patterns_found)} pattern matches for {section_name} but no amounts: {patterns_found}")
            else:
                self.logger.debug(f"No {section_name} patterns found in table")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding {section_name} amount: {e}")
            return None
    
    def _extract_adjacent_amount(self, table: pd.DataFrame, row_idx: int, col_idx: int, section_name: str) -> Optional[float]:
        """
        Extract amount from adjacent columns once section pattern is found
        
        Args:
            table: DataFrame containing data
            row_idx: Row index where pattern was found
            col_idx: Column index where pattern was found
            section_name: Section name for logging
            
        Returns:
            Amount found or None
        """
        try:
            row = table.iloc[row_idx]
            self.logger.debug(f"=== EXTRACTING ADJACENT AMOUNT FOR {section_name} ===")
            self.logger.debug(f"Pattern found at row {row_idx}, col {col_idx}")
            
            amounts_checked = []
            
            # Check columns to the right first (most common layout)
            for check_col in range(col_idx + 1, len(row)):
                cell_value = row.iloc[check_col]
                if pd.isna(cell_value):
                    continue
                
                cell_str = str(cell_value).strip()
                amounts_checked.append(f"Col {check_col}: '{cell_str}'")
                
                # Direct conversion approach - much simpler!
                amount = self._convert_cell_to_amount(cell_str)
                if amount is not None:
                    # Allow zero for perquisites
                    if amount >= 0:
                        self.logger.debug(f"Found {section_name} amount ₹{amount:,.2f} in column {check_col}")
                        return amount
                    else:
                        self.logger.debug(f"Negative amount ₹{amount:,.2f}, skipping")
                else:
                    self.logger.debug(f"No amount converted from '{cell_str}'")
            
            # If nothing found to the right, check columns to the left  
            for check_col in range(col_idx - 1, -1, -1):
                cell_value = row.iloc[check_col]
                if pd.isna(cell_value):
                    continue
                
                cell_str = str(cell_value).strip()
                amounts_checked.append(f"Col {check_col}: '{cell_str}'")
                
                amount = self._convert_cell_to_amount(cell_str)
                if amount is not None and amount >= 0:
                    self.logger.debug(f"Found {section_name} amount ₹{amount:,.2f} in column {check_col}")
                    return amount
            
            self.logger.warning(f"No valid amount found adjacent to {section_name} pattern. Checked: {amounts_checked}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting adjacent amount for {section_name}: {e}")
            return None
    
    def _convert_cell_to_amount(self, cell_str: str) -> Optional[float]:
        """
        Simple, direct cell-to-amount conversion without complex regex
        
        Args:
            cell_str: String value from DataFrame cell
            
        Returns:
            Float amount or None if conversion fails
        """
        if not cell_str:
            return None
            
        # Remove common formatting
        clean_str = cell_str.replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').replace('/-', '').strip()
        
        # Handle empty or non-numeric
        if not clean_str or clean_str.lower() in ['nan', 'none', '', '-']:
            return None
            
        try:
            # Direct conversion to float
            amount = float(clean_str)
            
            # Basic sanity check
            if amount > 100000000:  # 10 crores max
                return None
                
            return amount
            
        except (ValueError, TypeError):
            return None
    
    def _count_labels_in_column(self, column: pd.Series) -> int:
        """Count how many salary labels are found in a column"""
        count = 0
        
        for cell_value in column:
            if pd.isna(cell_value):
                continue
                
            cell_str = str(cell_value).lower().strip()
            
            for component_labels in self.salary_labels.values():
                if any(label in cell_str for label in component_labels):
                    count += 1
                    break
        
        return count
    
    def _count_labels_in_row(self, row: pd.Series) -> int:
        """Count how many salary labels are found in a row"""
        count = 0
        
        for cell_value in row:
            if pd.isna(cell_value):
                continue
                
            cell_str = str(cell_value).lower().strip()
            
            for component_labels in self.salary_labels.values():
                if any(label in cell_str for label in component_labels):
                    count += 1
                    break
        
        return count
    
    def _is_header_row(self, row: pd.Series) -> bool:
        """Check if a row appears to be a header"""
        non_empty_cells = sum(1 for cell in row if pd.notna(cell) and str(cell).strip())
        
        if non_empty_cells == 0:
            return False
        
        # Headers typically have text, not amounts
        amount_cells = 0
        for cell_value in row:
            if self.amount_extractor.extract_amount(str(cell_value)):
                amount_cells += 1
        
        # Row is likely header if <25% of cells contain amounts
        return (amount_cells / non_empty_cells) < 0.25
    
    def _has_meaningful_data(self, row: pd.Series) -> bool:
        """Check if a row contains meaningful data"""
        non_empty_cells = 0
        
        for cell_value in row:
            if pd.notna(cell_value) and str(cell_value).strip():
                non_empty_cells += 1
        
        return non_empty_cells >= 2  # At least 2 non-empty cells