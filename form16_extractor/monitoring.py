#!/usr/bin/env python3
"""
Form16 Extractor Monitoring & Logging System
============================================

Comprehensive logging, metrics collection, and monitoring for production Form16 extraction.
Implements structured logging, performance tracking, and extraction analytics.
"""

import logging
import time
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import sys
from pathlib import Path


class LogLevel(Enum):
    """Structured log levels with specific semantics"""
    TRACE = "trace"       # Detailed execution flow
    DEBUG = "debug"       # Development debugging
    INFO = "info"         # General information
    WARN = "warn"         # Warnings that don't stop processing
    ERROR = "error"       # Errors that might stop current operation
    CRITICAL = "critical" # Critical errors that stop entire system


class MetricType(Enum):
    """Types of metrics we collect"""
    COUNTER = "counter"           # Incrementing values (requests, errors)
    GAUGE = "gauge"               # Current values (processing time, confidence)
    HISTOGRAM = "histogram"       # Distribution of values
    TIMER = "timer"              # Time-based measurements


@dataclass
class ExtractionMetrics:
    """Structured metrics for a single extraction operation"""
    
    # Operation identifiers
    operation_id: str
    pdf_path: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Processing metrics
    total_processing_time: Optional[float] = None
    table_extraction_time: Optional[float] = None
    classification_time: Optional[float] = None
    field_extraction_time: Optional[float] = None
    
    # Data metrics
    tables_processed: int = 0
    tables_classified: int = 0
    fields_extracted: int = 0
    fields_attempted: int = 0
    
    # Quality metrics
    avg_classification_confidence: Optional[float] = None
    avg_extraction_confidence: Optional[float] = None
    
    # Success metrics
    success: bool = False
    errors_count: int = 0
    warnings_count: int = 0
    critical_errors_count: int = 0
    
    # Component-specific metrics
    component_success_rates: Dict[str, float] = field(default_factory=dict)
    component_processing_times: Dict[str, float] = field(default_factory=dict)
    component_confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Memory and resource usage
    peak_memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/storage"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass 
class SystemMetrics:
    """Aggregated system-wide metrics over time windows"""
    
    # Time window
    window_start: datetime
    window_end: datetime
    window_duration_minutes: float
    
    # Volume metrics
    total_extractions: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    # Performance metrics
    avg_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    max_processing_time: float = 0.0
    p95_processing_time: float = 0.0
    
    # Quality metrics
    avg_extraction_confidence: float = 0.0
    avg_classification_confidence: float = 0.0
    
    # Error metrics
    total_errors: int = 0
    total_warnings: int = 0
    critical_errors: int = 0
    error_rate: float = 0.0
    
    # Component performance
    component_success_rates: Dict[str, float] = field(default_factory=dict)
    component_avg_confidence: Dict[str, float] = field(default_factory=dict)
    
    # Resource utilization
    avg_memory_usage: Optional[float] = None
    peak_memory_usage: Optional[float] = None
    
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_extractions == 0:
            return 0.0
        return (self.successful_extractions / self.total_extractions) * 100


class StructuredLogger:
    """
    Production-grade structured logger with context tracking.
    
    Features:
    - JSON-structured logging for machine processing
    - Context preservation across extraction operations  
    - Automatic field enrichment (timestamps, operation IDs)
    - Multiple output destinations (console, file, monitoring systems)
    - Log level filtering and sampling
    """
    
    def __init__(
        self,
        name: str = "form16_extractor",
        level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        file_path: Optional[Path] = None,
        enable_metrics: bool = True,
        max_context_size: int = 1000
    ):
        self.name = name
        self.level = level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_metrics = enable_metrics
        self.max_context_size = max_context_size
        
        # Setup underlying logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value.upper()))
        
        # Setup handlers
        self._setup_handlers(file_path)
        
        # Context tracking
        self._context = threading.local()
        
        # Metrics collection
        if enable_metrics:
            self.metrics_collector = MetricsCollector()
        
    def _setup_handlers(self, file_path: Optional[Path]):
        """Setup logging handlers for console and file output"""
        
        # Create formatter for structured JSON logging
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file:
            if file_path is None:
                file_path = Path("logs") / "form16_extractor.log"
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def with_context(self, **context) -> 'ContextLogger':
        """Create a context-aware logger with additional fields"""
        return ContextLogger(self, context)
    
    def log(self, level: LogLevel, message: str, **extra_fields):
        """Core structured logging method"""
        
        # Build structured log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'logger': self.name,
            'message': message,
            **extra_fields
        }
        
        # Add context if available
        if hasattr(self._context, 'fields'):
            log_entry.update(self._context.fields)
        
        # Map our log levels to Python logging levels
        level_mapping = {
            LogLevel.TRACE: logging.DEBUG,  # TRACE maps to DEBUG
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        log_level = level_mapping[level]
        
        # Format as JSON for structured logging
        formatted_message = f"Data: {json.dumps(log_entry, default=str, separators=(',', ':'))}"
        
        self.logger.log(log_level, formatted_message)
        
        # Collect metrics if enabled
        if self.enable_metrics and hasattr(self, 'metrics_collector'):
            self.metrics_collector.record_log_event(level, log_entry)
    
    def trace(self, message: str, **extra):
        """Trace level logging for detailed execution flow"""
        self.log(LogLevel.TRACE, message, **extra)
    
    def debug(self, message: str, **extra):
        """Debug level logging for development"""
        self.log(LogLevel.DEBUG, message, **extra)
    
    def info(self, message: str, **extra):
        """Info level logging for general information"""
        self.log(LogLevel.INFO, message, **extra)
    
    def warn(self, message: str, **extra):
        """Warning level logging"""
        self.log(LogLevel.WARN, message, **extra)
    
    def error(self, message: str, **extra):
        """Error level logging"""
        self.log(LogLevel.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        """Critical level logging"""
        self.log(LogLevel.CRITICAL, message, **extra)


class ContextLogger:
    """Context-aware logger that automatically includes context fields"""
    
    def __init__(self, parent_logger: StructuredLogger, context: Dict[str, Any]):
        self.parent = parent_logger
        self.context = context
    
    def log(self, level: LogLevel, message: str, **extra):
        """Log with automatic context inclusion"""
        combined_fields = {**self.context, **extra}
        self.parent.log(level, message, **combined_fields)
    
    def trace(self, message: str, **extra):
        self.log(LogLevel.TRACE, message, **extra)
    
    def debug(self, message: str, **extra):
        self.log(LogLevel.DEBUG, message, **extra)
    
    def info(self, message: str, **extra):
        self.log(LogLevel.INFO, message, **extra)
    
    def warn(self, message: str, **extra):
        self.log(LogLevel.WARN, message, **extra)
    
    def error(self, message: str, **extra):
        self.log(LogLevel.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        self.log(LogLevel.CRITICAL, message, **extra)
    
    def with_context(self, **additional_context):
        """Add more context to existing context"""
        combined_context = {**self.context, **additional_context}
        return ContextLogger(self.parent, combined_context)


class MetricsCollector:
    """
    High-performance metrics collection for production monitoring.
    
    Features:
    - Thread-safe metric collection
    - Configurable time windows for aggregation
    - Memory-efficient circular buffers
    - Real-time calculation of percentiles and rates
    - Export capabilities for monitoring systems
    """
    
    def __init__(
        self,
        window_size_minutes: int = 60,
        max_samples: int = 10000,
        calculate_percentiles: bool = True
    ):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.max_samples = max_samples
        self.calculate_percentiles = calculate_percentiles
        
        # Thread-safe data structures
        self._lock = threading.Lock()
        
        # Circular buffers for metrics
        self._extraction_metrics: deque = deque(maxlen=max_samples)
        self._log_events: deque = deque(maxlen=max_samples)
        
        # Counters and gauges
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        
        # Processing time samples for percentile calculation  
        self._processing_times: deque = deque(maxlen=max_samples)
        
        # Component-specific metrics
        self._component_metrics: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=1000)))
    
    def record_extraction_metrics(self, metrics: ExtractionMetrics):
        """Record metrics for a single extraction operation"""
        with self._lock:
            self._extraction_metrics.append(metrics)
            
            # Update counters
            self._counters['total_extractions'] += 1
            if metrics.success:
                self._counters['successful_extractions'] += 1
            else:
                self._counters['failed_extractions'] += 1
            
            # Update processing times
            if metrics.total_processing_time:
                self._processing_times.append(metrics.total_processing_time)
            
            # Update component-specific metrics
            for component, success_rate in metrics.component_success_rates.items():
                self._component_metrics[component]['success_rates'].append(success_rate)
            
            for component, processing_time in metrics.component_processing_times.items():
                self._component_metrics[component]['processing_times'].append(processing_time)
            
            for component, confidence in metrics.component_confidence_scores.items():
                self._component_metrics[component]['confidence_scores'].append(confidence)
    
    def record_log_event(self, level: LogLevel, log_entry: Dict[str, Any]):
        """Record a log event for monitoring"""
        with self._lock:
            self._log_events.append({
                'timestamp': datetime.now(),
                'level': level,
                'entry': log_entry
            })
            
            # Update log level counters
            self._counters[f'log_{level.value}'] += 1
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics for the configured time window"""
        with self._lock:
            now = datetime.now()
            window_start = now - self.window_size
            
            # Filter metrics to current window
            current_extractions = [
                m for m in self._extraction_metrics
                if m.timestamp >= window_start
            ]
            
            if not current_extractions:
                return SystemMetrics(
                    window_start=window_start,
                    window_end=now,
                    window_duration_minutes=self.window_size.total_seconds() / 60
                )
            
            # Calculate aggregated metrics
            total_extractions = len(current_extractions)
            successful_extractions = sum(1 for m in current_extractions if m.success)
            failed_extractions = total_extractions - successful_extractions
            
            # Processing time metrics
            processing_times = [m.total_processing_time for m in current_extractions if m.total_processing_time]
            
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
                min_processing_time = min(processing_times)
                max_processing_time = max(processing_times)
                
                if self.calculate_percentiles:
                    sorted_times = sorted(processing_times)
                    p95_index = int(0.95 * len(sorted_times))
                    p95_processing_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_processing_time
                else:
                    p95_processing_time = max_processing_time
            else:
                avg_processing_time = min_processing_time = max_processing_time = p95_processing_time = 0.0
            
            # Quality metrics
            extraction_confidences = []
            classification_confidences = []
            
            for m in current_extractions:
                if m.avg_extraction_confidence:
                    extraction_confidences.append(m.avg_extraction_confidence)
                if m.avg_classification_confidence:
                    classification_confidences.append(m.avg_classification_confidence)
            
            avg_extraction_confidence = sum(extraction_confidences) / len(extraction_confidences) if extraction_confidences else 0.0
            avg_classification_confidence = sum(classification_confidences) / len(classification_confidences) if classification_confidences else 0.0
            
            # Component metrics
            component_success_rates = {}
            component_avg_confidence = {}
            
            for component, metrics in self._component_metrics.items():
                success_rates = list(metrics['success_rates'])
                confidences = list(metrics['confidence_scores'])
                
                if success_rates:
                    component_success_rates[component] = sum(success_rates) / len(success_rates)
                if confidences:
                    component_avg_confidence[component] = sum(confidences) / len(confidences)
            
            # Error metrics  
            total_errors = sum(m.errors_count for m in current_extractions)
            total_warnings = sum(m.warnings_count for m in current_extractions)
            critical_errors = sum(m.critical_errors_count for m in current_extractions)
            error_rate = (total_errors / total_extractions * 100) if total_extractions > 0 else 0.0
            
            return SystemMetrics(
                window_start=window_start,
                window_end=now,
                window_duration_minutes=self.window_size.total_seconds() / 60,
                total_extractions=total_extractions,
                successful_extractions=successful_extractions,
                failed_extractions=failed_extractions,
                avg_processing_time=avg_processing_time,
                min_processing_time=min_processing_time,
                max_processing_time=max_processing_time,
                p95_processing_time=p95_processing_time,
                avg_extraction_confidence=avg_extraction_confidence,
                avg_classification_confidence=avg_classification_confidence,
                total_errors=total_errors,
                total_warnings=total_warnings,
                critical_errors=critical_errors,
                error_rate=error_rate,
                component_success_rates=component_success_rates,
                component_avg_confidence=component_avg_confidence
            )
    
    def export_metrics(self, format: str = "json") -> str:
        """Export current metrics in specified format for external monitoring"""
        current_metrics = self.get_current_metrics()
        
        if format == "json":
            return json.dumps(asdict(current_metrics), default=str, indent=2)
        elif format == "prometheus":
            # Convert to Prometheus format for monitoring systems
            lines = []
            lines.append(f"form16_extraction_total {current_metrics.total_extractions}")
            lines.append(f"form16_extraction_successful {current_metrics.successful_extractions}")
            lines.append(f"form16_extraction_failed {current_metrics.failed_extractions}")
            lines.append(f"form16_processing_time_avg {current_metrics.avg_processing_time}")
            lines.append(f"form16_processing_time_p95 {current_metrics.p95_processing_time}")
            lines.append(f"form16_success_rate {current_metrics.success_rate()}")
            lines.append(f"form16_error_rate {current_metrics.error_rate}")
            
            for component, success_rate in current_metrics.component_success_rates.items():
                lines.append(f'form16_component_success_rate{{component="{component}"}} {success_rate}')
            
            return '\n'.join(lines)
        
        raise ValueError(f"Unsupported export format: {format}")


def create_production_logger(
    name: str = "form16_extractor",
    log_level: str = "INFO",
    enable_metrics: bool = True,
    log_file_path: Optional[str] = None
) -> StructuredLogger:
    """
    Factory function to create production-ready logger.
    
    Args:
        name: Logger name
        log_level: Logging level (TRACE, DEBUG, INFO, WARN, ERROR, CRITICAL)
        enable_metrics: Whether to enable metrics collection
        log_file_path: Optional custom log file path
        
    Returns:
        Configured StructuredLogger instance
    """
    
    level = LogLevel(log_level.lower())
    file_path = Path(log_file_path) if log_file_path else None
    
    return StructuredLogger(
        name=name,
        level=level,
        enable_console=True,
        enable_file=True,
        file_path=file_path,
        enable_metrics=enable_metrics,
        max_context_size=1000
    )