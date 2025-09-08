#!/usr/bin/env python3
"""
Base Extraction Interfaces
==========================

Common interfaces for all Form16 data extractors to ensure
consistent behavior and return formats across the system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeVar, Generic
from dataclasses import dataclass
import pandas as pd

# Generic type for extraction results
T = TypeVar('T')


@dataclass
class ExtractionResult(Generic[T]):
    """
    Standard result container for all extractors
    
    Provides consistent interface for extraction results with:
    - Extracted data of type T
    - Confidence scores per field
    - Processing metadata
    - Error information if any
    """
    data: T
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any]
    success: bool = True
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ValidationResult:
    """
    Standard result container for validation operations
    
    Provides consistent interface for validation results with:
    - Overall validation success status
    - Field-level validation results
    - Error messages and warnings
    """
    is_valid: bool
    field_results: Dict[str, bool]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IExtractor(ABC, Generic[T]):
    """
    Abstract base interface for all Form16 data extractors
    
    Ensures consistent interface across all extractor implementations:
    - Employee extractor
    - Employer extractor  
    - Salary extractor
    - Tax extractor
    - etc.
    """
    
    @abstractmethod
    def extract(self, tables: List[pd.DataFrame]) -> T:
        """
        Extract data from Form16 tables
        
        Args:
            tables: List of pandas DataFrames containing Form16 table data
            
        Returns:
            Extracted data object of type T
        """
        pass
    
    @abstractmethod
    def extract_with_confidence(self, tables: List[pd.DataFrame]) -> ExtractionResult[T]:
        """
        Extract data with confidence scores and metadata
        
        Args:
            tables: List of pandas DataFrames containing Form16 table data
            
        Returns:
            ExtractionResult containing data, confidence scores, and metadata
        """
        pass
    
    @abstractmethod
    def get_extractor_name(self) -> str:
        """
        Get human-readable name of this extractor
        
        Returns:
            Name string (e.g., "Employee Information Extractor")
        """
        pass
    
    @abstractmethod
    def get_supported_fields(self) -> List[str]:
        """
        Get list of fields this extractor can extract
        
        Returns:
            List of field names (e.g., ["name", "pan", "address"])
        """
        pass
    
    def validate_input(self, tables: List[pd.DataFrame]) -> ValidationResult:
        """
        Validate input tables before extraction
        
        Args:
            tables: List of pandas DataFrames to validate
            
        Returns:
            ValidationResult indicating if input is valid
        """
        # Default implementation - can be overridden by specific extractors
        errors = []
        warnings = []
        
        if not tables:
            errors.append("No tables provided for extraction")
        
        empty_tables = sum(1 for table in tables if table.empty)
        if empty_tables == len(tables):
            errors.append("All provided tables are empty")
        elif empty_tables > 0:
            warnings.append(f"{empty_tables}/{len(tables)} tables are empty")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results={},
            errors=errors,
            warnings=warnings,
            metadata={
                "total_tables": len(tables),
                "empty_tables": empty_tables
            }
        )


class IValidator(ABC):
    """
    Abstract base interface for data validation
    
    Provides consistent validation interface for:
    - PAN format validation
    - TAN format validation
    - Amount range validation
    - Cross-field validation
    """
    
    @abstractmethod
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate a value with optional context
        
        Args:
            value: Value to validate
            context: Optional context information for validation
            
        Returns:
            ValidationResult with validation outcome
        """
        pass
    
    @abstractmethod
    def get_validator_name(self) -> str:
        """
        Get human-readable name of this validator
        
        Returns:
            Name string (e.g., "PAN Format Validator")
        """
        pass


class IRepository(ABC, Generic[T]):
    """
    Abstract base interface for data storage
    
    For future database integration when needed.
    Currently deferred as not required for Phase 2-3.
    """
    
    @abstractmethod
    def save(self, data: T) -> bool:
        """Save data to storage"""
        pass
    
    @abstractmethod
    def load(self, identifier: str) -> T:
        """Load data from storage"""
        pass
    
    @abstractmethod
    def exists(self, identifier: str) -> bool:
        """Check if data exists in storage"""
        pass