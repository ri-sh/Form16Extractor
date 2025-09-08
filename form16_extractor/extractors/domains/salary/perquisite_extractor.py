#!/usr/bin/env python3
"""
Perquisite Extractor - Salary Domain Component
==============================================

Specialized extractor for perquisite values from Form16 documents.
Follows modular architecture pattern from older IncomeTaxAI project.

Key Features:
- 15 detailed perquisite category extraction
- Pattern recognition for 25x5 perquisite tables
- Integration with salary domain coordinator
- Comprehensive perquisite validation
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from .amount_extractor import AmountExtractor


class PerquisiteExtractor:
    """
    Specialized extractor for perquisite values in Form16 documents
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.amount_extractor = AmountExtractor()
        
        # Define 15 target perquisite categories (from old code)
        self.target_categories = [
            'accommodation_perquisite', 'car_perquisite', 'stock_options_esop',
            'concessional_loans', 'free_meals', 'insurance_premiums',
            'club_membership', 'phone_internet_bills', 'medical_treatment',
            'holiday_travel', 'furniture_fixtures', 'education_fees',
            'credit_card_fees', 'domestic_help', 'other_perquisites'
        ]
        
        # Perquisite pattern keywords for classification
        self.perquisite_patterns = {
            'accommodation_perquisite': [
                'accommodation', 'house rent', 'residential', 'housing',
                'rent free accommodation', 'quarters'
            ],
            'car_perquisite': [
                'motor car', 'vehicle', 'car facility', 'automobile',
                'transport facility', 'car perquisite'
            ],
            'stock_options_esop': [
                'stock options', 'esop', 'employee stock', 'share option',
                'equity compensation', 'stock purchase', 'non-qualified options',
                'stock options (non-qualified', 'other than esop'
            ],
            'concessional_loans': [
                'concessional loan', 'interest free loan', 'subsidized loan',
                'employee loan', 'advance'
            ],
            'free_meals': [
                'free meals', 'food facility', 'canteen', 'meal voucher',
                'subsidized food', 'lunch facility'
            ],
            'insurance_premiums': [
                'insurance premium', 'life insurance', 'medical insurance',
                'health insurance', 'group insurance'
            ],
            'club_membership': [
                'club membership', 'club facility', 'gym membership',
                'recreational club', 'sports club'
            ],
            'phone_internet_bills': [
                'telephone', 'mobile phone', 'internet', 'communication',
                'phone bills', 'telecom facility'
            ],
            'medical_treatment': [
                'medical treatment', 'medical facility', 'health care',
                'medical reimbursement', 'medical expenses'
            ],
            'holiday_travel': [
                'holiday travel', 'vacation', 'tour expenses',
                'family trip', 'recreational travel'
            ],
            'furniture_fixtures': [
                'furniture', 'fixtures', 'home furnishing',
                'office furniture', 'equipment'
            ],
            'education_fees': [
                'education', 'school fees', 'tuition fees',
                'educational expenses', 'children education'
            ],
            'credit_card_fees': [
                'credit card', 'card annual fee', 'banking charges',
                'credit facility'
            ],
            'domestic_help': [
                'domestic help', 'house keeping', 'driver',
                'domestic servant', 'household staff'
            ],
            'other_perquisites': [
                'other perquisites', 'miscellaneous perquisites',
                'other benefits', 'misc perq'
            ]
        }
        
        # Common perquisite table indicators
        self.perquisite_table_indicators = [
            'value of perquisite',
            'amount recovered',
            'amount chargeable',
            'perquisite under section 17(2)',
            'benefits provided',
            'facility provided'
        ]
    
    def extract_perquisites(self, tables_data: List[pd.DataFrame]) -> Dict[str, float]:
        """
        Extract perquisite values from Form16 tables
        
        Args:
            tables_data: List of DataFrame objects from tables
            
        Returns:
            Dictionary with perquisite categories and their amounts
        """
        
        self.logger.info(f"Extracting perquisites from {len(tables_data)} tables")
        
        # Initialize results
        results = {category: 0.0 for category in self.target_categories}
        total_perquisite_value = 0.0
        
        # Process each table
        for i, table_df in enumerate(tables_data):
            self.logger.debug(f"Processing table {i+1}/{len(tables_data)} for perquisites")
            
            # Check if this is a perquisite table
            if not self._is_perquisite_table(table_df):
                continue
            
            # Extract perquisite structure (25x5 tables, etc.)
            table_perquisites = self._extract_from_perquisite_table(table_df)
            
            # Merge results
            for category, amount in table_perquisites.items():
                if category in self.target_categories and amount > 0:
                    if results[category] == 0 or amount > results[category]:
                        results[category] = amount
                        self.logger.debug(f"Found {category}: ₹{amount:,.2f}")
            
            # Also look for total perquisite value
            total_from_table = self._extract_total_perquisite_value(table_df)
            if total_from_table > total_perquisite_value:
                total_perquisite_value = total_from_table
        
        # Calculate derived totals
        calculated_total = sum(amount for amount in results.values() if amount > 0)
        
        # Use the higher of calculated or extracted total
        final_total = max(calculated_total, total_perquisite_value)
        
        extracted_count = sum(1 for amount in results.values() if amount > 0)
        self.logger.info(f"Extracted {extracted_count}/15 perquisite categories, total: Rs {final_total:,.2f}")
        
        return {
            **results,
            'total_perquisites': final_total
        }
    
    def _is_perquisite_table(self, table_df: pd.DataFrame) -> bool:
        """
        Check if table contains detailed perquisite data (Form 12BA structure)
        
        Args:
            table_df: DataFrame to check
            
        Returns:
            True if table appears to contain detailed perquisite breakdown
        """
        
        # Convert table to string for pattern matching
        table_str = table_df.to_string().lower()
        
        # FIRST: Exclude salary summary tables that contain perquisite references but aren't perquisite tables
        salary_summary_indicators = [
            'gross salary', 'salary as per provisions', 'total salary',
            'allowances to the extent exempt', 'section 10(', 'travel concession'
        ]
        
        salary_summary_matches = sum(1 for indicator in salary_summary_indicators if indicator in table_str)
        if salary_summary_matches >= 2:
            self.logger.debug(f"Excluding salary summary table (not detailed perquisites)")
            return False
        
        # Look for specific Form 12BA perquisite table indicators
        form_12ba_indicators = [
            'value of perquisite', 'amount recovered', 'amount chargeable',
            'serial number', 's.no.', 'accommodation', 'cars/other automotive',
            'stock options', 'free meals', 'club expenses'
        ]
        
        form_12ba_matches = 0
        for indicator in form_12ba_indicators:
            if indicator in table_str:
                form_12ba_matches += 1
        
        # Check for Form 12BA table structure (typically 20-25 rows x 5 columns)
        is_form_12ba_structure = (
            table_df.shape[0] >= 15 and  # At least 15 perquisite categories
            table_df.shape[1] >= 4 and   # At least 4 columns (S.No, Description, Value, Chargeable)
            table_df.shape[0] <= 30      # Not too large (salary tables can be much larger)
        )
        
        # Must have multiple Form 12BA indicators AND proper structure
        is_perquisite = form_12ba_matches >= 3 and is_form_12ba_structure
        
        if is_perquisite:
            self.logger.debug(f"Identified Form 12BA perquisite table: {form_12ba_matches} indicators, shape={table_df.shape}")
        
        return is_perquisite
    
    def _extract_from_perquisite_table(self, table_df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract perquisites from a dedicated perquisite table
        
        Args:
            table_df: DataFrame containing perquisite data
            
        Returns:
            Dictionary with perquisite categories and amounts
        """
        
        results = {}
        
        # ONLY use Form 12BA structure extraction - no keyword fallback to avoid false positives
        form12ba_results = self._extract_from_form12ba_table(table_df)
        if form12ba_results:
            results.update(form12ba_results)
            self.logger.info(f"Found Form 12BA perquisites: {list(form12ba_results.keys())}")
        else:
            self.logger.debug(f"No valid perquisites found in Form 12BA table")
        
        # DISABLED: Keyword-based fallback extraction (causes false positives)
        # Only Form 12BA extraction is reliable enough for production use
        
        return results
    
    def _extract_from_form12ba_table(self, table_df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract perquisites from Form 12BA table structure
        
        Based on the discovered structure:
        - Column 0: S.No.
        - Column 1: Description (e.g., "Stock options (non-qualified options) other than ESOP")
        - Column 2: Value of perquisite as per rules (Rs.)
        - Column 4: Amount chargeable to tax (Rs.)
        
        Args:
            table_df: DataFrame containing Form 12BA data
            
        Returns:
            Dictionary with extracted perquisite amounts
        """
        
        results = {}
        
        # Check if this looks like a Form 12BA table (25x5 structure)
        if table_df.shape[0] < 15 or table_df.shape[1] < 5:
            return results
        
        # Extract from Form 12BA rows using category mapping
        for row_idx in range(table_df.shape[0]):
            # Get the description from column 0 or 1 (sometimes S.No is in column 0, description in column 1)
            desc_cell = None
            if row_idx < table_df.shape[0]:
                # Try column 0 first (sometimes contains "8 Free Meals")
                if 0 < table_df.shape[1] and pd.notna(table_df.iloc[row_idx, 0]):
                    desc_cell = table_df.iloc[row_idx, 0]
                # Then try column 1 (standard description column)
                elif 1 < table_df.shape[1] and pd.notna(table_df.iloc[row_idx, 1]):
                    desc_cell = table_df.iloc[row_idx, 1]
            
            if desc_cell is not None:
                desc_str = str(desc_cell).strip()
                category = self._map_description_to_category(desc_str)
                
                if category:
                    # Extract amount from column 4 (chargeable amount) or column 2 (value as per rules)
                    amount = self._extract_form12ba_amount(table_df, row_idx)
                    if amount > 0:
                        results[category] = amount
                        self.logger.info(f"Found {category}: ₹{amount:,.2f} from '{desc_str}'")

        return results
    
    def _extract_form12ba_amount(self, table_df: pd.DataFrame, row_idx: int) -> float:
        """
        Extract amount from Form 12BA table row
        
        Args:
            table_df: DataFrame containing the table
            row_idx: Row index to extract from
            
        Returns:
            Amount if found, 0.0 otherwise
        """
        
        # Try column 4 first (chargeable amount), then column 2 (value as per rules)
        for col_idx in [4, 2]:
            if col_idx < table_df.shape[1]:
                amount_cell = table_df.iloc[row_idx, col_idx]
                if pd.notna(amount_cell):
                    try:
                        amount = float(str(amount_cell).replace(',', '').replace('₹', '').replace('Rs.', '').strip())
                        if amount > 0:
                            return amount
                    except (ValueError, TypeError):
                        continue
        
        return 0.0
    
    def _map_description_to_category(self, desc_str: str) -> str:
        """Map Form 12BA description to perquisite category"""
        desc_lower = desc_str.lower()
        
        # Direct keyword mapping
        if 'stock options' in desc_lower and ('non-qualified' in desc_lower or 'other than esop' in desc_lower):
            return 'stock_options_esop'
        elif 'accommodation' in desc_lower:
            return 'accommodation_perquisite'
        elif any(word in desc_lower for word in ['car', 'automotive', 'vehicle']):
            return 'car_perquisite'
        elif 'free meals' in desc_lower or 'meals' in desc_lower:
            return 'free_meals'
        elif 'education' in desc_lower:
            return 'education_fees'
        elif 'credit card' in desc_lower:
            return 'credit_card_fees'
        elif 'club' in desc_lower:
            return 'club_membership'
        elif 'holiday' in desc_lower:
            return 'holiday_travel'
        elif any(word in desc_lower for word in ['sweeper', 'gardener', 'watchman', 'attendant']):
            return 'domestic_help'
        elif any(word in desc_lower for word in ['gas', 'electricity', 'water']):
            return 'other_perquisites'  # Utilities
        elif 'loan' in desc_lower:
            return 'concessional_loans'
        elif any(word in desc_lower for word in ['gift', 'voucher']):
            return 'other_perquisites'
        elif any(word in desc_lower for word in ['other benefit', 'amenity', 'service', 'privilege']):
            return 'other_perquisites'
        else:
            # Fallback for unrecognized categories
            return 'other_perquisites'
    
    def _extract_form12ba_amount(self, table_df: pd.DataFrame, row_idx: int) -> float:
        """
        Extract amount from Form 12BA table row
        
        Args:
            table_df: DataFrame containing the table
            row_idx: Row index to extract from
            
        Returns:
            Amount if found, 0.0 otherwise
        """
        
        # Try column 4 first (chargeable amount), then column 2 (value as per rules)
        for col_idx in [4, 2]:
            if col_idx < table_df.shape[1]:
                amount_cell = table_df.iloc[row_idx, col_idx]
                if pd.notna(amount_cell):
                    try:
                        amount = float(str(amount_cell).replace(',', '').replace('₹', '').replace('Rs.', '').strip())
                        if amount > 0:
                            return amount
                    except (ValueError, TypeError):
                        continue
        
        return 0.0
    
    def _find_perquisite_amount(self, table_df: pd.DataFrame, keywords: List[str], 
                              category: str) -> Optional[float]:
        """
        Find amount for a specific perquisite category
        
        Args:
            table_df: DataFrame to search
            keywords: Keywords that identify this perquisite category
            category: Category name for logging
            
        Returns:
            Amount if found, None otherwise
        """
        
        # Search through table for keywords
        for row_idx in range(table_df.shape[0]):
            for col_idx in range(table_df.shape[1]):
                cell_value = table_df.iloc[row_idx, col_idx]
                
                if pd.isna(cell_value):
                    continue
                
                cell_str = str(cell_value).lower().strip()
                
                # Check if this cell matches any keyword
                for keyword in keywords:
                    if keyword in cell_str:
                        # Look for amounts in surrounding cells
                        amount = self._search_surrounding_cells_for_amount(
                            table_df, row_idx, col_idx, category
                        )
                        if amount:
                            return amount
        
        return None
    
    def _search_surrounding_cells_for_amount(self, table_df: pd.DataFrame, 
                                           row: int, col: int, category: str) -> Optional[float]:
        """
        Search cells around a keyword match for amounts
        
        Args:
            table_df: DataFrame to search
            row: Row index of keyword match
            col: Column index of keyword match
            category: Category for context
            
        Returns:
            Amount if found, None otherwise
        """
        
        # For total perquisites, be more restrictive to avoid false positives
        if category == 'total_perquisites':
            # Only look in the same row, in value columns (2, 3, 4 for Form 12BA)
            amounts = []
            for col_idx in [2, 3, 4]:  # Value columns in Form 12BA
                if col_idx < table_df.shape[1]:
                    cell_value = table_df.iloc[row, col_idx]
                    if pd.notna(cell_value):
                        # Extract amount directly, not using amount_extractor to avoid parsing row numbers
                        try:
                            amount_str = str(cell_value).replace(',', '').replace('₹', '').replace('Rs.', '').strip()
                            amount = float(amount_str)
                            if amount > 0:
                                amounts.append(amount)
                        except (ValueError, TypeError):
                            continue
            return max(amounts) if amounts else None
        
        # For other categories, use normal search pattern
        search_offsets = [
            (0, 1), (0, 2), (0, 3),  # Right
            (1, 0), (2, 0),          # Down
            (1, 1), (1, 2)           # Diagonal
        ]
        
        amounts = []
        
        for row_offset, col_offset in search_offsets:
            new_row = row + row_offset
            new_col = col + col_offset
            
            # Check bounds
            if (0 <= new_row < table_df.shape[0] and 0 <= new_col < table_df.shape[1]):
                cell_value = table_df.iloc[new_row, new_col]
                amount = self.amount_extractor.extract_amount(str(cell_value), category)
                if amount:
                    amounts.append(amount)
        
        # Return the highest amount found (assuming it's the chargeable amount)
        return max(amounts) if amounts else None
    
    def _extract_total_perquisite_value(self, table_df: pd.DataFrame) -> float:
        """
        Extract total perquisite value from table
        
        Args:
            table_df: DataFrame to search
            
        Returns:
            Total perquisite value if found, 0.0 otherwise
        """
        
        total_keywords = [
            'total perquisites',
            'total value',
            'grand total',
            'aggregate perquisites',
            'total chargeable'
        ]
        
        for row_idx in range(table_df.shape[0]):
            for col_idx in range(table_df.shape[1]):
                cell_value = table_df.iloc[row_idx, col_idx]
                
                if pd.isna(cell_value):
                    continue
                
                cell_str = str(cell_value).lower().strip()
                
                # Check if this cell indicates total
                for keyword in total_keywords:
                    if keyword in cell_str:
                        # Look for amount in surrounding cells
                        amount = self._search_surrounding_cells_for_amount(
                            table_df, row_idx, col_idx, 'total_perquisites'
                        )
                        if amount:
                            return amount
        
        return 0.0
    
    def get_extraction_summary(self, results: Dict[str, float]) -> Dict[str, Any]:
        """
        Get summary of perquisite extraction results
        
        Args:
            results: Extraction results dictionary
            
        Returns:
            Summary information
        """
        
        # Exclude total from category count
        category_results = {k: v for k, v in results.items() if k != 'total_perquisites'}
        
        extracted_components = sum(1 for amount in category_results.values() if amount > 0)
        total_amount = results.get('total_perquisites', 0.0)
        
        return {
            'extracted_components': extracted_components,
            'total_components': len(self.target_categories),
            'extraction_rate': (extracted_components / len(self.target_categories)) * 100,
            'total_perquisite_amount': total_amount,
            'status': 'COMPLETED' if extracted_components >= 5 else 'PARTIAL',
            'major_perquisites': [
                {'category': k, 'amount': v} 
                for k, v in category_results.items() 
                if v > 50000
            ]
        }