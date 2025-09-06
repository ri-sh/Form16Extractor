"""
Form 16 Domain Models
====================

Comprehensive data models for all Form 16 fields with validation.
Designed to handle ANY Form 16 document structure robustly.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator, root_validator
import re


class TaxRegime(str, Enum):
    """Tax regime enumeration"""
    OLD = "old"
    NEW = "new"


class PAN(BaseModel):
    """PAN (Permanent Account Number) value object with validation"""
    value: str = Field(..., min_length=10, max_length=10)
    
    @validator('value')
    def validate_pan_format(cls, v):
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_pattern, v.upper()):
            raise ValueError(f"Invalid PAN format: {v}")
        return v.upper()


class TAN(BaseModel):
    """TAN (Tax Deduction Account Number) value object with validation"""
    value: str = Field(..., min_length=10, max_length=10)
    
    @validator('value')
    def validate_tan_format(cls, v):
        tan_pattern = r'^[A-Z]{4}[0-9]{5}[A-Z]{1}$'
        if not re.match(tan_pattern, v.upper()):
            raise ValueError(f"Invalid TAN format: {v}")
        return v.upper()


class Amount(BaseModel):
    """Amount value object with currency handling"""
    value: Decimal = Field(..., ge=0)
    currency: str = Field(default="INR")
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __add__(self, other):
        if isinstance(other, Amount):
            return Amount(value=self.value + other.value, currency=self.currency)
        return Amount(value=self.value + Decimal(str(other)), currency=self.currency)


class EmployeeInfo(BaseModel):
    """Employee information from Form 16"""
    name: Optional[str] = None
    pan: Optional[str] = None  # Will validate as PAN when populated
    address: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    employee_id: Optional[str] = None
    
    @validator('pan')
    def validate_employee_pan(cls, v):
        if v:
            try:
                return PAN(value=v).value
            except ValueError:
                return None  # Don't fail, just mark as invalid
        return v


class EmployerInfo(BaseModel):
    """Employer information from Form 16"""
    name: Optional[str] = None
    tan: Optional[str] = None  # Will validate as TAN when populated
    pan: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator('tan')
    def validate_employer_tan(cls, v):
        if v:
            try:
                return TAN(value=v).value
            except ValueError:
                return None
        return v


class SalaryBreakdown(BaseModel):
    """Comprehensive salary breakdown - ALL possible fields"""
    # Basic salary components
    basic_salary: Optional[Decimal] = Field(default=None, ge=0)
    dearness_allowance: Optional[Decimal] = Field(default=None, ge=0)
    
    # Allowances (Section 17(1))
    hra_received: Optional[Decimal] = Field(default=None, ge=0)
    transport_allowance: Optional[Decimal] = Field(default=None, ge=0)
    medical_allowance: Optional[Decimal] = Field(default=None, ge=0)
    special_allowance: Optional[Decimal] = Field(default=None, ge=0)
    overtime_allowance: Optional[Decimal] = Field(default=None, ge=0)
    commission_bonus: Optional[Decimal] = Field(default=None, ge=0)
    leave_travel_allowance: Optional[Decimal] = Field(default=None, ge=0)
    food_allowance: Optional[Decimal] = Field(default=None, ge=0)
    phone_allowance: Optional[Decimal] = Field(default=None, ge=0)
    other_allowances: Optional[Decimal] = Field(default=None, ge=0)
    
    # Perquisites (Section 17(2))
    perquisites_value: Optional[Decimal] = Field(default=None, ge=0)
    stock_options: Optional[Decimal] = Field(default=None, ge=0)
    accommodation_perquisite: Optional[Decimal] = Field(default=None, ge=0)
    car_perquisite: Optional[Decimal] = Field(default=None, ge=0)
    other_perquisites: Optional[Decimal] = Field(default=None, ge=0)
    
    # Profits in lieu of salary (Section 17(3))
    profit_in_lieu: Optional[Decimal] = Field(default=None, ge=0)
    
    # Calculated totals
    total_allowances: Optional[Decimal] = Field(default=None, ge=0)
    gross_salary: Optional[Decimal] = Field(default=None, ge=0)
    salary_section_17_1: Optional[Decimal] = Field(default=None, ge=0)
    total_income_section_17: Optional[Decimal] = Field(default=None, ge=0)
    
    # Exemptions and deductions
    hra_exemption: Optional[Decimal] = Field(default=None, ge=0)
    transport_exemption: Optional[Decimal] = Field(default=None, ge=0)
    other_exemptions: Optional[Decimal] = Field(default=None, ge=0)
    
    # Net amounts
    net_taxable_salary: Optional[Decimal] = Field(default=None, ge=0)
    
    def get_non_zero_fields(self) -> Dict[str, Decimal]:
        """Get all fields with non-zero values"""
        return {k: v for k, v in self.dict().items() 
                if v is not None and v > 0}
    
    def calculate_totals(self):
        """Calculate derived totals from components"""
        # Calculate total allowances
        allowance_fields = [
            'basic_salary', 'dearness_allowance', 'hra_received', 'transport_allowance',
            'medical_allowance', 'special_allowance', 'overtime_allowance', 'commission_bonus',
            'leave_travel_allowance', 'food_allowance', 'phone_allowance', 'other_allowances'
        ]
        
        if self.total_allowances is None:
            allowance_sum = sum(getattr(self, field) or 0 for field in allowance_fields)
            if allowance_sum > 0:
                self.total_allowances = allowance_sum
        
        # Calculate gross salary
        if self.gross_salary is None:
            gross = (self.total_allowances or 0) + (self.perquisites_value or 0) + (self.profit_in_lieu or 0)
            if gross > 0:
                self.gross_salary = gross


class TaxDeductionQuarterly(BaseModel):
    """Quarterly TDS breakdown"""
    quarter: str  # Q1, Q2, Q3, Q4
    amount_paid: Optional[Decimal] = Field(default=None, ge=0)
    tax_deducted: Optional[Decimal] = Field(default=None, ge=0)
    tax_deposited: Optional[Decimal] = Field(default=None, ge=0)
    receipt_number: Optional[str] = None
    deposit_date: Optional[date] = None
    challan_number: Optional[str] = None
    bsr_code: Optional[str] = None


class ChapterVIADeductions(BaseModel):
    """Chapter VI-A deductions - ALL sections"""
    # Section 80C
    section_80c_total: Optional[Decimal] = Field(default=None, ge=0)
    ppf_contribution: Optional[Decimal] = Field(default=None, ge=0)
    elss_investment: Optional[Decimal] = Field(default=None, ge=0)
    life_insurance_premium: Optional[Decimal] = Field(default=None, ge=0)
    home_loan_principal: Optional[Decimal] = Field(default=None, ge=0)
    nsc_investment: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80CCC
    section_80ccc: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80CCD
    section_80ccd_1: Optional[Decimal] = Field(default=None, ge=0)
    section_80ccd_1b: Optional[Decimal] = Field(default=None, ge=0)
    section_80ccd_2: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80D - Medical insurance
    section_80d_self_family: Optional[Decimal] = Field(default=None, ge=0)
    section_80d_parents: Optional[Decimal] = Field(default=None, ge=0)
    section_80d_total: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80E - Education loan interest
    section_80e: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80G - Donations
    section_80g: Optional[Decimal] = Field(default=None, ge=0)
    
    # Section 80TTA - Savings account interest
    section_80tta: Optional[Decimal] = Field(default=None, ge=0)
    
    # Other sections
    section_80u: Optional[Decimal] = Field(default=None, ge=0)  # Disability
    section_80gg: Optional[Decimal] = Field(default=None, ge=0)  # HRA without employer
    
    # Total deductions
    total_chapter_via_deductions: Optional[Decimal] = Field(default=None, ge=0)


class Section16Deductions(BaseModel):
    """Section 16 deductions"""
    standard_deduction: Optional[Decimal] = Field(default=None, ge=0)
    entertainment_allowance: Optional[Decimal] = Field(default=None, ge=0)
    professional_tax: Optional[Decimal] = Field(default=None, ge=0)
    total_section_16: Optional[Decimal] = Field(default=None, ge=0)


class TaxComputation(BaseModel):
    """Tax computation details"""
    # Income calculation
    gross_total_income: Optional[Decimal] = Field(default=None, ge=0)
    total_deductions: Optional[Decimal] = Field(default=None, ge=0)
    net_taxable_income: Optional[Decimal] = Field(default=None, ge=0)
    
    # Tax calculation
    tax_on_total_income: Optional[Decimal] = Field(default=None, ge=0)
    surcharge: Optional[Decimal] = Field(default=None, ge=0)
    health_education_cess: Optional[Decimal] = Field(default=None, ge=0)
    total_tax_liability: Optional[Decimal] = Field(default=None, ge=0)
    
    # Rebates and reliefs
    rebate_87a: Optional[Decimal] = Field(default=None, ge=0)
    relief_section_89: Optional[Decimal] = Field(default=None, ge=0)
    
    # Final calculation
    tax_payable: Optional[Decimal] = Field(default=None, ge=0)
    total_tds: Optional[Decimal] = Field(default=None, ge=0)
    refund_or_payable: Optional[Decimal] = Field(default=None)
    
    # Tax regime
    tax_regime: Optional[TaxRegime] = None


class Form16Metadata(BaseModel):
    """Form 16 certificate metadata"""
    certificate_number: Optional[str] = None
    assessment_year: Optional[str] = None
    financial_year: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    issue_date: Optional[date] = None
    last_updated: Optional[date] = None
    form16_type: Optional[str] = None  # e.g., "Regular", "Revised"
    reference_number: Optional[str] = None


class Form16Document(BaseModel):
    """Complete Form 16 document model - ROBUST for ANY Form 16"""
    # Core information
    metadata: Form16Metadata = Field(default_factory=Form16Metadata)
    employee: EmployeeInfo = Field(default_factory=EmployeeInfo)
    employer: EmployerInfo = Field(default_factory=EmployerInfo)
    
    # Financial data
    salary: SalaryBreakdown = Field(default_factory=SalaryBreakdown)
    quarterly_tds: List[TaxDeductionQuarterly] = Field(default_factory=list)
    chapter_via_deductions: ChapterVIADeductions = Field(default_factory=ChapterVIADeductions)
    section16_deductions: Section16Deductions = Field(default_factory=Section16Deductions)
    tax_computation: TaxComputation = Field(default_factory=TaxComputation)
    
    # Quality metrics
    extraction_confidence: Dict[str, float] = Field(default_factory=dict)
    extraction_errors: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    
    # Raw data preservation
    raw_tables: List[Dict[str, Any]] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get comprehensive extraction summary"""
        total_fields = self._count_total_fields()
        extracted_fields = self._count_extracted_fields()
        
        return {
            "total_possible_fields": total_fields,
            "extracted_fields": extracted_fields,
            "extraction_rate": (extracted_fields / total_fields * 100) if total_fields > 0 else 0,
            "confidence_scores": self.extraction_confidence,
            "missing_critical_fields": self.missing_fields,
            "extraction_errors": self.extraction_errors,
            "quality_score": self._calculate_quality_score()
        }
    
    def _count_total_fields(self) -> int:
        """Count all possible extractable fields"""
        # This is approximate - can be refined based on specific requirements
        return (
            len(EmployeeInfo.__fields__) +
            len(EmployerInfo.__fields__) + 
            len(SalaryBreakdown.__fields__) +
            len(ChapterVIADeductions.__fields__) +
            len(Section16Deductions.__fields__) +
            len(TaxComputation.__fields__) +
            len(Form16Metadata.__fields__) +
            4  # for quarterly TDS
        )
    
    def _count_extracted_fields(self) -> int:
        """Count successfully extracted fields"""
        count = 0
        
        # Count non-None fields in each section
        for field_name, field_value in self.employee.dict().items():
            if field_value is not None and str(field_value).strip():
                count += 1
                
        for field_name, field_value in self.employer.dict().items():
            if field_value is not None and str(field_value).strip():
                count += 1
                
        for field_name, field_value in self.salary.dict().items():
            if field_value is not None and field_value != 0:
                count += 1
                
        # Add other sections...
        count += len([q for q in self.quarterly_tds if q.tax_deducted and q.tax_deducted > 0])
        
        return count
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall extraction quality score"""
        if not self.extraction_confidence:
            return 0.0
            
        avg_confidence = sum(self.extraction_confidence.values()) / len(self.extraction_confidence)
        completeness = self._count_extracted_fields() / self._count_total_fields()
        error_penalty = max(0, 1 - len(self.extraction_errors) * 0.1)
        
        return (avg_confidence * 0.4 + completeness * 0.5 + error_penalty * 0.1) * 100
    
    def to_json_output(self) -> Dict[str, Any]:
        """Convert to clean JSON output for CLI"""
        return {
            "form16_data": {
                "employee_info": self.employee.dict(exclude_none=True),
                "employer_info": self.employer.dict(exclude_none=True),
                "salary_breakdown": self.salary.dict(exclude_none=True),
                "quarterly_tds": [q.dict(exclude_none=True) for q in self.quarterly_tds],
                "deductions": {
                    "chapter_vi_a": self.chapter_via_deductions.dict(exclude_none=True),
                    "section_16": self.section16_deductions.dict(exclude_none=True)
                },
                "tax_computation": self.tax_computation.dict(exclude_none=True),
                "metadata": self.metadata.dict(exclude_none=True)
            },
            "extraction_summary": self.get_extraction_summary(),
            "processing_info": self.processing_metadata
        }


class ExtractionResult(BaseModel):
    """Result container for extraction operations"""
    success: bool
    form16_document: Optional[Form16Document] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    
    def to_cli_output(self) -> Dict[str, Any]:
        """Convert to CLI-friendly output format"""
        if self.success and self.form16_document:
            output = self.form16_document.to_json_output()
            output["status"] = "success"
            output["processing_time_seconds"] = self.processing_time
            if self.warnings:
                output["warnings"] = self.warnings
            return output
        else:
            return {
                "status": "error",
                "error": self.error_message,
                "processing_time_seconds": self.processing_time,
                "warnings": self.warnings
            }