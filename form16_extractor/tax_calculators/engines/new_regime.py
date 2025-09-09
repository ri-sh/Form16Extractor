"""
New tax regime implementation.
"""

from typing import Dict, List
from decimal import Decimal

from .base_regime import BaseTaxRegime


class NewTaxRegime(BaseTaxRegime):
    """
    Implementation of the new tax regime (Section 115BAC).
    
    Features lower tax rates but restricts most deductions and exemptions.
    Only allows standard deduction and specific exemptions.
    """
    
    def __init__(self, config: Dict):
        """Initialize new tax regime with configuration."""
        super().__init__(config)
        self.restricted_deductions = set(config.get('restricted_deductions', []))
    
    def validate_deductions(self, deductions: Dict[str, Decimal]) -> List[str]:
        """Validate deductions against new regime restrictions."""
        errors = super().validate_deductions(deductions)
        
        # Check for restricted deductions
        for deduction_type, amount in deductions.items():
            if deduction_type in self.restricted_deductions and amount > 0:
                errors.append(
                    f"Deduction {deduction_type} not allowed under new tax regime"
                )
        
        return errors
    
    def calculate_standard_deduction(self, salary_income: Decimal) -> Decimal:
        """
        Calculate standard deduction for new regime.
        
        Args:
            salary_income: Gross salary income
            
        Returns:
            Standard deduction amount (capped at regime limit)
        """
        settings = self.get_regime_settings()
        return min(salary_income, settings.standard_deduction)
    
    def get_allowed_exemptions(self) -> List[str]:
        """
        Get list of exemptions allowed under new regime.
        
        Returns:
            List of allowed exemption types
        """
        return self.config.get('allowed_exemptions', [])
    
    def is_exemption_allowed(self, exemption_type: str) -> bool:
        """
        Check if specific exemption is allowed under new regime.
        
        Args:
            exemption_type: Type of exemption to check
            
        Returns:
            True if exemption is allowed, False otherwise
        """
        return exemption_type in self.get_allowed_exemptions()
    
    def calculate_rebate_87a(
        self, 
        tax_before_rebate: Decimal,
        total_income: Decimal
    ) -> Decimal:
        """
        Calculate rebate under Section 87A for new regime.
        
        New regime has higher rebate limit compared to old regime.
        """
        return super().calculate_rebate_87a(tax_before_rebate, total_income)
    
    def get_tax_benefit_vs_old_regime(
        self, 
        total_income: Decimal,
        old_regime_tax: Decimal,
        new_regime_tax: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate tax benefit of choosing new regime over old regime.
        
        Args:
            total_income: Total income amount
            old_regime_tax: Tax calculated under old regime
            new_regime_tax: Tax calculated under new regime
            
        Returns:
            Dictionary with benefit analysis
        """
        benefit = old_regime_tax - new_regime_tax
        benefit_percentage = (benefit / total_income) * 100 if total_income > 0 else Decimal('0')
        
        return {
            'absolute_benefit': benefit,
            'percentage_benefit': benefit_percentage,
            'recommended_regime': 'new' if benefit > 0 else 'old',
            'old_regime_tax': old_regime_tax,
            'new_regime_tax': new_regime_tax
        }