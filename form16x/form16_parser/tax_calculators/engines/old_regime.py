"""
Old tax regime implementation.
"""

from typing import Dict, List
from decimal import Decimal

from .base_regime import BaseTaxRegime


class OldTaxRegime(BaseTaxRegime):
    """
    Implementation of the old tax regime.
    
    Supports all traditional deductions under sections 80C, 80D, etc.
    and exemptions under Section 10 (HRA, LTA, etc.).
    """
    
    def __init__(self, config: Dict):
        """Initialize old tax regime with configuration."""
        super().__init__(config)
        self.deduction_limits = self._load_deduction_limits()
    
    def _load_deduction_limits(self) -> Dict[str, Decimal]:
        """Load deduction limits from configuration."""
        limits = {}
        deduction_config = self.config.get('deduction_limits', {})
        
        for section, limit in deduction_config.items():
            limits[section] = Decimal(str(limit))
        
        return limits
    
    def get_deduction_limit(self, section: str) -> Decimal:
        """
        Get deduction limit for specific section.
        
        Args:
            section: Deduction section (e.g., 'section_80c')
            
        Returns:
            Maximum deduction limit for the section
        """
        return self.deduction_limits.get(section, Decimal('0'))
    
    def validate_deductions(self, deductions: Dict[str, Decimal]) -> List[str]:
        """Validate deductions against old regime rules and limits."""
        errors = super().validate_deductions(deductions)
        
        # Check individual section limits
        for section, amount in deductions.items():
            limit = self.get_deduction_limit(section)
            if limit > 0 and amount > limit:
                errors.append(
                    f"Deduction {section} exceeds limit: {amount} > {limit}"
                )
        
        # Check combined limits (80C + 80CCC + 80CCD(1))
        combined_sections = ['section_80c', 'section_80ccc', 'section_80ccd_1']
        combined_amount = sum(
            deductions.get(section, Decimal('0')) 
            for section in combined_sections
        )
        combined_limit = Decimal('150000')  # Standard combined limit
        
        if combined_amount > combined_limit:
            errors.append(
                f"Combined 80C+80CCC+80CCD(1) exceeds limit: {combined_amount} > {combined_limit}"
            )
        
        return errors
    
    def calculate_standard_deduction(self, salary_income: Decimal) -> Decimal:
        """
        Calculate standard deduction for old regime.
        
        Args:
            salary_income: Gross salary income
            
        Returns:
            Standard deduction amount (capped at regime limit)
        """
        settings = self.get_regime_settings()
        return min(salary_income, settings.standard_deduction)
    
    def calculate_hra_exemption(
        self, 
        hra_received: Decimal,
        basic_salary: Decimal,
        rent_paid: Decimal,
        is_metro_city: bool = False
    ) -> Decimal:
        """
        Calculate HRA exemption under Section 10(13A).
        
        Args:
            hra_received: HRA component of salary
            basic_salary: Basic salary amount
            rent_paid: Annual rent paid
            is_metro_city: Whether employee works in metro city
            
        Returns:
            HRA exemption amount (minimum of three calculations)
        """
        if not self._allows_exemption('hra'):
            return Decimal('0')
        
        # Three calculations as per IT rules
        exemption_1 = hra_received
        
        # 50% for metro, 40% for non-metro
        percentage = Decimal('0.50') if is_metro_city else Decimal('0.40')
        exemption_2 = basic_salary * percentage
        
        # Rent paid minus 10% of basic salary
        exemption_3 = max(Decimal('0'), rent_paid - (basic_salary * Decimal('0.10')))
        
        # HRA exemption is minimum of the three
        return min(exemption_1, exemption_2, exemption_3)
    
    def calculate_professional_tax_deduction(self, professional_tax_paid: Decimal) -> Decimal:
        """
        Calculate professional tax deduction.
        
        Args:
            professional_tax_paid: Professional tax paid during the year
            
        Returns:
            Deductible professional tax amount
        """
        # Professional tax is fully deductible in old regime
        return professional_tax_paid