"""
Identity Extractor - Employee and Employer Information
====================================================

Robust extraction of identity fields from ANY Form 16 document.
Handles various layouts and formats with high accuracy.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from decimal import Decimal


class IdentityExtractor:
    """Extract employee and employer identity information from Form 16 tables"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # PAN/TAN patterns
        self.pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
        self.tan_pattern = re.compile(r'\b[A-Z]{4}[0-9]{5}[A-Z]{1}\b')
        
        # Common field indicators
        self.employee_name_indicators = [
            'employee name', 'name of employee', 'name', 'emp name',
            'employee', 'नाम', 'कर्मचारी का नाम'
        ]
        
        self.employer_name_indicators = [
            'employer name', 'name of employer', 'deductor name', 
            'company name', 'employer', 'name and address of employer',
            'नियोक्ता का नाम', 'कंपनी का नाम'
        ]
        
        self.designation_indicators = [
            'designation', 'position', 'job title', 'post', 'पदनाम'
        ]
        
        self.address_indicators = [
            'address', 'पता', 'residential address', 'office address'
        ]
    
    def extract(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        Extract all identity information from tables
        
        Returns comprehensive identity data with confidence scores
        """
        self.logger.info("🆔 Extracting identity information...")
        
        result = {
            'employee': {},
            'employer': {},
            'confidence': {},
            'extraction_metadata': {
                'tables_processed': len(tables),
                'extraction_method': 'comprehensive_identity_scan'
            }
        }
        
        # Process each table for identity information
        for i, table in enumerate(tables):
            try:
                self.logger.debug(f"Processing table {i} for identity data...")
                
                # Extract PAN/TAN information
                pan_data = self._extract_pan_information(table)
                tan_data = self._extract_tan_information(table)
                
                # Extract names
                name_data = self._extract_names(table)
                
                # Extract addresses
                address_data = self._extract_addresses(table)
                
                # Extract other identity fields
                other_data = self._extract_other_identity_fields(table)
                
                # Merge results with confidence scoring
                self._merge_identity_results(result, {
                    **pan_data, **tan_data, **name_data, 
                    **address_data, **other_data
                })
                
            except Exception as e:
                self.logger.warning(f"Error processing table {i} for identity: {str(e)}")
                continue
        
        # Post-process and validate results
        self._post_process_identity_results(result)
        
        # Log extraction summary
        self._log_identity_extraction_summary(result)
        
        return result
    
    def _extract_pan_information(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract PAN information with employee/employer distinction"""
        pan_results = {}
        
        # Convert table to string for regex search
        table_text = table.to_string(index=False, header=False)
        
        # Find all PAN matches
        pan_matches = self.pan_pattern.findall(table_text)
        
        if not pan_matches:
            return pan_results
        
        # Try to distinguish employee vs employer PAN based on context
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).upper()
                
                # Check if cell contains PAN
                pan_match = self.pan_pattern.search(cell_value)
                if not pan_match:
                    continue
                
                pan_value = pan_match.group()
                
                # Determine context - look at nearby cells
                context = self._get_cell_context(table, row_idx, col_idx, radius=2)
                context_text = ' '.join(context).lower()
                
                # Employee PAN indicators
                if any(indicator in context_text for indicator in [
                    'employee', 'emp', 'deductee', 'payee', 'कर्मचारी'
                ]):
                    pan_results['employee_pan'] = pan_value
                    pan_results['employee_pan_confidence'] = 0.9
                
                # Employer PAN indicators  
                elif any(indicator in context_text for indicator in [
                    'employer', 'deductor', 'company', 'नियोक्ता'
                ]):
                    pan_results['employer_pan'] = pan_value
                    pan_results['employer_pan_confidence'] = 0.8
                
                # If no clear context, assume first PAN is employee
                elif 'employee_pan' not in pan_results:
                    pan_results['employee_pan'] = pan_value
                    pan_results['employee_pan_confidence'] = 0.6
        
        return pan_results
    
    def _extract_tan_information(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract TAN (always employer TAN)"""
        tan_results = {}
        
        table_text = table.to_string(index=False, header=False)
        tan_matches = self.tan_pattern.findall(table_text)
        
        if tan_matches:
            # TAN always belongs to employer
            tan_results['employer_tan'] = tan_matches[0]
            tan_results['employer_tan_confidence'] = 0.95
        
        return tan_results
    
    def _extract_names(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract employee and employer names"""
        name_results = {}
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx])
                cell_lower = cell_value.lower().strip()
                
                # Skip empty or invalid cells
                if not cell_value or cell_lower in ['nan', 'none', '']:
                    continue
                
                # Check for employee name indicators
                if any(indicator in cell_lower for indicator in self.employee_name_indicators):
                    name = self._extract_name_from_context(table, row_idx, col_idx)
                    if name and self._is_valid_name(name):
                        name_results['employee_name'] = name
                        name_results['employee_name_confidence'] = 0.85
                
                # Check for employer name indicators
                elif any(indicator in cell_lower for indicator in self.employer_name_indicators):
                    name = self._extract_name_from_context(table, row_idx, col_idx)
                    if name and self._is_valid_company_name(name):
                        name_results['employer_name'] = name
                        name_results['employer_name_confidence'] = 0.8
        
        return name_results
    
    def _extract_addresses(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract employee and employer addresses"""
        address_results = {}
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx])
                cell_lower = cell_value.lower().strip()
                
                if any(indicator in cell_lower for indicator in self.address_indicators):
                    # Look for multi-line address in nearby cells
                    address = self._extract_address_from_context(table, row_idx, col_idx)
                    
                    if address:
                        # Try to determine if it's employee or employer address
                        context = self._get_cell_context(table, row_idx, col_idx, radius=3)
                        context_text = ' '.join(context).lower()
                        
                        if any(emp_indicator in context_text for emp_indicator in [
                            'employee', 'emp', 'deductee', 'payee'
                        ]):
                            address_results['employee_address'] = address
                            address_results['employee_address_confidence'] = 0.7
                        else:
                            address_results['employer_address'] = address
                            address_results['employer_address_confidence'] = 0.7
        
        return address_results
    
    def _extract_other_identity_fields(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract designation, department, and other identity fields"""
        other_results = {}
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx])
                cell_lower = cell_value.lower().strip()
                
                # Extract designation
                if any(indicator in cell_lower for indicator in self.designation_indicators):
                    designation = self._extract_value_from_context(table, row_idx, col_idx)
                    if designation and len(designation) > 2:
                        other_results['designation'] = designation
                        other_results['designation_confidence'] = 0.75
                
                # Extract employee ID
                if 'employee id' in cell_lower or 'emp id' in cell_lower:
                    emp_id = self._extract_value_from_context(table, row_idx, col_idx)
                    if emp_id:
                        other_results['employee_id'] = emp_id
                        other_results['employee_id_confidence'] = 0.8
        
        return other_results
    
    def _extract_name_from_context(self, table: pd.DataFrame, row: int, col: int) -> Optional[str]:
        """Extract name from cell context"""
        # Look in same cell first
        cell_value = str(table.iloc[row, col])
        
        # Check if cell contains both indicator and name
        if ':' in cell_value:
            parts = cell_value.split(':', 1)
            if len(parts) > 1:
                potential_name = parts[1].strip()
                if self._is_valid_name(potential_name):
                    return potential_name
        
        # Look in adjacent cells
        search_positions = [
            (row, col + 1), (row, col + 2),  # Right
            (row + 1, col), (row + 2, col),  # Below
        ]
        
        for check_row, check_col in search_positions:
            if (0 <= check_row < len(table) and 0 <= check_col < len(table.columns)):
                candidate = str(table.iloc[check_row, check_col]).strip()
                if candidate and candidate.lower() not in ['nan', 'none'] and self._is_valid_name(candidate):
                    return candidate
        
        return None
    
    def _extract_address_from_context(self, table: pd.DataFrame, row: int, col: int) -> Optional[str]:
        """Extract multi-line address from context"""
        address_lines = []
        
        # Look for address in nearby cells (address is usually multi-line)
        for r in range(row, min(row + 5, len(table))):
            for c in range(max(0, col - 1), min(col + 3, len(table.columns))):
                if r == row and c == col:
                    continue  # Skip the indicator cell
                
                cell_value = str(table.iloc[r, c]).strip()
                if (cell_value and cell_value.lower() not in ['nan', 'none'] and 
                    len(cell_value) > 3):
                    address_lines.append(cell_value)
        
        if address_lines:
            return ' '.join(address_lines[:3])  # Limit to first 3 lines
        
        return None
    
    def _extract_value_from_context(self, table: pd.DataFrame, row: int, col: int) -> Optional[str]:
        """Extract value from cell context (generic)"""
        # Same cell check
        cell_value = str(table.iloc[row, col])
        if ':' in cell_value:
            parts = cell_value.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip()
        
        # Adjacent cells
        for check_row, check_col in [(row, col + 1), (row + 1, col), (row, col + 2)]:
            if (0 <= check_row < len(table) and 0 <= check_col < len(table.columns)):
                candidate = str(table.iloc[check_row, check_col]).strip()
                if candidate and candidate.lower() not in ['nan', 'none']:
                    return candidate
        
        return None
    
    def _get_cell_context(self, table: pd.DataFrame, row: int, col: int, radius: int = 2) -> List[str]:
        """Get text context around a cell"""
        context = []
        
        for r in range(max(0, row - radius), min(len(table), row + radius + 1)):
            for c in range(max(0, col - radius), min(len(table.columns), col + radius + 1)):
                cell_value = str(table.iloc[r, c]).strip()
                if cell_value and cell_value.lower() not in ['nan', 'none']:
                    context.append(cell_value)
        
        return context
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if string looks like a person's name"""
        if not name or len(name) < 3:
            return False
        
        # Remove common patterns that aren't names
        invalid_patterns = [
            r'^\d+$',  # Only numbers
            r'^[^a-zA-Z\s]+$',  # No letters
            r'(form|table|page|section|part)',  # Document terms
            r'(amount|total|sum|rupees|rs\.)',  # Financial terms
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.search(pattern, name_lower):
                return False
        
        # Should contain letters and reasonable length
        return bool(re.search(r'[a-zA-Z]', name)) and len(name.split()) <= 5
    
    def _is_valid_company_name(self, name: str) -> bool:
        """Validate if string looks like a company name"""
        if not name or len(name) < 5:
            return False
        
        # Company name indicators
        company_indicators = [
            'ltd', 'limited', 'pvt', 'private', 'inc', 'incorporated',
            'corp', 'corporation', 'llp', 'company', 'co.', 'group',
            'technologies', 'systems', 'services', 'solutions'
        ]
        
        name_lower = name.lower()
        has_company_indicator = any(indicator in name_lower for indicator in company_indicators)
        
        # Allow reasonable length and company indicators
        return has_company_indicator or len(name) > 10
    
    def _merge_identity_results(self, main_result: Dict[str, Any], new_data: Dict[str, Any]):
        """Merge new identity data with existing results, keeping highest confidence"""
        
        for key, value in new_data.items():
            if key.endswith('_confidence'):
                continue
                
            confidence_key = f"{key}_confidence"
            new_confidence = new_data.get(confidence_key, 0.5)
            
            # Determine target section
            if key.startswith('employee_'):
                section = 'employee'
                field = key[9:]  # Remove 'employee_' prefix
            elif key.startswith('employer_'):
                section = 'employer' 
                field = key[9:]  # Remove 'employer_' prefix
            else:
                section = 'employee'  # Default
                field = key
            
            # Update if higher confidence or field doesn't exist
            if (field not in main_result[section] or 
                new_confidence > main_result['confidence'].get(f"{section}_{field}", 0)):
                
                main_result[section][field] = value
                main_result['confidence'][f"{section}_{field}"] = new_confidence
    
    def _post_process_identity_results(self, result: Dict[str, Any]):
        """Post-process and clean identity results"""
        # Clean employee name
        if 'name' in result['employee']:
            result['employee']['name'] = self._clean_name(result['employee']['name'])
        
        # Clean employer name
        if 'name' in result['employer']:
            result['employer']['name'] = self._clean_name(result['employer']['name'])
        
        # Validate PAN/TAN formats
        if 'pan' in result['employee']:
            if not self.pan_pattern.match(result['employee']['pan']):
                del result['employee']['pan']
                if 'employee_pan' in result['confidence']:
                    del result['confidence']['employee_pan']
        
        if 'tan' in result['employer']:
            if not self.tan_pattern.match(result['employer']['tan']):
                del result['employer']['tan']
                if 'employer_tan' in result['confidence']:
                    del result['confidence']['employer_tan']
    
    def _clean_name(self, name: str) -> str:
        """Clean and standardize name format"""
        if not name:
            return name
        
        # Remove extra whitespace
        cleaned = ' '.join(name.split())
        
        # Title case
        cleaned = cleaned.title()
        
        # Remove common prefixes/suffixes that might be extraction artifacts
        prefixes_to_remove = ['Name:', 'Employee Name:', 'Employer Name:']
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    def _log_identity_extraction_summary(self, result: Dict[str, Any]):
        """Log summary of identity extraction"""
        employee_fields = len([k for k, v in result['employee'].items() if v])
        employer_fields = len([k for k, v in result['employer'].items() if v])
        
        self.logger.info(f"✅ Identity extraction complete:")
        self.logger.info(f"   Employee fields: {employee_fields}")
        self.logger.info(f"   Employer fields: {employer_fields}")
        
        # Log key extractions
        if result['employee'].get('name'):
            self.logger.info(f"   Employee: {result['employee']['name']}")
        if result['employee'].get('pan'):
            self.logger.info(f"   Employee PAN: {result['employee']['pan']}")
        if result['employer'].get('name'):
            self.logger.info(f"   Employer: {result['employer']['name']}")
        if result['employer'].get('tan'):
            self.logger.info(f"   Employer TAN: {result['employer']['tan']}")