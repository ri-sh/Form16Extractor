"""
Simple hardcoded tax calculator for common assessment years.

This calculator provides basic tax calculations without requiring external
configuration files, making it more reliable for production use.
"""

from decimal import Decimal
from typing import Dict, Any, List
from .interfaces.calculator_interface import TaxRegimeType, AgeCategory


class SimpleTaxCalculator:
    """Simple hardcoded tax calculator for common scenarios."""
    
    def calculate_tax_both_regimes(
        self,
        gross_salary: Decimal,
        section_80c: Decimal = Decimal('0'),
        section_80ccd_1b: Decimal = Decimal('0'),
        tds_paid: Decimal = Decimal('0'),
        assessment_year: str = '2024-25'
    ) -> Dict[str, Any]:
        """
        Calculate tax for both old and new regimes.
        
        Args:
            gross_salary: Annual gross salary
            section_80c: Section 80C deductions (max 1.5L)
            section_80ccd_1b: Section 80CCD(1B) NPS deductions (max 50K)
            tds_paid: TDS already deducted
            assessment_year: Assessment year
            
        Returns:
            Dictionary with tax calculation results for both regimes
        """
        # Standard deduction (available in both regimes)
        standard_deduction = Decimal('50000')  # AY 2024-25
        
        # Old regime calculation
        old_taxable = gross_salary - standard_deduction - section_80c - section_80ccd_1b
        old_tax = self._calculate_old_regime_tax(old_taxable)
        
        # New regime calculation (limited deductions)
        new_taxable = gross_salary - standard_deduction - section_80ccd_1b  # Only NPS allowed
        new_tax = self._calculate_new_regime_tax(new_taxable)
        
        return {
            'results': {
                'old': {
                    'gross_salary': float(gross_salary),
                    'taxable_income': float(old_taxable),
                    'tax_liability': old_tax,
                    'tds_paid': float(tds_paid),
                    'balance': float(tds_paid) - old_tax,
                    'effective_tax_rate': (old_tax / float(gross_salary) * 100) if gross_salary > 0 else 0
                },
                'new': {
                    'gross_salary': float(gross_salary),
                    'taxable_income': float(new_taxable),
                    'tax_liability': new_tax,
                    'tds_paid': float(tds_paid),
                    'balance': float(tds_paid) - new_tax,
                    'effective_tax_rate': (new_tax / float(gross_salary) * 100) if gross_salary > 0 else 0
                }
            },
            'comparison': {
                'savings_with_new': max(0, old_tax - new_tax),
                'recommended_regime': 'new' if new_tax < old_tax else 'old'
            },
            'recommendation': f"{'NEW' if new_tax < old_tax else 'OLD'} regime saves ₹{abs(old_tax - new_tax):,.0f} annually"
        }
    
    def _calculate_old_regime_tax(self, taxable_income: Decimal) -> int:
        """Calculate tax under old regime for AY 2024-25."""
        tax = Decimal('0')
        
        # Old regime slabs for AY 2024-25
        if taxable_income <= 250000:
            tax = 0
        elif taxable_income <= 500000:
            tax = (taxable_income - 250000) * Decimal('0.05')
        elif taxable_income <= 1000000:
            tax = 12500 + (taxable_income - 500000) * Decimal('0.20')
        else:
            tax = 112500 + (taxable_income - 1000000) * Decimal('0.30')
        
        # Add 4% Health and Education Cess
        tax = tax * Decimal('1.04')
        
        # Rebate under section 87A (for income up to 5L)
        if taxable_income <= 500000:
            rebate = min(tax, 12500)
            tax = tax - rebate
        
        return int(tax)
    
    def _calculate_new_regime_tax(self, taxable_income: Decimal) -> int:
        """Calculate tax under new regime for AY 2024-25."""
        tax = Decimal('0')
        
        # New regime slabs for AY 2024-25
        if taxable_income <= 300000:
            tax = 0
        elif taxable_income <= 600000:
            tax = (taxable_income - 300000) * Decimal('0.05')
        elif taxable_income <= 900000:
            tax = 15000 + (taxable_income - 600000) * Decimal('0.10')
        elif taxable_income <= 1200000:
            tax = 45000 + (taxable_income - 900000) * Decimal('0.15')
        elif taxable_income <= 1500000:
            tax = 90000 + (taxable_income - 1200000) * Decimal('0.20')
        else:
            tax = 150000 + (taxable_income - 1500000) * Decimal('0.30')
        
        # Add 4% Health and Education Cess
        tax = tax * Decimal('1.04')
        
        # Rebate under section 87A (for income up to 7L in new regime)
        if taxable_income <= 700000:
            rebate = min(tax, 25000)
            tax = tax - rebate
        
        return int(tax)