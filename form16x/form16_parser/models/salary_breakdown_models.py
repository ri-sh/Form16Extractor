"""
Data models for salary breakdown analysis

Provides structured models for representing salary components, 
breakdowns, and tax optimization suggestions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from decimal import Decimal
from enum import Enum


class SalaryComponentType(str, Enum):
    """Types of salary components"""
    BASIC_SALARY = "basic_salary"
    HOUSE_RENT_ALLOWANCE = "hra" 
    DEARNESS_ALLOWANCE = "da"
    SPECIAL_ALLOWANCE = "special_allowance"
    TRANSPORT_ALLOWANCE = "transport"
    MEDICAL_ALLOWANCE = "medical"
    OTHER_ALLOWANCE = "other_allowance"
    PERQUISITES = "perquisites"
    PROFITS_IN_LIEU = "profits_in_lieu"


class OptimizationDifficulty(str, Enum):
    """Difficulty levels for tax optimization suggestions"""
    EASY = "easy"          # Can be done immediately
    MODERATE = "moderate"   # Requires some planning
    DIFFICULT = "difficult" # Requires significant changes


@dataclass
class SalaryComponent:
    """Represents a single salary component"""
    type: SalaryComponentType
    amount: Decimal
    description: str
    is_taxable: bool = True
    percentage_of_gross: Optional[float] = None
    
    def __post_init__(self):
        """Calculate percentage if gross salary is known"""
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))


@dataclass 
class SalaryBreakdown:
    """Complete salary breakdown with all components"""
    employee_name: str
    employer_name: str
    assessment_year: str
    gross_salary: Decimal
    components: List[SalaryComponent] = field(default_factory=list)
    total_tds: Decimal = field(default=Decimal('0'))
    net_salary: Optional[Decimal] = None
    
    def __post_init__(self):
        """Calculate derived values"""
        if isinstance(self.gross_salary, (int, float)):
            self.gross_salary = Decimal(str(self.gross_salary))
        if isinstance(self.total_tds, (int, float)):
            self.total_tds = Decimal(str(self.total_tds))
            
        # Calculate net salary
        self.net_salary = self.gross_salary - self.total_tds
        
        # Calculate percentages for components
        for component in self.components:
            if self.gross_salary > 0:
                component.percentage_of_gross = float(
                    (component.amount / self.gross_salary) * 100
                )
    
    def get_component_by_type(self, component_type: SalaryComponentType) -> Optional[SalaryComponent]:
        """Get a component by its type"""
        for component in self.components:
            if component.type == component_type:
                return component
        return None
    
    def get_total_taxable_amount(self) -> Decimal:
        """Calculate total taxable amount"""
        return sum(
            component.amount for component in self.components 
            if component.is_taxable
        )
    
    def get_total_non_taxable_amount(self) -> Decimal:
        """Calculate total non-taxable amount"""
        return sum(
            component.amount for component in self.components 
            if not component.is_taxable
        )


@dataclass
class TaxOptimizationSuggestion:
    """Represents a single tax optimization suggestion"""
    title: str
    description: str
    investment_type: str  # e.g., "80C Investment", "Health Insurance"
    suggested_amount: Decimal
    potential_tax_savings: Decimal
    difficulty: OptimizationDifficulty
    section: str  # Tax section like "80C", "80D", etc.
    current_utilization: Decimal = field(default=Decimal('0'))
    max_limit: Optional[Decimal] = None
    implementation_steps: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Convert numeric inputs to Decimal"""
        if isinstance(self.suggested_amount, (int, float)):
            self.suggested_amount = Decimal(str(self.suggested_amount))
        if isinstance(self.potential_tax_savings, (int, float)):
            self.potential_tax_savings = Decimal(str(self.potential_tax_savings))
        if isinstance(self.current_utilization, (int, float)):
            self.current_utilization = Decimal(str(self.current_utilization))
        if self.max_limit and isinstance(self.max_limit, (int, float)):
            self.max_limit = Decimal(str(self.max_limit))
    
    @property
    def remaining_limit(self) -> Decimal:
        """Calculate remaining investment limit"""
        if self.max_limit:
            return max(Decimal('0'), self.max_limit - self.current_utilization)
        return self.suggested_amount
    
    @property
    def roi_percentage(self) -> float:
        """Calculate ROI as tax savings percentage"""
        if self.suggested_amount > 0:
            return float((self.potential_tax_savings / self.suggested_amount) * 100)
        return 0.0


@dataclass
class TaxOptimizationAnalysis:
    """Complete tax optimization analysis"""
    employee_name: str
    current_regime: str  # "old" or "new"
    current_tax_liability: Decimal
    current_deductions: Dict[str, Decimal] = field(default_factory=dict)
    suggestions: List[TaxOptimizationSuggestion] = field(default_factory=list)
    potential_total_savings: Decimal = field(default=Decimal('0'))
    optimized_tax_liability: Decimal = field(default=Decimal('0'))
    
    def __post_init__(self):
        """Calculate total potential savings"""
        self.potential_total_savings = sum(
            suggestion.potential_tax_savings for suggestion in self.suggestions
        )
        self.optimized_tax_liability = max(
            Decimal('0'), 
            self.current_tax_liability - self.potential_total_savings
        )
    
    def add_suggestion(self, suggestion: TaxOptimizationSuggestion):
        """Add a new optimization suggestion"""
        self.suggestions.append(suggestion)
        self.__post_init__()  # Recalculate totals
    
    def get_suggestions_by_difficulty(self, difficulty: OptimizationDifficulty) -> List[TaxOptimizationSuggestion]:
        """Get suggestions filtered by difficulty"""
        return [s for s in self.suggestions if s.difficulty == difficulty]
    
    def get_suggestions_by_section(self, section: str) -> List[TaxOptimizationSuggestion]:
        """Get suggestions filtered by tax section"""
        return [s for s in self.suggestions if s.section == section]
    
    def get_top_suggestions(self, limit: int = 5) -> List[TaxOptimizationSuggestion]:
        """Get top suggestions by ROI"""
        return sorted(
            self.suggestions, 
            key=lambda x: x.roi_percentage, 
            reverse=True
        )[:limit]


@dataclass
class BreakdownDisplayOptions:
    """Options for displaying salary breakdown"""
    show_percentages: bool = False
    show_tax_implications: bool = False
    group_by_taxability: bool = False
    highlight_major_components: bool = True
    show_net_calculation: bool = True
    format_currency: bool = True