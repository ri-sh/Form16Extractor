"""
Gratuity and Pension Commutation Calculator

Implements comprehensive calculation for gratuity exemption and pension commutation
as per Income Tax Act provisions under Section 10.
"""

from decimal import Decimal
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import date


class EmploymentType(Enum):
    """Type of employment for gratuity calculation."""
    GOVERNMENT = "government"
    COVERED_UNDER_ACT = "covered_under_gratuity_act"  # Private sector covered under Payment of Gratuity Act 1972
    NOT_COVERED_UNDER_ACT = "not_covered_under_act"  # Private sector not covered


class PensionType(Enum):
    """Type of pension for commutation calculation."""
    GOVERNMENT_PENSION = "government"
    NON_GOVERNMENT_PENSION = "non_government"


@dataclass
class ServiceDetails:
    """Employee service details for gratuity calculation."""
    total_service_years: Decimal  # Can include fractional years
    total_service_months: int
    last_drawn_salary: Decimal  # Last drawn basic salary + DA
    is_termination_due_to_disability: bool = False
    date_of_joining: Optional[date] = None
    date_of_retirement: Optional[date] = None


@dataclass
class GratuityCalculation:
    """Result of gratuity calculation and exemption."""
    gross_gratuity_received: Decimal
    gratuity_formula_amount: Decimal
    maximum_exempt_limit: Decimal
    exempt_gratuity: Decimal
    taxable_gratuity: Decimal
    employment_type: EmploymentType
    calculation_method: str
    service_details: ServiceDetails


@dataclass
class CommutationCalculation:
    """Result of pension commutation calculation."""
    pension_commuted: Decimal
    commutation_factor: Decimal
    commuted_value: Decimal
    exempt_commutation: Decimal
    taxable_commutation: Decimal
    pension_type: PensionType
    calculation_method: str


class GratuityCalculator:
    """
    Calculator for gratuity exemption under Section 10(10) of Income Tax Act.
    
    Gratuity exemption calculation varies based on employment type:
    1. Government employees: Fully exempt
    2. Private sector covered under Act: Limited exemption
    3. Private sector not covered: Different calculation method
    """
    
    def __init__(self, assessment_year: str = "2024-25"):
        """Initialize gratuity calculator for given assessment year."""
        self.assessment_year = assessment_year
        self.max_exempt_limit = self._get_max_exempt_limit(assessment_year)
    
    def _get_max_exempt_limit(self, assessment_year: str) -> Decimal:
        """Get maximum gratuity exemption limit for assessment year."""
        # Exemption limit increased to Rs. 20 lakhs from AY 2020-21
        return Decimal('2000000')  # Rs. 20 lakhs
    
    def calculate_gratuity_exemption(
        self,
        gratuity_received: Decimal,
        service_details: ServiceDetails,
        employment_type: EmploymentType
    ) -> GratuityCalculation:
        """
        Calculate gratuity exemption based on employment type and service.
        
        Args:
            gratuity_received: Actual gratuity amount received
            service_details: Employee service details
            employment_type: Type of employment
            
        Returns:
            GratuityCalculation with exemption details
        """
        if employment_type == EmploymentType.GOVERNMENT:
            return self._calculate_government_gratuity(gratuity_received, service_details)
        elif employment_type == EmploymentType.COVERED_UNDER_ACT:
            return self._calculate_private_covered_gratuity(gratuity_received, service_details)
        else:
            return self._calculate_private_not_covered_gratuity(gratuity_received, service_details)
    
    def _calculate_government_gratuity(
        self,
        gratuity_received: Decimal,
        service_details: ServiceDetails
    ) -> GratuityCalculation:
        """Calculate gratuity for government employees (fully exempt)."""
        return GratuityCalculation(
            gross_gratuity_received=gratuity_received,
            gratuity_formula_amount=gratuity_received,
            maximum_exempt_limit=self.max_exempt_limit,
            exempt_gratuity=gratuity_received,  # Fully exempt for government employees
            taxable_gratuity=Decimal('0'),
            employment_type=EmploymentType.GOVERNMENT,
            calculation_method="Government employee - fully exempt",
            service_details=service_details
        )
    
    def _calculate_private_covered_gratuity(
        self,
        gratuity_received: Decimal,
        service_details: ServiceDetails
    ) -> GratuityCalculation:
        """
        Calculate gratuity for private sector employees covered under Payment of Gratuity Act 1972.
        
        Formula: (15/26) × Last drawn salary × Years of service
        Exemption: Least of (Formula amount, Actual amount, Rs. 20 lakhs)
        """
        # Calculate formula amount: (15/26) × Last salary × Years of service
        formula_amount = (
            Decimal('15') / Decimal('26') 
            * service_details.last_drawn_salary 
            * service_details.total_service_years
        )
        
        # Exemption is least of three amounts
        exempt_amount = min(
            formula_amount,
            gratuity_received,
            self.max_exempt_limit
        )
        
        taxable_amount = max(Decimal('0'), gratuity_received - exempt_amount)
        
        return GratuityCalculation(
            gross_gratuity_received=gratuity_received,
            gratuity_formula_amount=formula_amount,
            maximum_exempt_limit=self.max_exempt_limit,
            exempt_gratuity=exempt_amount,
            taxable_gratuity=taxable_amount,
            employment_type=EmploymentType.COVERED_UNDER_ACT,
            calculation_method="Private sector covered: (15/26) × Last salary × Service years",
            service_details=service_details
        )
    
    def _calculate_private_not_covered_gratuity(
        self,
        gratuity_received: Decimal,
        service_details: ServiceDetails
    ) -> GratuityCalculation:
        """
        Calculate gratuity for private sector employees NOT covered under Payment of Gratuity Act 1972.
        
        Formula: (15/30) × Last drawn salary × Years of service  [Half month salary for each year]
        Exemption: Least of (Formula amount, Actual amount, Rs. 20 lakhs)
        """
        # Calculate formula amount: (15/30) × Last salary × Years of service
        # This represents half month salary for each completed year of service
        formula_amount = (
            Decimal('15') / Decimal('30')  # Half month (15 days out of 30)
            * service_details.last_drawn_salary 
            * service_details.total_service_years
        )
        
        # Exemption is least of three amounts
        exempt_amount = min(
            formula_amount,
            gratuity_received,
            self.max_exempt_limit
        )
        
        taxable_amount = max(Decimal('0'), gratuity_received - exempt_amount)
        
        return GratuityCalculation(
            gross_gratuity_received=gratuity_received,
            gratuity_formula_amount=formula_amount,
            maximum_exempt_limit=self.max_exempt_limit,
            exempt_gratuity=exempt_amount,
            taxable_gratuity=taxable_amount,
            employment_type=EmploymentType.NOT_COVERED_UNDER_ACT,
            calculation_method="Private sector not covered: (15/30) × Last salary × Service years",
            service_details=service_details
        )
    
    def calculate_leave_encashment_exemption(
        self,
        leave_encashment_received: Decimal,
        service_details: ServiceDetails,
        employment_type: EmploymentType
    ) -> Decimal:
        """
        Calculate leave encashment exemption under Section 10(10AA).
        
        Args:
            leave_encashment_received: Leave encashment amount received
            service_details: Employee service details
            employment_type: Type of employment
            
        Returns:
            Exempt amount of leave encashment
        """
        if employment_type == EmploymentType.GOVERNMENT:
            # Government employees: Fully exempt
            return leave_encashment_received
        
        # Private sector: Limited exemption
        # Formula: (Salary × 10 months) OR (Salary × Average of previous 3 years)
        # But we'll use simplified approach: Last drawn salary × 10 months OR Rs. 3 lakhs, whichever is less
        max_exempt_limit = Decimal('300000')  # Rs. 3 lakhs
        formula_amount = service_details.last_drawn_salary * Decimal('10')  # 10 months salary
        
        exempt_amount = min(
            leave_encashment_received,
            formula_amount,
            max_exempt_limit
        )
        
        return exempt_amount


class PensionCommutationCalculator:
    """
    Calculator for pension commutation exemption under Section 10(10A).
    
    Pension commutation allows converting part of periodic pension into lump sum.
    The commuted amount has different tax treatment based on employment type.
    """
    
    def calculate_commutation_exemption(
        self,
        pension_commuted: Decimal,
        annual_pension_before_commutation: Decimal,
        commutation_factor: Decimal,
        pension_type: PensionType,
        received_gratuity: bool = False
    ) -> CommutationCalculation:
        """
        Calculate pension commutation exemption.
        
        Args:
            pension_commuted: Amount of pension commuted (lump sum received)
            annual_pension_before_commutation: Annual pension before commutation
            commutation_factor: Commutation factor used
            pension_type: Government or non-government pension
            received_gratuity: Whether employee received gratuity
            
        Returns:
            CommutationCalculation with exemption details
        """
        commuted_value = pension_commuted
        
        if pension_type == PensionType.GOVERNMENT_PENSION:
            # Government pension commutation is fully exempt
            exempt_amount = commuted_value
            taxable_amount = Decimal('0')
            method = "Government pension commutation - fully exempt"
            
        else:
            # Non-government pension commutation
            if received_gratuity:
                # If gratuity received, commutation is fully taxable
                exempt_amount = Decimal('0')
                taxable_amount = commuted_value
                method = "Non-government pension with gratuity - fully taxable"
            else:
                # If no gratuity received, 1/3rd of commuted value is exempt
                exempt_amount = commuted_value / Decimal('3')
                taxable_amount = commuted_value - exempt_amount
                method = "Non-government pension without gratuity - 1/3rd exempt"
        
        return CommutationCalculation(
            pension_commuted=pension_commuted,
            commutation_factor=commutation_factor,
            commuted_value=commuted_value,
            exempt_commutation=exempt_amount,
            taxable_commutation=taxable_amount,
            pension_type=pension_type,
            calculation_method=method
        )


# Utility functions for integration
def calculate_section_10_gratuity_exemption(
    gratuity_received: Decimal,
    years_of_service: Decimal,
    last_drawn_salary: Decimal,
    employment_type: EmploymentType,
    assessment_year: str = "2024-25"
) -> Decimal:
    """
    Utility function to calculate gratuity exemption quickly.
    
    Args:
        gratuity_received: Gratuity amount received
        years_of_service: Total years of service
        last_drawn_salary: Last drawn basic salary + DA
        employment_type: Type of employment
        assessment_year: Assessment year
        
    Returns:
        Exempt gratuity amount
    """
    service_details = ServiceDetails(
        total_service_years=years_of_service,
        total_service_months=int(years_of_service * 12),
        last_drawn_salary=last_drawn_salary
    )
    
    calculator = GratuityCalculator(assessment_year)
    calculation = calculator.calculate_gratuity_exemption(
        gratuity_received, service_details, employment_type
    )
    
    return calculation.exempt_gratuity


def calculate_section_10_leave_encashment_exemption(
    leave_encashment_received: Decimal,
    last_drawn_salary: Decimal,
    employment_type: EmploymentType
) -> Decimal:
    """
    Utility function to calculate leave encashment exemption.
    
    Args:
        leave_encashment_received: Leave encashment amount
        last_drawn_salary: Last drawn salary
        employment_type: Type of employment
        
    Returns:
        Exempt leave encashment amount
    """
    service_details = ServiceDetails(
        total_service_years=Decimal('1'),  # Not used for leave encashment
        total_service_months=12,
        last_drawn_salary=last_drawn_salary
    )
    
    calculator = GratuityCalculator()
    return calculator.calculate_leave_encashment_exemption(
        leave_encashment_received, service_details, employment_type
    )