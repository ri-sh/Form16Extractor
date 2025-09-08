#!/usr/bin/env python3

"""
Validation Mixin
=================

Shared validation utilities extracted from simple_extractor.py.
Contains validation logic for tax amounts, PAN, TAN, and other Form16 data.
"""

import re
from decimal import Decimal
from typing import Dict, Optional


class ValidationMixin:
    """Mixin providing validation utilities from simple_extractor.py"""
    
    def _validate_tax_amount(self, field_name: str, amount: Decimal) -> bool:
        """
        Validate that tax amount is reasonable for the field type (EXACT from simple_extractor.py)
        
        Args:
            field_name: Name of the tax field
            amount: Amount to validate
            
        Returns:
            True if amount is reasonable for the field type
        """
        
        if amount <= 0:
            return False
        
        # Reasonable ranges for tax computation fields (in INR)
        field_ranges = {
            'gross_total_income': (50000, 50000000),      # 50K to 5CR 
            'tax_on_total_income': (0, 15000000),         # 0 to 1.5CR
            'health_education_cess': (0, 600000),         # 0 to 6L
            'total_tax_liability': (0, 15000000)          # 0 to 1.5CR
        }
        
        min_val, max_val = field_ranges.get(field_name, (0, 100000000))
        
        if min_val <= amount <= max_val:
            return True
        
        return False
    
    def _validate_tax_computation_consistency(self, extracted_values: Dict[str, Decimal]) -> float:
        """
        Validate logical consistency between tax computation values (from simple_extractor.py)
        
        Args:
            extracted_values: Dict of extracted tax values
            
        Returns:
            Validation bonus score (0.0 to 1.0)
        """
        
        validation_bonus = 0.0
        
        gross_income = extracted_values.get('gross_total_income', Decimal('0'))
        tax_on_income = extracted_values.get('tax_on_total_income', Decimal('0'))
        cess = extracted_values.get('health_education_cess', Decimal('0'))
        total_liability = extracted_values.get('total_tax_liability', Decimal('0'))
        
        # Check if we have the key values
        if gross_income > 0 and tax_on_income > 0:
            # Tax should be reasonable percentage of income (5-35%)
            tax_rate = (tax_on_income / gross_income) * 100
            if 5 <= tax_rate <= 35:
                validation_bonus += 0.05
            
            # Cess should be ~4% of income tax
            if cess > 0:
                expected_cess = tax_on_income * Decimal('0.04')
                cess_diff = abs(cess - expected_cess) / expected_cess
                if cess_diff < Decimal('0.1'):  # Within 10%
                    validation_bonus += 0.05
            
            # Total liability should be sum of tax + cess
            if total_liability > 0:
                expected_total = tax_on_income + cess
                total_diff = abs(total_liability - expected_total) / expected_total
                if total_diff < Decimal('0.05'):  # Within 5%
                    validation_bonus += 0.1
        
        return validation_bonus
    
    def _is_reasonable_salary_amount(self, amount: Decimal) -> bool:
        """
        Check if amount is reasonable for salary field
        
        Args:
            amount: Amount to validate
            
        Returns:
            True if amount is reasonable for salary
        """
        # Salary should be between 1K and 50CR INR
        return Decimal('1000') <= amount <= Decimal('50000000')
    
    def _validate_pan(self, pan: str) -> bool:
        """
        Validate PAN format (from simple_extractor.py)
        
        PAN format: [A-Z]{5}[0-9]{4}[A-Z]
        Example: ABCDE1234F
        
        Args:
            pan: PAN string to validate
            
        Returns:
            True if PAN format is valid
        """
        if not pan or len(pan) != 10:
            return False
        
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        return bool(re.match(pan_pattern, pan.upper()))
    
    def _is_tan_pattern(self, text: str) -> bool:
        """
        Check if text matches TAN format (from simple_extractor.py)
        
        TAN format: [A-Z]{4}[0-9]{5}[A-Z]
        Example: ABCD12345E
        
        Args:
            text: Text to check
            
        Returns:
            True if text matches TAN pattern
        """
        if not text or len(text) != 10:
            return False
        return bool(re.match(r'^[A-Z]{4}[0-9]{5}[A-Z]$', text.upper()))
    
    def _validate_company_name(self, name: str) -> bool:
        """
        Validate if extracted text is a valid company name (from simple_extractor.py)
        
        Args:
            name: Company name to validate
            
        Returns:
            True if name appears to be a valid company name
        """
        if not name or len(name) < 5:
            return False
        
        # Common company indicators
        company_indicators = [
            'ltd', 'limited', 'private', 'pvt', 'company', 'corp', 'corporation',
            'inc', 'services', 'solutions', 'technologies', 'systems', 'group'
        ]
        
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in company_indicators)
    
    def _is_valid_person_name(self, text: str) -> bool:
        """
        Check if text is a valid person name (from simple_extractor.py)
        
        Args:
            text: Text to validate as person name
            
        Returns:
            True if text appears to be a valid person name
        """
        if not text or len(text.strip()) < 4:
            return False
        
        text = text.strip()
        
        # Avoid obvious non-names
        avoid_patterns = [
            'certificate', 'assessment year', 'financial year', 'address',
            'bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune',
            'itpl', 'sez', 'ward no', 'hudco', 'ltd', 'pvt', 'inc'
        ]
        
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in avoid_patterns):
            return False
            
        # Valid person name patterns
        name_patterns = [
            r'^[A-Z][a-z]+ [A-Z][a-z]+$',              # First Last
            r'^[A-Z]+ [A-Z]+$',                        # FIRST LAST  
            r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$', # First Middle Last
            r'^[A-Z]+ [A-Z]+ [A-Z]+$',                 # FIRST MIDDLE LAST
        ]
        
        for pattern in name_patterns:
            if re.match(pattern, text):
                return True
                
        return False
    
    def _validate_quarterly_tds_consistency(self, quarterly_records: list) -> float:
        """
        Validate consistency of quarterly TDS records
        
        Args:
            quarterly_records: List of quarterly TDS records
            
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if not quarterly_records:
            return 0.0
        
        consistency_score = 0.0
        
        # Check for valid quarters
        valid_quarters = {'Q1', 'Q2', 'Q3', 'Q4'}
        quarters_present = {record.quarter for record in quarterly_records if hasattr(record, 'quarter')}
        
        if quarters_present.issubset(valid_quarters):
            consistency_score += 0.3
        
        # Check for receipt numbers
        receipts_present = sum(1 for record in quarterly_records 
                             if hasattr(record, 'receipt_number') and record.receipt_number)
        if receipts_present > 0:
            consistency_score += 0.3
        
        # Check for amounts
        amounts_present = sum(1 for record in quarterly_records 
                            if hasattr(record, 'amount_paid') and record.amount_paid and record.amount_paid > 0)
        if amounts_present > 0:
            consistency_score += 0.4
        
        return consistency_score
    
    def _validate_date_format(self, date_str: str) -> bool:
        """
        Validate if date string is in expected format
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date format is valid
        """
        if not date_str:
            return False
        
        # Common date patterns in Form16
        date_patterns = [
            r'\d{2}-\w{3}-\d{4}',      # 05-Jun-2022
            r'\d{2}/\d{2}/\d{4}',      # 05/06/2022
            r'\d{4}-\d{2}-\d{2}',      # 2022-06-05
            r'\d{2}\.\d{2}\.\d{4}',    # 05.06.2022
        ]
        
        return any(re.match(pattern, date_str.strip()) for pattern in date_patterns)