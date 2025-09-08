#!/usr/bin/env python3
"""
Form16 Extractor Configuration Management
=========================================

Comprehensive configuration system for production Form16 extraction.
Supports environment-specific settings, validation, and runtime customization.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union, Type
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
import logging


class ExtractionStrategy(Enum):
    """Available extraction strategies"""
    POSITION_TEMPLATE = "position_template"
    SEMANTIC_SEARCH = "semantic_search"
    ENHANCED_PATTERN_MATCHING = "enhanced_pattern_matching"
    HYBRID = "hybrid"


class LogLevel(Enum):
    """Logging levels"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for different extraction components"""
    
    # Minimum confidence thresholds for accepting results
    employee_name: float = 0.8
    employee_pan: float = 0.9
    employer_info: float = 0.7
    salary_amounts: float = 0.85
    tax_computation: float = 0.8
    deductions: float = 0.75
    quarterly_tds: float = 0.7
    metadata: float = 0.8
    
    # Classification confidence thresholds
    table_classification: float = 0.6
    field_extraction: float = 0.7
    
    # Validation thresholds
    cross_validation: float = 0.9
    consistency_check: float = 0.8
    
    def __post_init__(self):
        """Validate threshold ranges"""
        for field in fields(self):
            value = getattr(self, field.name)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Confidence threshold {field.name} must be between 0.0 and 1.0, got {value}")


@dataclass
class ProcessingLimits:
    """Processing limits and timeouts"""
    
    # Timeout settings (seconds)
    total_extraction_timeout: float = 60.0
    component_timeout: float = 10.0
    table_classification_timeout: float = 5.0
    pdf_processing_timeout: float = 30.0
    
    # Resource limits
    max_tables_per_document: int = 100
    max_pages_per_document: int = 50
    max_memory_usage_mb: int = 512
    max_concurrent_extractions: int = 5
    
    # Retry settings
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    
    def __post_init__(self):
        """Validate limits"""
        if self.total_extraction_timeout <= 0:
            raise ValueError("Total extraction timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


@dataclass
class ExtractionSettings:
    """Extraction behavior configuration"""
    
    # Strategy preferences for each component
    employee_strategy: ExtractionStrategy = ExtractionStrategy.ENHANCED_PATTERN_MATCHING
    employer_strategy: ExtractionStrategy = ExtractionStrategy.ENHANCED_PATTERN_MATCHING  
    salary_strategy: ExtractionStrategy = ExtractionStrategy.POSITION_TEMPLATE
    tax_strategy: ExtractionStrategy = ExtractionStrategy.SEMANTIC_SEARCH
    deductions_strategy: ExtractionStrategy = ExtractionStrategy.POSITION_TEMPLATE
    quarterly_tds_strategy: ExtractionStrategy = ExtractionStrategy.ENHANCED_PATTERN_MATCHING
    metadata_strategy: ExtractionStrategy = ExtractionStrategy.ENHANCED_PATTERN_MATCHING
    
    # Feature toggles
    enable_cross_validation: bool = True
    enable_confidence_boosting: bool = True
    enable_fallback_strategies: bool = True
    enable_partial_extraction: bool = True
    
    # Output preferences
    include_processing_metadata: bool = True
    include_confidence_scores: bool = True
    include_extraction_timestamps: bool = True
    exclude_null_fields: bool = False
    
    # Advanced settings
    strict_validation: bool = False
    enable_experimental_features: bool = False
    debug_mode: bool = False


@dataclass
class LoggingConfig:
    """Logging and monitoring configuration"""
    
    # Log levels
    console_log_level: LogLevel = LogLevel.INFO
    file_log_level: LogLevel = LogLevel.DEBUG
    
    # Output destinations
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    enable_structured_logging: bool = True
    enable_metrics_collection: bool = True
    
    # File settings
    log_file_path: Optional[str] = None  # Default: logs/form16_extractor.log
    log_file_max_size_mb: int = 100
    log_file_backup_count: int = 5
    log_rotation_interval: str = "midnight"  # daily, midnight, or size-based
    
    # Metrics settings
    metrics_window_minutes: int = 60
    enable_prometheus_export: bool = False
    prometheus_port: int = 9090
    
    # Performance tracking
    track_component_performance: bool = True
    track_memory_usage: bool = False
    sample_rate: float = 1.0  # 1.0 = log everything, 0.1 = sample 10%


@dataclass
class Form16ExtractorConfig:
    """Master configuration for Form16 extractor"""
    
    # Core configuration sections
    confidence_thresholds: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)
    processing_limits: ProcessingLimits = field(default_factory=ProcessingLimits)
    extraction_settings: ExtractionSettings = field(default_factory=ExtractionSettings)
    logging_config: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment and deployment
    environment: str = "development"  # development, staging, production
    version: str = "1.0.0"
    deployment_name: str = "default"
    
    # Feature flags
    enable_error_handling: bool = True
    enable_performance_monitoring: bool = True
    enable_health_checks: bool = False
    
    def __post_init__(self):
        """Post-initialization validation"""
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Form16ExtractorConfig':
        """Create configuration from dictionary"""
        
        # Extract nested configurations
        confidence_data = config_dict.get('confidence_thresholds', {})
        limits_data = config_dict.get('processing_limits', {})
        extraction_data = config_dict.get('extraction_settings', {})
        logging_data = config_dict.get('logging_config', {})
        
        # Convert enum values
        if 'extraction_settings' in config_dict:
            extraction_dict = config_dict['extraction_settings'].copy()
            for key, value in extraction_dict.items():
                if key.endswith('_strategy') and isinstance(value, str):
                    try:
                        extraction_dict[key] = ExtractionStrategy(value)
                    except ValueError:
                        pass  # Keep original value if not valid enum
        else:
            extraction_dict = {}
        
        if 'logging_config' in config_dict:
            logging_dict = config_dict['logging_config'].copy()
            for level_field in ['console_log_level', 'file_log_level']:
                if level_field in logging_dict and isinstance(logging_dict[level_field], str):
                    try:
                        logging_dict[level_field] = LogLevel(logging_dict[level_field])
                    except ValueError:
                        pass
        else:
            logging_dict = {}
        
        return cls(
            confidence_thresholds=ConfidenceThresholds(**confidence_data),
            processing_limits=ProcessingLimits(**limits_data),
            extraction_settings=ExtractionSettings(**extraction_dict),
            logging_config=LoggingConfig(**logging_dict),
            environment=config_dict.get('environment', 'development'),
            version=config_dict.get('version', '1.0.0'),
            deployment_name=config_dict.get('deployment_name', 'default'),
            enable_error_handling=config_dict.get('enable_error_handling', True),
            enable_performance_monitoring=config_dict.get('enable_performance_monitoring', True),
            enable_health_checks=config_dict.get('enable_health_checks', False)
        )
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'Form16ExtractorConfig':
        """Load configuration from JSON or YAML file"""
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_environment(cls) -> 'Form16ExtractorConfig':
        """Load configuration from environment variables"""
        
        config_data = {}
        
        # Environment settings
        config_data['environment'] = os.getenv('FORM16_ENVIRONMENT', 'development')
        config_data['deployment_name'] = os.getenv('FORM16_DEPLOYMENT_NAME', 'default')
        
        # Feature flags
        config_data['enable_error_handling'] = os.getenv('FORM16_ENABLE_ERROR_HANDLING', 'true').lower() == 'true'
        config_data['enable_performance_monitoring'] = os.getenv('FORM16_ENABLE_MONITORING', 'true').lower() == 'true'
        
        # Confidence thresholds
        confidence_thresholds = {}
        if os.getenv('FORM16_EMPLOYEE_CONFIDENCE_THRESHOLD'):
            confidence_thresholds['employee_name'] = float(os.getenv('FORM16_EMPLOYEE_CONFIDENCE_THRESHOLD'))
        if os.getenv('FORM16_SALARY_CONFIDENCE_THRESHOLD'):
            confidence_thresholds['salary_amounts'] = float(os.getenv('FORM16_SALARY_CONFIDENCE_THRESHOLD'))
        
        if confidence_thresholds:
            config_data['confidence_thresholds'] = confidence_thresholds
        
        # Processing limits
        processing_limits = {}
        if os.getenv('FORM16_EXTRACTION_TIMEOUT'):
            processing_limits['total_extraction_timeout'] = float(os.getenv('FORM16_EXTRACTION_TIMEOUT'))
        if os.getenv('FORM16_MAX_RETRIES'):
            processing_limits['max_retries'] = int(os.getenv('FORM16_MAX_RETRIES'))
        
        if processing_limits:
            config_data['processing_limits'] = processing_limits
        
        # Logging configuration
        logging_config = {}
        if os.getenv('FORM16_LOG_LEVEL'):
            logging_config['console_log_level'] = os.getenv('FORM16_LOG_LEVEL').lower()
        if os.getenv('FORM16_LOG_FILE'):
            logging_config['log_file_path'] = os.getenv('FORM16_LOG_FILE')
        if os.getenv('FORM16_ENABLE_METRICS'):
            logging_config['enable_metrics_collection'] = os.getenv('FORM16_ENABLE_METRICS', 'true').lower() == 'true'
        
        if logging_config:
            config_data['logging_config'] = logging_config
        
        return cls.from_dict(config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        
        def convert_value(value):
            if isinstance(value, Enum):
                return value.value
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, (list, tuple)):
                return [convert_value(item) for item in value]
            else:
                return value
        
        return convert_value(self)
    
    def save_to_file(self, config_path: Union[str, Path], format: str = 'yaml'):
        """Save configuration to file"""
        
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if format.lower() in ['yaml', 'yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(config_dict, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        
        issues = []
        
        # Check confidence thresholds
        confidence = self.confidence_thresholds
        if confidence.employee_name < 0.5:
            issues.append("Employee name confidence threshold is very low (< 0.5)")
        if confidence.salary_amounts < 0.7:
            issues.append("Salary amounts confidence threshold may be too low for financial data")
        
        # Check processing limits
        limits = self.processing_limits
        if limits.total_extraction_timeout < 10.0:
            issues.append("Total extraction timeout may be too short (< 10s)")
        if limits.max_concurrent_extractions > 10:
            issues.append("High concurrent extraction limit may cause resource issues")
        
        # Environment-specific checks
        if self.environment == 'production':
            if self.extraction_settings.debug_mode:
                issues.append("Debug mode should be disabled in production")
            if self.logging_config.file_log_level.value == 'trace':
                issues.append("Trace logging may be too verbose for production")
        
        return issues
    
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration specific to a component"""
        
        config = {
            'confidence_threshold': getattr(self.confidence_thresholds, f"{component_name}", 0.8),
            'strategy': getattr(self.extraction_settings, f"{component_name}_strategy", ExtractionStrategy.HYBRID),
            'timeout': self.processing_limits.component_timeout,
            'enable_fallback': self.extraction_settings.enable_fallback_strategies,
            'debug_mode': self.extraction_settings.debug_mode
        }
        
        return config


# Predefined configurations for different environments
DEVELOPMENT_CONFIG = Form16ExtractorConfig(
    environment="development",
    confidence_thresholds=ConfidenceThresholds(
        employee_name=0.7,  # Lower thresholds for development
        salary_amounts=0.8,
        table_classification=0.5
    ),
    extraction_settings=ExtractionSettings(
        debug_mode=True,
        enable_experimental_features=True,
        strict_validation=False
    ),
    logging_config=LoggingConfig(
        console_log_level=LogLevel.DEBUG,
        file_log_level=LogLevel.TRACE,
        track_memory_usage=True
    )
)

PRODUCTION_CONFIG = Form16ExtractorConfig(
    environment="production",
    confidence_thresholds=ConfidenceThresholds(
        employee_name=0.85,  # Higher thresholds for production
        salary_amounts=0.9,
        tax_computation=0.85,
        table_classification=0.7
    ),
    processing_limits=ProcessingLimits(
        total_extraction_timeout=45.0,  # Shorter timeout for production
        max_concurrent_extractions=3,   # Conservative concurrency
        max_retries=3
    ),
    extraction_settings=ExtractionSettings(
        debug_mode=False,
        enable_experimental_features=False,
        strict_validation=True,
        enable_cross_validation=True
    ),
    logging_config=LoggingConfig(
        console_log_level=LogLevel.INFO,
        file_log_level=LogLevel.WARN,
        enable_prometheus_export=True,
        sample_rate=0.1  # Sample 10% of logs in production
    ),
    enable_health_checks=True
)


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
    use_env_vars: bool = True
) -> Form16ExtractorConfig:
    """
    Load configuration with priority order:
    1. Explicit config file (if provided)
    2. Environment variables (if use_env_vars=True)
    3. Predefined environment config (if environment specified)
    4. Default development config
    """
    
    # 1. Try explicit config file
    if config_path:
        return Form16ExtractorConfig.from_file(config_path)
    
    # 2. Try environment variables
    if use_env_vars:
        try:
            return Form16ExtractorConfig.from_environment()
        except Exception:
            pass  # Fall back to defaults
    
    # 3. Try predefined environment config
    if environment:
        if environment.lower() == 'production':
            return PRODUCTION_CONFIG
        elif environment.lower() == 'development':
            return DEVELOPMENT_CONFIG
    
    # 4. Default to development config
    return DEVELOPMENT_CONFIG


def create_sample_config(output_path: Union[str, Path], format: str = 'yaml'):
    """Create a sample configuration file with all options documented"""
    
    sample_config = Form16ExtractorConfig(
        environment="production",
        version="1.0.0",
        deployment_name="sample_deployment"
    )
    
    sample_config.save_to_file(output_path, format)
    print(f"Sample configuration saved to: {output_path}")