"""
Base tax regime implementation with common functionality.
"""

from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from abc import ABC

from ..interfaces.regime_interface import ITaxRegime, TaxSlab, RegimeSettings, TaxSlabCalculation
from ..interfaces.calculator_interface import AgeCategory


class BaseTaxRegime(ITaxRegime, ABC):
    """
    Base implementation of tax regime with common functionality.
    
    Provides shared methods for tax calculations while allowing
    regime-specific customizations through configuration.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize base tax regime with configuration.
        
        Args:
            config: Tax regime configuration dictionary
        """
        self.config = config
        self._tax_slabs_cache = {}
        self._regime_settings = None
    
    def get_tax_slabs(self, age_category: AgeCategory) -> List[TaxSlab]:
        """Get tax slabs for the regime based on age category."""
        if age_category not in self._tax_slabs_cache:
            self._tax_slabs_cache[age_category] = self._build_tax_slabs(age_category)
        
        return self._tax_slabs_cache[age_category]
    
    def _build_tax_slabs(self, age_category: AgeCategory) -> List[TaxSlab]:
        """Build tax slab objects from configuration."""
        slab_config = self.config['tax_slabs'][age_category.value]
        slabs = []
        
        for slab_data in slab_config:
            from_amount = Decimal(str(slab_data['from']))
            to_amount = Decimal(str(slab_data['to'])) if slab_data['to'] is not None else None
            rate = float(slab_data['rate'])
            
            slabs.append(TaxSlab(
                from_amount=from_amount,
                to_amount=to_amount,
                rate_percent=rate
            ))
        
        return slabs
    
    def get_regime_settings(self) -> RegimeSettings:
        """Get regime-specific settings."""
        if self._regime_settings is None:
            self._regime_settings = self._build_regime_settings()
        
        return self._regime_settings
    
    def _build_regime_settings(self) -> RegimeSettings:
        """Build regime settings from configuration."""
        basic_settings = self.config['basic_settings']
        surcharge_config = self.config['surcharge']
        rebate_config = self.config['rebate_87a']
        cess_config = self.config['cess']
        
        # Build age-based exemption limits
        exemption_limits = {}
        for age_str, limit in basic_settings['basic_exemption_limits'].items():
            age_category = AgeCategory(age_str)
            exemption_limits[age_category] = Decimal(str(limit))
        
        return RegimeSettings(
            standard_deduction=Decimal(str(basic_settings['standard_deduction'])),
            basic_exemption_limit=exemption_limits,
            rebate_limit=Decimal(str(rebate_config['income_limit'])),
            rebate_max_amount=Decimal(str(rebate_config['max_rebate'])),
            surcharge_threshold_1=Decimal(str(surcharge_config['threshold_1'])),
            surcharge_rate_1=float(surcharge_config['rate_1']),
            surcharge_threshold_2=Decimal(str(surcharge_config['threshold_2'])),
            surcharge_rate_2=float(surcharge_config['rate_2']),
            surcharge_threshold_3=Decimal(str(surcharge_config.get('threshold_3', 0))),
            surcharge_rate_3=float(surcharge_config.get('rate_3', 0)),
            surcharge_threshold_4=Decimal(str(surcharge_config.get('threshold_4', 0))),
            surcharge_rate_4=float(surcharge_config.get('rate_4', 0)),
            health_education_cess_rate=float(cess_config['health_education_cess_rate']),
            allows_section_80c=self._allows_deduction('section_80c'),
            allows_section_80d=self._allows_deduction('section_80d'),
            allows_hra_exemption=self._allows_exemption('hra'),
            allows_lta_exemption=self._allows_exemption('lta')
        )
    
    def calculate_slab_wise_tax(
        self, 
        taxable_income: Decimal,
        age_category: AgeCategory
    ) -> List[TaxSlabCalculation]:
        """Calculate tax slab-wise for the given income."""
        slabs = self.get_tax_slabs(age_category)
        slab_calculations = []
        remaining_income = taxable_income
        
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            # Calculate taxable amount in this slab
            if slab.to_amount is None:
                # Highest slab - all remaining income
                taxable_in_slab = remaining_income
            else:
                # Limited slab
                slab_width = slab.to_amount - slab.from_amount
                taxable_in_slab = min(remaining_income, slab_width)
            
            # Calculate tax on this slab
            tax_on_slab = self._round_currency(
                taxable_in_slab * Decimal(str(slab.rate_percent / 100))
            )
            
            slab_calculations.append(TaxSlabCalculation(
                slab_from=slab.from_amount,
                slab_to=slab.to_amount,
                rate_percent=slab.rate_percent,
                taxable_amount_in_slab=taxable_in_slab,
                tax_on_slab=tax_on_slab
            ))
            
            remaining_income -= taxable_in_slab
        
        return slab_calculations
    
    def calculate_surcharge(
        self, 
        tax_before_surcharge: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """Calculate surcharge based on income level."""
        settings = self.get_regime_settings()
        
        if total_income <= settings.surcharge_threshold_1:
            return Decimal('0')
        
        surcharge_rate = 0.0
        
        if total_income <= settings.surcharge_threshold_2:
            surcharge_rate = settings.surcharge_rate_1
        elif settings.surcharge_threshold_3 and total_income <= settings.surcharge_threshold_3:
            surcharge_rate = settings.surcharge_rate_2
        elif settings.surcharge_threshold_4 and total_income <= settings.surcharge_threshold_4:
            surcharge_rate = settings.surcharge_rate_3
        else:
            # Use rate_4 for old regime (above 5Cr), or rate_3 for new regime (capped at 25%)
            if settings.surcharge_rate_4:
                surcharge_rate = settings.surcharge_rate_4  # Old regime: 37%
            else:
                surcharge_rate = settings.surcharge_rate_3 or settings.surcharge_rate_2  # New regime: 25%
        
        surcharge = self._round_currency(
            tax_before_surcharge * Decimal(str(surcharge_rate / 100))
        )
        
        # Apply marginal relief if applicable
        surcharge = self._apply_marginal_relief(
            surcharge, tax_before_surcharge, total_income, settings
        )
        
        return surcharge
    
    def calculate_rebate_87a(
        self, 
        tax_before_rebate: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """Calculate rebate under Section 87A."""
        settings = self.get_regime_settings()
        
        if total_income > settings.rebate_limit:
            return Decimal('0')
        
        return min(tax_before_rebate, settings.rebate_max_amount)
    
    def validate_deductions(self, deductions: Dict[str, Decimal]) -> List[str]:
        """Validate that deductions are allowed under this regime."""
        errors = []
        allowed_deductions = set(self.config.get('allowed_deductions', []))
        
        for deduction_type, amount in deductions.items():
            if deduction_type not in allowed_deductions:
                errors.append(f"Deduction {deduction_type} not allowed under this regime")
            
            if amount < 0:
                errors.append(f"Deduction {deduction_type} cannot be negative: {amount}")
        
        return errors
    
    def _allows_deduction(self, deduction_type: str) -> bool:
        """Check if specific deduction is allowed."""
        allowed = self.config.get('allowed_deductions', [])
        return deduction_type in allowed
    
    def _allows_exemption(self, exemption_type: str) -> bool:
        """Check if specific exemption is allowed."""
        allowed = self.config.get('allowed_exemptions', [])
        return exemption_type in allowed
    
    def _apply_marginal_relief(
        self, 
        surcharge: Decimal, 
        tax_before_surcharge: Decimal,
        total_income: Decimal,
        settings: RegimeSettings
    ) -> Decimal:
        """
        Apply marginal relief for surcharge as per Indian tax laws.
        
        Marginal relief ensures that the total additional tax (including surcharge)
        due to crossing the threshold doesn't exceed the excess income over the threshold.
        """
        if total_income <= settings.surcharge_threshold_1:
            return surcharge
        
        # Determine the applicable threshold and rate
        threshold = None
        excess_income = Decimal('0')
        
        if total_income <= settings.surcharge_threshold_2:
            # Income between 50L to 1Cr - 10% surcharge
            threshold = settings.surcharge_threshold_1  # 50L
            excess_income = total_income - threshold
        elif settings.surcharge_threshold_3 and total_income <= settings.surcharge_threshold_3:
            # Income between 1Cr to 2Cr - 15% surcharge  
            threshold = settings.surcharge_threshold_2  # 1Cr
            excess_income = total_income - threshold
        elif hasattr(settings, 'surcharge_threshold_4') and settings.surcharge_threshold_4 and total_income <= settings.surcharge_threshold_4:
            # Income between 2Cr to 5Cr - 25% surcharge
            threshold = settings.surcharge_threshold_3  # 2Cr
            excess_income = total_income - threshold
        else:
            # Income above 5Cr - 25% (new regime) or 37% (old regime)
            if hasattr(settings, 'surcharge_threshold_4') and settings.surcharge_threshold_4:
                threshold = settings.surcharge_threshold_4  # 5Cr
                excess_income = total_income - threshold
            else:
                # Fallback
                threshold = settings.surcharge_threshold_3 or settings.surcharge_threshold_2
                excess_income = total_income - threshold
        
        if not threshold or excess_income <= 0:
            return surcharge
        
        # Calculate tax at threshold (without surcharge)
        # Recalculate tax liability at threshold income
        threshold_slabs = self.get_tax_slabs(AgeCategory.BELOW_60)  # Use default for calculation
        threshold_tax = Decimal('0')
        remaining_threshold = threshold
        
        for slab in threshold_slabs:
            if remaining_threshold <= 0:
                break
                
            if slab.to_amount is None:
                # Highest slab
                taxable_in_slab = remaining_threshold
            else:
                # Limited slab
                slab_width = slab.to_amount - slab.from_amount
                taxable_in_slab = min(remaining_threshold, slab_width)
            
            threshold_tax += taxable_in_slab * Decimal(str(slab.rate_percent / 100))
            remaining_threshold -= taxable_in_slab
        
        # Apply marginal relief formula:
        # Total tax with surcharge should not exceed threshold tax + excess income
        max_total_tax = threshold_tax + excess_income
        total_tax_with_surcharge = tax_before_surcharge + surcharge
        
        if total_tax_with_surcharge > max_total_tax:
            # Apply marginal relief - reduce surcharge
            relief_amount = total_tax_with_surcharge - max_total_tax
            return max(Decimal('0'), surcharge - relief_amount)
        
        return surcharge
    
    def _round_currency(self, amount: Decimal) -> Decimal:
        """Round amount to nearest rupee using banker's rounding."""
        return amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)