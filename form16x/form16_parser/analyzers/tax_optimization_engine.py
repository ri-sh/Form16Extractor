"""
Tax Optimization Engine

Analyzes current tax situation and provides actionable optimization suggestions
based on available deduction sections and investment opportunities.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from ..models.salary_breakdown_models import (
    TaxOptimizationAnalysis, TaxOptimizationSuggestion, OptimizationDifficulty
)

logger = logging.getLogger(__name__)


class TaxOptimizationEngine:
    """Engine for analyzing tax optimization opportunities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Current limits for AY 2024-25
        self.deduction_limits = {
            '80C': Decimal('150000'),
            '80CCD_1B': Decimal('50000'),
            '80D': Decimal('25000'),     # Self + family
            '80D_PARENTS': Decimal('25000'),  # Parents (additional)
            '80TTA': Decimal('10000'),   # Savings account interest
            '80EE': Decimal('50000'),    # Home loan interest (first time buyers)
            '80EEA': Decimal('150000'),  # Home loan interest (affordable housing)
        }
        
        # Tax rates for calculating savings (approximate for middle income)
        self.marginal_tax_rates = {
            'old_regime': Decimal('0.30'),  # 30% (including cess)
            'new_regime': Decimal('0.20')   # 20% (average for middle income)
        }
    
    def analyze_optimization_opportunities(
        self, 
        tax_data: Dict[str, Any], 
        form16_data: Dict[str, Any],
        target_savings: Optional[int] = None
    ) -> TaxOptimizationAnalysis:
        """
        Analyze tax data and provide optimization suggestions
        
        Args:
            tax_data: Tax calculation results
            form16_data: Form16 extracted data
            target_savings: Target tax savings amount (optional)
            
        Returns:
            TaxOptimizationAnalysis: Complete optimization analysis
        """
        try:
            # Extract current tax situation
            employee_name = self._extract_employee_name(form16_data)
            current_regime = tax_data.get('recommended_regime', 'new')
            
            regime_data = tax_data.get('regime_comparison', {}).get(f'{current_regime}_regime', {})
            current_tax_liability = Decimal(str(regime_data.get('tax_liability', 0)))
            current_deductions = regime_data.get('deductions_used', {})
            
            # Create analysis object
            analysis = TaxOptimizationAnalysis(
                employee_name=employee_name,
                current_regime=current_regime,
                current_tax_liability=current_tax_liability,
                current_deductions={k: Decimal(str(v)) for k, v in current_deductions.items()}
            )
            
            # Generate suggestions
            suggestions = self._generate_optimization_suggestions(
                current_deductions, current_regime, form16_data, target_savings
            )
            
            for suggestion in suggestions:
                analysis.add_suggestion(suggestion)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing optimization opportunities: {e}")
            raise
    
    def _extract_employee_name(self, form16_data: Dict[str, Any]) -> str:
        """Extract employee name from Form16 data"""
        try:
            return (
                form16_data.get('form16', {})
                .get('part_a', {})
                .get('employee', {})
                .get('name') or 'Employee'
            )
        except:
            return 'Employee'
    
    def _generate_optimization_suggestions(
        self, 
        current_deductions: Dict[str, Any], 
        regime: str,
        form16_data: Dict[str, Any],
        target_savings: Optional[int]
    ) -> List[TaxOptimizationSuggestion]:
        """Generate list of optimization suggestions"""
        
        suggestions = []
        marginal_rate = self.marginal_tax_rates.get(regime, Decimal('0.25'))
        
        # Section 80C suggestions
        suggestions.extend(self._suggest_80c_investments(current_deductions, marginal_rate))
        
        # Section 80D suggestions  
        suggestions.extend(self._suggest_80d_investments(current_deductions, marginal_rate))
        
        # Section 80CCD(1B) suggestions
        suggestions.extend(self._suggest_80ccd_1b_investments(current_deductions, marginal_rate))
        
        # Bank interest optimization (80TTA)
        suggestions.extend(self._suggest_bank_interest_optimization(form16_data, marginal_rate))
        
        # Home loan interest suggestions
        suggestions.extend(self._suggest_home_loan_optimization(current_deductions, marginal_rate))
        
        # Sort by potential savings (highest first)
        suggestions.sort(key=lambda x: x.potential_tax_savings, reverse=True)
        
        # If target savings specified, prioritize to meet target
        if target_savings:
            suggestions = self._prioritize_for_target(suggestions, target_savings)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _suggest_80c_investments(self, current_deductions: Dict, marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest Section 80C investment opportunities"""
        suggestions = []
        
        current_80c = Decimal(str(current_deductions.get('80C', 0)))
        remaining_limit = self.deduction_limits['80C'] - current_80c
        
        if remaining_limit <= 0:
            return suggestions
        
        # PPF investment
        if remaining_limit >= Decimal('50000'):
            suggestions.append(TaxOptimizationSuggestion(
                title="Public Provident Fund (PPF) Investment",
                description="Long-term investment with tax-free returns and 15-year lock-in",
                investment_type="80C Investment",
                suggested_amount=min(remaining_limit, Decimal('150000')),
                potential_tax_savings=min(remaining_limit, Decimal('150000')) * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80C",
                current_utilization=current_80c,
                max_limit=self.deduction_limits['80C'],
                implementation_steps=[
                    "Open PPF account with any nationalized bank",
                    "Set up monthly SIP for consistent investment",
                    "Ensure investment before March 31st for current year benefit"
                ]
            ))
        
        # ELSS Mutual Funds
        if remaining_limit >= Decimal('25000'):
            suggestions.append(TaxOptimizationSuggestion(
                title="Equity Linked Savings Scheme (ELSS)",
                description="Mutual fund investment with 3-year lock-in and potential for higher returns",
                investment_type="80C Investment",
                suggested_amount=min(remaining_limit, Decimal('100000')),
                potential_tax_savings=min(remaining_limit, Decimal('100000')) * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80C",
                current_utilization=current_80c,
                max_limit=self.deduction_limits['80C'],
                implementation_steps=[
                    "Choose reputable fund house (SBI, HDFC, ICICI)",
                    "Start monthly SIP for rupee cost averaging",
                    "Monitor performance quarterly"
                ]
            ))
        
        # Fixed Deposits (5-year)
        if remaining_limit >= Decimal('10000'):
            suggestions.append(TaxOptimizationSuggestion(
                title="Tax-Saving Fixed Deposit",
                description="Safe investment option with guaranteed returns and 5-year lock-in",
                investment_type="80C Investment", 
                suggested_amount=min(remaining_limit, Decimal('50000')),
                potential_tax_savings=min(remaining_limit, Decimal('50000')) * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80C",
                current_utilization=current_80c,
                max_limit=self.deduction_limits['80C'],
                implementation_steps=[
                    "Visit your bank branch or use internet banking",
                    "Choose 5-year tax-saving FD option",
                    "Ensure deposit before March 31st"
                ]
            ))
        
        return suggestions
    
    def _suggest_80d_investments(self, current_deductions: Dict, marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest Section 80D health insurance opportunities"""
        suggestions = []
        
        current_80d = Decimal(str(current_deductions.get('80D', 0)))
        remaining_limit = self.deduction_limits['80D'] - current_80d
        
        if remaining_limit <= 0:
            return suggestions
        
        # Health insurance for self and family
        suggestions.append(TaxOptimizationSuggestion(
            title="Health Insurance Premium",
            description="Comprehensive health coverage for self and family with tax benefits",
            investment_type="Health Insurance",
            suggested_amount=remaining_limit,
            potential_tax_savings=remaining_limit * marginal_rate,
            difficulty=OptimizationDifficulty.MODERATE,
            section="80D",
            current_utilization=current_80d,
            max_limit=self.deduction_limits['80D'],
            implementation_steps=[
                "Compare health insurance plans online",
                "Choose adequate sum insured (minimum 5 lakhs recommended)",
                "Pay annual premium before March 31st",
                "Keep premium payment receipts for ITR filing"
            ]
        ))
        
        # Parents health insurance (additional limit)
        if current_deductions.get('80D_parents', 0) == 0:
            suggestions.append(TaxOptimizationSuggestion(
                title="Health Insurance for Parents",
                description="Additional tax benefit for parents' health insurance premium",
                investment_type="Health Insurance",
                suggested_amount=self.deduction_limits['80D_PARENTS'],
                potential_tax_savings=self.deduction_limits['80D_PARENTS'] * marginal_rate,
                difficulty=OptimizationDifficulty.MODERATE,
                section="80D",
                current_utilization=Decimal('0'),
                max_limit=self.deduction_limits['80D_PARENTS'],
                implementation_steps=[
                    "Purchase health insurance for parents",
                    "Higher deduction limit if parents are senior citizens",
                    "Coordinate with existing family coverage"
                ]
            ))
        
        return suggestions
    
    def _suggest_80ccd_1b_investments(self, current_deductions: Dict, marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest Section 80CCD(1B) NPS investments"""
        suggestions = []
        
        current_80ccd_1b = Decimal(str(current_deductions.get('80CCD(1B)', 0)))
        remaining_limit = self.deduction_limits['80CCD_1B'] - current_80ccd_1b
        
        if remaining_limit <= 0:
            return suggestions
        
        suggestions.append(TaxOptimizationSuggestion(
            title="National Pension Scheme (NPS) - Additional Investment",
            description="Additional NPS investment under Section 80CCD(1B) over and above 80C limit",
            investment_type="Retirement Planning",
            suggested_amount=remaining_limit,
            potential_tax_savings=remaining_limit * marginal_rate,
            difficulty=OptimizationDifficulty.MODERATE,
            section="80CCD(1B)",
            current_utilization=current_80ccd_1b,
            max_limit=self.deduction_limits['80CCD_1B'],
            implementation_steps=[
                "Open NPS account if not already available",
                "Make additional contribution beyond employer contribution",
                "Choose appropriate asset allocation based on age",
                "Set up systematic investment for regular contributions"
            ]
        ))
        
        return suggestions
    
    def _suggest_bank_interest_optimization(self, form16_data: Dict, marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest bank interest optimization under Section 80TTA"""
        suggestions = []
        
        try:
            # Check if bank interest is reported in Form16
            other_income = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('other_income', {})
                .get('income_from_other_sources', 0) or 0
            )
            
            # If no bank interest claimed, suggest optimization
            if other_income == 0:
                suggestions.append(TaxOptimizationSuggestion(
                    title="Savings Account Interest Optimization",
                    description="Optimize savings account interest to claim Section 80TTA deduction",
                    investment_type="Interest Income Planning",
                    suggested_amount=self.deduction_limits['80TTA'],
                    potential_tax_savings=self.deduction_limits['80TTA'] * marginal_rate,
                    difficulty=OptimizationDifficulty.EASY,
                    section="80TTA",
                    current_utilization=Decimal('0'),
                    max_limit=self.deduction_limits['80TTA'],
                    implementation_steps=[
                        "Maintain higher savings account balance to earn interest",
                        "Consider high-yield savings accounts",
                        "Claim interest up to Rs. 10,000 under Section 80TTA",
                        "Report interest income in ITR filing"
                    ]
                ))
        except Exception as e:
            self.logger.warning(f"Error analyzing bank interest optimization: {e}")
        
        return suggestions
    
    def _suggest_home_loan_optimization(self, current_deductions: Dict, marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest home loan interest optimization"""
        suggestions = []
        
        # Check if home loan interest is being claimed
        current_home_loan = current_deductions.get('home_loan_interest', 0)
        
        if current_home_loan == 0:
            # First-time home buyer benefit
            suggestions.append(TaxOptimizationSuggestion(
                title="Home Loan for First-Time Buyers",
                description="Additional deduction for first-time home buyers under Section 80EE",
                investment_type="Real Estate Investment",
                suggested_amount=self.deduction_limits['80EE'],
                potential_tax_savings=self.deduction_limits['80EE'] * marginal_rate,
                difficulty=OptimizationDifficulty.DIFFICULT,
                section="80EE",
                current_utilization=Decimal('0'),
                max_limit=self.deduction_limits['80EE'],
                implementation_steps=[
                    "Purchase property with loan amount below Rs. 35 lakhs",
                    "Ensure property value is below Rs. 50 lakhs",
                    "Must be first-time home buyer",
                    "Claim additional Rs. 50,000 deduction beyond standard home loan interest"
                ]
            ))
        
        return suggestions
    
    def _prioritize_for_target(self, suggestions: List[TaxOptimizationSuggestion], target_savings: int) -> List[TaxOptimizationSuggestion]:
        """Prioritize suggestions to meet target savings"""
        target = Decimal(str(target_savings))
        prioritized = []
        cumulative_savings = Decimal('0')
        
        # Sort by ease of implementation and ROI
        suggestions.sort(key=lambda x: (x.difficulty.value, -x.roi_percentage))
        
        for suggestion in suggestions:
            prioritized.append(suggestion)
            cumulative_savings += suggestion.potential_tax_savings
            
            if cumulative_savings >= target:
                break
        
        return prioritized
    
    def create_dummy_optimization_analysis(self, income_level: str = "medium") -> TaxOptimizationAnalysis:
        """Create dummy tax optimization analysis for demo purposes"""
        
        income_configs = {
            "medium": {
                "current_tax": Decimal('78723'),
                "current_80c": Decimal('0'),
                "current_80d": Decimal('0'),
                "regime": "new"
            },
            "high": {
                "current_tax": Decimal('350000'),
                "current_80c": Decimal('50000'),
                "current_80d": Decimal('15000'),
                "regime": "old"
            }
        }
        
        config = income_configs.get(income_level, income_configs["medium"])
        
        analysis = TaxOptimizationAnalysis(
            employee_name="Ashish Mittal",
            current_regime=config["regime"],
            current_tax_liability=config["current_tax"],
            current_deductions={
                '80C': config["current_80c"],
                '80D': config["current_80d"]
            }
        )
        
        # Add sample suggestions
        marginal_rate = self.marginal_tax_rates[f"{config['regime']}_regime"]
        
        # PPF suggestion
        ppf_amount = Decimal('100000')
        analysis.add_suggestion(TaxOptimizationSuggestion(
            title="Public Provident Fund Investment",
            description="Long-term tax-free investment with guaranteed returns",
            investment_type="80C Investment",
            suggested_amount=ppf_amount,
            potential_tax_savings=ppf_amount * marginal_rate,
            difficulty=OptimizationDifficulty.EASY,
            section="80C",
            current_utilization=config["current_80c"],
            max_limit=self.deduction_limits['80C'],
            implementation_steps=[
                "Open PPF account with nationalized bank",
                "Set up automatic monthly transfer",
                "Ensure investment before March 31st"
            ]
        ))
        
        # Health insurance suggestion
        health_amount = Decimal('25000')
        analysis.add_suggestion(TaxOptimizationSuggestion(
            title="Health Insurance Premium",
            description="Comprehensive family health coverage with tax benefits",
            investment_type="Health Insurance",
            suggested_amount=health_amount,
            potential_tax_savings=health_amount * marginal_rate,
            difficulty=OptimizationDifficulty.MODERATE,
            section="80D",
            current_utilization=config["current_80d"],
            max_limit=self.deduction_limits['80D'],
            implementation_steps=[
                "Compare health insurance plans",
                "Choose family floater plan",
                "Pay premium before March 31st"
            ]
        ))
        
        return analysis