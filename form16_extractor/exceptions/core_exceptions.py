#!/usr/bin/env python3
"""
Form16 Extractor Exception Classes
==================================

Comprehensive error handling for production Form16 extraction.
Staff Software Engineer approach to graceful error handling and recovery.
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for graduated response"""
    LOW = "low"           # Non-critical, partial data available
    MEDIUM = "medium"     # Some functionality lost, most data available  
    HIGH = "high"         # Significant functionality lost, basic data available
    CRITICAL = "critical" # Complete failure, no usable data


class Form16ExtractionError(Exception):
    """Base exception for Form16 extraction errors with enhanced context"""
    
    def __init__(
        self, 
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        partial_data: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.severity = severity
        self.error_code = error_code
        self.context = context or {}
        self.partial_data = partial_data or {}
        self.recovery_suggestions = recovery_suggestions or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to detailed dictionary for logging/monitoring"""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "severity": self.severity.value,
            "error_code": self.error_code,
            "context": self.context,
            "partial_data_available": bool(self.partial_data),
            "recovery_suggestions": self.recovery_suggestions
        }


class PDFProcessingError(Form16ExtractionError):
    """PDF processing and table extraction errors"""
    
    def __init__(self, message: str, pdf_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.pdf_path = pdf_path
        self.context.update({"pdf_path": pdf_path})


class TableClassificationError(Form16ExtractionError):
    """Table classification and structure analysis errors"""
    
    def __init__(
        self, 
        message: str, 
        table_index: Optional[int] = None,
        table_shape: Optional[tuple] = None,
        page_number: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.table_index = table_index
        self.table_shape = table_shape
        self.page_number = page_number
        self.context.update({
            "table_index": table_index,
            "table_shape": table_shape, 
            "page_number": page_number
        })


class FieldExtractionError(Form16ExtractionError):
    """Field extraction and data parsing errors"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        extractor_component: Optional[str] = None,
        extraction_strategy: Optional[str] = None,
        confidence_score: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.extractor_component = extractor_component
        self.extraction_strategy = extraction_strategy
        self.confidence_score = confidence_score
        self.context.update({
            "field_name": field_name,
            "extractor_component": extractor_component,
            "extraction_strategy": extraction_strategy,
            "confidence_score": confidence_score
        })


class DataValidationError(Form16ExtractionError):
    """Data validation and consistency check errors"""
    
    def __init__(
        self,
        message: str,
        validation_rule: Optional[str] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.validation_rule = validation_rule
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.context.update({
            "validation_rule": validation_rule,
            "expected_value": expected_value,
            "actual_value": actual_value
        })


class ComponentInitializationError(Form16ExtractionError):
    """Component initialization and configuration errors"""
    
    def __init__(
        self,
        message: str,
        component_name: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.component_name = component_name
        self.config_key = config_key
        self.context.update({
            "component_name": component_name,
            "config_key": config_key
        })


class ExtractionTimeoutError(Form16ExtractionError):
    """Extraction timeout and performance errors"""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        self.context.update({
            "timeout_seconds": timeout_seconds,
            "operation": operation
        })


# Common error codes for monitoring and alerting
class ErrorCodes:
    """Standardized error codes for production monitoring"""
    
    # PDF Processing (P001-P099)
    PDF_CORRUPT = "P001"
    PDF_ENCRYPTED = "P002" 
    PDF_NO_TABLES = "P003"
    PDF_UNSUPPORTED_VERSION = "P004"
    
    # Table Classification (T001-T099)
    TABLE_UNCLASSIFIABLE = "T001"
    TABLE_MALFORMED = "T002"
    TABLE_INSUFFICIENT_DATA = "T003"
    
    # Field Extraction (F001-F199)
    FIELD_NOT_FOUND = "F001"
    FIELD_AMBIGUOUS = "F002"
    FIELD_INVALID_FORMAT = "F003"
    
    # Employee fields (F001-F049)
    EMPLOYEE_NAME_NOT_FOUND = "F011"
    EMPLOYEE_PAN_INVALID = "F012"
    EMPLOYEE_DESIGNATION_MISSING = "F013"
    
    # Salary fields (F050-F099)
    SALARY_GROSS_MISSING = "F051"
    SALARY_BASIC_MISSING = "F052"
    SALARY_AMOUNTS_INCONSISTENT = "F053"
    
    # TDS fields (F100-F149)  
    TDS_QUARTERLY_MISSING = "F101"
    TDS_RECEIPT_INVALID = "F102"
    TDS_AMOUNT_MISMATCH = "F103"
    
    # Tax Computation (F150-F199)
    TAX_COMPUTATION_MISSING = "F151"
    TAX_LIABILITY_INVALID = "F152"
    TAX_CALCULATION_INCONSISTENT = "F153"
    
    # Data Validation (V001-V099)
    VALIDATION_CROSS_CHECK_FAILED = "V001"
    VALIDATION_CONSISTENCY_FAILED = "V002"
    VALIDATION_FORMAT_INVALID = "V003"
    
    # System/Configuration (S001-S099)
    CONFIG_INVALID = "S001"
    COMPONENT_INIT_FAILED = "S002"
    TIMEOUT_EXCEEDED = "S003"


def create_recovery_suggestions(error_code: str) -> List[str]:
    """Generate contextual recovery suggestions based on error code"""
    
    recovery_map = {
        ErrorCodes.PDF_CORRUPT: [
            "Try re-downloading or re-scanning the PDF",
            "Use alternative PDF reader tools",
            "Check if PDF is password protected"
        ],
        ErrorCodes.EMPLOYEE_NAME_NOT_FOUND: [
            "Check if document is a valid Form16",
            "Try manual extraction from header sections", 
            "Verify document orientation and quality"
        ],
        ErrorCodes.TDS_QUARTERLY_MISSING: [
            "Verify document contains Part A with quarterly details",
            "Check if document is summary-only format",
            "Look for TDS details in separate challan documents"
        ],
        ErrorCodes.SALARY_AMOUNTS_INCONSISTENT: [
            "Cross-validate with tax computation section",
            "Check for calculation errors in source document",
            "Verify currency formatting and decimal places"
        ]
    }
    
    return recovery_map.get(error_code, [
        "Review document quality and format",
        "Try alternative extraction strategies", 
        "Contact support with document sample"
    ])