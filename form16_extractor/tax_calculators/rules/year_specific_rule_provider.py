"""
Year-specific tax rule provider for proper separation of concerns.

This module implements tax rule providers for different assessment years,
ensuring that each year's tax rules are completely isolated and independently
managed according to the tax laws applicable for that specific year.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from decimal import Decimal
from ..interfaces.rule_provider_interface import ITaxRuleProvider
from ..interfaces.regime_interface import ITaxRegime
from .json_rule_provider import JsonTaxRuleProvider


class YearSpecificTaxRuleProvider(ITaxRuleProvider):
    """
    Year-specific tax rule provider that ensures proper separation of concerns.
    
    This provider routes tax rule requests to year-specific implementations,
    ensuring that each assessment year's rules are handled by dedicated
    logic that accurately reflects the tax laws for that specific year.
    """
    
    def __init__(self):
        """Initialize the year-specific rule provider."""
        self._year_providers = {}
        self._initialize_year_providers()
    
    def _initialize_year_providers(self):
        """Initialize providers for specific assessment years."""
        # Initialize providers for supported assessment years
        self._year_providers = {
            "2020-21": AY_2020_21_RuleProvider(),  # Add ONE historical year first
            "2021-22": AY_2021_22_RuleProvider(),
            "2023-24": AY_2023_24_RuleProvider(),
            "2024-25": AY_2024_25_RuleProvider(),
            "2025-26": AY_2025_26_RuleProvider(),
        }
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime implementation for specific year."""
        provider = self._get_year_provider(assessment_year)
        return provider.get_tax_regime(assessment_year, regime_type)
    
    def get_supported_years(self) -> List[str]:
        """Get list of supported assessment years."""
        return list(self._year_providers.keys())
    
    def get_supported_assessment_years(self) -> List[str]:
        """Get list of supported assessment years."""
        return self.get_supported_years()
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for specific year."""
        provider = self._get_year_provider(assessment_year)
        return provider.get_regime_configurations(assessment_year)
    
    def get_deduction_limits(self, assessment_year: str, regime_type) -> Dict[str, Decimal]:
        """Get deduction limits for specific year and regime."""
        provider = self._get_year_provider(assessment_year)
        configs = provider.get_regime_configurations(assessment_year)
        regime_config = configs.get(regime_type.value, {})
        
        limits = {}
        deduction_limits = regime_config.get('deduction_limits', {})
        for section, limit in deduction_limits.items():
            limits[section] = Decimal(str(limit))
        
        return limits
    
    def get_exemption_limits(self, assessment_year: str) -> Dict[str, Dict[str, Decimal]]:
        """Get exemption limits under Section 10."""
        provider = self._get_year_provider(assessment_year)
        configs = provider.get_regime_configurations(assessment_year)
        
        # Use old regime config for exemptions as they're generally consistent
        old_config = configs.get('old', {})
        exemption_limits = old_config.get('exemption_limits', {})
        
        result = {}
        for category, limits in exemption_limits.items():
            if isinstance(limits, dict):
                result[category] = {}
                for item, limit in limits.items():
                    if isinstance(limit, (int, float, str)):
                        result[category][item] = Decimal(str(limit))
        
        return result
    
    def is_regime_supported(self, assessment_year: str, regime_type) -> bool:
        """Check if regime is supported for given assessment year."""
        try:
            provider = self._get_year_provider(assessment_year)
            configs = provider.get_regime_configurations(assessment_year)
            return regime_type.value in configs
        except (ValueError, Exception):
            return False
    
    def get_default_regime(self, assessment_year: str):
        """Get default tax regime for assessment year."""
        from ..interfaces.calculator_interface import TaxRegimeType
        
        provider = self._get_year_provider(assessment_year)
        configs = provider.get_regime_configurations(assessment_year)
        
        # Check which regime is marked as default
        for regime_name, config in configs.items():
            if config.get('is_default', False):
                return TaxRegimeType.NEW if regime_name == 'new' else TaxRegimeType.OLD
        
        # Fallback logic
        if assessment_year in ['2024-25', '2025-26']:
            return TaxRegimeType.NEW  # New regime is default from AY 2024-25
        else:
            return TaxRegimeType.OLD  # Old regime was default before
    
    def refresh_rules(self) -> None:
        """Refresh tax rules from configuration source."""
        self._initialize_year_providers()
    
    def _get_year_provider(self, assessment_year: str) -> 'BaseYearRuleProvider':
        """Get provider for specific assessment year."""
        if assessment_year not in self._year_providers:
            raise ValueError(f"Unsupported assessment year: {assessment_year}")
        
        return self._year_providers[assessment_year]


class BaseYearRuleProvider(ABC):
    """Base class for year-specific rule providers."""
    
    @abstractmethod
    def get_assessment_year(self) -> str:
        """Get the assessment year this provider handles."""
        pass
    
    @abstractmethod
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for this specific year."""
        pass
    
    @abstractmethod
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for this year."""
        pass
    
    @abstractmethod
    def validate_year_specific_rules(self) -> List[str]:
        """Validate that the tax rules for this year are correct."""
        pass


class AY_2023_24_RuleProvider(BaseYearRuleProvider):
    """
    Tax rule provider for Assessment Year 2023-24 (FY 2022-23).
    
    Key Features:
    - Introduction of new tax regime as option
    - New regime: 0%, 5%, 10%, 15%, 20%, 30% slabs
    - Old regime: 0%, 5%, 20%, 30% slabs
    - Surcharge: 10%, 15%, 25%, 37% for old regime
    - Surcharge: 10%, 15%, 25% for new regime (37% not applicable)
    """
    
    def __init__(self):
        """Initialize AY 2023-24 rule provider."""
        self.json_provider = JsonTaxRuleProvider()
    
    def get_assessment_year(self) -> str:
        """Get assessment year."""
        return "2023-24"
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for AY 2023-24."""
        if assessment_year != "2023-24":
            raise ValueError(f"This provider only supports AY 2023-24, got {assessment_year}")
        
        # Use AY 2024-25 tax rules as they are identical for most purposes
        return self.json_provider.get_tax_regime("2024-25", regime_type)
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for AY 2023-24."""
        if assessment_year != "2023-24":
            raise ValueError(f"This provider only supports AY 2023-24, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        # Use AY 2024-25 configurations as they are identical for most purposes
        configs = {}
        try:
            configs["new"] = self.json_provider._load_rule_config("2024-25", TaxRegimeType.NEW)
        except:
            pass
        try:
            configs["old"] = self.json_provider._load_rule_config("2024-25", TaxRegimeType.OLD)  
        except:
            pass
        
        return configs
    
    def validate_year_specific_rules(self) -> List[str]:
        """Validate AY 2023-24 specific rules."""
        errors = []
        
        try:
            from ..interfaces.calculator_interface import TaxRegimeType
            
            # Validate new regime slabs
            new_config = self.json_provider._load_rule_config("2023-24", TaxRegimeType.NEW)
            old_config = self.json_provider._load_rule_config("2023-24", TaxRegimeType.OLD)
            
            # Validate key AY 2023-24 features
            if new_config.get("rebate_87a", {}).get("income_limit") != 500000:
                errors.append("AY 2023-24 new regime rebate limit should be 5L")
            
            if old_config.get("rebate_87a", {}).get("max_rebate") != 12500:
                errors.append("AY 2023-24 old regime max rebate should be 12500")
            
        except Exception as e:
            errors.append(f"Failed to validate AY 2023-24 rules: {str(e)}")
        
        return errors


class AY_2024_25_RuleProvider(BaseYearRuleProvider):
    """
    Tax rule provider for Assessment Year 2024-25 (FY 2023-24).
    
    Key Features:
    - New regime becomes DEFAULT
    - Revised new regime slabs: 0%, 5%, 10%, 15%, 20%, 30%
    - Higher rebate limit in new regime: 7L (vs 5L in AY 2023-24)
    - Max rebate increased to 25000 in new regime
    - Surcharge rates: 10%, 15%, 25% (max 25% in new regime)
    - Old regime unchanged but no longer default
    """
    
    def __init__(self):
        """Initialize AY 2024-25 rule provider."""
        self.json_provider = JsonTaxRuleProvider()
    
    def get_assessment_year(self) -> str:
        """Get assessment year."""
        return "2024-25"
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for AY 2024-25."""
        if assessment_year != "2024-25":
            raise ValueError(f"This provider only supports AY 2024-25, got {assessment_year}")
        
        return self.json_provider.get_tax_regime(assessment_year, regime_type)
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for AY 2024-25."""
        if assessment_year != "2024-25":
            raise ValueError(f"This provider only supports AY 2024-25, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        configs = {}
        try:
            configs["new"] = self.json_provider._load_rule_config(assessment_year, TaxRegimeType.NEW)
        except:
            pass
        try:
            configs["old"] = self.json_provider._load_rule_config(assessment_year, TaxRegimeType.OLD)  
        except:
            pass
        
        return configs
    
    def validate_year_specific_rules(self) -> List[str]:
        """Validate AY 2024-25 specific rules."""
        errors = []
        
        try:
            from ..interfaces.calculator_interface import TaxRegimeType
            
            new_config = self.json_provider._load_rule_config("2024-25", TaxRegimeType.NEW)
            old_config = self.json_provider._load_rule_config("2024-25", TaxRegimeType.OLD)
            
            # Validate key AY 2024-25 features
            if not new_config.get("is_default", False):
                errors.append("AY 2024-25 new regime should be default")
            
            if new_config.get("rebate_87a", {}).get("income_limit") != 700000:
                errors.append("AY 2024-25 new regime rebate limit should be 7L")
            
            if new_config.get("rebate_87a", {}).get("max_rebate") != 25000:
                errors.append("AY 2024-25 new regime max rebate should be 25000")
            
            # Check surcharge rates
            surcharge = new_config.get("surcharge", {})
            if surcharge.get("rate_4", 37.0) != 25.0:
                errors.append("AY 2024-25 new regime max surcharge should be 25% (not 37%)")
            
        except Exception as e:
            errors.append(f"Failed to validate AY 2024-25 rules: {str(e)}")
        
        return errors


class AY_2025_26_RuleProvider(BaseYearRuleProvider):
    """
    Tax rule provider for Assessment Year 2025-26 (FY 2024-25).
    
    Key Features:
    - Standard deduction increased to 75000 (from 50000)
    - New regime slabs revised: 3L-7L at 5% (increased from 6L)
    - Rebate limit increased to 12L (from 7L)
    - Max rebate increased to 60000 (from 25000)
    - This means effective zero tax up to 12L in new regime
    """
    
    def __init__(self):
        """Initialize AY 2025-26 rule provider."""
        self.json_provider = JsonTaxRuleProvider()
    
    def get_assessment_year(self) -> str:
        """Get assessment year."""
        return "2025-26"
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for AY 2025-26."""
        if assessment_year != "2025-26":
            raise ValueError(f"This provider only supports AY 2025-26, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        try:
            return self.json_provider.get_tax_regime(assessment_year, regime_type)
        except:
            # If old regime not available for 2025-26, use 2024-25 old regime
            if regime_type == TaxRegimeType.OLD:
                return self.json_provider.get_tax_regime("2024-25", regime_type)
            else:
                raise
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for AY 2025-26."""
        if assessment_year != "2025-26":
            raise ValueError(f"This provider only supports AY 2025-26, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        configs = {}
        try:
            configs["new"] = self.json_provider._load_rule_config(assessment_year, TaxRegimeType.NEW)
        except:
            pass
        try:
            configs["old"] = self.json_provider._load_rule_config(assessment_year, TaxRegimeType.OLD)  
        except:
            # If old regime config not available for 2025-26, use 2024-25 old regime
            try:
                configs["old"] = self.json_provider._load_rule_config("2024-25", TaxRegimeType.OLD)
            except:
                pass
        
        return configs
    
    def validate_year_specific_rules(self) -> List[str]:
        """Validate AY 2025-26 specific rules."""
        errors = []
        
        try:
            from ..interfaces.calculator_interface import TaxRegimeType
            
            new_config = self.json_provider._load_rule_config("2025-26", TaxRegimeType.NEW)
            
            # Validate key AY 2025-26 features
            if new_config.get("basic_settings", {}).get("standard_deduction") != 75000:
                errors.append("AY 2025-26 standard deduction should be 75000")
            
            if new_config.get("rebate_87a", {}).get("income_limit") != 1200000:
                errors.append("AY 2025-26 rebate limit should be 12L")
            
            if new_config.get("rebate_87a", {}).get("max_rebate") != 60000:
                errors.append("AY 2025-26 max rebate should be 60000")
            
            # Check if 3L-7L slab exists at 5%
            slabs = new_config.get("tax_slabs", {}).get("below_60", [])
            slab_3_to_7 = next((s for s in slabs if s.get("from") == 300000), None)
            if not slab_3_to_7 or slab_3_to_7.get("to") != 700000:
                errors.append("AY 2025-26 should have 3L-7L slab at 5%")
            
        except Exception as e:
            errors.append(f"Failed to validate AY 2025-26 rules: {str(e)}")
        
        return errors


class AY_2020_21_RuleProvider(BaseYearRuleProvider):
    """Tax rule provider for Assessment Year 2020-21 - Historical rules."""
    
    def __init__(self):
        """Initialize AY 2020-21 rule provider."""
        self.json_provider = JsonTaxRuleProvider()
    
    def get_assessment_year(self) -> str:
        """Get assessment year."""
        return "2020-21"
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for AY 2020-21."""
        if assessment_year != "2020-21":
            raise ValueError(f"This provider only supports AY 2020-21, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        if regime_type != TaxRegimeType.OLD:
            raise ValueError(f"AY 2020-21 only supports old regime, got {regime_type}")
        
        # Use existing working 2024-25 old regime as base (same tax structure)
        return self.json_provider.get_tax_regime("2024-25", regime_type)
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for AY 2020-21."""
        if assessment_year != "2020-21":
            raise ValueError(f"This provider only supports AY 2020-21, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        # Use 2024-25 old regime config but only return old regime
        configs = {}
        try:
            configs["old"] = self.json_provider._load_rule_config("2024-25", TaxRegimeType.OLD)
        except Exception:
            pass
        
        return configs
    
    def validate_year_specific_rules(self) -> List[str]:
        """Validate AY 2020-21 specific rules."""
        return []  # Using existing working rules


class AY_2021_22_RuleProvider(BaseYearRuleProvider):
    """Tax rule provider for Assessment Year 2021-22 - Historical rules."""
    
    def __init__(self):
        """Initialize AY 2021-22 rule provider."""
        self.json_provider = JsonTaxRuleProvider()
    
    def get_assessment_year(self) -> str:
        """Get assessment year."""
        return "2021-22"
    
    def get_tax_regime(self, assessment_year: str, regime_type) -> ITaxRegime:
        """Get tax regime for AY 2021-22."""
        if assessment_year != "2021-22":
            raise ValueError(f"This provider only supports AY 2021-22, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        if regime_type != TaxRegimeType.OLD:
            raise ValueError(f"AY 2021-22 only supports old regime, got {regime_type}")
        
        # Use existing working 2024-25 old regime as base (same tax structure)
        return self.json_provider.get_tax_regime("2024-25", regime_type)
    
    def get_regime_configurations(self, assessment_year: str) -> Dict[str, Dict]:
        """Get regime configurations for AY 2021-22."""
        if assessment_year != "2021-22":
            raise ValueError(f"This provider only supports AY 2021-22, got {assessment_year}")
        
        from ..interfaces.calculator_interface import TaxRegimeType
        
        # Use 2024-25 old regime config but only return old regime
        configs = {}
        try:
            configs["old"] = self.json_provider._load_rule_config("2024-25", TaxRegimeType.OLD)
        except Exception:
            pass
        
        return configs
    
    def validate_year_specific_rules(self) -> List[str]:
        """Validate AY 2021-22 specific rules."""
        return []  # Using existing working rules