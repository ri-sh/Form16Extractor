#!/usr/bin/env python3
"""
Text Processing Utilities
=========================

Centralized utilities for text cleaning, amount detection, and pattern matching.
Used across all extractors to ensure consistent data processing.
"""

import re
import logging
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pandas as pd


logger = logging.getLogger(__name__)


class TextCleaner:
    """Centralized text cleaning utilities"""
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text"""
        if not text or pd.isna(text):
            return ""
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', str(text))
        
        # Remove leading/trailing whitespace
        return text.strip()
    
    @staticmethod
    def remove_special_chars(text: str, keep_chars: str = "") -> str:
        """Remove special characters except those specified"""
        if not text or pd.isna(text):
            return ""
        
        # Default characters to keep
        default_keep = ".,()-/"
        keep_chars = keep_chars or default_keep
        
        # Create pattern to remove everything except alphanumeric and keep_chars
        pattern = f"[^a-zA-Z0-9\s{re.escape(keep_chars)}]"
        
        return re.sub(pattern, "", str(text))
    
    @staticmethod
    def clean_address(address: str) -> str:
        """Clean and format address text"""
        if not address or pd.isna(address):
            return ""
        
        address = str(address)
        
        # Normalize whitespace
        address = TextCleaner.normalize_whitespace(address)
        
        # Remove multiple commas
        address = re.sub(r',+', ',', address)
        
        # Remove leading/trailing commas
        address = address.strip(',').strip()
        
        # Capitalize first letter of each line
        lines = address.split(',')
        lines = [line.strip().capitalize() for line in lines if line.strip()]
        
        return ', '.join(lines)
    
    @staticmethod
    def clean_company_name(name: str) -> str:
        """Clean and standardize company name"""
        if not name or pd.isna(name):
            return ""
        
        name = str(name)
        
        # Normalize whitespace
        name = TextCleaner.normalize_whitespace(name)
        
        # Remove trailing punctuation
        name = name.rstrip('.,;:')
        
        # Standardize common company suffixes
        suffixes = {
            'limited': 'LIMITED',
            'ltd': 'LTD',
            'private': 'PRIVATE', 
            'pvt': 'PVT',
            'corporation': 'CORPORATION',
            'corp': 'CORP',
            'company': 'COMPANY',
            'co': 'CO'
        }
        
        for old_suffix, new_suffix in suffixes.items():
            pattern = rf'\b{old_suffix}\b'
            name = re.sub(pattern, new_suffix, name, flags=re.IGNORECASE)
        
        return name.strip()
    
    @staticmethod
    def clean_person_name(name: str) -> str:
        """Clean person name"""
        if not name or pd.isna(name):
            return ""
        
        name = str(name)
        
        # Normalize whitespace
        name = TextCleaner.normalize_whitespace(name)
        
        # Remove trailing colons or dashes
        name = re.sub(r'[:\-\s]+$', '', name)
        
        # Capitalize properly (first letter of each word)
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name.strip()


class AmountExtractor:
    """Extract and validate monetary amounts from text"""
    
    # Currency patterns
    CURRENCY_SYMBOLS = ['₹', 'Rs.', 'Rs ', 'INR', 'rs.', 'rs ']
    AMOUNT_PATTERN = re.compile(r'[\d,]+\.?\d*')
    
    @staticmethod
    def extract_amount(text: str) -> Optional[Decimal]:
        """
        Extract monetary amount from text
        
        Args:
            text: Text that may contain amount
            
        Returns:
            Decimal amount or None if not found
        """
        if not text or pd.isna(text):
            return None
        
        text_str = str(text).strip()
        
        # Remove currency symbols
        for symbol in AmountExtractor.CURRENCY_SYMBOLS:
            text_str = text_str.replace(symbol, '')
        
        # Remove spaces and other non-numeric chars except comma and dot
        text_str = re.sub(r'[^\d,.]', '', text_str)
        
        if not text_str:
            return None
        
        try:
            # Handle Indian number formatting (commas)
            if ',' in text_str:
                # Remove commas (Indian formatting: 1,23,456.78)
                text_str = text_str.replace(',', '')
            
            return Decimal(text_str)
            
        except (InvalidOperation, ValueError):
            logger.debug(f"Could not extract amount from: {text}")
            return None
    
    @staticmethod
    def is_valid_amount(amount: Decimal, min_amount: float = 0, max_amount: float = 100000000) -> bool:
        """Validate if amount is within reasonable bounds"""
        if not amount:
            return False
        
        amount_float = float(amount)
        return min_amount <= amount_float <= max_amount
    
    @staticmethod
    def detect_currency_format(text: str) -> str:
        """Detect currency format used in text"""
        if not text or pd.isna(text):
            return "unknown"
        
        text_str = str(text).lower()
        
        for symbol in AmountExtractor.CURRENCY_SYMBOLS:
            if symbol.lower() in text_str:
                return symbol
        
        return "numeric"
    
    @staticmethod
    def format_amount(amount: Decimal, currency: str = "INR") -> str:
        """Format amount with currency"""
        if not amount:
            return "0.00"
        
        # Indian number formatting
        amount_str = f"{amount:,.2f}"
        
        if currency == "INR":
            return f"₹ {amount_str}"
        else:
            return f"{currency} {amount_str}"


class PatternMatcher:
    """Pattern matching utilities for common Form16 patterns"""
    
    # Standard patterns
    PAN_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    TAN_PATTERN = re.compile(r'^[A-Z]{4}[0-9]{5}[A-Z]{1}$')
    
    # Date patterns (multiple formats)
    DATE_PATTERNS = [
        re.compile(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})'),  # DD/MM/YYYY or DD-MM-YYYY
        re.compile(r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})'),  # YYYY/MM/DD or YYYY-MM-DD
        re.compile(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', re.IGNORECASE)
    ]
    
    # Assessment year pattern
    ASSESSMENT_YEAR_PATTERN = re.compile(r'(\d{4})\s*-\s*(\d{2,4})')
    
    @staticmethod
    def is_valid_pan(text: str) -> bool:
        """Check if text is valid PAN format"""
        if not text or pd.isna(text):
            return False
        
        return bool(PatternMatcher.PAN_PATTERN.match(str(text).strip().upper()))
    
    @staticmethod
    def is_valid_tan(text: str) -> bool:
        """Check if text is valid TAN format"""
        if not text or pd.isna(text):
            return False
        
        return bool(PatternMatcher.TAN_PATTERN.match(str(text).strip().upper()))
    
    @staticmethod
    def extract_date(text: str) -> Optional[datetime]:
        """Extract date from text using multiple patterns"""
        if not text or pd.isna(text):
            return None
        
        text_str = str(text).strip()
        
        for pattern in PatternMatcher.DATE_PATTERNS:
            match = pattern.search(text_str)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.groups()[1].isalpha():  # Month name format
                            day, month_name, year = match.groups()
                            month_map = {
                                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                                'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                            }
                            month = month_map.get(month_name.lower()[:3])
                            if month:
                                return datetime(int(year), month, int(day))
                        else:  # Numeric format
                            parts = [int(x) for x in match.groups()]
                            if parts[2] > 31:  # Year is last
                                return datetime(parts[2], parts[1], parts[0])
                            else:  # Year is first
                                return datetime(parts[0], parts[1], parts[2])
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def extract_assessment_year(text: str) -> Optional[Tuple[int, int]]:
        """Extract assessment year from text (returns start_year, end_year)"""
        if not text or pd.isna(text):
            return None
        
        text_str = str(text).strip()
        match = PatternMatcher.ASSESSMENT_YEAR_PATTERN.search(text_str)
        
        if match:
            start_year = int(match.group(1))
            end_part = match.group(2)
            
            # Handle 2-digit end year (e.g., 2023-24)
            if len(end_part) == 2:
                end_year = int(f"{str(start_year)[:2]}{end_part}")
            else:
                end_year = int(end_part)
            
            return (start_year, end_year)
        
        return None
    
    @staticmethod
    def is_company_name(text: str) -> bool:
        """Check if text looks like a company name vs person name"""
        if not text or pd.isna(text):
            return False
        
        text_upper = str(text).upper()
        
        # Company indicators
        company_words = [
            'LIMITED', 'LTD', 'PRIVATE', 'PVT', 'CORPORATION', 'CORP',
            'COMPANY', 'CO', 'INC', 'INCORPORATED', 'LLC', 'LLP',
            'SERVICES', 'SOLUTIONS', 'TECHNOLOGIES', 'SYSTEMS',
            'INDIA', 'GLOBAL', 'INTERNATIONAL', 'ENTERPRISES'
        ]
        
        # Check for company indicators
        for indicator in company_words:
            if indicator in text_upper:
                return True
        
        # Check if it's all caps (common for company names)
        if text.isupper() and len(text) > 10:
            return True
        
        # Check if it doesn't look like "Firstname Lastname"
        words = text.split()
        if len(words) == 2 and words[0].istitle() and words[1].istitle():
            return False  # Likely person name
        
        return len(words) > 2  # Multiple words suggest company
    
    @staticmethod
    def is_person_name(text: str) -> bool:
        """Check if text looks like a person name vs company name"""
        return not PatternMatcher.is_company_name(text)
    
    @staticmethod
    def normalize_column_header(header: str) -> str:
        """Normalize column header for consistent matching"""
        if not header or pd.isna(header):
            return ""
        
        header_str = str(header).strip().lower()
        
        # Remove common prefixes/suffixes
        header_str = re.sub(r'^(sl\.?\s*no\.?|s\.?\s*no\.?|sr\.?\s*no\.?)', '', header_str)
        header_str = re.sub(r'\(.*\)$', '', header_str)  # Remove parentheses
        
        # Normalize whitespace and punctuation
        header_str = re.sub(r'[^\w\s]', ' ', header_str)
        header_str = re.sub(r'\s+', ' ', header_str)
        
        return header_str.strip()


class DataValidator:
    """Validation utilities for extracted data"""
    
    @staticmethod
    def is_reasonable_salary(amount: Decimal) -> bool:
        """Check if salary amount is reasonable"""
        if not amount:
            return False
        
        amount_float = float(amount)
        # Reasonable salary range: 50k to 1 crore per year
        return 50000 <= amount_float <= 10000000
    
    @staticmethod
    def is_reasonable_tax(tax_amount: Decimal, salary_amount: Optional[Decimal] = None) -> bool:
        """Check if tax amount is reasonable"""
        if not tax_amount:
            return tax_amount == 0 or tax_amount is None  # Zero tax is valid
        
        tax_float = float(tax_amount)
        
        # Tax should be positive and reasonable
        if tax_float < 0 or tax_float > 5000000:  # Max 50L tax
            return False
        
        # If salary is provided, check tax percentage
        if salary_amount and salary_amount > 0:
            tax_percentage = (tax_float / float(salary_amount)) * 100
            return tax_percentage <= 45  # Max ~45% effective tax rate
        
        return True
    
    @staticmethod
    def validate_pan_tan_consistency(employee_pan: str, employer_tan: str) -> bool:
        """Validate PAN and TAN are properly formatted"""
        pan_valid = PatternMatcher.is_valid_pan(employee_pan) if employee_pan else True
        tan_valid = PatternMatcher.is_valid_tan(employer_tan) if employer_tan else True
        
        return pan_valid and tan_valid
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
        """Validate date range is logical"""
        if not start_date or not end_date:
            return True  # Missing dates are not invalid
        
        # End date should be after start date
        if end_date <= start_date:
            return False
        
        # Should not be more than 2 years apart
        days_diff = (end_date - start_date).days
        return days_diff <= 730  # ~2 years