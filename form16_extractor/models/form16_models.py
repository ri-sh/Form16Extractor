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
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class TaxRegime(str, Enum):
    """Tax regime enumeration"""
    OLD = "old"
    NEW = "new"


class PAN(BaseModel):
    """PAN (Permanent Account Number) value object with validation"""
    value: str = Field(..., min_length=10, max_length=10)
    
    @field_validator('value')
    @classmethod
    def validate_pan_format(cls, v):
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_pattern, v.upper()):
            raise ValueError(f"Invalid PAN format: {v}")
        return v.upper()


class TAN(BaseModel):
    """TAN (Tax Deduction Account Number) value object with validation"""
    value: str = Field(..., min_length=10, max_length=10)
    
    @field_validator('value')  
    @classmethod
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
    department: Optional[str] = None
    employment_type: Optional[str] = None
    employee_id: Optional[str] = None
    
    @field_validator('pan')
    @classmethod
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
    
    @field_validator('tan')
    @classmethod
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
    
    # Detailed perquisite breakdown from Form 12BA
    detailed_perquisites: Dict[str, float] = Field(default_factory=dict)
    
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
        """Convert to standard Form16 JSON format matching form16_json_structure.json"""
        import datetime
        
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "status": "success",
            "metadata": {
                "file_name": self.processing_metadata.get("file_name", "unknown.pdf"),
                "processing_time_seconds": self.processing_metadata.get("processing_time", 0.0),
                "extraction_timestamp": timestamp,
                "extractor_version": "1.0.0"
            },
            "form16": {
                "part_a": {
                    "header": {
                        "form_number": "FORM NO. 16",
                        "rule_reference": "[See rule 31(1)(a)]",
                        "certificate_description": "Certificate under Section 203 of the Income-tax Act, 1961",
                        "certificate_number": self.metadata.certificate_number if self.metadata else None,
                        "last_updated": None
                    },
                    "employer": {
                        "name": self.employer.name if self.employer else None,
                        "address": self.employer.address if self.employer else None,
                        "tan": self.employer.tan if self.employer else None,
                        "pan": self.employer.pan if self.employer else None,
                        "contact_number": None,
                        "email": None
                    },
                    "employee": {
                        "name": self.employee.name if self.employee else None,
                        "pan": self.employee.pan if self.employee else None,
                        "address": self.employee.address if self.employee else None,
                        "employee_reference_number": None
                    },
                    "employment_period": {
                        "from": None,
                        "to": None
                    },
                    "assessment_year": None,
                    "quarterly_tds_summary": self._format_quarterly_tds_summary(),
                    "verification": {
                        "place": None,
                        "date": None,
                        "person_responsible": {
                            "name": None,
                            "designation": None,
                            "father_name": None
                        }
                    }
                },
                "part_b": {
                    "header": {
                        "form_number": "FORM NO. 16",
                        "part": "PART B",
                        "certificate_description": "Details of Salary Paid and any other income and tax deducted",
                        "certificate_number": None,
                        "last_updated": None
                    },
                    "financial_year": None,
                    "assessment_year": None,
                    "employee_status": {
                        "is_director": False,
                        "has_substantial_interest": False,
                        "opted_out_of_115bac": None
                    },
                    "gross_salary": self._format_salary_breakdown(),
                    "allowances_exempt_under_section_10": self._format_exemptions(),
                    "deductions_under_section_16": self._format_section16_deductions(),
                    "chapter_vi_a_deductions": self._format_chapter_via_deductions(),
                    "tax_computation": self._format_tax_computation(),
                    "employee_declaration": {
                        "declaration_date": None,
                        "place": None,
                        "employee_name": self.employee.name if self.employee else None
                    }
                }
            },
            "extraction_metrics": {
                "confidence_scores": {
                    "employee": self._get_confidence_scores("employee"),
                    "employer": self._get_confidence_scores("employer"),
                    "salary": self._get_confidence_scores("salary"),
                    "deductions": self._get_confidence_scores("deductions"),
                    "tax": self._get_confidence_scores("tax")
                },
                "extraction_summary": self.get_extraction_summary()
            }
        }
    
    def _format_quarterly_tds_summary(self) -> Dict[str, Any]:
        """Format quarterly TDS data for part_a structure"""
        quarters = {"quarter_1": {}, "quarter_2": {}, "quarter_3": {}, "quarter_4": {}}
        
        for i, q in enumerate(self.quarterly_tds[:4]):
            quarter_key = f"quarter_{i+1}"
            quarters[quarter_key] = {
                "period": None,
                "receipt_numbers": [q.receipt_number] if q.receipt_number else [],
                "amount_deducted": float(q.tax_deducted) if q.tax_deducted else None,
                "amount_deposited": float(q.tax_deposited) if q.tax_deposited else None,
                "deposited_date": None,
                "status": None
            }
        
        total_deducted = sum(float(q.tax_deducted or 0) for q in self.quarterly_tds)
        total_deposited = sum(float(q.tax_deposited or 0) for q in self.quarterly_tds)
        
        quarters["total_tds"] = {
            "deducted": total_deducted if total_deducted > 0 else None,
            "deposited": total_deposited if total_deposited > 0 else None
        }
        
        return quarters
    
    def _format_salary_breakdown(self) -> Dict[str, Any]:
        """Format salary data for part_b gross_salary structure"""
        if not self.salary:
            return {
                "section_17_1_salary": None,
                "section_17_2_perquisites": None, 
                "section_17_3_profits_in_lieu": None,
                "total": None,
                "salary_from_other_employers": None
            }
        
        return {
            "section_17_1_salary": float(self.salary.salary_section_17_1) if self.salary.salary_section_17_1 else None,
            "section_17_2_perquisites": float(self.salary.perquisites_value) if self.salary.perquisites_value else None,
            "section_17_3_profits_in_lieu": float(self.salary.profit_in_lieu) if self.salary.profit_in_lieu is not None else None,
            "total": float(self.salary.gross_salary) if self.salary.gross_salary else None,
            "salary_from_other_employers": None
        }
    
    def _format_exemptions(self) -> Dict[str, Any]:
        """Format exemptions for part_b structure"""
        if not self.salary:
            return {
                "house_rent_allowance": None,
                "leave_travel_allowance": None,
                "gratuity": None,
                "commuted_pension": None,
                "cash_equivalent_of_leave": None,
                "other_exemptions": [],
                "total_exemption": None
            }
        
        return {
            "house_rent_allowance": float(self.salary.hra_exemption) if self.salary.hra_exemption else None,
            "leave_travel_allowance": None,
            "gratuity": None,
            "commuted_pension": None,
            "cash_equivalent_of_leave": None,
            "other_exemptions": [],
            "total_exemption": float(self.salary.other_exemptions) if self.salary.other_exemptions else None
        }
    
    def _format_section16_deductions(self) -> Dict[str, Any]:
        """Format Section 16 deductions"""
        if not self.section16_deductions:
            return {
                "standard_deduction": None,
                "entertainment_allowance": None,
                "professional_tax": None,
                "total": None
            }
        
        return {
            "standard_deduction": float(self.section16_deductions.standard_deduction) if self.section16_deductions.standard_deduction else None,
            "entertainment_allowance": float(self.section16_deductions.entertainment_allowance) if self.section16_deductions.entertainment_allowance else None,
            "professional_tax": float(self.section16_deductions.professional_tax) if self.section16_deductions.professional_tax else None,
            "total": float(self.section16_deductions.total_section_16) if self.section16_deductions.total_section_16 else None
        }
    
    def _format_chapter_via_deductions(self) -> Dict[str, Any]:
        """Format Chapter VI-A deductions with comprehensive structure"""
        if not self.chapter_via_deductions:
            return {"total_deductions": None}
        
        return {
            "section_80C": {
                "components": {
                    "life_insurance_premium": float(self.chapter_via_deductions.life_insurance_premium) if self.chapter_via_deductions.life_insurance_premium else None,
                    "provident_fund": float(self.chapter_via_deductions.ppf_contribution) if self.chapter_via_deductions.ppf_contribution else None,
                    "ppf": None,
                    "nsc": None,
                    "ulip": None,
                    "tuition_fees": None,
                    "principal_repayment_housing_loan": None,
                    "sukanya_samriddhi": None,
                    "fixed_deposit_5years": None,
                    "others": None
                },
                "gross_amount": float(self.chapter_via_deductions.section_80c_total) if self.chapter_via_deductions.section_80c_total else None,
                "deductible_amount": float(self.chapter_via_deductions.section_80c_total) if self.chapter_via_deductions.section_80c_total else None
            },
            "total_deductions": float(self.chapter_via_deductions.total_chapter_via_deductions) if self.chapter_via_deductions.total_chapter_via_deductions else None
        }
    
    def _format_tax_computation(self) -> Dict[str, Any]:
        """Format tax computation data"""
        if not self.tax_computation:
            return {
                "tax_on_total_income": None,
                "total_tax_liability": None,
                "health_and_education_cess": None
            }
        
        return {
            "tax_on_total_income": float(self.tax_computation.tax_on_total_income) if self.tax_computation.tax_on_total_income else None,
            "total_tax_liability": float(self.tax_computation.total_tax_liability) if self.tax_computation.total_tax_liability else None,
            "health_and_education_cess": float(self.tax_computation.health_education_cess) if self.tax_computation.health_education_cess else None
        }
    
    def _get_confidence_scores(self, section: str) -> Dict[str, float]:
        """Get confidence scores for a section"""
        # Default confidence scores - can be enhanced with actual confidence data
        default_scores = {
            "employee": {"name": 0.95, "pan": 0.95, "address": 0.7},
            "employer": {"name": 0.9, "tan": 0.95, "address": 0.9},
            "salary": {},
            "deductions": {},
            "tax": {}
        }
        return default_scores.get(section, {})


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