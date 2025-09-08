"""
Employee Information Extractor
=============================

Extracts employee information from Form16 tables using patterns
identified from real Form16 documents.

Based on analysis of actual Form16.pdf structure.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from form16_extractor.models.form16_models import EmployeeInfo
from form16_extractor.extractors.base.interfaces import IExtractor, ExtractionResult


class EmployeeExtractor(IExtractor[EmployeeInfo]):
    """Extract employee information from Form16 tables"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Header patterns to identify employee sections (structure-based, not data-based)
        self.employee_section_headers = {
            'employee_address_section': [
                'Name and address of the Employee',
                'Name and address of the Employee/Specified senior citizen',
                'Name and Address of Employee',
                'Employee Name and Address',
                'Name & Address of Employee',
            ],
            'employee_pan_section': [
                'PAN of the Employee',
                'PAN of the Employee/Specified senior citizen', 
                'Employee PAN',
                'PAN of Employee',
                'Employee\'s PAN',
            ],
            'employee_reference_section': [
                'Employee Reference No',
                'Employee Reference Number', 
                'Reference No. provided by the Employer',
                'Employee Ref No',
                'Employee Code',
                'Emp ID',
                'Employee ID',
            ],
            'key_value_employee_section': [
                'Employee Name',
                'Employee ID', 
                'Employee Designation',
                'Employee PAN',
                'Emp Name',
                'Emp ID',
                'Emp PAN',
                'Designation',
            ],
            'designation_section': [
                'Employee Designation',
                'Designation',
                'Job Title',
                'Position',
                'Role',
            ],
            # Additional patterns found in various Form16 formats
            'verification_section_patterns': [
                'working in the capacity of',
                'designation',
                'Full Name',
            ]
        }
        
        # Confidence scoring weights
        self.confidence_weights = {
            'exact_key_match': 0.95,
            'partial_key_match': 0.8,
            'format_validation': 0.95,
            'context_match': 0.7
        }
    
    def extract(self, tables: List[pd.DataFrame]) -> EmployeeInfo:
        """Extract employee information from Form16 tables (IExtractor interface)"""
        return self.extract_employee_info(tables)
    
    def extract_employee_info(self, tables: List[pd.DataFrame]) -> EmployeeInfo:
        """
        Extract employee information from Form16 tables
        
        Args:
            tables: List of DataFrame objects from Form16
            
        Returns:
            EmployeeInfo object with extracted data
        """
        self.logger.info(f"Extracting employee info from {len(tables)} tables")
        
        employee_info = EmployeeInfo()
        
        # Extract from each table
        for i, table in enumerate(tables):
            if table.empty:
                continue
                
            self.logger.debug(f"Processing table {i} ({table.shape[0]}x{table.shape[1]})")
            
            # Try different extraction strategies
            table_results = self._extract_from_table(table, i)
            
            # Update employee_info with best results
            self._merge_results(employee_info, table_results)
        
        # Post-process and validate
        employee_info = self._post_process_employee_info(employee_info)
        
        self.logger.info(f"Employee extraction complete: "
                        f"Name: {employee_info.name}, PAN: {employee_info.pan}")
        
        return employee_info
    
    def extract_with_confidence(self, tables: List[pd.DataFrame]) -> ExtractionResult[EmployeeInfo]:
        """
        Extract employee info with confidence scores (IExtractor interface)
        
        Returns:
            ExtractionResult with employee info and confidence scores
        """
        employee_info = self.extract_employee_info(tables)
        
        # Calculate confidence scores for each field
        confidence_scores = self._calculate_confidence_scores(tables, employee_info)
        
        return ExtractionResult(
            data=employee_info,
            confidence_scores=confidence_scores,
            metadata={
                'extractor': self.get_extractor_name(),
                'fields_attempted': self.get_supported_fields(),
                'tables_processed': len(tables)
            },
            success=True
        )
    
    def get_extractor_name(self) -> str:
        """Get the name of this extractor (IExtractor interface)"""
        return "Employee Information Extractor"
    
    def get_supported_fields(self) -> List[str]:
        """Get list of fields this extractor supports (IExtractor interface)"""
        return ["name", "pan", "address", "designation", "department", "employment_type", "employee_id"]
    
    def extract_with_confidence_legacy(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        result = self.extract_with_confidence(tables)
        return {
            'employee_info': result.data,
            'confidence_scores': result.confidence_scores
        }
    
    def _extract_from_table(self, table: pd.DataFrame, table_index: int) -> Dict[str, Any]:
        """Extract employee data from a single table"""
        
        results = {}
        
        # Convert table to searchable text
        table_text = self._table_to_text(table)
        
        # Strategy 1: Key-value pair extraction (most common in Form16)
        kv_results = self._extract_key_value_pairs(table, table_text)
        results.update(kv_results)
        
        # Strategy 2: Address block extraction (PART A format)
        address_results = self._extract_address_block(table, table_text)
        results.update(address_results)
        
        # Strategy 3: Structured table extraction
        structured_results = self._extract_structured_table(table)
        results.update(structured_results)
        
        # Strategy 4: Verification section extraction (for designation and other fields)
        verification_results = self._extract_from_verification_section(table, table_text)
        results.update(verification_results)
        
        return results
    
    def _extract_key_value_pairs(self, table: pd.DataFrame, table_text: str) -> Dict[str, Any]:
        """Extract using key-value structure detection (no regex for data)"""
        
        results = {}
        
        # Look for key-value structure in the table
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                
                # Check if this cell contains an employee header
                for header in self.employee_section_headers['key_value_employee_section']:
                    if header in cell_value:
                        # Look for the value in adjacent cells
                        value = self._find_adjacent_value(table, row_idx, col_idx)
                        
                        if value and self._is_valid_employee_data(header, value):
                            field_name = self._map_header_to_field(header)
                            if field_name:
                                results[field_name] = {
                                    'value': value,
                                    'confidence': self.confidence_weights['exact_key_match'],
                                    'method': 'key_value_structure'
                                }
        
        return results
    
    def _find_adjacent_value(self, table: pd.DataFrame, row_idx: int, col_idx: int) -> str:
        """Find value adjacent to a header cell"""
        
        # Check right (next column)
        if col_idx + 1 < len(table.columns):
            value = str(table.iloc[row_idx, col_idx + 1]).strip()
            if value and value.lower() not in ['nan', 'none', ':', '']:
                return value
        
        # Check next column after colon
        if col_idx + 2 < len(table.columns):
            value = str(table.iloc[row_idx, col_idx + 2]).strip()
            if value and value.lower() not in ['nan', 'none', ':', '']:
                return value
        
        # Check below (next row, same column)
        if row_idx + 1 < len(table):
            value = str(table.iloc[row_idx + 1, col_idx]).strip()
            if value and value.lower() not in ['nan', 'none', ':', '']:
                return value
        
        return None
    
    def _map_header_to_field(self, header: str) -> str:
        """Map header text to field name"""
        header_lower = header.lower()
        if 'name' in header_lower:
            return 'name'
        elif 'pan' in header_lower:
            return 'pan'
        elif 'id' in header_lower:
            return 'employee_id'
        elif 'designation' in header_lower:
            return 'designation'
        return None
    
    def _is_valid_employee_data(self, header: str, value: str) -> bool:
        """Check if value is valid for the header type (structure-based validation)"""
        
        if not value or len(value.strip()) < 2:
            return False
        
        header_lower = header.lower()
        value_clean = value.strip()
        
        # PAN validation (only place we use minimal regex as specified)
        if 'pan' in header_lower:
            return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value_clean))
        
        # Employee ID validation
        elif 'id' in header_lower:
            return value_clean.isdigit() and 3 <= len(value_clean) <= 10
        
        # Name validation (avoid company names)
        elif 'name' in header_lower:
            return not any(word in value_clean.lower() for word in 
                         ['limited', 'ltd', 'pvt', 'private', 'company', 'corp', 'inc', 'services'])
        
        # Designation validation
        elif 'designation' in header_lower:
            return 2 <= len(value_clean) <= 100 and not value_clean.startswith(')')
        
        return True
    
    def _extract_address_block(self, table: pd.DataFrame, table_text: str) -> Dict[str, Any]:
        """Extract from address block format (PART A - Page 2 format)"""
        
        results = {}
        
        # Strategy 1: Look for side-by-side employer/employee columns
        employee_data = self._extract_employee_from_columns(table)
        if employee_data:
            results.update(employee_data)
        
        # Strategy 2: Look for address block pattern in text
        lines = table_text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for employee address block start
            if 'name and address of the employee' in line_lower:
                # Extract name from next line
                if i + 1 < len(lines):
                    name_candidate = lines[i + 1].strip()
                    if name_candidate and len(name_candidate) > 2:
                        # Skip if this looks like employer name
                        if not any(word in name_candidate.lower() for word in ['limited', 'ltd', 'pvt', 'private', 'company', 'corp', 'inc']):
                            results['name'] = {
                                'value': name_candidate,
                                'confidence': self.confidence_weights['context_match'],
                                'method': 'address_block'
                            }
                
                # Extract address from following lines
                address_parts = []
                for j in range(i + 2, min(i + 5, len(lines))):
                    if j < len(lines):
                        addr_line = lines[j].strip()
                        if addr_line and not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', addr_line):
                            address_parts.append(addr_line)
                
                if address_parts:
                    results['address'] = {
                        'value': ', '.join(address_parts),
                        'confidence': self.confidence_weights['context_match'],
                        'method': 'address_block'
                    }
            
            # Look for PAN in the address block area
            pan_match = re.search(r'([A-Z]{5}[0-9]{4}[A-Z]{1})', line)
            if pan_match and 'employee' in line_lower:
                results['pan'] = {
                    'value': pan_match.group(1),
                    'confidence': self.confidence_weights['format_validation'],
                    'method': 'address_block'
                }
        
        return results
    
    def _extract_employee_from_columns(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract employee data from side-by-side employer/employee columns (structure-based)"""
        
        results = {}
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                
                # Look for employee address section headers
                for header in self.employee_section_headers['employee_address_section']:
                    if header in cell_value:
                        employee_column = col_idx
                        
                        # Look for employee data in the next few rows in this column
                        for data_row in range(row_idx + 1, min(row_idx + 6, len(table))):
                            employee_cell = str(table.iloc[data_row, employee_column]).strip()
                            
                            if employee_cell and employee_cell.lower() not in ['nan', 'none', '']:
                                # Split multi-line employee data
                                employee_lines = [line.strip() for line in employee_cell.split('\n') if line.strip()]
                                
                                if employee_lines:
                                    # First non-empty line should be the name
                                    potential_name = employee_lines[0]
                                    
                                    # Structure-based validation: person name vs company name
                                    if self._is_person_name(potential_name):
                                        results['name'] = {
                                            'value': potential_name,
                                            'confidence': self.confidence_weights['exact_key_match'],
                                            'method': 'column_extraction'
                                        }
                                    
                                    # Remaining lines are address
                                    if len(employee_lines) > 1:
                                        address_parts = employee_lines[1:]
                                        results['address'] = {
                                            'value': ', '.join(address_parts),
                                            'confidence': self.confidence_weights['exact_key_match'],
                                            'method': 'column_extraction'
                                        }
                                
                                break  # Found employee data, move to next section
                
                # Look for employee PAN section
                for pan_header in self.employee_section_headers['employee_pan_section']:
                    if pan_header in cell_value:
                        employee_column = col_idx
                        
                        # Check next row for PAN value
                        if row_idx + 1 < len(table):
                            pan_cell = str(table.iloc[row_idx + 1, employee_column]).strip()
                            if self._is_valid_pan_format(pan_cell):
                                results['pan'] = {
                                    'value': pan_cell,
                                    'confidence': self.confidence_weights['format_validation'],
                                    'method': 'column_extraction'
                                }
                        
                        break
                
                # Look for employee reference/ID section  
                for ref_header in self.employee_section_headers['employee_reference_section']:
                    if ref_header in cell_value:
                        employee_column = col_idx
                        
                        # Check next row for Employee ID
                        if row_idx + 1 < len(table):
                            id_cell = str(table.iloc[row_idx + 1, employee_column]).strip()
                            if self._is_valid_employee_id(id_cell):
                                results['employee_id'] = {
                                    'value': id_cell,
                                    'confidence': self.confidence_weights['exact_key_match'],
                                    'method': 'column_extraction'
                                }
                        
                        break
        
        return results
    
    def _is_person_name(self, name: str) -> bool:
        """Check if text looks like a person name vs company name"""
        if not name or len(name.strip()) < 2:
            return False
        
        name_lower = name.lower().strip()
        
        # Company indicators
        company_words = ['limited', 'ltd', 'pvt', 'private', 'company', 'corp', 'inc', 'services', 
                        'solutions', 'technologies', 'systems', 'group', 'enterprises']
        
        return not any(word in name_lower for word in company_words)
    
    def _is_valid_pan_format(self, pan: str) -> bool:
        """Validate PAN format (minimal regex as specified)"""
        if not pan:
            return False
        return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan.strip()))
    
    def _is_valid_employee_id(self, emp_id: str) -> bool:
        """Validate employee ID format"""
        if not emp_id:
            return False
        id_clean = emp_id.strip()
        return id_clean.isdigit() and 3 <= len(id_clean) <= 10
    
    def _extract_structured_table(self, table: pd.DataFrame) -> Dict[str, Any]:
        """Extract from structured table format"""
        
        results = {}
        
        # Look through table cells for employee data
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                
                if not cell_value or cell_value.lower() in ['nan', 'none', '']:
                    continue
                
                # Check for PAN pattern
                pan_match = re.match(r'^([A-Z]{5}[0-9]{4}[A-Z]{1})$', cell_value)
                if pan_match:
                    # Verify this is employee PAN (not employer PAN)
                    context = self._get_cell_context(table, row_idx, col_idx)
                    if 'employee' in context.lower():
                        results['pan'] = {
                            'value': pan_match.group(1),
                            'confidence': self.confidence_weights['format_validation'],
                            'method': 'structured_table'
                        }
                
                # Check for employee ID pattern
                if cell_value.isdigit() and len(cell_value) >= 4:
                    context = self._get_cell_context(table, row_idx, col_idx)
                    if 'employee id' in context.lower():
                        results['employee_id'] = {
                            'value': cell_value,
                            'confidence': self.confidence_weights['exact_key_match'],
                            'method': 'structured_table'
                        }
        
        return results
    
    def _extract_from_verification_section(self, table: pd.DataFrame, table_text: str) -> Dict[str, Any]:
        """Extract data from verification section (commonly contains designation info)"""
        
        results = {}
        
        # Look for verification section patterns
        lines = table_text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Look for "working in the capacity of" pattern for designation
            if 'working in the capacity of' in line_clean.lower():
                # Extract designation after this phrase
                capacity_match = re.search(r'working in the capacity of\s+([^()]+)', line_clean, re.IGNORECASE)
                if capacity_match:
                    designation = capacity_match.group(1).strip()
                    if designation and 'designation' not in designation.lower():
                        results['designation'] = {
                            'value': designation,
                            'confidence': self.confidence_weights['exact_key_match'],
                            'method': 'verification_section'
                        }
            
            # Look for "Designation:" patterns
            if 'designation:' in line_clean.lower():
                # Check if designation value is on same line
                if '|' in line_clean:
                    parts = line_clean.split('|')
                    for part in parts:
                        if 'designation:' in part.lower():
                            continue
                        elif part.strip() and len(part.strip()) > 2:
                            results['designation'] = {
                                'value': part.strip(),
                                'confidence': self.confidence_weights['exact_key_match'],
                                'method': 'verification_section'
                            }
                            break
                
                # Check next line for designation value
                if i + 1 < len(lines) and 'designation' not in results:
                    next_line = lines[i + 1].strip()
                    if next_line and len(next_line) > 2 and '|' in next_line:
                        parts = next_line.split('|')
                        for part in parts:
                            if part.strip() and len(part.strip()) > 2:
                                results['designation'] = {
                                    'value': part.strip(),
                                    'confidence': self.confidence_weights['exact_key_match'],
                                    'method': 'verification_section'
                                }
                                break
            
            # Look for "Full Name:" patterns
            if 'full name:' in line_clean.lower():
                name_match = re.search(r'full name:\s*([A-Z\s]+)', line_clean, re.IGNORECASE)
                if name_match:
                    name_candidate = name_match.group(1).strip()
                    if name_candidate and self._is_person_name(name_candidate):
                        results['name'] = {
                            'value': name_candidate,
                            'confidence': self.confidence_weights['exact_key_match'],
                            'method': 'verification_section'
                        }
        
        # Strategy for table-based verification section
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                
                # Look for designation section headers
                for header in self.employee_section_headers['designation_section']:
                    if header in cell_value and 'designation' not in results:
                        # Look for value in adjacent cells
                        value = self._find_adjacent_value(table, row_idx, col_idx)
                        if value and self._is_valid_designation(value):
                            results['designation'] = {
                                'value': value,
                                'confidence': self.confidence_weights['exact_key_match'],
                                'method': 'verification_table'
                            }
                            break
        
        return results
    
    def _is_valid_designation(self, designation: str) -> bool:
        """Check if text looks like a valid job designation"""
        if not designation or len(designation.strip()) < 2:
            return False
            
        designation_clean = designation.strip()
        
        # Exclude certain patterns that don't look like designations
        invalid_patterns = [
            ') do hereby certify',
            'hereby certify',
            'do hereby',
            'son / daughter',
            'working in',
        ]
        
        for pattern in invalid_patterns:
            if pattern in designation_clean.lower():
                return False
        
        return 2 <= len(designation_clean) <= 100
    
    def _table_to_text(self, table: pd.DataFrame) -> str:
        """Convert table to searchable text"""
        text_parts = []
        
        for row_idx in range(len(table)):
            row_parts = []
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                if cell_value and cell_value.lower() not in ['nan', 'none']:
                    row_parts.append(cell_value)
            
            if row_parts:
                text_parts.append(' '.join(row_parts))
        
        return '\n'.join(text_parts)
    
    def _get_cell_context(self, table: pd.DataFrame, row_idx: int, col_idx: int) -> str:
        """Get context around a cell for validation"""
        context_parts = []
        
        # Check surrounding cells
        for r_offset in [-1, 0, 1]:
            for c_offset in [-2, -1, 0, 1, 2]:
                new_row = row_idx + r_offset
                new_col = col_idx + c_offset
                
                if (0 <= new_row < len(table) and 0 <= new_col < len(table.columns)):
                    cell_value = str(table.iloc[new_row, new_col]).strip()
                    if cell_value and cell_value.lower() not in ['nan', 'none']:
                        context_parts.append(cell_value)
        
        return ' '.join(context_parts)
    
    def _validate_field_value(self, field_name: str, value: str) -> bool:
        """Validate extracted field value"""
        
        if not value or value.lower() in ['nan', 'none', '']:
            return False
        
        if field_name == 'pan':
            # Validate PAN format: AAAAA9999A
            return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value))
        
        elif field_name == 'employee_id':
            # Should be numeric and reasonable length
            return value.isdigit() and 3 <= len(value) <= 10
        
        elif field_name == 'name':
            # Should be reasonable name length and not contain special chars
            return 2 <= len(value) <= 100 and not re.search(r'[0-9@#$%^&*]', value)
        
        elif field_name == 'designation':
            # Should be reasonable length
            return 2 <= len(value) <= 100
        
        elif field_name == 'address':
            # Should be reasonable address length
            return 5 <= len(value) <= 500
        
        return True
    
    def _merge_results(self, employee_info: EmployeeInfo, table_results: Dict[str, Any]) -> None:
        """Merge table extraction results into employee_info"""
        
        for field_name, result in table_results.items():
            current_value = getattr(employee_info, field_name, None)
            new_value = result['value']
            new_confidence = result['confidence']
            
            # Update if we don't have a value or new value has higher confidence
            if not current_value or not hasattr(employee_info, f'_{field_name}_confidence'):
                setattr(employee_info, field_name, new_value)
                setattr(employee_info, f'_{field_name}_confidence', new_confidence)
            else:
                current_confidence = getattr(employee_info, f'_{field_name}_confidence', 0)
                if new_confidence > current_confidence:
                    setattr(employee_info, field_name, new_value)
                    setattr(employee_info, f'_{field_name}_confidence', new_confidence)
    
    def _post_process_employee_info(self, employee_info: EmployeeInfo) -> EmployeeInfo:
        """Post-process and clean employee info"""
        
        # Clean and validate PAN
        if employee_info.pan:
            employee_info.pan = employee_info.pan.upper().strip()
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', employee_info.pan):
                self.logger.warning(f"Invalid PAN format: {employee_info.pan}")
                employee_info.pan = None
        
        # Clean name
        if employee_info.name:
            employee_info.name = employee_info.name.strip()
            # Remove any trailing colons or special characters
            employee_info.name = re.sub(r'[:\-\s]+$', '', employee_info.name)
        
        # Clean address
        if employee_info.address:
            employee_info.address = employee_info.address.strip()
            # Remove multiple spaces
            employee_info.address = re.sub(r'\s+', ' ', employee_info.address)
        
        return employee_info
    
    def _calculate_confidence_scores(self, tables: List[pd.DataFrame], 
                                   employee_info: EmployeeInfo) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields"""
        
        confidence_scores = {}
        
        for field_name in ['name', 'pan', 'employee_id', 'designation', 'address']:
            confidence_attr = f'_{field_name}_confidence'
            if hasattr(employee_info, confidence_attr):
                confidence_scores[field_name] = getattr(employee_info, confidence_attr)
            else:
                # Default confidence based on field presence and validation
                field_value = getattr(employee_info, field_name, None)
                if field_value:
                    confidence_scores[field_name] = 0.7  # Default medium confidence
                else:
                    confidence_scores[field_name] = 0.0
        
        return confidence_scores