#!/usr/bin/env python3
"""
Employer Information Extractor
=============================

Extracts employer details from Form16 documents including:
- Employer/Deductor name
- TAN (Tax Deduction Account Number)
- Employer address
- PAN of deductor (if available)
"""

import re
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from form16_extractor.models.form16_models import EmployerInfo
from form16_extractor.extractors.base.interfaces import IExtractor, ExtractionResult
from form16_extractor.pdf.table_classifier import TableType

logger = logging.getLogger(__name__)


class EmployerExtractor(IExtractor[EmployerInfo]):
    """Extract employer information from Form16 tables"""
    
    def __init__(self):
        """Initialize employer extractor with patterns and keywords"""
        self.logger = logging.getLogger(__name__)
        
        # Headers that indicate employer sections
        self.employer_headers = {
            'name_address': [
                'name and address of the employer',
                'name and address of the deductor',
                'employer/specified bank',
                'deductor name',
                'employer name'
            ],
            'tan': [
                'tan of the deductor',
                'tan of the employer',
                'deductor tan',
                'employer tan',
                'tan'
            ],
            'pan': [
                'pan of the deductor',
                'pan of the employer',
                'deductor pan',
                'employer pan'
            ]
        }
        
        # Legal entity indicators for company names
        self.company_indicators = [
            'LIMITED', 'LTD', 'PRIVATE', 'PVT', 'CORPORATION', 'CORP',
            'COMPANY', 'CO', 'INC', 'INCORPORATED', 'LLC', 'LLP',
            'SERVICES', 'SOLUTIONS', 'TECHNOLOGIES', 'INDIA', 'GLOBAL'
        ]
        
        # TAN format regex (4 letters + 5 digits + 1 letter)
        self.tan_pattern = re.compile(r'^[A-Z]{4}\d{5}[A-Z]$')
        
        # PAN format regex (for deductor PAN if needed)
        self.pan_pattern = re.compile(r'^[A-Z]{5}\d{4}[A-Z]$')
    
    def extract_employer_info(self, tables: List[pd.DataFrame]) -> EmployerInfo:
        """
        Extract employer information from Form16 tables
        
        Args:
            tables: List of pandas DataFrames containing Form16 table data
            
        Returns:
            EmployerInfo object with extracted employer details
        """
        employer_info = EmployerInfo()
        
        for table in tables:
            if table.empty:
                continue
            
            # Try different extraction strategies
            self._extract_from_address_block(table, employer_info)
            self._extract_from_key_value_pairs(table, employer_info)
            self._extract_tan_from_headers(table, employer_info)
            self._extract_from_columns(table, employer_info)
        
        return employer_info
    
    def extract(self, tables_by_type_or_list) -> any:
        """Extract employer information - handles both interfaces"""
        # Handle both List[pd.DataFrame] and Dict[TableType, List] interfaces
        if isinstance(tables_by_type_or_list, dict):
            # Traditional component interface: extract(tables_by_type) -> Tuple[EmployerInfo, Dict]
            tables_by_type = tables_by_type_or_list
            employer_tables = (tables_by_type.get(TableType.PART_B_EMPLOYER_EMPLOYEE, []) +
                              tables_by_type.get(TableType.HEADER_METADATA, []))
            
            # Extract tables from table_info dicts
            table_list = [table_info['table'] for table_info in employer_tables]
            
            result = self.extract_employer_info(table_list)
            metadata = {'strategy': 'domain_employer_extractor', 'confidence': 0.8, 'tables_used': len(table_list)}
            
            return result, metadata
        else:
            # Domain interface: extract(tables: List[pd.DataFrame]) -> EmployerInfo
            return self.extract_employer_info(tables_by_type_or_list)
    
    def extract_with_confidence(self, tables: List[pd.DataFrame]) -> ExtractionResult[EmployerInfo]:
        """
        Extract employer information with confidence scores (IExtractor interface)
        
        Args:
            tables: List of pandas DataFrames
            
        Returns:
            ExtractionResult with employer info and confidence scores
        """
        employer_info = self.extract_employer_info(tables)
        
        # Calculate confidence scores
        confidence_scores = {
            'name': self._calculate_name_confidence(employer_info.name),
            'tan': self._calculate_tan_confidence(employer_info.tan),
            'address': self._calculate_address_confidence(employer_info.address),
            'pan': self._calculate_pan_confidence(employer_info.pan)
        }
        
        return ExtractionResult(
            data=employer_info,
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
        return "Employer Information Extractor"
    
    def get_supported_fields(self) -> List[str]:
        """Get list of fields this extractor supports (IExtractor interface)"""
        return ["name", "tan", "pan", "address", "contact_info"]
    
    def extract_with_confidence_legacy(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        result = self.extract_with_confidence(tables)
        return {
            'employer_info': result.data,
            'confidence_scores': result.confidence_scores
        }
    
    def _extract_from_address_block(self, table: pd.DataFrame, employer_info: EmployerInfo):
        """Extract employer data from address block format"""
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                
                # Look for employer name/address headers
                if any(header in cell_value.lower() for header in self.employer_headers['name_address']):
                    # Check next row for employer data
                    if row_idx + 1 < len(table):
                        # Look in the same column first
                        next_cell = str(table.iloc[row_idx + 1, col_idx]).strip()
                        if self._is_company_name(next_cell):
                            self._parse_employer_block(next_cell, employer_info)
                        
                        # Also check adjacent columns
                        for offset in [-1, 1]:
                            if 0 <= col_idx + offset < len(table.columns):
                                adjacent_cell = str(table.iloc[row_idx + 1, col_idx + offset]).strip()
                                if self._is_company_name(adjacent_cell):
                                    self._parse_employer_block(adjacent_cell, employer_info)
    
    def _extract_from_key_value_pairs(self, table: pd.DataFrame, employer_info: EmployerInfo):
        """Extract from key-value pair format"""
        
        for row_idx in range(len(table)):
            if len(table.columns) >= 2:
                key = str(table.iloc[row_idx, 0]).strip().lower()
                value = str(table.iloc[row_idx, 1]).strip()
                
                # Extract employer name
                if 'employer name' in key or 'deductor name' in key or 'company name' in key:
                    if value and value.lower() not in ['nan', 'none', '']:
                        employer_info.name = self._clean_company_name(value)
                
                # Extract TAN
                if 'tan' in key and 'employer' in key or 'deductor' in key:
                    if self.tan_pattern.match(value.upper()):
                        employer_info.tan = value.upper()
                
                # Extract address
                if 'employer address' in key or 'deductor address' in key:
                    if value and value.lower() not in ['nan', 'none', '']:
                        employer_info.address = self._clean_address(value)
    
    def _extract_tan_from_headers(self, table: pd.DataFrame, employer_info: EmployerInfo):
        """Extract TAN from tables with TAN headers"""
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip().lower()
                
                # Look for TAN headers
                if any(header in cell_value for header in self.employer_headers['tan']):
                    # Check next row for TAN value
                    if row_idx + 1 < len(table):
                        tan_value = str(table.iloc[row_idx + 1, col_idx]).strip().upper()
                        if self.tan_pattern.match(tan_value):
                            employer_info.tan = tan_value
                    
                    # Also check same row adjacent columns
                    for offset in [1, 2]:
                        if col_idx + offset < len(table.columns):
                            tan_value = str(table.iloc[row_idx, col_idx + offset]).strip().upper()
                            if self.tan_pattern.match(tan_value):
                                employer_info.tan = tan_value
    
    def _extract_from_columns(self, table: pd.DataFrame, employer_info: EmployerInfo):
        """Extract from column-based format (employer vs employee columns)"""
        
        # Identify employer column
        employer_col = None
        
        for col_idx in range(len(table.columns)):
            # Check first few rows for employer indicators
            for row_idx in range(min(3, len(table))):
                cell_value = str(table.iloc[row_idx, col_idx]).strip().lower()
                if 'employer' in cell_value or 'deductor' in cell_value:
                    employer_col = col_idx
                    break
        
        if employer_col is not None:
            # Extract data from employer column
            for row_idx in range(len(table)):
                cell_value = str(table.iloc[row_idx, employer_col]).strip()
                
                # Check if it's company data
                if self._is_company_name(cell_value):
                    self._parse_employer_block(cell_value, employer_info)
                
                # Check for TAN
                if self.tan_pattern.match(cell_value.upper()):
                    employer_info.tan = cell_value.upper()
    
    def _parse_employer_block(self, text: str, employer_info: EmployerInfo):
        """Parse employer name and address from text block"""
        
        if not text or text.lower() in ['nan', 'none', '']:
            return
        
        lines = text.split('\n')
        
        # First line is usually company name
        if lines and not employer_info.name:
            potential_name = lines[0].strip()
            if self._is_company_name(potential_name):
                employer_info.name = self._clean_company_name(potential_name)
        
        # Rest is address (excluding contact info)
        if len(lines) > 1 and not employer_info.address:
            address_lines = []
            for line in lines[1:]:
                line = line.strip()
                # Skip phone numbers and emails
                if not re.match(r'^[\+\(]?\d', line) and '@' not in line:
                    address_lines.append(line)
            
            if address_lines:
                employer_info.address = self._clean_address(', '.join(address_lines))
    
    def _is_company_name(self, text: str) -> bool:
        """Check if text is likely a company name"""
        
        if not text or text.lower() in ['nan', 'none', '']:
            return False
        
        text_upper = text.upper()
        
        # Check for company indicators
        for indicator in self.company_indicators:
            if indicator in text_upper:
                return True
        
        # Check if it's all caps (common for company names)
        if text.isupper() and len(text) > 10:
            return True
        
        # Check if it doesn't look like a person's name
        if not re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', text):
            # Not in "Firstname Lastname" format
            if len(text.split()) > 2:  # Multiple words
                return True
        
        return False
    
    def _clean_company_name(self, name: str) -> str:
        """Clean and standardize company name"""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove trailing punctuation
        name = name.rstrip('.,;:')
        
        # Ensure uppercase for standard company suffixes
        for suffix in ['LIMITED', 'LTD', 'PRIVATE', 'PVT']:
            pattern = re.compile(rf'\b{suffix}\b', re.IGNORECASE)
            name = pattern.sub(suffix, name)
        
        return name.strip()
    
    def _clean_address(self, address: str) -> str:
        """Clean and format address"""
        
        # Remove multiple commas
        address = re.sub(r',+', ',', address)
        
        # Remove extra whitespace
        address = ' '.join(address.split())
        
        # Remove leading/trailing commas
        address = address.strip(',').strip()
        
        return address
    
    def _calculate_name_confidence(self, name: Optional[str]) -> float:
        """Calculate confidence score for employer name"""
        
        if not name:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Higher confidence if it has company indicators
        for indicator in self.company_indicators:
            if indicator in name.upper():
                confidence += 0.2
                break
        
        # Higher confidence for longer names
        if len(name) > 20:
            confidence += 0.2
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _calculate_tan_confidence(self, tan: Optional[str]) -> float:
        """Calculate confidence score for TAN"""
        
        if not tan:
            return 0.0
        
        # High confidence if matches TAN format
        if self.tan_pattern.match(tan):
            return 0.95
        
        return 0.3
    
    def _calculate_address_confidence(self, address: Optional[str]) -> float:
        """Calculate confidence score for address"""
        
        if not address:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Higher confidence if has PIN code
        if re.search(r'\d{6}', address):
            confidence += 0.2
        
        # Higher confidence if has state name
        states = ['Karnataka', 'Maharashtra', 'Delhi', 'Tamil Nadu', 'Gujarat', 'Haryana']
        for state in states:
            if state in address:
                confidence += 0.2
                break
        
        # Higher confidence for longer addresses
        if len(address) > 50:
            confidence += 0.1
        
        return min(confidence, 0.9)
    
    def _calculate_pan_confidence(self, pan: Optional[str]) -> float:
        """Calculate confidence score for PAN"""
        
        if not pan:
            return 0.0
        
        # High confidence if matches PAN format
        if self.pan_pattern.match(pan):
            return 0.95
        
        return 0.3