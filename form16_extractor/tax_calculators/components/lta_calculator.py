"""
LTA (Leave Travel Allowance) Exemption Calculator

Implements LTA exemption calculation as per Section 10(5) of Income Tax Act.
LTA exemption is available for domestic travel expenses incurred during leave.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import date, datetime


class TravelMode(Enum):
    """Mode of travel for LTA exemption."""
    AIR = "air"
    TRAIN = "train" 
    BUS = "bus"
    OWN_VEHICLE = "own_vehicle"
    MIXED = "mixed"


class TravelType(Enum):
    """Type of travel for LTA purposes."""
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"  # Not eligible for LTA exemption


@dataclass
class TravelDetails:
    """Travel details for LTA exemption calculation."""
    travel_date: date
    origin: str
    destination: str
    travel_mode: TravelMode
    travel_type: TravelType
    actual_cost: Decimal
    family_members: int = 1  # Including employee
    is_shortest_route: bool = True


@dataclass
class LTAJourney:
    """LTA journey details for block year calculation."""
    journey_id: str
    travel_year: int
    travel_details: List[TravelDetails]  # Onward and return journey
    total_lta_claimed: Decimal
    total_actual_cost: Decimal
    exempt_amount: Decimal
    taxable_amount: Decimal


@dataclass
class LTACalculation:
    """Result of LTA exemption calculation."""
    block_year: str  # e.g., "2022-2025"
    journeys_in_block: List[LTAJourney]
    total_lta_received: Decimal
    total_actual_travel_cost: Decimal
    total_exempt_amount: Decimal
    total_taxable_amount: Decimal
    journeys_utilized: int
    journeys_available: int
    calculation_method: str


class LTACalculator:
    """
    Calculator for LTA exemption under Section 10(5).
    
    Key LTA Rules:
    1. Only DOMESTIC travel is eligible for exemption
    2. Block year concept: 4 calendar years, can claim for 2 journeys
    3. Current block: 2022-2025, Previous: 2018-2021
    4. Journey = To and fro (onward + return) counts as ONE journey
    5. Employee + family members eligible
    6. Exemption = Minimum of (LTA received, Actual travel cost)
    7. Travel should be by shortest route
    8. Only transport cost eligible (not boarding/lodging)
    
    Block Years:
    - 2014-2017: 2 journeys allowed
    - 2018-2021: 2 journeys allowed  
    - 2022-2025: 2 journeys allowed (current block)
    - 2026-2029: 2 journeys allowed (future block)
    """
    
    def __init__(self):
        """Initialize LTA calculator with block year definitions."""
        self.current_block = (2022, 2025)
        self.previous_block = (2018, 2021)
        self.journeys_per_block = 2
        
        # Air fare calculation matrices (these are indicative - actual rates vary)
        # Based on economy class fares for shortest route
        self.air_fare_matrix = self._initialize_air_fare_matrix()
    
    def _initialize_air_fare_matrix(self) -> Dict[str, Dict[str, Decimal]]:
        """Initialize air fare matrix for major Indian cities (indicative rates)."""
        # This is a simplified matrix - in practice, would need comprehensive fare data
        return {
            'delhi': {
                'mumbai': Decimal('8000'),
                'bangalore': Decimal('7500'),
                'chennai': Decimal('8500'),
                'kolkata': Decimal('7000'),
                'hyderabad': Decimal('7000'),
                'pune': Decimal('6500')
            },
            'mumbai': {
                'delhi': Decimal('8000'),
                'bangalore': Decimal('6500'),
                'chennai': Decimal('7500'),
                'kolkata': Decimal('8500'),
                'goa': Decimal('4000')
            },
            'bangalore': {
                'delhi': Decimal('7500'),
                'mumbai': Decimal('6500'),
                'chennai': Decimal('4500'),
                'kolkata': Decimal('8000'),
                'hyderabad': Decimal('3500')
            }
            # Additional cities would be added in production
        }
    
    def calculate_lta_exemption(
        self,
        lta_received: Decimal,
        travel_details: List[TravelDetails],
        assessment_year: str,
        previous_block_journeys: int = 0
    ) -> LTACalculation:
        """
        Calculate LTA exemption for given travel details.
        
        Args:
            lta_received: Total LTA amount received from employer
            travel_details: List of travel details for the journey
            assessment_year: Assessment year (e.g., "2024-25")
            previous_block_journeys: Number of journeys utilized in current block
            
        Returns:
            LTACalculation with detailed exemption breakdown
        """
        # Determine block year from assessment year
        financial_year = int(assessment_year.split('-')[0])
        calendar_year = financial_year - 1  # AY 2024-25 corresponds to CY 2023
        
        block_year_range = self._get_block_year(calendar_year)
        
        # Validate travel eligibility
        eligible_travels = self._filter_eligible_travels(travel_details)
        
        if not eligible_travels:
            return LTACalculation(
                block_year=f"{block_year_range[0]}-{block_year_range[1]}",
                journeys_in_block=[],
                total_lta_received=lta_received,
                total_actual_travel_cost=Decimal('0'),
                total_exempt_amount=Decimal('0'),
                total_taxable_amount=lta_received,
                journeys_utilized=previous_block_journeys,
                journeys_available=self.journeys_per_block,
                calculation_method="No eligible domestic travel found"
            )
        
        # Check if journey quota is available
        journeys_available = self.journeys_per_block - previous_block_journeys
        if journeys_available <= 0:
            return LTACalculation(
                block_year=f"{block_year_range[0]}-{block_year_range[1]}",
                journeys_in_block=[],
                total_lta_received=lta_received,
                total_actual_travel_cost=Decimal('0'),
                total_exempt_amount=Decimal('0'),
                total_taxable_amount=lta_received,
                journeys_utilized=previous_block_journeys,
                journeys_available=0,
                calculation_method="Block year journey quota exhausted"
            )
        
        # Calculate exemption for eligible travel
        total_actual_cost = sum(travel.actual_cost for travel in eligible_travels)
        
        # For air travel, validate against economy class fare for shortest route
        validated_cost = self._validate_travel_costs(eligible_travels)
        
        # LTA exemption = Minimum of (LTA received, Actual/Validated travel cost)
        exempt_amount = min(lta_received, validated_cost)
        taxable_amount = max(Decimal('0'), lta_received - exempt_amount)
        
        # Create journey record
        journey = LTAJourney(
            journey_id=f"journey_{calendar_year}",
            travel_year=calendar_year,
            travel_details=eligible_travels,
            total_lta_claimed=lta_received,
            total_actual_cost=total_actual_cost,
            exempt_amount=exempt_amount,
            taxable_amount=taxable_amount
        )
        
        return LTACalculation(
            block_year=f"{block_year_range[0]}-{block_year_range[1]}",
            journeys_in_block=[journey],
            total_lta_received=lta_received,
            total_actual_travel_cost=total_actual_cost,
            total_exempt_amount=exempt_amount,
            total_taxable_amount=taxable_amount,
            journeys_utilized=previous_block_journeys + 1,
            journeys_available=journeys_available - 1,
            calculation_method="Domestic travel - least of LTA received and actual cost"
        )
    
    def calculate_optimal_lta_planning(
        self,
        annual_lta_component: Decimal,
        block_year_start: int,
        family_size: int = 2
    ) -> Dict[str, any]:
        """
        Calculate optimal LTA planning for tax benefits.
        
        Args:
            annual_lta_component: Annual LTA component in salary
            block_year_start: Start year of current block (e.g., 2022)
            family_size: Number of family members including employee
            
        Returns:
            Dictionary with LTA planning suggestions
        """
        block_lta_amount = annual_lta_component * 4  # 4 years in block
        per_journey_lta = block_lta_amount / 2  # 2 journeys per block
        
        # Calculate typical travel costs for family
        estimated_air_cost_per_person = Decimal('8000')  # Average domestic air fare
        estimated_train_cost_per_person = Decimal('2000')  # Average AC train fare
        
        total_air_cost = estimated_air_cost_per_person * family_size
        total_train_cost = estimated_train_cost_per_person * family_size
        
        # Calculate optimal utilization
        if per_journey_lta >= total_air_cost:
            recommended_mode = "Air travel"
            max_exemption_per_journey = total_air_cost
        else:
            recommended_mode = "Train travel (AC classes)"
            max_exemption_per_journey = min(per_journey_lta, total_train_cost)
        
        total_possible_exemption = max_exemption_per_journey * 2  # 2 journeys
        
        return {
            'block_period': f"{block_year_start}-{block_year_start + 3}",
            'total_lta_in_block': float(block_lta_amount),
            'lta_per_journey': float(per_journey_lta),
            'family_size': family_size,
            'estimated_air_cost_family': float(total_air_cost),
            'estimated_train_cost_family': float(total_train_cost),
            'recommended_travel_mode': recommended_mode,
            'max_exemption_per_journey': float(max_exemption_per_journey),
            'total_possible_exemption': float(total_possible_exemption),
            'utilization_percentage': float((total_possible_exemption / block_lta_amount) * 100),
            'suggestions': [
                f"Plan 2 domestic trips in {block_year_start}-{block_year_start + 3} block",
                f"Use {recommended_mode.lower()} for maximum tax benefit",
                f"Potential tax saving: ₹{total_possible_exemption:,.0f} over 4 years",
                "Keep all travel receipts and ensure shortest route travel"
            ]
        }
    
    def validate_lta_claim(
        self, 
        travel_details: List[TravelDetails],
        lta_claimed: Decimal
    ) -> Tuple[bool, List[str]]:
        """
        Validate LTA claim for compliance.
        
        Args:
            travel_details: Travel details to validate
            lta_claimed: LTA amount claimed
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        is_valid = True
        
        # Check if any international travel
        international_travels = [t for t in travel_details if t.travel_type == TravelType.INTERNATIONAL]
        if international_travels:
            issues.append("International travel is not eligible for LTA exemption")
            is_valid = False
        
        # Check if travel costs seem reasonable
        for travel in travel_details:
            if travel.actual_cost <= 0:
                issues.append(f"Invalid travel cost: ₹{travel.actual_cost}")
                is_valid = False
            
            # Check if air travel cost seems excessive
            if travel.travel_mode == TravelMode.AIR and travel.actual_cost > Decimal('50000'):
                issues.append("Air travel cost seems excessive - verify if correct")
        
        # Check if total claimed cost is reasonable compared to LTA
        total_cost = sum(t.actual_cost for t in travel_details)
        if lta_claimed > total_cost * Decimal('2'):
            issues.append("LTA claimed significantly exceeds travel cost - may be questioned")
        
        return is_valid, issues
    
    def get_block_year_status(self, current_year: int) -> Dict[str, any]:
        """Get current block year status and available journeys."""
        current_block_range = self._get_block_year(current_year)
        
        return {
            'current_block': f"{current_block_range[0]}-{current_block_range[1]}",
            'years_remaining_in_block': current_block_range[1] - current_year,
            'total_journeys_allowed': self.journeys_per_block,
            'block_year_progress': f"{current_year - current_block_range[0] + 1}/4 years"
        }
    
    def _get_block_year(self, calendar_year: int) -> Tuple[int, int]:
        """Get block year range for given calendar year."""
        # Block years are 4-year periods: 2018-2021, 2022-2025, 2026-2029, etc.
        block_start = ((calendar_year - 2018) // 4) * 4 + 2018
        return (block_start, block_start + 3)
    
    def _filter_eligible_travels(self, travel_details: List[TravelDetails]) -> List[TravelDetails]:
        """Filter travels eligible for LTA exemption."""
        return [
            travel for travel in travel_details
            if travel.travel_type == TravelType.DOMESTIC
        ]
    
    def _validate_travel_costs(self, travel_details: List[TravelDetails]) -> Decimal:
        """
        Validate and adjust travel costs based on mode of transport rules.
        
        For air travel: Cost should not exceed economy class fare by shortest route
        For train: Generally accepted as claimed (AC classes)
        For bus: Generally accepted as claimed
        """
        total_validated_cost = Decimal('0')
        
        for travel in travel_details:
            if travel.travel_mode == TravelMode.AIR:
                # For air travel, validate against economy class rates
                max_air_fare = self._get_max_air_fare(travel.origin, travel.destination)
                validated_cost = min(travel.actual_cost, max_air_fare * travel.family_members)
            else:
                # For train/bus, generally accept actual cost
                validated_cost = travel.actual_cost
            
            total_validated_cost += validated_cost
        
        return total_validated_cost
    
    def _get_max_air_fare(self, origin: str, destination: str) -> Decimal:
        """Get maximum allowable air fare for given route."""
        origin_key = origin.lower()
        destination_key = destination.lower()
        
        if origin_key in self.air_fare_matrix and destination_key in self.air_fare_matrix[origin_key]:
            return self.air_fare_matrix[origin_key][destination_key]
        
        # Default maximum air fare if route not in matrix
        return Decimal('15000')  # Conservative estimate


# Utility functions for easy integration
def calculate_lta_exemption_quick(
    lta_received: Decimal,
    actual_travel_cost: Decimal,
    is_domestic: bool = True,
    assessment_year: str = "2024-25"
) -> Decimal:
    """
    Quick utility to calculate LTA exemption.
    
    Args:
        lta_received: LTA amount received
        actual_travel_cost: Actual travel cost incurred
        is_domestic: Whether travel was domestic
        assessment_year: Assessment year
        
    Returns:
        LTA exemption amount
    """
    if not is_domestic:
        return Decimal('0')  # International travel not eligible
    
    # Simple calculation: minimum of LTA received and actual cost
    return min(lta_received, actual_travel_cost)


def get_lta_planning_advice(annual_lta: Decimal, family_size: int = 2) -> List[str]:
    """Get LTA tax planning advice."""
    return [
        f"Plan 2 domestic journeys in each 4-year block period",
        f"With family of {family_size}, consider air travel if LTA > ₹{8000 * family_size:,.0f} per trip",
        f"Annual LTA component: ₹{annual_lta:,.0f} - utilize effectively for tax savings",
        "Keep all travel receipts, tickets, and boarding passes",
        "Ensure travel is by shortest route for air travel exemption",
        "Only transport cost is eligible - not accommodation or food expenses"
    ]