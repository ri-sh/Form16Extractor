"""
Interface definitions for Form16 consolidation system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ...models.form16_models import Form16Data


class ConsolidationMode(Enum):
    """Modes for consolidation processing."""
    STRICT = "strict"          # Fail on any validation errors
    PERMISSIVE = "permissive"  # Continue with warnings
    AUTO = "auto"              # Auto-detect best mode


@dataclass
class ConsolidationConfig:
    """Configuration for Form16 consolidation."""
    
    # Processing mode
    mode: ConsolidationMode = ConsolidationMode.AUTO
    
    # Validation settings
    allow_duplicate_deductions: bool = False
    max_tds_variance_percent: float = 5.0
    require_form26as_validation: bool = False
    
    # Aggregation settings
    consolidate_quarterly_data: bool = True
    detect_employment_gaps: bool = True
    
    # Tolerance settings
    amount_tolerance: float = 1.0  # Rupees
    date_tolerance_days: int = 7
    
    # Advanced settings
    enable_ml_duplicate_detection: bool = False
    confidence_threshold: float = 0.8


@dataclass 
class ConsolidationResult:
    """Result of consolidation operation."""
    
    success: bool
    employee_pan: str
    financial_year: str
    
    # Aggregated data
    total_salary: float
    total_tds: float
    total_deductions: Dict[str, float]
    
    # Source information
    source_count: int
    employer_names: List[str]
    
    # Quality metrics
    confidence_score: float
    validation_errors: List[str]
    validation_warnings: List[str]
    
    # Detailed breakdowns
    employer_breakdown: Dict[str, Dict[str, Any]]
    quarterly_breakdown: Dict[str, Dict[str, Any]]
    
    # Processing metadata
    processing_time_ms: float
    timestamp: str


class IForm16Consolidator(ABC):
    """
    Interface for Form16 consolidation implementations.
    
    Defines the contract for consolidating multiple Form16s
    from different employers for the same employee and FY.
    """
    
    @abstractmethod
    def consolidate(
        self, 
        form16_list: List[Form16Data],
        config: Optional[ConsolidationConfig] = None
    ) -> ConsolidationResult:
        """
        Consolidate multiple Form16s into a single result.
        
        Args:
            form16_list: List of Form16 data to consolidate
            config: Optional configuration for consolidation process
            
        Returns:
            ConsolidationResult with aggregated data and validation results
            
        Raises:
            ConsolidationError: If consolidation fails critically
            ValidationError: If validation fails in strict mode
        """
        pass
    
    @abstractmethod
    def validate_consistency(
        self, 
        form16_list: List[Form16Data]
    ) -> List[str]:
        """
        Validate consistency across multiple Form16s.
        
        Args:
            form16_list: List of Form16 data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def detect_duplicates(
        self, 
        form16_list: List[Form16Data]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect potential duplicate deductions across Form16s.
        
        Args:
            form16_list: List of Form16 data to analyze
            
        Returns:
            Dictionary mapping deduction types to lists of potential duplicates
        """
        pass