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
            '80TTB': Decimal('50000'),   # Senior citizen interest
            '80EE': Decimal('50000'),    # Home loan interest (first time buyers)
            '80EEA': Decimal('150000'),  # Home loan interest (affordable housing)
            '80E': Decimal('999999'),    # Education loan interest (no limit)
            '80G': Decimal('999999'),    # Charitable donations (no fixed limit, depends on income)
            '80U': Decimal('75000'),     # Disability deduction
            '80GG': Decimal('60000'),    # Rent paid (when no HRA)
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
        
        # HRA optimization suggestions (only for old regime)
        if regime == 'old':
            suggestions.extend(self._suggest_hra_optimization(form16_data, marginal_rate))
        
        # Additional investment and deduction opportunities (old regime only)
        if regime == 'old':
            suggestions.extend(self._suggest_charitable_donations(form16_data, marginal_rate))
            suggestions.extend(self._suggest_education_loan_optimization(form16_data, marginal_rate))
            suggestions.extend(self._suggest_senior_citizen_benefits(form16_data, marginal_rate))
        
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
        
        # ELSS Mutual Funds - Top Priority for younger investors
        if remaining_limit >= Decimal('25000'):
            elss_amount = min(remaining_limit, Decimal('100000'))
            suggestions.append(TaxOptimizationSuggestion(
                title="ELSS Mutual Funds (Tax Saver)",
                description="Best tax-saving option: equity MF with 3-year lock-in, potential 12-15% returns",
                investment_type="Mutual Fund - ELSS",
                suggested_amount=elss_amount,
                potential_tax_savings=elss_amount * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80C",
                current_utilization=current_80c,
                max_limit=self.deduction_limits['80C'],
                implementation_steps=[
                    "Open demat account or invest through fund house directly",
                    "Choose top-performing ELSS funds (Axis Long Term Equity, Mirae Asset Tax Saver)",
                    "Start monthly SIP of ₹8,500 for ₹1L annual investment",
                    "Complete KYC and link bank account for auto-debit",
                    "Track NAV and performance on monthly basis"
                ]
            ))
        
        # Large Cap ELSS for Conservative Investors
        if remaining_limit >= Decimal('50000'):
            conservative_amount = min(remaining_limit, Decimal('75000'))
            suggestions.append(TaxOptimizationSuggestion(
                title="Conservative ELSS Funds",
                description="Large-cap focused ELSS for stable returns with lower volatility",
                investment_type="Mutual Fund - ELSS (Conservative)",
                suggested_amount=conservative_amount,
                potential_tax_savings=conservative_amount * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80C",
                current_utilization=current_80c,
                max_limit=self.deduction_limits['80C'],
                implementation_steps=[
                    "Choose large-cap oriented ELSS funds for stability",
                    "Consider SBI Long Term Equity Fund or HDFC TaxSaver",
                    "Set up monthly SIP for disciplined investing",
                    "Review fund performance annually",
                    "Maintain emergency fund alongside ELSS investment"
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
        
        # NPS Tier-I Account - Primary Retirement Planning
        suggestions.append(TaxOptimizationSuggestion(
            title="NPS Tier-I Additional Contribution",
            description="Extra ₹50,000 tax deduction over 80C limit | Best for long-term retirement planning",
            investment_type="Retirement Planning - NPS",
            suggested_amount=remaining_limit,
            potential_tax_savings=remaining_limit * marginal_rate,
            difficulty=OptimizationDifficulty.MODERATE,
            section="80CCD(1B)",
            current_utilization=current_80ccd_1b,
            max_limit=self.deduction_limits['80CCD_1B'],
            implementation_steps=[
                "Open NPS Tier-I account through bank or online (eNPS)",
                "Choose Aggressive/Moderate/Conservative asset allocation based on age",
                "Set up monthly auto-debit for systematic contribution",
                "Monitor fund performance and rebalance annually",
                "Remember: 60% corpus tax-free at retirement, 40% compulsory annuity"
            ]
        ))
        
        # Add Corporate NPS guidance if applicable
        if remaining_limit >= Decimal('30000'):
            suggestions.append(TaxOptimizationSuggestion(
                title="Corporate NPS Enhancement",
                description="Maximize employer NPS matching + additional 80CCD(1B) contribution",
                investment_type="Employer-Matched Retirement",
                suggested_amount=min(remaining_limit, Decimal('50000')),
                potential_tax_savings=min(remaining_limit, Decimal('50000')) * marginal_rate,
                difficulty=OptimizationDifficulty.EASY,
                section="80CCD(1B)",
                current_utilization=current_80ccd_1b,
                max_limit=self.deduction_limits['80CCD_1B'],
                implementation_steps=[
                    "Check if employer offers NPS with matching contribution",
                    "Maximize employer matching first (free money)",
                    "Top up to ₹50,000 limit for maximum tax benefit",
                    "Choose equity-heavy allocation if age < 40",
                    "Review and rebalance portfolio annually"
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
    
    def _suggest_hra_optimization(self, form16_data: Dict[str, Any], marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest HRA optimization opportunities (only applicable in old regime)"""
        suggestions = []
        
        try:
            # Extract current salary and HRA information
            salary_data = form16_data.get('form16', {}).get('part_b', {})
            current_gross = Decimal(str(salary_data.get('gross_salary', {}).get('total', 2500000)))  # Demo default
            current_basic = Decimal(str(current_gross * Decimal('0.5')))  # Assume 50% basic
            
            # Get current HRA from allowances exempt under section 10
            allowances_exempt = salary_data.get('allowances_exempt_under_section_10', {})
            current_hra_received = Decimal(str(allowances_exempt.get('house_rent_allowance', 0)))
            
            # Calculate optimal HRA structure based on 2024-25 rules
            # Metro cities: 50% of basic salary, Non-metro: 40% of basic salary
            optimal_hra_metro = current_basic * Decimal('0.5')  # 50% of basic for metro
            optimal_hra_non_metro = current_basic * Decimal('0.4')  # 40% of basic for non-metro
            
            # If current HRA is significantly less than optimal, suggest restructuring
            if current_hra_received < optimal_hra_metro * Decimal('0.6'):  # If less than 60% of optimal
                
                # Metro city HRA optimization
                additional_hra_metro = optimal_hra_metro - current_hra_received
                if additional_hra_metro > Decimal('50000'):  # Only suggest if meaningful amount
                    
                    tax_savings_metro = additional_hra_metro * marginal_rate
                    
                    suggestions.append(TaxOptimizationSuggestion(
                        title="HRA Salary Restructuring (Metro)",
                        description="Optimize salary structure for maximum HRA benefits in metro cities (50% of basic)",
                        investment_type="Salary Restructuring",
                        suggested_amount=additional_hra_metro,
                        potential_tax_savings=tax_savings_metro,
                        difficulty=OptimizationDifficulty.MODERATE,
                        section="10(13A)",
                        current_utilization=current_hra_received,
                        max_limit=optimal_hra_metro,
                        implementation_steps=[
                            "Negotiate salary restructuring with HR",
                            "Increase HRA to 50% of basic salary",
                            "Ensure actual rent documentation",
                            "Submit Form 12BB with rent receipts",
                            "Get landlord's PAN if rent > ₹1 lakh annually"
                        ]
                    ))
                
                # Non-metro city HRA optimization  
                additional_hra_non_metro = optimal_hra_non_metro - current_hra_received
                if additional_hra_non_metro > Decimal('40000'):  # Only suggest if meaningful amount
                    
                    tax_savings_non_metro = additional_hra_non_metro * marginal_rate
                    
                    suggestions.append(TaxOptimizationSuggestion(
                        title="HRA Salary Restructuring (Non-Metro)",
                        description="Optimize salary structure for maximum HRA benefits in non-metro cities (40% of basic)",
                        investment_type="Salary Restructuring", 
                        suggested_amount=additional_hra_non_metro,
                        potential_tax_savings=tax_savings_non_metro,
                        difficulty=OptimizationDifficulty.MODERATE,
                        section="10(13A)",
                        current_utilization=current_hra_received,
                        max_limit=optimal_hra_non_metro,
                        implementation_steps=[
                            "Negotiate salary restructuring with HR",
                            "Increase HRA to 40% of basic salary",
                            "Ensure actual rent documentation",
                            "Submit Form 12BB with rent receipts", 
                            "Get landlord's PAN if rent > ₹1 lakh annually"
                        ]
                    ))
            
            # Alternative: Section 80GG for those without HRA
            if current_hra_received == 0:
                section_80gg_benefit = min(Decimal('60000'), current_gross * Decimal('0.25'))  # ₹5k/month or 25% of income
                if section_80gg_benefit > Decimal('20000'):
                    tax_savings_80gg = section_80gg_benefit * marginal_rate
                    
                    suggestions.append(TaxOptimizationSuggestion(
                        title="Rent Deduction under Section 80GG",
                        description="Claim rent deduction when HRA is not provided by employer",
                        investment_type="Rent Deduction",
                        suggested_amount=section_80gg_benefit,
                        potential_tax_savings=tax_savings_80gg,
                        difficulty=OptimizationDifficulty.EASY,
                        section="80GG",
                        current_utilization=Decimal('0'),
                        max_limit=section_80gg_benefit,
                        implementation_steps=[
                            "Ensure you don't receive HRA from employer",
                            "Maintain rent receipts and agreements",
                            "File Form 10BA with ITR",
                            "Ensure rent payment through traceable methods",
                            "You or spouse should not own house in same city"
                        ]
                    ))
        
        except Exception as e:
            self.logger.error(f"Error generating HRA suggestions: {e}")
        
        return suggestions
    
    def _suggest_charitable_donations(self, form16_data: Dict[str, Any], marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest charitable donation opportunities under Section 80G"""
        suggestions = []
        
        try:
            # Extract current income to calculate donation potential
            salary_data = form16_data.get('form16', {}).get('part_b', {})
            current_gross = Decimal(str(salary_data.get('gross_salary', {}).get('total', 2500000)))  # Demo default
            
            # Section 80G allows deduction up to 10% of adjusted gross total income for many charities
            max_donation_benefit = current_gross * Decimal('0.10')  # 10% of income
            suggested_donation = min(max_donation_benefit, Decimal('50000'))  # Suggest reasonable amount
            
            if suggested_donation >= Decimal('5000'):
                tax_savings = suggested_donation * marginal_rate
                
                suggestions.append(TaxOptimizationSuggestion(
                    title="Charitable Donations (Section 80G)",
                    description="Tax-deductible donations to approved charities - do good while saving tax",
                    investment_type="Charitable Contribution",
                    suggested_amount=suggested_donation,
                    potential_tax_savings=tax_savings,
                    difficulty=OptimizationDifficulty.EASY,
                    section="80G",
                    current_utilization=Decimal('0'),
                    max_limit=max_donation_benefit,
                    implementation_steps=[
                        "Choose eligible charities with 80G certificate",
                        "Consider PM CARES Fund (100% deduction)",
                        "Donate to approved NGOs, educational institutions",
                        "Keep donation receipts with 80G certificate",
                        "Ensure donations are through traceable methods (not cash)"
                    ]
                ))
        
        except Exception as e:
            self.logger.error(f"Error generating charitable donation suggestions: {e}")
        
        return suggestions
    
    def _suggest_education_loan_optimization(self, form16_data: Dict[str, Any], marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest education loan interest deduction under Section 80E"""
        suggestions = []
        
        try:
            # This is mainly informational since we can't determine if user has education loan
            # But important to mention for completeness
            potential_interest_amount = Decimal('100000')  # Example annual interest
            tax_savings = potential_interest_amount * marginal_rate
            
            suggestions.append(TaxOptimizationSuggestion(
                title="Education Loan Interest Deduction",
                description="Unlimited deduction for education loan interest (self/spouse/children)",
                investment_type="Education Loan Benefit",
                suggested_amount=potential_interest_amount,
                potential_tax_savings=tax_savings,
                difficulty=OptimizationDifficulty.EASY,
                section="80E",
                current_utilization=Decimal('0'),
                max_limit=Decimal('999999'),  # No limit
                implementation_steps=[
                    "Ensure education loan is from approved financial institution",
                    "Loan must be for higher education (self, spouse, children)",
                    "Keep interest certificate from bank/NBFC",
                    "Claim full interest amount paid during the year",
                    "Deduction available for maximum 8 years or until loan is repaid"
                ]
            ))
        
        except Exception as e:
            self.logger.error(f"Error generating education loan suggestions: {e}")
        
        return suggestions
    
    def _suggest_senior_citizen_benefits(self, form16_data: Dict[str, Any], marginal_rate: Decimal) -> List[TaxOptimizationSuggestion]:
        """Suggest senior citizen specific tax benefits"""
        suggestions = []
        
        try:
            # Section 80TTB for senior citizens (interest income)
            senior_interest_benefit = Decimal('50000')  # ₹50,000 limit for senior citizens
            tax_savings = senior_interest_benefit * marginal_rate
            
            suggestions.append(TaxOptimizationSuggestion(
                title="Senior Citizen Interest Income Benefit",
                description="₹50,000 deduction on interest income for senior citizens (60+ years)",
                investment_type="Senior Citizen Benefit",
                suggested_amount=senior_interest_benefit,
                potential_tax_savings=tax_savings,
                difficulty=OptimizationDifficulty.EASY,
                section="80TTB",
                current_utilization=Decimal('0'),
                max_limit=self.deduction_limits['80TTB'],
                implementation_steps=[
                    "Applicable only if you/parents are 60+ years old",
                    "Optimize bank FD/savings account interest",
                    "Consider tax-free bonds for senior citizens",
                    "Higher basic exemption limit (₹3 lakh for 60-80 years)",
                    "Additional health insurance deduction limit (₹50,000)"
                ]
            ))
        
        except Exception as e:
            self.logger.error(f"Error generating senior citizen suggestions: {e}")
        
        return suggestions