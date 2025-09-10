"""
Salary Breakdown Analyzer

Analyzes Form16 data to create detailed salary breakdowns with component-wise analysis.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from ..models.salary_breakdown_models import (
    SalaryBreakdown, SalaryComponent, SalaryComponentType, BreakdownDisplayOptions
)
from ..models.form16_models import Form16Document

logger = logging.getLogger(__name__)


class SalaryBreakdownAnalyzer:
    """Analyzes salary data and creates detailed breakdowns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_form16_salary(self, form16_data: Dict[str, Any]) -> SalaryBreakdown:
        """
        Analyze Form16 data and create detailed salary breakdown
        
        Args:
            form16_data: Extracted Form16 data dictionary
            
        Returns:
            SalaryBreakdown: Detailed salary breakdown analysis
        """
        try:
            # Extract basic employee info
            employee_name = self._extract_employee_name(form16_data)
            employer_name = self._extract_employer_name(form16_data)
            assessment_year = self._extract_assessment_year(form16_data)
            
            # Extract salary components
            gross_salary = self._extract_gross_salary(form16_data)
            components = self._extract_salary_components(form16_data)
            total_tds = self._extract_total_tds(form16_data)
            
            # Create breakdown
            breakdown = SalaryBreakdown(
                employee_name=employee_name,
                employer_name=employer_name,
                assessment_year=assessment_year,
                gross_salary=gross_salary,
                components=components,
                total_tds=total_tds
            )
            
            return breakdown
            
        except Exception as e:
            self.logger.error(f"Error analyzing salary breakdown: {e}")
            raise
    
    def _extract_employee_name(self, form16_data: Dict[str, Any]) -> str:
        """Extract employee name from Form16 data"""
        try:
            # Try part_a first
            name = (
                form16_data.get('form16', {})
                .get('part_a', {})
                .get('employee', {})
                .get('name')
            )
            
            # Try employee_declaration as fallback (where name is often found)
            if not name:
                name = (
                    form16_data.get('form16', {})
                    .get('part_b', {})
                    .get('employee_declaration', {})
                    .get('employee_name')
                )
            
            # Try tax_calculations section
            if not name:
                name = (
                    form16_data.get('tax_calculations', {})
                    .get('employee_info', {})
                    .get('name')
                )
            
            return name or 'Unknown Employee'
        except:
            return 'Unknown Employee'
    
    def _extract_employer_name(self, form16_data: Dict[str, Any]) -> str:
        """Extract employer name from Form16 data"""
        try:
            # Try part_a first
            name = (
                form16_data.get('form16', {})
                .get('part_a', {})
                .get('employer', {})
                .get('name')
            )
            
            # Try part_b gross_salary section (where employer name is often found)
            if not name:
                name = (
                    form16_data.get('form16', {})
                    .get('part_b', {})
                    .get('gross_salary', {})
                    .get('employer', {})
                    .get('name')
                )
            
            # Try tax_calculations section
            if not name:
                name = (
                    form16_data.get('tax_calculations', {})
                    .get('employee_info', {})
                    .get('employer')
                )
            
            return name or 'Unknown Employer'
        except:
            return 'Unknown Employer'
    
    def _extract_assessment_year(self, form16_data: Dict[str, Any]) -> str:
        """Extract assessment year from Form16 data"""
        try:
            # Try multiple locations for assessment year
            part_a_year = (
                form16_data.get('form16', {})
                .get('part_a', {})
                .get('assessment_year')
            )
            part_b_year = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('assessment_year')
            )
            
            return part_a_year or part_b_year or '2024-25'
        except:
            return '2024-25'
    
    def _extract_gross_salary(self, form16_data: Dict[str, Any]) -> Decimal:
        """Extract gross salary from Form16 data"""
        try:
            gross_salary = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('gross_salary', {})
                .get('total')
            )
            return Decimal(str(gross_salary)) if gross_salary else Decimal('0')
        except:
            return Decimal('0')
    
    def _extract_total_tds(self, form16_data: Dict[str, Any]) -> Decimal:
        """Extract total TDS from Form16 data"""
        try:
            tds = (
                form16_data.get('form16', {})
                .get('part_a', {})
                .get('quarterly_tds_summary', {})
                .get('total_tds', {})
                .get('deducted')
            )
            return Decimal(str(tds)) if tds else Decimal('0')
        except:
            return Decimal('0')
    
    def _extract_salary_components(self, form16_data: Dict[str, Any]) -> List[SalaryComponent]:
        """Extract detailed salary components from Form16 data"""
        components = []
        
        try:
            gross_salary_data = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('gross_salary', {})
            )
            
            # Basic salary (Section 17(1))
            section_17_1 = gross_salary_data.get('section_17_1_salary')
            if section_17_1:
                components.append(SalaryComponent(
                    type=SalaryComponentType.BASIC_SALARY,
                    amount=Decimal(str(section_17_1)),
                    description="Basic salary and other allowances under Section 17(1)",
                    is_taxable=True
                ))
            
            # Perquisites (Section 17(2))
            section_17_2 = gross_salary_data.get('section_17_2_perquisites')
            if section_17_2 and section_17_2 > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.PERQUISITES,
                    amount=Decimal(str(section_17_2)),
                    description="Perquisites and benefits under Section 17(2)",
                    is_taxable=True
                ))
            
            # Profits in lieu of salary (Section 17(3))
            section_17_3 = gross_salary_data.get('section_17_3_profits_in_lieu')
            if section_17_3 and section_17_3 > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.PROFITS_IN_LIEU,
                    amount=Decimal(str(section_17_3)),
                    description="Profits in lieu of salary under Section 17(3)",
                    is_taxable=True
                ))
            
            # Try to break down Section 17(1) further if possible
            components.extend(self._analyze_section_17_1_breakdown(form16_data, section_17_1))
            
            # Add exemptions as negative components
            components.extend(self._extract_exemption_components(form16_data))
            
        except Exception as e:
            self.logger.warning(f"Error extracting salary components: {e}")
        
        return components
    
    def _analyze_section_17_1_breakdown(self, form16_data: Dict[str, Any], total_17_1: Optional[float]) -> List[SalaryComponent]:
        """Try to break down Section 17(1) into sub-components"""
        components = []
        
        if not total_17_1:
            return components
        
        try:
            # Check for HRA information
            allowances = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('allowances_exempt_under_section_10', {})
            )
            
            hra_exempt = allowances.get('house_rent_allowance')
            if hra_exempt and hra_exempt > 0:
                # Estimate HRA received (typically HRA exempt is portion of HRA received)
                estimated_hra_received = hra_exempt * 1.5  # Rough estimate
                estimated_hra_received = min(estimated_hra_received, total_17_1 * 0.5)  # Cap at 50% of salary
                
                components.append(SalaryComponent(
                    type=SalaryComponentType.HOUSE_RENT_ALLOWANCE,
                    amount=Decimal(str(estimated_hra_received)),
                    description="House Rent Allowance (estimated from exemption)",
                    is_taxable=True
                ))
                
                # Remaining would be basic + other allowances
                remaining = total_17_1 - estimated_hra_received
                if remaining > 0:
                    components.append(SalaryComponent(
                        type=SalaryComponentType.BASIC_SALARY,
                        amount=Decimal(str(remaining)),
                        description="Basic salary and other allowances",
                        is_taxable=True
                    ))
            
            # Check for other allowances
            lta_exempt = allowances.get('leave_travel_allowance')
            if lta_exempt and lta_exempt > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.OTHER_ALLOWANCE,
                    amount=Decimal(str(lta_exempt * 1.2)),  # Estimate total LTA
                    description="Leave Travel Allowance (estimated)",
                    is_taxable=True
                ))
        
        except Exception as e:
            self.logger.warning(f"Error analyzing Section 17(1) breakdown: {e}")
        
        return components
    
    def _extract_exemption_components(self, form16_data: Dict[str, Any]) -> List[SalaryComponent]:
        """Extract exempt allowances as separate components"""
        components = []
        
        try:
            allowances = (
                form16_data.get('form16', {})
                .get('part_b', {})
                .get('allowances_exempt_under_section_10', {})
            )
            
            # HRA exemption
            hra_exempt = allowances.get('house_rent_allowance')
            if hra_exempt and hra_exempt > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.HOUSE_RENT_ALLOWANCE,
                    amount=Decimal(str(-hra_exempt)),  # Negative as it reduces taxable income
                    description="HRA exemption under Section 10(13A)",
                    is_taxable=False
                ))
            
            # LTA exemption
            lta_exempt = allowances.get('leave_travel_allowance')
            if lta_exempt and lta_exempt > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.OTHER_ALLOWANCE,
                    amount=Decimal(str(-lta_exempt)),  # Negative
                    description="LTA exemption under Section 10(5)",
                    is_taxable=False
                ))
            
            # Medical reimbursement
            medical_exempt = allowances.get('medical_reimbursement')
            if medical_exempt and medical_exempt > 0:
                components.append(SalaryComponent(
                    type=SalaryComponentType.MEDICAL_ALLOWANCE,
                    amount=Decimal(str(-medical_exempt)),  # Negative
                    description="Medical reimbursement exemption",
                    is_taxable=False
                ))
        
        except Exception as e:
            self.logger.warning(f"Error extracting exemption components: {e}")
        
        return components
    
    def create_dummy_breakdown(self, income_level: str = "medium") -> SalaryBreakdown:
        """Create a dummy salary breakdown for demo purposes"""
        
        income_configs = {
            "low": {
                "gross": Decimal('600000'),
                "basic": Decimal('300000'),
                "hra": Decimal('120000'),
                "special": Decimal('150000'),
                "transport": Decimal('30000'),
                "tds": Decimal('12000')
            },
            "medium": {
                "gross": Decimal('1200000'),
                "basic": Decimal('600000'),
                "hra": Decimal('240000'),
                "special": Decimal('300000'),
                "transport": Decimal('60000'),
                "tds": Decimal('78724')
            },
            "high": {
                "gross": Decimal('2400000'),
                "basic": Decimal('1200000'),
                "hra": Decimal('480000'),
                "special": Decimal('600000'),
                "transport": Decimal('120000'),
                "tds": Decimal('350000')
            }
        }
        
        config = income_configs.get(income_level, income_configs["medium"])
        
        components = [
            SalaryComponent(
                type=SalaryComponentType.BASIC_SALARY,
                amount=config["basic"],
                description="Basic salary as per employment contract",
                is_taxable=True
            ),
            SalaryComponent(
                type=SalaryComponentType.HOUSE_RENT_ALLOWANCE,
                amount=config["hra"],
                description="House Rent Allowance (40% of basic)",
                is_taxable=True
            ),
            SalaryComponent(
                type=SalaryComponentType.SPECIAL_ALLOWANCE,
                amount=config["special"],
                description="Special allowance and other benefits",
                is_taxable=True
            ),
            SalaryComponent(
                type=SalaryComponentType.TRANSPORT_ALLOWANCE,
                amount=config["transport"],
                description="Transport and conveyance allowance",
                is_taxable=True
            ),
            # HRA exemption (negative component)
            SalaryComponent(
                type=SalaryComponentType.HOUSE_RENT_ALLOWANCE,
                amount=Decimal(str(-config["hra"] * Decimal('0.3'))),  # 30% exemption
                description="HRA exemption under Section 10(13A)",
                is_taxable=False
            )
        ]
        
        return SalaryBreakdown(
            employee_name="Ashish Mittal",
            employer_name="Taxedo Technologies",
            assessment_year="2024-25",
            gross_salary=config["gross"],
            components=components,
            total_tds=config["tds"]
        )