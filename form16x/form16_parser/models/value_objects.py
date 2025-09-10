#!/usr/bin/env python3
"""
Value Objects for Form16 Data
=============================

Implements domain-specific value objects with validation:
- PAN (Permanent Account Number)
- TAN (Tax Deduction Account Number)  
- Amount (Currency handling)
- DateRange (Period validation)
"""

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Union
from dataclasses import dataclass


@dataclass(frozen=True)
class PAN:
    """
    PAN (Permanent Account Number) value object
    
    Format: AAAAA9999A (5 letters + 4 digits + 1 letter)
    Example: ABCDE1234F
    """
    value: str
    
    def __post_init__(self):
        if not self.is_valid(self.value):
            raise ValueError(f"Invalid PAN format: {self.value}")
    
    @staticmethod
    def is_valid(pan: str) -> bool:
        """Validate PAN format"""
        if not pan or len(pan) != 10:
            return False
        return bool(re.match(r'^[A-Z]{5}\d{4}[A-Z]$', pan.upper()))
    
    @classmethod
    def from_string(cls, pan_str: Optional[str]) -> Optional['PAN']:
        """Create PAN from string, return None if invalid"""
        if not pan_str:
            return None
        
        pan_str = pan_str.strip().upper()
        if cls.is_valid(pan_str):
            return cls(pan_str)
        return None
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TAN:
    """
    TAN (Tax Deduction Account Number) value object
    
    Format: AAAA99999A (4 letters + 5 digits + 1 letter)
    Example: ABCD12345E
    """
    value: str
    
    def __post_init__(self):
        if not self.is_valid(self.value):
            raise ValueError(f"Invalid TAN format: {self.value}")
    
    @staticmethod
    def is_valid(tan: str) -> bool:
        """Validate TAN format"""
        if not tan or len(tan) != 10:
            return False
        return bool(re.match(r'^[A-Z]{4}\d{5}[A-Z]$', tan.upper()))
    
    @classmethod
    def from_string(cls, tan_str: Optional[str]) -> Optional['TAN']:
        """Create TAN from string, return None if invalid"""
        if not tan_str:
            return None
        
        tan_str = tan_str.strip().upper()
        if cls.is_valid(tan_str):
            return cls(tan_str)
        return None
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Amount:
    """
    Amount value object with currency handling
    
    Handles:
    - INR currency
    - Decimal precision
    - Validation (non-negative)
    - String parsing from various formats
    """
    value: Decimal
    currency: str = "INR"
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Amount cannot be negative: {self.value}")
    
    @classmethod
    def from_string(cls, amount_str: Union[str, int, float]) -> Optional['Amount']:
        """
        Create Amount from string with flexible parsing
        
        Handles formats like:
        - "150000.00"
        - "Rs. 150000"
        - "INR 1,50,000.00" 
        - "150000"
        - 150000.0
        """
        if amount_str is None:
            return None
        
        try:
            # Handle numeric types
            if isinstance(amount_str, (int, float)):
                return cls(Decimal(str(amount_str)))
            
            # Clean string input
            clean_str = str(amount_str).strip()
            if not clean_str or clean_str.lower() in ['nan', 'none', '']:
                return None
            
            # Remove currency symbols and separators
            clean_str = re.sub(r'[^\d\.]', '', clean_str)
            
            if not clean_str:
                return None
            
            # Convert to Decimal
            decimal_value = Decimal(clean_str)
            return cls(decimal_value)
            
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def zero(cls) -> 'Amount':
        """Create zero amount"""
        return cls(Decimal('0'))
    
    def __str__(self) -> str:
        return f"{self.currency} {self.value:,.2f}"
    
    def __add__(self, other: 'Amount') -> 'Amount':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} + {other.currency}")
        return Amount(self.value + other.value, self.currency)
    
    def __sub__(self, other: 'Amount') -> 'Amount':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} - {other.currency}")
        return Amount(self.value - other.value, self.currency)
    
    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Amount':
        return Amount(self.value * Decimal(str(multiplier)), self.currency)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Amount):
            return False
        return self.value == other.value and self.currency == other.currency
    
    def __lt__(self, other: 'Amount') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} vs {other.currency}")
        return self.value < other.value


@dataclass(frozen=True)
class DateRange:
    """
    Date range value object for employment periods, financial years, etc.
    
    Handles:
    - Date validation
    - Period validation (from < to)
    - Financial year periods
    - String parsing
    """
    from_date: date
    to_date: date
    
    def __post_init__(self):
        if self.from_date >= self.to_date:
            raise ValueError(f"Invalid date range: {self.from_date} to {self.to_date}")
    
    @classmethod
    def from_strings(cls, from_str: str, to_str: str, date_format: str = "%d-%b-%Y") -> Optional['DateRange']:
        """
        Create DateRange from string dates
        
        Args:
            from_str: Start date string (e.g., "01-Apr-2021")
            to_str: End date string (e.g., "31-Mar-2022")  
            date_format: Date format pattern
            
        Returns:
            DateRange object or None if parsing fails
        """
        try:
            from_date = datetime.strptime(from_str.strip(), date_format).date()
            to_date = datetime.strptime(to_str.strip(), date_format).date()
            return cls(from_date, to_date)
        except (ValueError, AttributeError):
            return None
    
    @classmethod
    def financial_year(cls, year: int) -> 'DateRange':
        """
        Create DateRange for financial year
        
        Args:
            year: Starting year of financial year (e.g., 2021 for FY 2021-22)
            
        Returns:
            DateRange from 1st April to 31st March
        """
        from_date = date(year, 4, 1)  # 1st April
        to_date = date(year + 1, 3, 31)  # 31st March next year
        return cls(from_date, to_date)
    
    def duration_days(self) -> int:
        """Get duration in days"""
        return (self.to_date - self.from_date).days + 1
    
    def duration_months(self) -> int:
        """Get approximate duration in months"""
        return ((self.to_date.year - self.from_date.year) * 12 + 
                (self.to_date.month - self.from_date.month))
    
    def contains(self, check_date: date) -> bool:
        """Check if date falls within this range"""
        return self.from_date <= check_date <= self.to_date
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another"""
        return (self.from_date <= other.to_date and 
                other.from_date <= self.to_date)
    
    def __str__(self) -> str:
        return f"{self.from_date.strftime('%d-%b-%Y')} to {self.to_date.strftime('%d-%b-%Y')}"


@dataclass(frozen=True)
class FinancialYear:
    """
    Financial Year value object
    
    Handles Indian financial year format (Apr to Mar)
    """
    start_year: int
    
    def __post_init__(self):
        if self.start_year < 1950 or self.start_year > 2100:
            raise ValueError(f"Invalid financial year: {self.start_year}")
    
    @property
    def end_year(self) -> int:
        """End year of financial year"""
        return self.start_year + 1
    
    @property
    def date_range(self) -> DateRange:
        """Get DateRange for this financial year"""
        return DateRange.financial_year(self.start_year)
    
    @classmethod
    def from_string(cls, fy_str: str) -> Optional['FinancialYear']:
        """
        Parse financial year from string
        
        Handles formats like:
        - "2021-2022"  
        - "2021-22"
        - "FY 2021-22"
        """
        if not fy_str:
            return None
        
        # Extract year patterns
        years = re.findall(r'20\d{2}', fy_str)
        if len(years) >= 1:
            start_year = int(years[0])
            return cls(start_year)
        
        return None
    
    def __str__(self) -> str:
        return f"FY {self.start_year}-{self.end_year % 100:02d}"


@dataclass(frozen=True) 
class AssessmentYear:
    """
    Assessment Year value object
    
    Assessment year is the year following the financial year
    """
    year: int
    
    def __post_init__(self):
        if self.year < 1951 or self.year > 2101:  # One year after FY range
            raise ValueError(f"Invalid assessment year: {self.year}")
    
    @property
    def financial_year(self) -> FinancialYear:
        """Get corresponding financial year"""
        return FinancialYear(self.year - 1)
    
    @classmethod
    def from_financial_year(cls, fy: FinancialYear) -> 'AssessmentYear':
        """Create assessment year from financial year"""
        return cls(fy.end_year)
    
    def __str__(self) -> str:
        return f"AY {self.year}-{(self.year + 1) % 100:02d}"