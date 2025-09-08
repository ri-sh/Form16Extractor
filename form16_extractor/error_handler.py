#!/usr/bin/env python3
"""
Form16 Extractor Error Handler
==============================

Centralized error handling and recovery system for production Form16 extraction.
Implements graceful degradation with partial results and comprehensive error reporting.
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    Form16ExtractionError, ErrorSeverity, ErrorCodes,
    PDFProcessingError, TableClassificationError, FieldExtractionError,
    DataValidationError, ExtractionTimeoutError,
    create_recovery_suggestions
)
from .models.form16_models import Form16Document


@dataclass
class ExtractionResult:
    """Complete extraction result with success/failure context"""
    
    success: bool
    document: Optional[Form16Document] = None
    errors: List[Form16ExtractionError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    partial_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: Optional[float] = None
    extraction_confidence: Optional[Dict[str, float]] = None
    
    @property
    def has_partial_data(self) -> bool:
        """Check if any usable data was extracted despite errors"""
        return self.document is not None or bool(self.partial_data)
    
    @property
    def error_summary(self) -> Dict[str, Any]:
        """Generate summary of all errors for monitoring"""
        return {
            "total_errors": len(self.errors),
            "error_severities": [e.severity.value for e in self.errors],
            "error_codes": [e.error_code for e in self.errors if e.error_code],
            "critical_errors": len([e for e in self.errors if e.severity == ErrorSeverity.CRITICAL]),
            "has_recovery_suggestions": any(e.recovery_suggestions for e in self.errors)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for logging/API responses"""
        return {
            "success": self.success,
            "has_partial_data": self.has_partial_data,
            "document": self.document.dict() if self.document else None,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
            "partial_data": self.partial_data,
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "extraction_confidence": self.extraction_confidence,
            "error_summary": self.error_summary
        }


class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies for different failure modes"""
    RETRY_WITH_FALLBACK = "retry_with_fallback"
    PARTIAL_EXTRACTION = "partial_extraction"
    SKIP_COMPONENT = "skip_component"
    FAIL_FAST = "fail_fast"
    LOG_AND_CONTINUE = "log_and_continue"


class ProductionErrorHandler:
    """
    Production-grade error handler with graceful degradation.
    
    Key Features:
    - Contextual error recovery based on error type and severity
    - Partial data preservation when full extraction fails
    - Comprehensive error logging and monitoring support
    - Configurable timeout and retry mechanisms
    - Performance tracking and optimization insights
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 2,
        timeout_seconds: float = 30.0,
        enable_partial_extraction: bool = True,
        enable_performance_tracking: bool = True
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.enable_partial_extraction = enable_partial_extraction
        self.enable_performance_tracking = enable_performance_tracking
        
        # Recovery strategy mapping based on error types
        self.recovery_strategies = {
            PDFProcessingError: ErrorRecoveryStrategy.FAIL_FAST,
            TableClassificationError: ErrorRecoveryStrategy.PARTIAL_EXTRACTION,
            FieldExtractionError: ErrorRecoveryStrategy.LOG_AND_CONTINUE,
            DataValidationError: ErrorRecoveryStrategy.LOG_AND_CONTINUE,
            ExtractionTimeoutError: ErrorRecoveryStrategy.RETRY_WITH_FALLBACK
        }
    
    @contextmanager
    def extraction_context(self, operation_name: str, **context):
        """Context manager for tracking extraction operations with error handling"""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            self.logger.info(f"Starting extraction operation: {operation_name}", extra=context)
            yield errors, warnings
            
        except Form16ExtractionError as e:
            errors.append(e)
            self._handle_known_error(e, operation_name, context)
            
        except Exception as e:
            # Convert unknown errors to Form16ExtractionError
            extraction_error = Form16ExtractionError(
                message=f"Unexpected error in {operation_name}: {str(e)}",
                severity=ErrorSeverity.HIGH,
                error_code=ErrorCodes.COMPONENT_INIT_FAILED,
                context={**context, "operation": operation_name, "traceback": traceback.format_exc()}
            )
            errors.append(extraction_error)
            self._handle_unknown_error(e, operation_name, context)
            
        finally:
            processing_time = time.time() - start_time
            if self.enable_performance_tracking:
                self._track_performance(operation_name, processing_time, errors, **context)
    
    def safe_extract_component(
        self, 
        component_name: str,
        extractor_func: callable,
        *args,
        fallback_value: Any = None,
        required: bool = False,
        **kwargs
    ) -> Tuple[Any, List[Form16ExtractionError], List[str]]:
        """
        Safely extract data using component with comprehensive error handling.
        
        Args:
            component_name: Name of the extraction component
            extractor_func: Function to call for extraction
            *args, **kwargs: Arguments passed to extractor function
            fallback_value: Value to return if extraction fails
            required: Whether this component is required for valid extraction
            
        Returns:
            Tuple of (result, errors, warnings)
        """
        errors = []
        warnings = []
        
        try:
            with self.extraction_context(f"extract_{component_name}") as (ctx_errors, ctx_warnings):
                result = extractor_func(*args, **kwargs)
                
                # Validate result
                if result is None and required:
                    error = FieldExtractionError(
                        message=f"Required component {component_name} returned None",
                        severity=ErrorSeverity.HIGH,
                        error_code=ErrorCodes.FIELD_NOT_FOUND,
                        extractor_component=component_name
                    )
                    errors.append(error)
                    result = fallback_value
                
                errors.extend(ctx_errors)
                warnings.extend(ctx_warnings)
                
                return result, errors, warnings
                
        except Exception as e:
            # Handle component-specific errors
            if isinstance(e, Form16ExtractionError):
                errors.append(e)
            else:
                error = FieldExtractionError(
                    message=f"Component {component_name} failed: {str(e)}",
                    severity=ErrorSeverity.MEDIUM if not required else ErrorSeverity.HIGH,
                    error_code=ErrorCodes.COMPONENT_INIT_FAILED,
                    extractor_component=component_name,
                    context={"traceback": traceback.format_exc()}
                )
                errors.append(error)
            
            # Apply recovery strategy
            strategy = self._get_recovery_strategy(type(e) if isinstance(e, Form16ExtractionError) else FieldExtractionError)
            
            if strategy == ErrorRecoveryStrategy.FAIL_FAST and required:
                raise
            elif strategy == ErrorRecoveryStrategy.PARTIAL_EXTRACTION:
                warnings.append(f"Using fallback value for {component_name} due to extraction failure")
                return fallback_value, errors, warnings
            else:
                # Log and continue with fallback
                self.logger.warning(f"Component {component_name} failed, using fallback", 
                                  exc_info=True, extra={"component": component_name})
                return fallback_value, errors, warnings
    
    def create_extraction_result(
        self,
        document: Optional[Form16Document] = None,
        errors: List[Form16ExtractionError] = None,
        warnings: List[str] = None,
        partial_data: Dict[str, Any] = None,
        processing_time: Optional[float] = None,
        extraction_confidence: Optional[Dict[str, float]] = None
    ) -> ExtractionResult:
        """Create comprehensive extraction result with error analysis"""
        
        errors = errors or []
        warnings = warnings or []
        partial_data = partial_data or {}
        
        # Determine overall success based on error severity
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        success = len(critical_errors) == 0 and (document is not None or bool(partial_data))
        
        # Add metadata about extraction process
        metadata = {
            "extraction_timestamp": time.time(),
            "error_handler_version": "1.0.0",
            "total_components_attempted": len(extraction_confidence) if extraction_confidence else 0,
            "recovery_strategies_applied": len([e for e in errors if e.recovery_suggestions])
        }
        
        return ExtractionResult(
            success=success,
            document=document,
            errors=errors,
            warnings=warnings,
            partial_data=partial_data,
            metadata=metadata,
            processing_time=processing_time,
            extraction_confidence=extraction_confidence
        )
    
    def _handle_known_error(
        self, 
        error: Form16ExtractionError, 
        operation: str, 
        context: Dict[str, Any]
    ):
        """Handle known Form16 extraction errors with appropriate logging"""
        
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"Form16 extraction error in {operation}: {error.message}",
            extra={
                "error_type": type(error).__name__,
                "error_code": error.error_code,
                "severity": error.severity.value,
                "context": {**context, **error.context},
                "recovery_suggestions": error.recovery_suggestions
            }
        )
    
    def _handle_unknown_error(
        self, 
        error: Exception, 
        operation: str, 
        context: Dict[str, Any]
    ):
        """Handle unexpected errors with full context preservation"""
        
        self.logger.error(
            f"Unexpected error in {operation}: {str(error)}",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "operation": operation,
                "context": context,
                "traceback": traceback.format_exc()
            }
        )
    
    def _get_recovery_strategy(self, error_type: type) -> ErrorRecoveryStrategy:
        """Determine recovery strategy based on error type"""
        return self.recovery_strategies.get(error_type, ErrorRecoveryStrategy.LOG_AND_CONTINUE)
    
    def _track_performance(
        self, 
        operation: str, 
        processing_time: float, 
        errors: List[Form16ExtractionError],
        **context
    ):
        """Track performance metrics for monitoring and optimization"""
        
        self.logger.info(
            f"Performance tracking for {operation}",
            extra={
                "operation": operation,
                "processing_time": processing_time,
                "error_count": len(errors),
                "success": len([e for e in errors if e.severity != ErrorSeverity.CRITICAL]) == 0,
                **context
            }
        )