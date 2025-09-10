"""
Multi-company Form16 consolidation system.

Handles consolidation of multiple Form16s from different employers
for the same financial year as per Indian Income Tax rules.
"""

from typing import List, Dict, Optional, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

from ..models.form16_models import Form16Document
from ..utils.validation import ValidationError
from ..exceptions.consolidation_exceptions import ConsolidationError


class ConsolidationStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ConsolidationWarning:
    type: str
    message: str
    affected_employers: List[str]
    severity: str = "medium"


@dataclass
class ConsolidatedSalaryData:
    """Consolidated salary data from multiple employers."""
    
    # Aggregate salary components
    total_section_17_1_salary: Decimal = Decimal('0')
    total_section_17_2_perquisites: Decimal = Decimal('0')
    total_section_17_3_profits: Decimal = Decimal('0')
    total_gross_salary: Decimal = Decimal('0')
    
    # Employer-wise breakdown
    employer_wise_salary: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)
    
    # Quarterly aggregation
    quarterly_breakdown: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)


@dataclass
class ConsolidatedTDSData:
    """Consolidated TDS data from multiple employers."""
    
    total_tds_deducted: Decimal = Decimal('0')
    total_tds_deposited: Decimal = Decimal('0')
    
    # Employer-wise TDS
    employer_wise_tds: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)
    
    # Quarter-wise aggregation
    quarterly_tds: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)
    
    # Receipt numbers for verification
    all_receipt_numbers: List[str] = field(default_factory=list)


@dataclass
class ConsolidatedDeductionsData:
    """Consolidated deductions with duplicate detection."""
    
    # Section-wise consolidated amounts
    section_80c_total: Decimal = Decimal('0')
    section_80d_total: Decimal = Decimal('0')
    section_80ccd_1b_total: Decimal = Decimal('0')
    
    # Other deductions
    other_deductions: Dict[str, Decimal] = field(default_factory=dict)
    
    # Duplicate detection results
    potential_duplicates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Employer-wise claimed deductions
    employer_wise_deductions: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)


@dataclass
class ConsolidationResult:
    """Result of multi-company Form16 consolidation."""
    
    status: ConsolidationStatus
    employee_pan: str
    financial_year: str
    assessment_year: str
    
    # Consolidated data
    salary_data: ConsolidatedSalaryData
    tds_data: ConsolidatedTDSData
    deductions_data: ConsolidatedDeductionsData
    
    # Source information
    source_employers: List[str]
    form16_count: int
    
    # Validation results
    warnings: List[ConsolidationWarning] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    
    # Processing metadata
    processing_timestamp: str = ""
    consolidation_confidence: float = 0.0


class MultiCompanyForm16Consolidator:
    """
    Consolidates multiple Form16s from different employers for the same employee.
    
    Implements Indian tax rules for handling multiple employers in the same FY:
    - Aggregates salary income from all sources
    - Consolidates TDS deductions
    - Detects duplicate deduction claims
    - Validates against tax compliance rules
    """
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def consolidate_form16s(self, form16_list: List[Form16Document]) -> ConsolidationResult:
        """
        Consolidate multiple Form16s for the same employee.
        
        Args:
            form16_list: List of extracted Form16 document objects
            
        Returns:
            ConsolidationResult with aggregated data and validation results
        """
        if not form16_list:
            raise ValidationError("No Form16 data provided for consolidation")
        
        # Validate input data
        self._validate_form16_consistency(form16_list)
        
        # Extract common information
        employee_pan = form16_list[0].part_a.employee.pan
        financial_year = self._determine_financial_year(form16_list)
        assessment_year = self._determine_assessment_year(financial_year)
        
        # Consolidate different components
        salary_data = self._consolidate_salary_data(form16_list)
        tds_data = self._consolidate_tds_data(form16_list)
        deductions_data = self._consolidate_deductions(form16_list)
        
        # Perform validations
        warnings = self._validate_consolidated_data(salary_data, tds_data, deductions_data)
        
        # Calculate confidence score
        confidence = self._calculate_consolidation_confidence(form16_list, warnings)
        
        result = ConsolidationResult(
            status=ConsolidationStatus.SUCCESS if not warnings else ConsolidationStatus.WARNING,
            employee_pan=employee_pan,
            financial_year=financial_year,
            assessment_year=assessment_year,
            salary_data=salary_data,
            tds_data=tds_data,
            deductions_data=deductions_data,
            source_employers=[f16.part_a.employer.name for f16 in form16_list],
            form16_count=len(form16_list),
            warnings=warnings,
            consolidation_confidence=confidence
        )
        
        return result
    
    def _validate_form16_consistency(self, form16_list: List[Form16Document]) -> None:
        """Validate that all Form16s belong to same employee and FY."""
        
        if len(form16_list) < 2:
            return
            
        base_pan = form16_list[0].part_a.employee.pan
        base_name = form16_list[0].part_a.employee.name
        base_fy = self._extract_financial_year_from_form16(form16_list[0])
        
        for i, form16 in enumerate(form16_list[1:], 1):
            # Check PAN consistency
            if form16.part_a.employee.pan != base_pan:
                raise ValidationError(
                    f"PAN mismatch: Form16 #{i} has {form16.part_a.employee.pan}, "
                    f"expected {base_pan}"
                )
            
            # Check name consistency (allowing for minor variations)
            if not self._names_match(form16.part_a.employee.name, base_name):
                raise ValidationError(
                    f"Employee name mismatch: Form16 #{i} has '{form16.part_a.employee.name}', "
                    f"base name is '{base_name}'"
                )
            
            # Check financial year consistency
            current_fy = self._extract_financial_year_from_form16(form16)
            if current_fy and base_fy and current_fy != base_fy:
                raise ValidationError(
                    f"Financial year mismatch: Form16 #{i} is for FY {current_fy}, "
                    f"but base Form16 is for FY {base_fy}. Cannot consolidate Form16s from different years."
                )
    
    def _consolidate_salary_data(self, form16_list: List[Form16Document]) -> ConsolidatedSalaryData:
        """Consolidate salary data from all employers."""
        
        consolidated = ConsolidatedSalaryData()
        
        for form16 in form16_list:
            employer_name = form16.part_a.employer.name
            part_b = form16.part_b
            
            # Aggregate totals
            if part_b.gross_salary.section_17_1_salary:
                consolidated.total_section_17_1_salary += Decimal(str(part_b.gross_salary.section_17_1_salary))
            
            if part_b.gross_salary.section_17_2_perquisites:
                consolidated.total_section_17_2_perquisites += Decimal(str(part_b.gross_salary.section_17_2_perquisites))
            
            if part_b.gross_salary.section_17_3_profits_in_lieu:
                consolidated.total_section_17_3_profits += Decimal(str(part_b.gross_salary.section_17_3_profits_in_lieu))
            
            if part_b.gross_salary.total:
                consolidated.total_gross_salary += Decimal(str(part_b.gross_salary.total))
            
            # Store employer-wise breakdown
            consolidated.employer_wise_salary[employer_name] = {
                'section_17_1': Decimal(str(part_b.gross_salary.section_17_1_salary or 0)),
                'section_17_2': Decimal(str(part_b.gross_salary.section_17_2_perquisites or 0)),
                'section_17_3': Decimal(str(part_b.gross_salary.section_17_3_profits_in_lieu or 0)),
                'total': Decimal(str(part_b.gross_salary.total or 0))
            }
            
            # Aggregate quarterly data if available
            if hasattr(form16.part_a, 'quarterly_tds_summary'):
                for quarter, data in form16.part_a.quarterly_tds_summary.__dict__.items():
                    if quarter.startswith('quarter_') and hasattr(data, 'amount_paid_credited'):
                        if quarter not in consolidated.quarterly_breakdown:
                            consolidated.quarterly_breakdown[quarter] = {}
                        
                        consolidated.quarterly_breakdown[quarter][employer_name] = Decimal(
                            str(data.amount_paid_credited or 0)
                        )
        
        return consolidated
    
    def _consolidate_tds_data(self, form16_list: List[Form16Document]) -> ConsolidatedTDSData:
        """Consolidate TDS data from all employers."""
        
        consolidated = ConsolidatedTDSData()
        
        for form16 in form16_list:
            employer_name = form16.part_a.employer.name
            
            # Aggregate total TDS
            if hasattr(form16.part_a.quarterly_tds_summary, 'total_tds'):
                if form16.part_a.quarterly_tds_summary.total_tds.deducted:
                    consolidated.total_tds_deducted += Decimal(
                        str(form16.part_a.quarterly_tds_summary.total_tds.deducted)
                    )
                
                if form16.part_a.quarterly_tds_summary.total_tds.deposited:
                    consolidated.total_tds_deposited += Decimal(
                        str(form16.part_a.quarterly_tds_summary.total_tds.deposited)
                    )
            
            # Store employer-wise TDS
            tds_deducted = Decimal(str(form16.part_a.quarterly_tds_summary.total_tds.deducted or 0))
            tds_deposited = Decimal(str(form16.part_a.quarterly_tds_summary.total_tds.deposited or 0))
            
            consolidated.employer_wise_tds[employer_name] = {
                'deducted': tds_deducted,
                'deposited': tds_deposited
            }
            
            # Collect receipt numbers
            for quarter_name in ['quarter_1', 'quarter_2', 'quarter_3', 'quarter_4']:
                quarter_data = getattr(form16.part_a.quarterly_tds_summary, quarter_name, None)
                if quarter_data and hasattr(quarter_data, 'receipt_numbers'):
                    consolidated.all_receipt_numbers.extend(quarter_data.receipt_numbers or [])
        
        return consolidated
    
    def _consolidate_deductions(self, form16_list: List[Form16Document]) -> ConsolidatedDeductionsData:
        """Consolidate deductions with duplicate detection."""
        
        consolidated = ConsolidatedDeductionsData()
        section_80c_claims = []
        section_80d_claims = []
        section_80ccd_1b_claims = []
        
        for form16 in form16_list:
            employer_name = form16.part_a.employer.name
            deductions = form16.part_b.chapter_vi_a_deductions
            
            # Track claims per employer for duplicate detection
            employer_deductions = {}
            
            # Section 80C
            if deductions.section_80C and deductions.section_80C.deductible_amount:
                amount = Decimal(str(deductions.section_80C.deductible_amount))
                section_80c_claims.append({
                    'employer': employer_name,
                    'amount': amount,
                    'components': deductions.section_80C.components.__dict__ if deductions.section_80C.components else {}
                })
                employer_deductions['section_80C'] = amount
            
            # Section 80D
            if deductions.section_80D and deductions.section_80D.deductible_amount:
                amount = Decimal(str(deductions.section_80D.deductible_amount))
                section_80d_claims.append({
                    'employer': employer_name,
                    'amount': amount
                })
                employer_deductions['section_80D'] = amount
            
            # Section 80CCD(1B)
            if deductions.section_80CCD_1B and deductions.section_80CCD_1B.deductible_amount:
                amount = Decimal(str(deductions.section_80CCD_1B.deductible_amount))
                section_80ccd_1b_claims.append({
                    'employer': employer_name,
                    'amount': amount
                })
                employer_deductions['section_80CCD_1B'] = amount
            
            consolidated.employer_wise_deductions[employer_name] = employer_deductions
        
        # Detect duplicates and consolidate
        consolidated.section_80c_total, duplicates_80c = self._detect_and_consolidate_deductions(
            section_80c_claims, "Section 80C", limit=150000
        )
        consolidated.section_80d_total, duplicates_80d = self._detect_and_consolidate_deductions(
            section_80d_claims, "Section 80D", limit=25000
        )
        consolidated.section_80ccd_1b_total, duplicates_80ccd = self._detect_and_consolidate_deductions(
            section_80ccd_1b_claims, "Section 80CCD(1B)", limit=50000
        )
        
        consolidated.potential_duplicates.extend(duplicates_80c + duplicates_80d + duplicates_80ccd)
        
        return consolidated
    
    def _detect_and_consolidate_deductions(
        self, 
        claims: List[Dict], 
        section_name: str, 
        limit: int
    ) -> tuple[Decimal, List[Dict]]:
        """Detect duplicate deduction claims and consolidate properly."""
        
        if not claims:
            return Decimal('0'), []
        
        duplicates = []
        total_claimed = sum(claim['amount'] for claim in claims)
        
        # Check for over-limit claims
        if total_claimed > limit:
            duplicates.append({
                'type': 'over_limit',
                'section': section_name,
                'claimed_amount': float(total_claimed),
                'limit': limit,
                'excess': float(total_claimed - limit),
                'employers': [claim['employer'] for claim in claims]
            })
        
        # Check for identical claims (potential duplicates)
        claim_amounts = [claim['amount'] for claim in claims]
        unique_amounts = set(claim_amounts)
        
        if len(unique_amounts) < len(claim_amounts):
            # Found duplicate amounts
            for amount in unique_amounts:
                employers_with_amount = [
                    claim['employer'] for claim in claims if claim['amount'] == amount
                ]
                if len(employers_with_amount) > 1:
                    duplicates.append({
                        'type': 'duplicate_amount',
                        'section': section_name,
                        'amount': float(amount),
                        'employers': employers_with_amount
                    })
        
        # Return the maximum allowable amount (respecting limits)
        final_amount = min(total_claimed, Decimal(str(limit)))
        return final_amount, duplicates
    
    def _validate_consolidated_data(
        self, 
        salary_data: ConsolidatedSalaryData,
        tds_data: ConsolidatedTDSData,
        deductions_data: ConsolidatedDeductionsData
    ) -> List[ConsolidationWarning]:
        """Validate consolidated data for consistency and compliance."""
        
        warnings = []
        
        # Check TDS vs Salary ratio
        if salary_data.total_gross_salary > 0:
            tds_ratio = float(tds_data.total_tds_deducted / salary_data.total_gross_salary)
            if tds_ratio > 0.35:  # More than 35% TDS seems high
                warnings.append(ConsolidationWarning(
                    type="high_tds_ratio",
                    message=f"TDS ratio is {tds_ratio:.2%}, which seems high",
                    affected_employers=list(salary_data.employer_wise_salary.keys()),
                    severity="medium"
                ))
        
        # Check for potential duplicate deductions
        if deductions_data.potential_duplicates:
            warnings.append(ConsolidationWarning(
                type="duplicate_deductions",
                message=f"Found {len(deductions_data.potential_duplicates)} potential duplicate deduction claims",
                affected_employers=[],
                severity="high"
            ))
        
        # Check TDS deducted vs deposited mismatch
        if abs(tds_data.total_tds_deducted - tds_data.total_tds_deposited) > Decimal('1'):
            warnings.append(ConsolidationWarning(
                type="tds_mismatch",
                message="TDS deducted and deposited amounts do not match",
                affected_employers=list(tds_data.employer_wise_tds.keys()),
                severity="high"
            ))
        
        return warnings
    
    def _calculate_consolidation_confidence(
        self, 
        form16_list: List[Form16Document], 
        warnings: List[ConsolidationWarning]
    ) -> float:
        """Calculate confidence score for the consolidation."""
        
        base_confidence = 0.9
        
        # Reduce confidence for warnings
        for warning in warnings:
            if warning.severity == "high":
                base_confidence -= 0.2
            elif warning.severity == "medium":
                base_confidence -= 0.1
        
        # Reduce confidence for incomplete data
        incomplete_count = 0
        for form16 in form16_list:
            if not form16.part_b.gross_salary.total:
                incomplete_count += 1
        
        if incomplete_count > 0:
            base_confidence -= (incomplete_count / len(form16_list)) * 0.3
        
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_financial_year(self, form16_list: List[Form16Document]) -> str:
        """Determine financial year from Form16 data."""
        # Try to extract from the first Form16
        first_fy = self._extract_financial_year_from_form16(form16_list[0])
        if first_fy:
            return first_fy
        
        # Fallback to current assessment year
        return "2023-24"
    
    def _extract_financial_year_from_form16(self, form16: Form16Document) -> Optional[str]:
        """
        Extract financial year from Form16 document.
        
        Attempts multiple approaches to determine the financial year:
        1. Direct field from Part A
        2. Assessment year minus 1
        3. Employment period dates
        4. Quarterly TDS period dates
        """
        # Method 1: Direct financial year field
        if hasattr(form16.part_a, 'financial_year') and form16.part_a.financial_year:
            return form16.part_a.financial_year
        
        # Method 2: Assessment year field
        if hasattr(form16.part_a, 'assessment_year') and form16.part_a.assessment_year:
            ay = form16.part_a.assessment_year
            # Convert AY to FY (AY 2024-25 -> FY 2023-24)
            try:
                ay_parts = ay.split('-')
                if len(ay_parts) == 2:
                    fy_start = int(ay_parts[0]) - 1
                    fy_end = int(ay_parts[1]) - 1
                    return f"{fy_start}-{fy_end:02d}"
            except (ValueError, AttributeError):
                pass
        
        # Method 3: Employment period
        if (hasattr(form16.part_a, 'employment_period') and 
            form16.part_a.employment_period and
            form16.part_a.employment_period.from_date):
            
            from_date = form16.part_a.employment_period.from_date
            # If employment starts between April-March, determine FY
            try:
                if hasattr(from_date, 'year'):
                    year = from_date.year
                    month = from_date.month
                    if month >= 4:  # April onwards = start of FY
                        return f"{year}-{(year + 1) % 100:02d}"
                    else:  # Jan-Mar = end of FY
                        return f"{year - 1}-{year % 100:02d}"
            except (AttributeError, ValueError):
                pass
        
        # Method 4: Quarterly periods (check Quarter 1 which is Apr-Jun)
        if (hasattr(form16.part_a, 'quarterly_tds_summary') and
            hasattr(form16.part_a.quarterly_tds_summary, 'quarter_1') and
            form16.part_a.quarterly_tds_summary.quarter_1.period):
            
            q1_period = form16.part_a.quarterly_tds_summary.quarter_1.period
            # Quarter 1 period format could be "Apr 2023 - Jun 2023"
            try:
                import re
                year_match = re.search(r'(\d{4})', str(q1_period))
                if year_match:
                    year = int(year_match.group(1))
                    return f"{year}-{(year + 1) % 100:02d}"
            except (ValueError, AttributeError, TypeError):
                # Failed to parse year from document - continue without it
                pass
        
        return None
    
    def _determine_assessment_year(self, financial_year: str) -> str:
        """Convert financial year to assessment year."""
        fy_parts = financial_year.split('-')
        if len(fy_parts) == 2:
            ay_start = int(fy_parts[0]) + 1
            ay_end = int(fy_parts[1]) + 1
            return f"{ay_start}-{ay_end:02d}"
        return ""
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names are similar (allowing minor variations)."""
        name1_clean = name1.strip().upper().replace('.', '').replace(',', '')
        name2_clean = name2.strip().upper().replace('.', '').replace(',', '')
        return name1_clean == name2_clean
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for consolidation."""
        return {
            'max_tds_ratio': 0.35,
            'section_80c_limit': 150000,
            'section_80d_limit': 25000,
            'section_80ccd_1b_limit': 50000
        }