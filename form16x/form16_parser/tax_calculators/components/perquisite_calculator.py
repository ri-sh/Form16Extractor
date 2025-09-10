"""
Enhanced Perquisite Valuation Calculator

Implements comprehensive perquisite valuation as per Income Tax Rules.
Covers various types of perquisites including accommodation, motor car, loans, etc.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import date


class PerquisiteType(Enum):
    """Types of perquisites."""
    ACCOMMODATION = "accommodation"
    MOTOR_CAR = "motor_car"
    INTEREST_FREE_LOAN = "interest_free_loan"
    CLUB_MEMBERSHIP = "club_membership"
    CREDIT_CARD = "credit_card"
    FREE_MEALS = "free_meals"
    HOLIDAY_EXPENSES = "holiday_expenses"
    FREE_EDUCATION = "free_education"
    MEDICAL_TREATMENT = "medical_treatment"
    SWEEPER_GARDENER = "sweeper_gardener"
    GAS_ELECTRICITY_WATER = "gas_electricity_water"
    OTHER_BENEFITS = "other_benefits"
    ESOP_STOCK_OPTIONS = "esop_stock_options"


class AccommodationType(Enum):
    """Types of accommodation provided by employer."""
    OWNED_BY_EMPLOYER = "owned"
    RENTED_BY_EMPLOYER = "rented"
    HOTEL_BOARDING_LODGING = "hotel"


class MotorCarType(Enum):
    """Types of motor car provision."""
    EMPLOYER_OWNED = "employer_owned"
    EMPLOYER_HIRED = "employer_hired" 
    EMPLOYEE_OWNED_EMPLOYER_MAINTAINED = "employee_owned_employer_maintained"


@dataclass
class AccommodationDetails:
    """Details of accommodation perquisite."""
    accommodation_type: AccommodationType
    rent_paid_by_employer: Optional[Decimal] = None
    hotel_charges: Optional[Decimal] = None
    unfurnished_accommodation: bool = True
    city_type: str = "non_metro"  # "metro" or "non_metro"
    

@dataclass
class MotorCarDetails:
    """Details of motor car perquisite."""
    car_type: MotorCarType
    engine_capacity: Optional[Decimal] = None  # in CC
    cost_of_car: Optional[Decimal] = None
    maintenance_cost: Optional[Decimal] = None
    fuel_provided: bool = False
    driver_provided: bool = False
    personal_use_available: bool = True


@dataclass
class LoanDetails:
    """Details of interest-free or concessional loan."""
    loan_amount: Decimal
    interest_rate_charged: Decimal  # Rate charged by employer
    market_interest_rate: Decimal  # Prevailing market rate
    loan_period_months: int


@dataclass
class PerquisiteCalculation:
    """Result of perquisite valuation."""
    perquisite_type: PerquisiteType
    taxable_value: Decimal
    calculation_method: str
    details: Dict[str, any]
    exempt_portion: Decimal = Decimal('0')
    
    @property
    def net_taxable_value(self) -> Decimal:
        """Net taxable value after exemptions."""
        return max(Decimal('0'), self.taxable_value - self.exempt_portion)


class PerquisiteCalculator:
    """
    Enhanced calculator for perquisite valuation as per IT Rules.
    
    Implements detailed valuation rules for different types of perquisites
    including accommodation, motor car, loans, and other benefits.
    """
    
    def __init__(self, assessment_year: str = "2024-25"):
        """Initialize perquisite calculator for given assessment year."""
        self.assessment_year = assessment_year
        self.sbi_rate = self._get_sbi_base_rate(assessment_year)
    
    def _get_sbi_base_rate(self, assessment_year: str) -> Decimal:
        """Get SBI base rate for the assessment year."""
        # These are approximate rates - should be updated with actual SBI rates
        sbi_rates = {
            "2023-24": Decimal('8.50'),
            "2024-25": Decimal('9.00'),
            "2025-26": Decimal('9.50')
        }
        return sbi_rates.get(assessment_year, Decimal('9.00'))
    
    def calculate_accommodation_perquisite(
        self,
        basic_salary: Decimal,
        accommodation_details: AccommodationDetails,
        amount_recovered: Decimal = Decimal('0')
    ) -> PerquisiteCalculation:
        """
        Calculate accommodation perquisite value.
        
        Args:
            basic_salary: Basic salary of employee
            accommodation_details: Details of accommodation provided
            amount_recovered: Amount recovered from employee
            
        Returns:
            PerquisiteCalculation for accommodation
        """
        if accommodation_details.accommodation_type == AccommodationType.OWNED_BY_EMPLOYER:
            # For employer-owned accommodation
            rate_percent = Decimal('15') if accommodation_details.city_type == "metro" else Decimal('10')
            if not accommodation_details.unfurnished_accommodation:
                rate_percent += Decimal('5')  # Additional 5% for furnished
            
            perquisite_value = (basic_salary * rate_percent) / Decimal('100')
            method = f"Basic salary × {rate_percent}% (employer-owned, {'furnished' if not accommodation_details.unfurnished_accommodation else 'unfurnished'})"
            
        elif accommodation_details.accommodation_type == AccommodationType.RENTED_BY_EMPLOYER:
            # For rented accommodation
            if accommodation_details.rent_paid_by_employer:
                rent_paid = accommodation_details.rent_paid_by_employer
                rate_percent = Decimal('15') if accommodation_details.city_type == "metro" else Decimal('10')
                basic_salary_component = (basic_salary * rate_percent) / Decimal('100')
                
                perquisite_value = min(rent_paid, basic_salary_component)
                method = f"Minimum of rent paid ({rent_paid}) and basic salary × {rate_percent}% ({basic_salary_component})"
            else:
                perquisite_value = Decimal('0')
                method = "No rent amount provided"
                
        else:  # Hotel/boarding/lodging
            if accommodation_details.hotel_charges:
                daily_limit = Decimal('1000')  # Rs. 1000 per day limit for hotels
                perquisite_value = min(accommodation_details.hotel_charges, daily_limit * 365)
                method = f"Hotel charges limited to Rs. 1000 per day"
            else:
                perquisite_value = Decimal('0')
                method = "No hotel charges provided"
        
        taxable_value = max(Decimal('0'), perquisite_value - amount_recovered)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.ACCOMMODATION,
            taxable_value=taxable_value,
            calculation_method=method,
            details={
                'gross_perquisite_value': float(perquisite_value),
                'amount_recovered': float(amount_recovered),
                'accommodation_type': accommodation_details.accommodation_type.value,
                'city_type': accommodation_details.city_type
            }
        )
    
    def calculate_motor_car_perquisite(
        self,
        basic_salary: Decimal,
        motor_car_details: MotorCarDetails,
        amount_recovered: Decimal = Decimal('0')
    ) -> PerquisiteCalculation:
        """
        Calculate motor car perquisite value.
        
        Args:
            basic_salary: Basic salary of employee
            motor_car_details: Details of motor car provided
            amount_recovered: Amount recovered from employee
            
        Returns:
            PerquisiteCalculation for motor car
        """
        if not motor_car_details.personal_use_available:
            # No perquisite if car not available for personal use
            return PerquisiteCalculation(
                perquisite_type=PerquisiteType.MOTOR_CAR,
                taxable_value=Decimal('0'),
                calculation_method="No personal use available",
                details={'personal_use': False}
            )
        
        # Determine rate based on engine capacity
        engine_cc = motor_car_details.engine_capacity or Decimal('1600')  # Default assumption
        
        if engine_cc <= 1600:
            monthly_rate = Decimal('1800')
            rate_description = "≤1600 CC"
        else:
            monthly_rate = Decimal('2700')
            rate_description = ">1600 CC"
        
        annual_perquisite = monthly_rate * 12
        
        # Additional perquisite for fuel
        if motor_car_details.fuel_provided:
            fuel_perquisite = Decimal('1200') if engine_cc <= 1600 else Decimal('1800')
            annual_perquisite += fuel_perquisite * 12
            rate_description += " + fuel"
        
        # Additional perquisite for driver
        if motor_car_details.driver_provided:
            driver_perquisite = Decimal('1200') * 12  # Rs. 1000 per month for driver
            annual_perquisite += driver_perquisite
            rate_description += " + driver"
        
        # Special case for employee-owned car maintained by employer
        if motor_car_details.car_type == MotorCarType.EMPLOYEE_OWNED_EMPLOYER_MAINTAINED:
            if motor_car_details.maintenance_cost:
                annual_perquisite = motor_car_details.maintenance_cost
                rate_description = "Actual maintenance cost"
        
        taxable_value = max(Decimal('0'), annual_perquisite - amount_recovered)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.MOTOR_CAR,
            taxable_value=taxable_value,
            calculation_method=f"Motor car perquisite ({rate_description})",
            details={
                'gross_perquisite_value': float(annual_perquisite),
                'amount_recovered': float(amount_recovered),
                'engine_capacity': float(engine_cc) if engine_cc else None,
                'fuel_provided': motor_car_details.fuel_provided,
                'driver_provided': motor_car_details.driver_provided,
                'car_type': motor_car_details.car_type.value
            }
        )
    
    def calculate_loan_perquisite(
        self,
        loan_details: LoanDetails,
        assessment_year: str
    ) -> PerquisiteCalculation:
        """
        Calculate interest-free or concessional loan perquisite.
        
        Args:
            loan_details: Details of loan provided
            assessment_year: Assessment year for calculation
            
        Returns:
            PerquisiteCalculation for loan benefit
        """
        # Interest benefit = (Market rate - Charged rate) × Loan amount × Period
        interest_benefit = (
            (loan_details.market_interest_rate - loan_details.interest_rate_charged)
            * loan_details.loan_amount
            * Decimal(loan_details.loan_period_months)
        ) / (Decimal('100') * Decimal('12'))
        
        # Exemption limit for loan perquisite (Rs. 20,000 for certain loans)
        exempt_limit = Decimal('20000')
        
        taxable_value = max(Decimal('0'), interest_benefit)
        exempt_portion = min(exempt_limit, taxable_value)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.INTEREST_FREE_LOAN,
            taxable_value=taxable_value,
            calculation_method=f"Interest benefit: ({loan_details.market_interest_rate}% - {loan_details.interest_rate_charged}%) × loan amount",
            details={
                'loan_amount': float(loan_details.loan_amount),
                'market_rate': float(loan_details.market_interest_rate),
                'charged_rate': float(loan_details.interest_rate_charged),
                'period_months': loan_details.loan_period_months,
                'interest_benefit': float(interest_benefit)
            },
            exempt_portion=exempt_portion
        )
    
    def calculate_club_membership_perquisite(
        self,
        membership_cost: Decimal,
        entry_fee: Decimal = Decimal('0'),
        annual_subscription: Decimal = Decimal('0'),
        amount_recovered: Decimal = Decimal('0')
    ) -> PerquisiteCalculation:
        """Calculate club membership perquisite."""
        total_cost = membership_cost + entry_fee + annual_subscription
        taxable_value = max(Decimal('0'), total_cost - amount_recovered)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.CLUB_MEMBERSHIP,
            taxable_value=taxable_value,
            calculation_method="Actual cost of club membership",
            details={
                'membership_cost': float(membership_cost),
                'entry_fee': float(entry_fee),
                'annual_subscription': float(annual_subscription),
                'amount_recovered': float(amount_recovered)
            }
        )
    
    def calculate_credit_card_perquisite(
        self,
        annual_charges: Decimal,
        amount_recovered: Decimal = Decimal('0')
    ) -> PerquisiteCalculation:
        """Calculate credit card perquisite."""
        taxable_value = max(Decimal('0'), annual_charges - amount_recovered)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.CREDIT_CARD,
            taxable_value=taxable_value,
            calculation_method="Annual charges for credit card",
            details={
                'annual_charges': float(annual_charges),
                'amount_recovered': float(amount_recovered)
            }
        )
    
    def calculate_free_meals_perquisite(
        self,
        meal_vouchers_value: Decimal,
        canteen_subsidy: Decimal = Decimal('0'),
        amount_recovered: Decimal = Decimal('0')
    ) -> PerquisiteCalculation:
        """Calculate free meals perquisite."""
        # Meal vouchers up to Rs. 50 per meal are exempt (Rs. 1300 per month)
        monthly_exempt_limit = Decimal('1300')
        annual_exempt_limit = monthly_exempt_limit * 12
        
        total_benefit = meal_vouchers_value + canteen_subsidy
        taxable_value = max(Decimal('0'), total_benefit - annual_exempt_limit - amount_recovered)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.FREE_MEALS,
            taxable_value=taxable_value,
            calculation_method="Meal benefits above exempt limit of Rs. 1300/month",
            details={
                'meal_vouchers': float(meal_vouchers_value),
                'canteen_subsidy': float(canteen_subsidy),
                'exempt_limit': float(annual_exempt_limit),
                'amount_recovered': float(amount_recovered)
            },
            exempt_portion=min(annual_exempt_limit, total_benefit)
        )
    
    def calculate_esop_perquisite(
        self,
        shares_allotted: int,
        fair_market_value_per_share: Decimal,
        exercise_price_per_share: Decimal,
        exercise_date: date
    ) -> PerquisiteCalculation:
        """
        Calculate ESOP (Employee Stock Option Plan) perquisite.
        
        Args:
            shares_allotted: Number of shares allotted
            fair_market_value_per_share: FMV on exercise date
            exercise_price_per_share: Price paid by employee
            exercise_date: Date of exercise
            
        Returns:
            PerquisiteCalculation for ESOP benefit
        """
        benefit_per_share = fair_market_value_per_share - exercise_price_per_share
        total_benefit = benefit_per_share * Decimal(shares_allotted)
        
        # ESOP benefits are taxable as perquisites
        taxable_value = max(Decimal('0'), total_benefit)
        
        return PerquisiteCalculation(
            perquisite_type=PerquisiteType.ESOP_STOCK_OPTIONS,
            taxable_value=taxable_value,
            calculation_method=f"(FMV - Exercise Price) × Shares: ({fair_market_value_per_share} - {exercise_price_per_share}) × {shares_allotted}",
            details={
                'shares_allotted': shares_allotted,
                'fmv_per_share': float(fair_market_value_per_share),
                'exercise_price': float(exercise_price_per_share),
                'benefit_per_share': float(benefit_per_share),
                'exercise_date': exercise_date.isoformat()
            }
        )
    
    def calculate_comprehensive_perquisites(
        self,
        basic_salary: Decimal,
        perquisite_details: Dict[str, any]
    ) -> List[PerquisiteCalculation]:
        """
        Calculate all perquisites comprehensively.
        
        Args:
            basic_salary: Basic salary of employee
            perquisite_details: Dictionary containing all perquisite details
            
        Returns:
            List of PerquisiteCalculation for all applicable perquisites
        """
        calculations = []
        
        # Accommodation
        if 'accommodation' in perquisite_details:
            calc = self.calculate_accommodation_perquisite(
                basic_salary,
                perquisite_details['accommodation']['details'],
                perquisite_details['accommodation'].get('amount_recovered', Decimal('0'))
            )
            calculations.append(calc)
        
        # Motor Car
        if 'motor_car' in perquisite_details:
            calc = self.calculate_motor_car_perquisite(
                basic_salary,
                perquisite_details['motor_car']['details'],
                perquisite_details['motor_car'].get('amount_recovered', Decimal('0'))
            )
            calculations.append(calc)
        
        # Add other perquisites as needed...
        
        return calculations
    
    def get_total_taxable_perquisites(self, calculations: List[PerquisiteCalculation]) -> Decimal:
        """Get total taxable value of all perquisites."""
        return sum(calc.net_taxable_value for calc in calculations)