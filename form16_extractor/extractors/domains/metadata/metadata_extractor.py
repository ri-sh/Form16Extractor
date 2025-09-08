#!/usr/bin/env python3

"""
Metadata Extractor Component
============================

Component for extracting Form16 metadata from tables.
Contains EXACT logic from simple_extractor._extract_form16_metadata().

This component fixes the missing 3-4 metadata fields causing field differences.
"""

import pandas as pd
import re
from typing import Dict, Any, List, Optional, Tuple

from form16_extractor.extractors.base.abstract_field_extractor import AbstractFieldExtractor
from form16_extractor.models.form16_models import Form16Metadata
from form16_extractor.pdf.table_classifier import TableType


class MetadataExtractorComponent(AbstractFieldExtractor):
    """
    Component for extracting Form16 metadata.
    
    EXACT implementation from simple_extractor._extract_form16_metadata()
    to fix missing metadata fields in modular extractor.
    """
    
    def __init__(self):
        super().__init__()
    
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Get metadata tables (EXACT from simple_extractor.py)
        
        Args:
            tables_by_type: Classified tables
            
        Returns:
            List of metadata table_info dicts
        """
        return (tables_by_type.get(TableType.VERIFICATION_SECTION, []) +
                tables_by_type.get(TableType.HEADER_METADATA, []) +
                tables_by_type.get(TableType.PART_B_EMPLOYER_EMPLOYEE, []))
    
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract metadata using EXACT logic from simple_extractor._extract_form16_metadata()
        
        Args:
            tables: List of metadata table_info dicts
            
        Returns:
            Dict of extracted metadata values
        """
        
        extracted_values = {}
        
        for table_info in tables:
            table = table_info['table']
            
            # Extract metadata fields using comprehensive pattern matching approach
            for i in range(len(table)):
                for j in range(len(table.columns)):
                    cell_value = str(table.iloc[i, j]).strip()
                    cell_lower = cell_value.lower()
                    
                    # Skip empty cells
                    if not cell_value or cell_value.lower() in ['nan', 'none']:
                        continue
                    
                    # Enhanced certificate number extraction - handle multiline patterns
                    if 'certificate' in cell_lower:
                        # Extract from multiline patterns like "Certificate No.\nRKQNGHA" 
                        cert_match = self._extract_certificate_from_multiline(cell_value)
                        if cert_match:
                            extracted_values['certificate_number'] = cert_match
                        else:
                            # Try adjacent search
                            cert_num = self._search_nearby_for_metadata_value(
                                table, i, j, self._looks_like_certificate_number
                            )
                            if cert_num:
                                extracted_values['certificate_number'] = cert_num.upper()
                    
                    # Direct certificate number pattern - generic approach
                    elif len(cell_value) >= 6 and self._looks_like_certificate_number(cell_value):
                        extracted_values['certificate_number'] = cell_value.upper()
                    
                    # Enhanced assessment year extraction using older codebase approach
                    if 'assessment year' in cell_lower:
                        year = self._search_nearby_for_metadata_value(
                            table, i, j, self._is_year_pattern
                        )
                        if year:
                            extracted_values['assessment_year'] = year
                    elif self._is_year_pattern(cell_value):
                        extracted_values['assessment_year'] = cell_value
                    
                    # Enhanced financial year extraction
                    if 'financial year' in cell_lower:
                        year = self._search_nearby_for_metadata_value(
                            table, i, j, self._is_financial_year_pattern
                        )
                        if year:
                            extracted_values['financial_year'] = year
                    elif self._is_financial_year_pattern(cell_value):
                        extracted_values['financial_year'] = cell_value
                    
                    # Enhanced date extraction - handle multiline patterns like "Last updated on\n05-Jun-2022"
                    if 'last updated' in cell_lower:
                        date_match = self._extract_date_from_multiline(cell_value)
                        if date_match:
                            extracted_values['issue_date'] = date_match
                        else:
                            # Try adjacent search
                            date_val = self._search_nearby_for_metadata_value(
                                table, i, j, self._is_date_pattern
                            )
                            if date_val:
                                extracted_values['issue_date'] = date_val
                    elif self._is_date_pattern(cell_value):
                        extracted_values['issue_date'] = cell_value
                    
                    # Place of issue extraction
                    if 'place' in cell_lower and ('issue' in cell_lower or 'signature' in cell_lower):
                        place = self._search_nearby_for_metadata_value(
                            table, i, j, self._looks_like_place_name
                        )
                        if place:
                            extracted_values['place_of_issue'] = place
                    elif self._looks_like_place_name(cell_value) and len(cell_value) > 4:
                        extracted_values['place_of_issue'] = cell_value
        
        return extracted_values
    
    def create_model(self, data: Dict[str, Any]) -> Form16Metadata:
        """
        Create Form16Metadata from extracted data
        
        Args:
            data: Extracted metadata values
            
        Returns:
            Form16Metadata model
        """
        # Create metadata with string dates (to avoid Pydantic validation errors)
        metadata_dict = {
            'certificate_number': data.get('certificate_number'),
            'assessment_year': data.get('assessment_year'),
            'financial_year': data.get('financial_year'),
        }
        
        # Only add non-None values to avoid validation errors
        if data.get('place_of_issue'):
            metadata_dict['place_of_issue'] = data.get('place_of_issue')
            
        # Handle date fields - store as strings in reference_number field for now
        if data.get('issue_date'):
            metadata_dict['reference_number'] = f"Issue Date: {data.get('issue_date')}"
            
        return Form16Metadata(**metadata_dict)
    
    def get_strategy_name(self) -> str:
        """Return strategy name for metadata"""
        return "enhanced_pattern_matching"
    
    def calculate_confidence(self, data: Dict[str, Any], tables: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence for metadata extraction
        
        Args:
            data: Extracted data
            tables: Tables used
            
        Returns:
            Confidence score
        """
        if not data:
            return 0.0
        
        # Base confidence for pattern matching
        base_confidence = 0.8
        
        # High confidence fields
        high_confidence_fields = ['certificate_number', 'assessment_year', 'financial_year']
        high_conf_count = sum(1 for field in high_confidence_fields if data.get(field))
        
        if high_conf_count >= 2:
            base_confidence = 0.95
        elif high_conf_count >= 1:
            base_confidence = 0.9
        
        return base_confidence
    
    # ===============================
    # HELPER METHODS (EXACT from simple_extractor.py)
    # ===============================
    
    def _extract_certificate_from_multiline(self, cell_value: str) -> Optional[str]:
        """Extract certificate number from multiline patterns like 'Certificate No.\nRKQNGHA'"""
        if not cell_value:
            return None
        
        # Split by newlines and look for certificate pattern after "Certificate"
        lines = cell_value.split('\n')
        for i, line in enumerate(lines):
            if 'certificate' in line.lower():
                # Look for the actual certificate number in next lines or same line
                for j in range(i, min(i+3, len(lines))):  # Check up to 2 lines after
                    potential_cert = lines[j].replace('Certificate No.', '').replace('Certificate Number', '').strip()
                    if potential_cert and self._looks_like_certificate_number(potential_cert):
                        return potential_cert.upper()
        return None
    
    def _extract_date_from_multiline(self, cell_value: str) -> Optional[str]:
        """Extract date from multiline patterns like 'Last updated on\n05-Jun-2022'"""
        if not cell_value:
            return None
        
        lines = cell_value.split('\n')
        for line in lines:
            if self._is_date_pattern(line.strip()):
                return line.strip()
        return None
    
    def _looks_like_certificate_number(self, text: str) -> bool:
        """Check if text looks like a certificate number (alphanumeric, 6+ chars, not common words)"""
        if not text or len(text) < 6:
            return False
        
        text = text.strip().upper()
        
        # Must contain letters and/or numbers only
        if not re.match(r'^[A-Z0-9]+$', text):
            return False
        
        # Certificate numbers can be letters only or mixed alphanumeric
        has_letters = any(c.isalpha() for c in text)
        has_numbers = any(c.isdigit() for c in text)
        
        # Should have either all letters (6+ chars) or mixed alphanumeric
        if has_letters and len(text) >= 6:
            # Avoid common English words
            avoid_words = ['CERTIFICATE', 'NUMBER', 'SECTION', 'INCOME', 'DEDUCTION', 'SALARY']
            return text not in avoid_words
        
        return False
    
    def _is_year_pattern(self, text: str) -> bool:
        """Check if text matches assessment year pattern like '2022-23'"""
        if not text:
            return False
        
        text = text.strip()
        # Be more flexible - allow both 2-digit and 4-digit formats
        patterns = [
            r'^20\d{2}-\d{2}$',      # 2022-23
            r'^20\d{2}-20\d{2}$',    # 2022-2023 (some forms use this)
            r'^\d{4}-\d{2}$'         # Generic year-year format
        ]
        return any(re.match(pattern, text) for pattern in patterns)
    
    def _is_financial_year_pattern(self, text: str) -> bool:
        """Check if text matches financial year pattern"""
        # Same as assessment year for Indian tax system
        return self._is_year_pattern(text)
    
    def _is_date_pattern(self, text: str) -> bool:
        """Check if text matches date patterns commonly found in Form16"""
        if not text:
            return False
        
        text = text.strip()
        date_patterns = [
            r'\d{2}-\w{3}-\d{4}',      # 05-Jun-2022
            r'\d{2}/\d{2}/\d{4}',      # 05/06/2022
            r'\d{4}-\d{2}-\d{2}',      # 2022-06-05
            r'\d{2}\.\d{2}\.\d{4}',    # 05.06.2022
            r'\d{1,2}\s+\w+\s+\d{4}',  # 5 June 2022
        ]
        return any(re.match(pattern, text) for pattern in date_patterns)
    
    def _looks_like_place_name(self, text: str) -> bool:
        """Check if text looks like a place name"""
        if not text or len(text.strip()) < 3:
            return False
        
        text = text.strip()
        
        # Common Indian cities/places
        common_places = [
            'bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune', 'kolkata',
            'gurgaon', 'noida', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
            'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna', 'vadodara'
        ]
        
        text_lower = text.lower()
        
        # Check if it's a known place
        if any(place in text_lower for place in common_places):
            return True
        
        # Check if it looks like a place (starts with capital, contains only letters/spaces)
        if re.match(r'^[A-Z][a-zA-Z\s]+$', text) and len(text) <= 50:
            # Avoid obvious non-places
            avoid_words = ['certificate', 'number', 'section', 'deduction', 'income', 'salary', 'employee']
            return not any(avoid in text_lower for avoid in avoid_words)
        
        return False
    
    def _search_nearby_for_metadata_value(self, table: pd.DataFrame, center_row: int, 
                                        center_col: int, validation_func) -> Optional[str]:
        """Search nearby cells for a value that passes validation (based on older codebase)"""
        
        # Define search positions (same as older codebase approach)
        search_positions = [
            (center_row, center_col),
            (center_row, center_col + 1),
            (center_row, center_col + 2), 
            (center_row + 1, center_col),
            (center_row + 2, center_col),
            (center_row, center_col - 1),
            (center_row - 1, center_col)
        ]
        
        for row_pos, col_pos in search_positions:
            if 0 <= row_pos < len(table) and 0 <= col_pos < len(table.columns):
                cell_value = str(table.iloc[row_pos, col_pos]).strip()
                if cell_value and cell_value.lower() not in ['nan', 'none', '']:
                    if validation_func(cell_value):
                        return cell_value
        
        return None