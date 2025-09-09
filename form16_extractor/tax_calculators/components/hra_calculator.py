"""
HRA (House Rent Allowance) Exemption Calculator

Implements comprehensive HRA exemption calculation as per Section 10(13A) of Income Tax Act.
HRA exemption is one of the most common and significant tax benefits available.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CityType(Enum):
    """City classification for HRA exemption calculation."""
    METRO = "metro"  # Mumbai, Delhi, Kolkata, Chennai
    NON_METRO = "non_metro"


@dataclass
class HRADetails:
    """HRA component details for exemption calculation."""
    hra_received: Decimal  # HRA component in salary
    basic_salary: Decimal  # Basic salary (including DA if forming part of retirement benefits)
    rent_paid: Decimal     # Annual rent paid by employee
    city_type: CityType    # Metro or non-metro city
    months_in_rented_accommodation: int = 12  # Months employee stayed in rented accommodation


@dataclass
class HRACalculation:
    """Result of HRA exemption calculation."""
    hra_received: Decimal
    rent_paid: Decimal
    basic_salary: Decimal
    city_type: CityType
    
    # Three calculation components for least-of rule
    actual_hra_received: Decimal
    rent_minus_10_percent_basic: Decimal
    metro_allowance_calculation: Decimal
    
    # Final result
    exempt_hra: Decimal
    taxable_hra: Decimal
    calculation_method: str
    exemption_percentage: float


class HRACalculator:
    """
    Calculator for HRA exemption under Section 10(13A).
    
    HRA Exemption Formula (Least of three):
    1. Actual HRA received
    2. Rent paid minus 10% of basic salary
    3. 50% of basic salary (metro cities) OR 40% of basic salary (non-metro cities)
    
    Key Points:
    - Taxpayer must actually pay rent (rent receipts required)
    - Exemption only for months when taxpayer stayed in rented accommodation  
    - Basic salary includes DA if it forms part of retirement benefits
    - Metro cities: Mumbai, Delhi, Kolkata, Chennai (as per IT department)
    """
    
    def __init__(self):
        """Initialize HRA calculator."""
        # Metro cities as per Income Tax Department
        self.metro_cities = {
            'mumbai', 'delhi', 'kolkata', 'chennai',
            'new delhi', 'bombay', 'calcutta', 'madras'
        }
        
        # HRA percentage rates
        self.metro_rate = Decimal('50')      # 50% for metro cities
        self.non_metro_rate = Decimal('40')  # 40% for non-metro cities
    
    def calculate_hra_exemption(self, hra_details: HRADetails) -> HRACalculation:
        """
        Calculate HRA exemption using the statutory least-of-three formula.
        
        Args:
            hra_details: HRA component details
            
        Returns:
            HRACalculation with detailed breakdown and exemption amount
            
        Note:
            This calculation is critical for tax optimization as HRA exemption
            can significantly reduce taxable salary income for most employees.
        """
        # Validate inputs
        self._validate_hra_details(hra_details)
        
        # Calculate pro-rata amounts if employee didn't stay full year in rented accommodation
        months_factor = Decimal(hra_details.months_in_rented_accommodation) / Decimal('12')
        
        # Prorate HRA and rent for actual months in rented accommodation
        prorated_hra = hra_details.hra_received * months_factor
        prorated_rent = hra_details.rent_paid * months_factor
        
        # Component 1: Actual HRA received (prorated)
        actual_hra_received = prorated_hra
        
        # Component 2: Rent paid minus 10% of basic salary (prorated)
        # 10% of basic salary is the minimum expected personal accommodation cost
        ten_percent_basic = (hra_details.basic_salary * Decimal('10')) / Decimal('100')
        rent_minus_10_percent_basic = max(Decimal('0'), prorated_rent - ten_percent_basic)
        
        # Component 3: Percentage of basic salary based on city type (prorated)
        rate = self.metro_rate if hra_details.city_type == CityType.METRO else self.non_metro_rate
        metro_allowance_calculation = (hra_details.basic_salary * rate * months_factor) / Decimal('100')
        
        # HRA exemption is the LEAST of the three components
        exempt_hra = min(
            actual_hra_received,
            rent_minus_10_percent_basic,  
            metro_allowance_calculation
        )
        
        # Taxable HRA = Total HRA - Exempt HRA
        taxable_hra = max(Decimal('0'), hra_details.hra_received - exempt_hra)
        
        # Determine which component was the limiting factor
        calculation_method = self._determine_calculation_method(
            actual_hra_received, rent_minus_10_percent_basic, metro_allowance_calculation
        )
        
        # Calculate exemption percentage
        exemption_percentage = float((exempt_hra / hra_details.hra_received) * 100) if hra_details.hra_received > 0 else 0.0
        
        return HRACalculation(
            hra_received=hra_details.hra_received,
            rent_paid=hra_details.rent_paid,
            basic_salary=hra_details.basic_salary,
            city_type=hra_details.city_type,
            actual_hra_received=actual_hra_received,
            rent_minus_10_percent_basic=rent_minus_10_percent_basic,
            metro_allowance_calculation=metro_allowance_calculation,
            exempt_hra=exempt_hra,
            taxable_hra=taxable_hra,
            calculation_method=calculation_method,
            exemption_percentage=exemption_percentage
        )
    
    def calculate_optimal_hra_rent_ratio(
        self, 
        basic_salary: Decimal,
        hra_component: Decimal,
        city_type: CityType
    ) -> Dict[str, Decimal]:
        """
        Calculate optimal rent amount for maximum HRA exemption.
        
        This is useful for tax planning - employees can optimize their rent
        to maximize HRA exemption benefits.
        
        Args:
            basic_salary: Monthly basic salary
            hra_component: Monthly HRA component in salary
            city_type: Metro or non-metro city
            
        Returns:
            Dictionary with optimal rent calculations and scenarios
        """
        # Annual amounts for calculation
        annual_basic = basic_salary * 12
        annual_hra = hra_component * 12
        
        # Calculate percentage-based allowance (Component 3)
        rate = self.metro_rate if city_type == CityType.METRO else self.non_metro_rate
        percentage_allowance = (annual_basic * rate) / Decimal('100')
        
        # Scenario 1: Rent where Component 2 equals Component 3
        # rent - (10% of basic) = percentage_allowance
        # rent = percentage_allowance + (10% of basic)
        optimal_rent_scenario_1 = percentage_allowance + (annual_basic * Decimal('10') / Decimal('100'))
        
        # Scenario 2: Rent where Component 2 equals Component 1 (actual HRA)
        # rent - (10% of basic) = annual_hra
        # rent = annual_hra + (10% of basic)
        optimal_rent_scenario_2 = annual_hra + (annual_basic * Decimal('10') / Decimal('100'))
        
        # Maximum possible exemption (least of all three components when optimized)
        max_possible_exemption = min(annual_hra, percentage_allowance)
        
        # Recommended optimal rent (to achieve maximum exemption)
        if annual_hra <= percentage_allowance:
            # HRA component is limiting factor
            recommended_rent = annual_hra + (annual_basic * Decimal('10') / Decimal('100'))
            limiting_factor = "HRA component"
        else:
            # Percentage allowance is limiting factor  
            recommended_rent = optimal_rent_scenario_1
            limiting_factor = "City-based percentage"
        
        return {
            'annual_basic_salary': annual_basic,
            'annual_hra_component': annual_hra,
            'city_based_allowance': percentage_allowance,
            'optimal_rent_scenario_1': optimal_rent_scenario_1,
            'optimal_rent_scenario_2': optimal_rent_scenario_2,
            'recommended_optimal_rent': recommended_rent,
            'max_possible_exemption': max_possible_exemption,
            'limiting_factor': limiting_factor,
            'city_type': city_type.value,
            'metro_rate_percent': float(rate)
        }
    
    def validate_hra_claim(self, hra_details: HRADetails) -> Tuple[bool, List[str]]:
        """
        Validate HRA claim for compliance and optimization.
        
        Args:
            hra_details: HRA details to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        is_valid = True
        
        # Basic validation
        if hra_details.hra_received <= 0:
            issues.append("HRA received must be positive")
            is_valid = False
        
        if hra_details.basic_salary <= 0:
            issues.append("Basic salary must be positive")
            is_valid = False
        
        if hra_details.rent_paid < 0:
            issues.append("Rent paid cannot be negative")
            is_valid = False
        
        # Practical validation
        if hra_details.rent_paid == 0 and hra_details.hra_received > 0:
            issues.append("Cannot claim HRA exemption without paying rent")
        
        # Check if rent seems reasonable compared to salary
        monthly_basic = hra_details.basic_salary / 12
        monthly_rent = hra_details.rent_paid / 12
        
        if monthly_rent > monthly_basic:
            issues.append("Warning: Monthly rent exceeds monthly basic salary - verify if correct")
        
        # Check if rent is significantly higher than optimal
        optimal_calc = self.calculate_optimal_hra_rent_ratio(
            monthly_basic, hra_details.hra_received / 12, hra_details.city_type
        )
        
        if hra_details.rent_paid > optimal_calc['recommended_optimal_rent'] * Decimal('1.2'):
            issues.append("Consider optimizing rent amount for maximum HRA benefit")
        
        return is_valid, issues
    
    def _validate_hra_details(self, hra_details: HRADetails) -> None:
        """Validate HRA details for calculation."""
        if hra_details.months_in_rented_accommodation < 1 or hra_details.months_in_rented_accommodation > 12:
            raise ValueError("Months in rented accommodation must be between 1 and 12")
        
        if hra_details.hra_received < 0 or hra_details.basic_salary < 0 or hra_details.rent_paid < 0:
            raise ValueError("HRA received, basic salary, and rent paid cannot be negative")
    
    def _determine_calculation_method(
        self,
        actual_hra: Decimal,
        rent_minus_basic: Decimal,
        metro_allowance: Decimal
    ) -> str:
        """Determine which component was the limiting factor in HRA calculation."""
        components = [
            (actual_hra, "Actual HRA received"),
            (rent_minus_basic, "Rent paid minus 10% of basic salary"),
            (metro_allowance, "City-based percentage of basic salary")
        ]
        
        # Find the minimum component
        min_component = min(components, key=lambda x: x[0])
        return min_component[1]
    
    def is_metro_city(self, city_name: str) -> bool:
        """Check if given city is classified as metro for HRA purposes."""
        return city_name.lower().strip() in self.metro_cities


# Utility functions for easy integration
def calculate_hra_exemption_quick(
    hra_received: Decimal,
    basic_salary: Decimal,
    rent_paid: Decimal,
    is_metro: bool = False
) -> Decimal:
    """
    Quick utility function to calculate HRA exemption.
    
    Args:
        hra_received: Annual HRA received
        basic_salary: Annual basic salary
        rent_paid: Annual rent paid
        is_metro: Whether employee works in metro city
        
    Returns:
        HRA exemption amount
    """
    city_type = CityType.METRO if is_metro else CityType.NON_METRO
    
    hra_details = HRADetails(
        hra_received=hra_received,
        basic_salary=basic_salary,
        rent_paid=rent_paid,
        city_type=city_type
    )
    
    calculator = HRACalculator()
    calculation = calculator.calculate_hra_exemption(hra_details)
    
    return calculation.exempt_hra


def get_hra_optimization_suggestions(
    current_hra: Decimal,
    current_basic: Decimal,
    current_rent: Decimal,
    city_type: CityType
) -> Dict[str, any]:
    """
    Get HRA optimization suggestions for tax planning.
    
    Args:
        current_hra: Current HRA component
        current_basic: Current basic salary
        current_rent: Current rent paid
        city_type: Metro or non-metro city
        
    Returns:
        Dictionary with optimization suggestions
    """
    calculator = HRACalculator()
    
    # Current calculation
    current_details = HRADetails(current_hra, current_basic, current_rent, city_type)
    current_calc = calculator.calculate_hra_exemption(current_details)
    
    # Optimal calculation
    optimal_calc = calculator.calculate_optimal_hra_rent_ratio(
        current_basic / 12, current_hra / 12, city_type
    )
    
    return {
        'current_exemption': float(current_calc.exempt_hra),
        'current_exemption_percentage': current_calc.exemption_percentage,
        'optimal_rent': float(optimal_calc['recommended_optimal_rent']),
        'max_possible_exemption': float(optimal_calc['max_possible_exemption']),
        'potential_additional_saving': float(optimal_calc['max_possible_exemption'] - current_calc.exempt_hra),
        'limiting_factor': optimal_calc['limiting_factor'],
        'suggestions': [
            f"Consider rent of ₹{optimal_calc['recommended_optimal_rent']:,.0f} for maximum HRA benefit",
            f"Maximum possible HRA exemption: ₹{optimal_calc['max_possible_exemption']:,.0f}",
            f"Current exemption utilization: {current_calc.exemption_percentage:.1f}%"
        ]
    }