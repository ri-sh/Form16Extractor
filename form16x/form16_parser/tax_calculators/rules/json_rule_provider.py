"""
JSON-based tax rule provider implementation.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal
from functools import lru_cache

from ..interfaces.rule_provider_interface import ITaxRuleProvider
from ..interfaces.calculator_interface import TaxRegimeType
from ..engines.old_regime import OldTaxRegime
from ..engines.new_regime import NewTaxRegime


class UnsupportedYearError(Exception):
    """Raised when assessment year is not supported."""
    pass


class UnsupportedRegimeError(Exception):
    """Raised when regime is not supported for the given year."""
    pass


class JsonTaxRuleProvider(ITaxRuleProvider):
    """
    Tax rule provider that loads rules from JSON configuration files.
    
    Supports multi-year tax rules with caching for performance.
    Configuration files are organized by assessment year and regime type.
    """
    
    def __init__(self, config_base_path: Optional[str] = None):
        """
        Initialize the JSON rule provider.
        
        Args:
            config_base_path: Base path for tax rule configuration files.
                            If None, uses package default location.
        """
        if config_base_path is None:
            # Use package's config directory
            package_dir = Path(__file__).parent.parent.parent
            config_base_path = package_dir / "config" / "tax_rules"
        
        self.config_base_path = Path(config_base_path)
        self._rule_cache = {}
        self._validate_config_structure()
    
    def _validate_config_structure(self) -> None:
        """Validate that config directory structure exists."""
        if not self.config_base_path.exists():
            raise FileNotFoundError(f"Tax rules config directory not found: {self.config_base_path}")
        
        if not self.config_base_path.is_dir():
            raise NotADirectoryError(f"Tax rules config path is not a directory: {self.config_base_path}")
    
    @lru_cache(maxsize=32)
    def _load_rule_config(self, assessment_year: str, regime_type: TaxRegimeType) -> Dict:
        """
        Load tax rule configuration from JSON file with caching.
        
        Args:
            assessment_year: Assessment year (e.g., '2024-25')
            regime_type: Tax regime type
            
        Returns:
            Dictionary containing tax rule configuration
            
        Raises:
            UnsupportedYearError: If year directory doesn't exist
            UnsupportedRegimeError: If regime file doesn't exist
        """
        year_dir = self.config_base_path / f"ay_{assessment_year.replace('-', '_')}"
        if not year_dir.exists():
            raise UnsupportedYearError(f"Assessment year {assessment_year} not supported")
        
        regime_file = year_dir / f"{regime_type.value}_regime.json"
        if not regime_file.exists():
            raise UnsupportedRegimeError(
                f"Regime {regime_type.value} not supported for year {assessment_year}"
            )
        
        try:
            with open(regime_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate required fields
            self._validate_config_format(config, assessment_year, regime_type)
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {regime_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading config from {regime_file}: {e}")
    
    def _validate_config_format(self, config: Dict, assessment_year: str, regime_type: TaxRegimeType) -> None:
        """Validate that config has required structure."""
        required_fields = ['assessment_year', 'regime_type', 'tax_slabs', 'surcharge', 'rebate_87a', 'cess']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' in config for {assessment_year} {regime_type.value}")
        
        # Validate assessment year matches
        if config['assessment_year'] != assessment_year:
            raise ValueError(
                f"Config assessment year {config['assessment_year']} doesn't match requested {assessment_year}"
            )
        
        # Validate regime type matches
        if config['regime_type'] != regime_type.value:
            raise ValueError(
                f"Config regime type {config['regime_type']} doesn't match requested {regime_type.value}"
            )
    
    def get_tax_regime(self, assessment_year: str, regime_type: TaxRegimeType):
        """Get tax regime implementation for specific year and type."""
        config = self._load_rule_config(assessment_year, regime_type)
        
        if regime_type == TaxRegimeType.OLD:
            return OldTaxRegime(config)
        elif regime_type == TaxRegimeType.NEW:
            return NewTaxRegime(config)
        else:
            raise UnsupportedRegimeError(f"Unknown regime type: {regime_type}")
    
    def get_deduction_limits(self, assessment_year: str, regime_type: TaxRegimeType) -> Dict[str, Decimal]:
        """Get deduction limits for specific year and regime."""
        config = self._load_rule_config(assessment_year, regime_type)
        deduction_limits = config.get('deduction_limits', {})
        
        # Convert to Decimal for precision
        return {
            section: Decimal(str(limit)) 
            for section, limit in deduction_limits.items()
        }
    
    def get_exemption_limits(self, assessment_year: str) -> Dict[str, Dict[str, Decimal]]:
        """Get exemption limits under Section 10."""
        # Try to load from new regime first (more current), fallback to old
        try:
            config = self._load_rule_config(assessment_year, TaxRegimeType.NEW)
        except UnsupportedRegimeError:
            config = self._load_rule_config(assessment_year, TaxRegimeType.OLD)
        
        exemption_limits = config.get('exemption_limits', {})
        
        # Convert numeric values to Decimal
        converted_limits = {}
        for category, limits in exemption_limits.items():
            if isinstance(limits, dict):
                converted_limits[category] = {
                    key: Decimal(str(value)) if isinstance(value, (int, float)) else value
                    for key, value in limits.items()
                }
            else:
                converted_limits[category] = limits
        
        return converted_limits
    
    def get_supported_years(self) -> List[str]:
        """Get list of supported assessment years."""
        supported_years = []
        
        for year_dir in self.config_base_path.iterdir():
            if year_dir.is_dir() and year_dir.name.startswith('ay_'):
                # Convert ay_2024_25 to 2024-25
                year = year_dir.name[3:].replace('_', '-')
                supported_years.append(year)
        
        return sorted(supported_years)
    
    def is_regime_supported(self, assessment_year: str, regime_type: TaxRegimeType) -> bool:
        """Check if regime is supported for given assessment year."""
        try:
            self._load_rule_config(assessment_year, regime_type)
            return True
        except (UnsupportedYearError, UnsupportedRegimeError):
            return False
    
    def get_default_regime(self, assessment_year: str) -> TaxRegimeType:
        """Get default tax regime for assessment year."""
        # Check if new regime config marks itself as default
        try:
            new_config = self._load_rule_config(assessment_year, TaxRegimeType.NEW)
            if new_config.get('is_default', False):
                return TaxRegimeType.NEW
        except UnsupportedRegimeError:
            pass
        
        # Check if old regime exists and is marked as default
        try:
            old_config = self._load_rule_config(assessment_year, TaxRegimeType.OLD)
            if old_config.get('is_default', False):
                return TaxRegimeType.OLD
        except UnsupportedRegimeError:
            pass
        
        # Default fallback logic based on year
        # From AY 2024-25 onwards, new regime is generally default
        year_start = int(assessment_year.split('-')[0])
        if year_start >= 2024:
            return TaxRegimeType.NEW
        else:
            return TaxRegimeType.OLD
    
    def refresh_rules(self) -> None:
        """Refresh tax rules from configuration source."""
        # Clear the LRU cache to force reload of config files
        self._load_rule_config.cache_clear()
        self._rule_cache.clear()