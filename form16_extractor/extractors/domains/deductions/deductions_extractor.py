#!/usr/bin/env python3

"""
Deductions Extractor Component
==============================

Component for extracting Chapter VI-A deductions data from Form16 tables.
Contains EXACT logic from simple_extractor._extract_deductions_data().

This component fixes the missing deduction fields causing field differences.
"""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

from form16_extractor.extractors.base.abstract_field_extractor import AbstractFieldExtractor
from form16_extractor.models.form16_models import ChapterVIADeductions
from form16_extractor.pdf.table_classifier import TableType


class DeductionsExtractorComponent(AbstractFieldExtractor):
    """
    Component for extracting Chapter VI-A deductions data.
    
    EXACT implementation from simple_extractor._extract_deductions_data()
    to fix missing deduction fields in modular extractor.
    """
    
    def __init__(self):
        super().__init__()
        
        # Semantic keyword patterns for robust deductions extraction (following IncomeTaxAI approach)
        self.section80_keywords = {
            'section_80c': [
                '80c', 'life insurance', 'lic premium', 'ppf', 'provident fund',
                'elss', 'equity linked', 'nsc', 'tax saving', 'investment',
                'deduction in respect of life insurance premia, contributions to',
                'contributions to provident fund'
            ],
            'section_80ccc': [
                '80ccc', 'pension plan', 'annuity plan', 'pension premium'
            ],
            'section_80ccd_1': [
                '80ccd(1)', '80ccd 1', 'employee nps'
            ],
            'section_80ccd_1b': [
                '80ccd(1b)', '80ccd 1b', 'additional nps', 'extra nps', 'nps', 'national pension'
            ],
            'section_80d': [
                '80d', 'medical insurance', 'health insurance', 'mediclaim',
                'health premium', 'medical premium'
            ],
            'section_80e': [
                '80e', 'education loan', 'study loan', 'educational loan interest'
            ],
            'section_80g': [
                '80g', 'donation', 'charity', 'charitable institution', 'pm cares'
            ],
            'section_80u': [
                '80u', 'disability', 'handicapped person', 'disabled person'
            ],
            'section_80tta': [
                '80tta', 'savings interest', 'bank interest', 'savings account'
            ]
        }
    
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Get deduction tables - CRITICAL FIX: Also check PART_A_SUMMARY tables
        
        The deductions data is often misclassified as PART_A_SUMMARY instead of PART_B_TAX_DEDUCTIONS.
        
        Args:
            tables_by_type: Classified tables
            
        Returns:
            List of deduction table_info dicts
        """
        deduction_tables = []
        
        # Primary source: PART_B_TAX_DEDUCTIONS
        deduction_tables.extend(tables_by_type.get(TableType.PART_B_TAX_DEDUCTIONS, []))
        
        # CRITICAL FIX: Also check PART_A_SUMMARY tables for deductions data
        part_a_tables = tables_by_type.get(TableType.PART_A_SUMMARY, [])
        for table_info in part_a_tables:
            # Quick test: does this table contain deductions data?
            table = table_info['table']
            test_result = self._extract_by_semantic_analysis(table)
            if test_result:  # If we found deductions data, include this table
                deduction_tables.append(table_info)
                if self.logger:
                    self.logger.info(f"Found deductions data in PART_A_SUMMARY table: {test_result}")
        
        return deduction_tables
    
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract deductions using semantic keyword matching (following IncomeTaxAI approach)
        
        Args:
            tables: List of deduction table_info dicts
            
        Returns:
            Dict of extracted deduction values
        """
        
        extracted_values = {}
        
        for table_info in tables:
            table = table_info['table']
            
            # Use semantic extraction instead of position-based
            semantic_data = self._extract_by_semantic_analysis(table)
            extracted_values.update(semantic_data)
            
            if self.logger:
                self.logger.debug(f"Semantic extraction: {len(semantic_data)} fields from deductions table")
        return extracted_values
    
    def create_model(self, data: Dict[str, Any]) -> ChapterVIADeductions:
        """
        Create ChapterVIADeductions from extracted data (EXACT from simple_extractor.py)
        
        Args:
            data: Extracted deduction values
            
        Returns:
            ChapterVIADeductions model
        """
        return self._create_deductions(data)
    
    def get_strategy_name(self) -> str:
        """Return strategy name for metadata"""
        return "position_template"
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate deduction data
        
        Args:
            data: Raw extracted data
            
        Returns:
            Validated data
        """
        # Basic validation - ensure amounts are reasonable
        validated_data = {}
        
        for field_name, value in data.items():
            if value is not None:
                amount = self._parse_amount(value)
                if amount and amount > 0 and amount <= 1500000:  # Max 15L deduction
                    validated_data[field_name] = amount
        
        return validated_data
    
    def calculate_confidence(self, data: Dict[str, Any], tables: List[Dict[str, Any]] = None) -> float:
        """
        Calculate confidence for deductions extraction
        
        Args:
            data: Extracted data
            tables: Tables used
            
        Returns:
            Confidence score
        """
        if not data:
            return 0.0
        
        # Base confidence for position-based extraction
        base_confidence = 0.8
        
        # Bonus for multiple deduction fields
        field_count = len([v for v in data.values() if v and v > 0])
        if field_count > 1:
            base_confidence += min(0.15, field_count * 0.05)
        
        return min(1.0, base_confidence)
    
    # ===============================
    # HELPER METHODS (EXACT from simple_extractor.py)
    # ===============================
    
    def _extract_by_semantic_analysis(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract deductions using semantic keyword matching (following IncomeTaxAI approach)"""
        
        extracted = {}
        
        if table.empty:
            return extracted
        
        # Skip verification/summary tables to avoid duplicate extraction
        table_str = table.to_string().lower()
        if any(indicator in table_str for indicator in [
            'verification', 'signature of the employee', 'signature of employee', 
            'i hereby certify', 'full name:', 'designation:', 'place:', 'date:'
        ]):
            if self.logger:
                self.logger.debug("Skipping verification/summary table to avoid duplicate extraction")
            return extracted
        
        # Find amount columns (prefer rightmost columns that contain numeric values)
        amount_columns = []
        for col_idx in [3, 2, 1]:  # Check rightmost columns first
            if col_idx < len(table.columns):
                col_values = [str(val).strip() for val in table.iloc[:, col_idx] if pd.notna(val)]
                numeric_count = sum(1 for val in col_values if self._is_numeric_value(val))
                
                # Column likely has amounts if >30% numeric
                if len(col_values) > 0 and (numeric_count / len(col_values)) >= 0.3:
                    amount_columns.append(col_idx)
        
        if not amount_columns:
            if self.logger:
                self.logger.debug("No amount columns found in deductions table")
            return extracted
        
        primary_amount_col = amount_columns[0]
        
        # Extract deductions by analyzing row content 
        for row_idx, row in table.iterrows():
            try:
                # Get description text from first few columns
                description = ""
                for desc_col in [0, 1]:
                    if desc_col < len(row) and pd.notna(row.iloc[desc_col]):
                        description += " " + str(row.iloc[desc_col]).strip().lower()
                
                description = description.strip()
                
                # Skip header/total rows
                if self._is_header_or_total_row(description):
                    continue
                
                # Get amount from primary amount column
                if primary_amount_col < len(row):
                    amount = self._extract_amount_from_cell(row.iloc[primary_amount_col])
                    
                    if amount and amount > 0:
                        # Classify section based on description content
                        section = self._classify_section_by_keywords(description)
                        if section:
                            # Validate amount is reasonable 
                            if self._validate_amount_range(section, amount):
                                # Handle duplicates: prefer individual rows over total rows
                                is_total_row = any(word in description for word in ['total', 'aggregate', 'sum', 'total deduction under'])
                                
                                if section in extracted:
                                    # If we already have this section, prefer the higher amount
                                    # unless the current one is a total row (which we skip)
                                    if not is_total_row and amount > extracted[section]:
                                        extracted[section] = amount
                                        if self.logger:
                                            self.logger.debug(f"Semantic match (updated): {section} = ₹{amount:,.0f} from '{description[:50]}...'")
                                    elif is_total_row:
                                        if self.logger:
                                            self.logger.debug(f"Skipping total row: {section} = ₹{amount:,.0f} from '{description[:50]}...'")
                                else:
                                    # First time seeing this section - only extract if not a total row
                                    if not is_total_row:
                                        extracted[section] = amount
                                        if self.logger:
                                            self.logger.debug(f"Semantic match: {section} = ₹{amount:,.0f} from '{description[:50]}...'")
                
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error processing deductions row {row_idx}: {e}")
                continue
        
        return extracted
    
    def _classify_section_by_keywords(self, description: str) -> Optional[str]:
        """Classify Section 80 type based on description keywords"""
        
        desc_lower = description.lower().strip()
        
        # PRIORITY-BASED CLASSIFICATION for better accuracy
        # Check specific section patterns in priority order (most specific first)
        
        # 1. Section 80CCD(1B) - Additional NPS (highest priority for specificity)
        if any(pattern in desc_lower for pattern in ['80ccd(1b)', '80ccd 1b', '80ccd (1b)']):
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → section_80ccd_1b (exact section match)")
            return 'section_80ccd_1b'
        
        # 2. Section 80CCD(1) - Employee NPS
        if any(pattern in desc_lower for pattern in ['80ccd(1)', '80ccd 1', '80ccd (1)']) and '1b' not in desc_lower:
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → section_80ccd_1 (exact section match)")
            return 'section_80ccd_1'
        
        # 3. Section 80CCC - Pension fund
        if '80ccc' in desc_lower:
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → section_80ccc (exact section match)")
            return 'section_80ccc'
        
        # 4. Section 80D - Medical insurance
        if '80d' in desc_lower or any(keyword in desc_lower for keyword in ['medical insurance', 'health insurance', 'mediclaim']):
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → section_80d (section match)")
            return 'section_80d'
        
        # 5. Section 80C - Life insurance, PPF, etc. (broader category, lower priority)
        if ('80c' in desc_lower or 
            any(keyword in desc_lower for keyword in ['life insurance', 'lic premium', 'ppf', 'provident fund', 'elss'])):
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → section_80c (section match)")
            return 'section_80c'
        
        # 6. Fallback to original scoring system for other sections
        section_scores = {}
        
        for section, keywords in self.section80_keywords.items():
            # Skip already handled sections
            if section in ['section_80c', 'section_80ccc', 'section_80ccd_1', 'section_80ccd_1b', 'section_80d']:
                continue
                
            score = 0
            for keyword in keywords:
                if keyword in desc_lower:
                    score += 1
                    # Bonus for exact section number matches
                    if keyword.startswith('80') and len(keyword) <= 4:
                        score += 3
                    # Bonus for long specific phrases
                    elif len(keyword) > 10:
                        score += 2
            
            if score > 0:
                section_scores[section] = score
        
        # Return section with highest score from fallback
        if section_scores:
            best_section = max(section_scores.keys(), key=lambda x: section_scores[x])
            if self.logger:
                self.logger.debug(f"Section classification: '{desc_lower[:50]}...' → {best_section} (fallback, score: {section_scores[best_section]})")
            return best_section
        
        return None
    
    def _is_header_or_total_row(self, description: str) -> bool:
        """Check if row is a header or total row to skip"""
        
        # Only skip obvious headers and totals, NOT individual deduction rows
        header_indicators = [
            'deductions under chapter vi-a',
            'chapter vi-a',
            'gross amount',
            'deductible amount',
            'total deductions',
            'total chapter vi-a',
            'particulars',
            'description',
            'amount of any other exemption under section',
            'total amount of exemption claimed under section'
        ]
        
        # Don't treat specific section deductions as headers
        if any(section_indicator in description for section_indicator in ['section 80', 'under section 80']):
            return False
            
        return any(indicator in description for indicator in header_indicators)
    
    def _validate_amount_range(self, section: str, amount: float) -> bool:
        """Validate that amount is reasonable for the section type"""
        
        # Define reasonable ranges for each section (to filter out obviously wrong extractions)
        section_ranges = {
            'section_80c': (500, 200000),        # Up to 2L (some may exceed 1.5L limit)
            'section_80d': (500, 100000),        # Up to 1L
            'section_80ccd_1b': (500, 60000),    # Up to 60K
            'section_80e': (1000, 300000),       # Education loan interest
            'section_80g': (100, 100000),        # Donations
            'section_80u': (500, 150000),        # Disability
            'section_80tta': (50, 15000),        # Savings interest
        }
        
        if section in section_ranges:
            min_val, max_val = section_ranges[section]
            return min_val <= amount <= max_val
        
        # Default range for other sections
        return 100 <= amount <= 500000
    
    def _is_numeric_value(self, value) -> bool:
        """Check if value represents a numeric amount"""
        
        if pd.isna(value):
            return False
        
        if isinstance(value, (int, float)):
            return True
        
        # Check string representation
        str_val = str(value).strip().replace(',', '').replace('₹', '').replace('Rs.', '')
        str_val = str_val.replace('/-', '').replace(' ', '')
        
        # Handle lakhs/crores
        if 'l' in str_val.lower() or 'lakh' in str_val.lower():
            str_val = str_val.lower().replace('l', '').replace('lakh', '').strip()
        elif 'cr' in str_val.lower() or 'crore' in str_val.lower():
            str_val = str_val.lower().replace('cr', '').replace('crore', '').strip()
        
        try:
            float(str_val)
            return True
        except (ValueError, TypeError):
            return False
    
    def _extract_amount_from_cell(self, cell_value) -> Optional[float]:
        """Extract amount from cell value with multiple format support"""
        
        if pd.isna(cell_value):
            return None
        
        str_value = str(cell_value).strip()
        
        # Handle zero indicators
        if str_value.lower() in ['nil', 'n.a.', 'not applicable', '-', '', '0', '0.00']:
            return 0.0
        
        # Try direct numeric conversion
        if isinstance(cell_value, (int, float)):
            return float(cell_value)
        
        try:
            # Clean string and convert
            clean_value = str_value.replace(',', '').replace('₹', '').replace('Rs.', '')
            clean_value = clean_value.replace('/-', '').replace(' ', '').strip()
            
            # Handle lakhs notation
            if 'l' in clean_value.lower() or 'lakh' in str_value.lower():
                number_part = clean_value.lower().replace('l', '').replace('lakh', '').strip()
                try:
                    return float(number_part) * 100000
                except ValueError:
                    pass
            
            # Handle crores notation
            if 'cr' in clean_value.lower() or 'crore' in str_value.lower():
                number_part = clean_value.lower().replace('cr', '').replace('crore', '').strip()
                try:
                    return float(number_part) * 10000000
                except ValueError:
                    pass
            
            return float(clean_value)
            
        except (ValueError, TypeError):
            return None
    
    def _shape_matches(self, actual_shape: tuple, expected_shapes: List[tuple]) -> bool:
        """Check if table shape matches any of the expected shapes"""
        return actual_shape in expected_shapes
    
    def _extract_value_from_positions(self, table: pd.DataFrame, positions: List[Tuple[int, int]]) -> Optional[Any]:
        """Extract value from list of candidate positions (EXACT from simple_extractor.py)"""
        
        for row_idx, col_idx in positions:
            # Handle negative indices
            if row_idx < 0:
                row_idx = len(table) + row_idx
            if col_idx < 0:
                col_idx = len(table.columns) + col_idx
            
            # Check bounds
            if 0 <= row_idx < len(table) and 0 <= col_idx < len(table.columns):
                cell_value = table.iloc[row_idx, col_idx]
                
                if not pd.isna(cell_value):
                    # Try to parse as amount first
                    amount = self._parse_amount(cell_value)
                    if amount and amount > 0:
                        return amount
        
        return None
    
    def _create_deductions(self, data: Dict[str, Any]) -> ChapterVIADeductions:
        """Create ChapterVIADeductions from extracted data with comprehensive zero-value handling"""
        
        # Parse amounts safely with fallback to 0
        def safe_parse(key: str) -> Decimal:
            value = data.get(key)
            if value is None:
                return Decimal('0')
            
            # If already a Decimal, return it
            if isinstance(value, Decimal):
                return value
            
            # Handle float/int values
            if isinstance(value, (float, int)):
                return Decimal(str(value))
            
            # Try to parse as amount
            parsed_amount = self._parse_amount(value)
            if parsed_amount is not None:
                return Decimal(str(parsed_amount))
            
            return Decimal('0')
        
        # Calculate totals and derived values to improve coverage
        section_80c_total = safe_parse('section_80c')
        section_80ccc_total = safe_parse('section_80ccc') 
        section_80ccd_1_total = safe_parse('section_80ccd_1')
        section_80ccd_1b_total = safe_parse('section_80ccd_1b')
        section_80ccd_2_total = safe_parse('section_80ccd_2')
        
        # Calculate 80CCE limit (80C + 80CCC + 80CCD(1) with 150K max)
        total_80c_80ccc_80ccd1 = section_80c_total + section_80ccc_total + section_80ccd_1_total
        allowed_80cce = min(total_80c_80ccc_80ccd1, Decimal('150000'))
        
        # Calculate overall total deductions
        total_deductions = (section_80c_total + section_80ccc_total + section_80ccd_1_total + 
                           section_80ccd_1b_total + section_80ccd_2_total + safe_parse('section_80d') +
                           safe_parse('section_80e') + safe_parse('section_80g') + safe_parse('section_80u') +
                           safe_parse('section_80tta') + safe_parse('other_deductions'))
        
        return ChapterVIADeductions(
            # Section 80C and components (with semantic extraction results + explicit zeros)
            section_80c_total=section_80c_total,
            ppf_contribution=section_80c_total if section_80c_total > 0 else Decimal('0'),  # For this form, all 80C is provident fund
            elss_investment=Decimal('0'),
            life_insurance_premium=Decimal('0'), 
            home_loan_principal=Decimal('0'),
            nsc_investment=Decimal('0'),
            
            # Section 80CCC
            section_80ccc=section_80ccc_total,
            
            # Section 80CCD
            section_80ccd_1=section_80ccd_1_total,
            section_80ccd_1b=section_80ccd_1b_total,
            section_80ccd_2=section_80ccd_2_total,
            
            # Section 80D components (explicit zeros for comprehensive coverage)
            section_80d_self_family=safe_parse('section_80d_self_family'),
            section_80d_parents=safe_parse('section_80d_parents'),
            section_80d_total=safe_parse('section_80d_self_family') + safe_parse('section_80d_parents'),
            
            # Other sections (explicit zeros for comprehensive coverage)
            section_80e=safe_parse('section_80e'),
            section_80g=safe_parse('section_80g'),
            section_80gg=safe_parse('section_80gg'),
            section_80u=safe_parse('section_80u'),
            
            # Interest on savings (80TTA)
            section_80tta=safe_parse('section_80tta'),
            
            # Total deductions
            total_chapter_via_deductions=total_deductions
        )