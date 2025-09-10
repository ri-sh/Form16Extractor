"""
Interface for tax rule providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .regime_interface import ITaxRegime, RegimeSettings
from .calculator_interface import TaxRegimeType, AgeCategory


class ITaxRuleProvider(ABC):
    """
    Interface for tax rule provider implementations.
    
    Provides tax rules, limits, and configurations for different
    assessment years, enabling multi-year support.
    """
    
    @abstractmethod
    def get_tax_regime(
        self, 
        assessment_year: str,
        regime_type: TaxRegimeType
    ) -> ITaxRegime:
        """
        Get tax regime implementation for specific year and type.
        
        Args:
            assessment_year: Assessment year (e.g., '2024-25')
            regime_type: Type of tax regime (old/new)
            
        Returns:
            ITaxRegime implementation
            
        Raises:
            UnsupportedYearError: If assessment year not supported
            UnsupportedRegimeError: If regime not available for year
        """
        pass
    
    @abstractmethod
    def get_deduction_limits(
        self, 
        assessment_year: str,
        regime_type: TaxRegimeType
    ) -> Dict[str, Decimal]:
        """
        Get deduction limits for specific year and regime.
        
        Args:
            assessment_year: Assessment year
            regime_type: Tax regime type
            
        Returns:
            Dictionary mapping deduction sections to limits
        """
        pass
    
    @abstractmethod
    def get_exemption_limits(
        self, 
        assessment_year: str
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get exemption limits under Section 10.
        
        Args:
            assessment_year: Assessment year
            
        Returns:
            Dictionary mapping exemption types to limits by category
        """
        pass
    
    @abstractmethod
    def get_supported_years(self) -> List[str]:
        """
        Get list of supported assessment years.
        
        Returns:
            List of assessment year strings
        """
        pass
    
    @abstractmethod
    def is_regime_supported(
        self, 
        assessment_year: str,
        regime_type: TaxRegimeType
    ) -> bool:
        """
        Check if regime is supported for given assessment year.
        
        Args:
            assessment_year: Assessment year to check
            regime_type: Regime type to check
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    @abstractmethod
    def get_default_regime(self, assessment_year: str) -> TaxRegimeType:
        """
        Get default tax regime for assessment year.
        
        Args:
            assessment_year: Assessment year
            
        Returns:
            Default regime type for the year
        """
        pass
    
    @abstractmethod
    def refresh_rules(self) -> None:
        """
        Refresh tax rules from configuration source.
        
        This method should reload rules from the configuration
        system to pick up any updates.
        """
        pass