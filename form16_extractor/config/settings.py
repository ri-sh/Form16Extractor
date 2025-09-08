#!/usr/bin/env python3
"""
Configuration Settings
======================

Environment-based configuration for Form16 extractor.
Supports different settings for development, testing, and production.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing" 
    PRODUCTION = "production"


@dataclass
class ExtractionSettings:
    """Settings for PDF and data extraction"""
    
    # PDF Processing
    extraction_timeout_seconds: int = 120
    max_table_extraction_retries: int = 3
    confidence_threshold: float = 0.5
    
    # Extraction Strategies (ordered by preference)
    preferred_strategies: list = None
    
    # Performance
    max_concurrent_extractions: int = 1
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    
    def __post_init__(self):
        if self.preferred_strategies is None:
            self.preferred_strategies = [
                "camelot_lattice",
                "camelot_stream", 
                "tabula_lattice",
                "pdfplumber",
                "fallback"
            ]


@dataclass
class ValidationSettings:
    """Settings for data validation"""
    
    # Validation strictness
    enable_strict_validation: bool = False
    enable_business_rule_validation: bool = True
    enable_cross_field_validation: bool = True
    
    # Amount validation
    min_salary_amount: float = 0.0
    max_salary_amount: float = 100000000.0  # 10 crores
    
    # Date validation
    min_financial_year: int = 2000
    max_financial_year: int = 2030


@dataclass
class OutputSettings:
    """Settings for output generation"""
    
    # JSON output
    include_null_fields: bool = True
    include_confidence_scores: bool = True
    include_extraction_metadata: bool = True
    pretty_print_json: bool = True
    
    # File output
    default_output_format: str = "json"
    create_backup_files: bool = False


@dataclass
class LoggingSettings:
    """Settings for logging configuration"""
    
    # Logging levels
    log_level: str = "INFO"
    enable_file_logging: bool = True
    log_file_path: Optional[str] = None
    max_log_file_size_mb: int = 10
    log_retention_days: int = 30
    
    # Log format
    enable_structured_logging: bool = False
    include_timestamp: bool = True
    include_process_info: bool = False


class Settings:
    """Main settings class with environment-based configuration"""
    
    def __init__(self, environment: Optional[Environment] = None):
        self.environment = environment or self._detect_environment()
        self.project_root = Path(__file__).parent.parent.parent
        
        # Load settings based on environment
        self.extraction = ExtractionSettings()
        self.validation = ValidationSettings()
        self.output = OutputSettings()
        self.logging = LoggingSettings()
        
        # Apply environment-specific overrides
        self._apply_environment_settings()
        self._load_from_env_vars()
    
    def _detect_environment(self) -> Environment:
        """Auto-detect environment from ENV vars"""
        env_str = os.getenv("FORM16_ENV", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            return Environment.DEVELOPMENT
    
    def _apply_environment_settings(self):
        """Apply environment-specific setting overrides"""
        
        if self.environment == Environment.DEVELOPMENT:
            # Development: More verbose, less strict
            self.logging.log_level = "DEBUG"
            self.validation.enable_strict_validation = False
            self.output.pretty_print_json = True
            self.extraction.enable_caching = False
            
        elif self.environment == Environment.TESTING:
            # Testing: Minimal output, strict validation
            self.logging.log_level = "WARNING"
            self.logging.enable_file_logging = False
            self.validation.enable_strict_validation = True
            self.output.pretty_print_json = False
            self.extraction.enable_caching = False
            
        elif self.environment == Environment.PRODUCTION:
            # Production: Optimized for performance
            self.logging.log_level = "INFO"
            self.logging.enable_file_logging = True
            self.validation.enable_strict_validation = False
            self.output.pretty_print_json = False
            self.extraction.enable_caching = True
            self.extraction.max_concurrent_extractions = 2
    
    def _load_from_env_vars(self):
        """Load settings from environment variables"""
        
        # Extraction settings
        if timeout := os.getenv("FORM16_EXTRACTION_TIMEOUT"):
            self.extraction.extraction_timeout_seconds = int(timeout)
        
        if threshold := os.getenv("FORM16_CONFIDENCE_THRESHOLD"):
            self.extraction.confidence_threshold = float(threshold)
        
        # Validation settings  
        if os.getenv("FORM16_STRICT_VALIDATION", "").lower() == "true":
            self.validation.enable_strict_validation = True
        
        # Logging settings
        if log_level := os.getenv("FORM16_LOG_LEVEL"):
            self.logging.log_level = log_level.upper()
        
        if log_file := os.getenv("FORM16_LOG_FILE"):
            self.logging.log_file_path = log_file
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        return self.project_root / "data"
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory path"""
        return self.project_root / "logs"
    
    @property
    def cache_dir(self) -> Path:
        """Get cache directory path"""
        return self.project_root / ".cache"
    
    def get_log_file_path(self) -> Path:
        """Get full log file path"""
        if self.logging.log_file_path:
            return Path(self.logging.log_file_path)
        
        self.logs_dir.mkdir(exist_ok=True)
        return self.logs_dir / f"form16_extractor_{self.environment.value}.log"
    
    def create_directories(self):
        """Create necessary directories"""
        for directory in [self.data_dir, self.logs_dir, self.cache_dir]:
            directory.mkdir(exist_ok=True)


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings


def reset_settings():
    """Reset global settings (useful for testing)"""
    global _settings
    _settings = None