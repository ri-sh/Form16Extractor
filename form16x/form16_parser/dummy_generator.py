#!/usr/bin/env python3
"""
Dummy Data Generator for Demo Mode
=================================

Generates realistic but fake data for demo recordings and testing.
All data is clearly marked as fake for demonstration purposes.
"""

import random
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DummyEmployee:
    """Dummy employee data for demos"""
    name: str = "ASHISH MITTAL"
    pan: str = "DEMO12345X" 
    employee_id: str = "EMP001"
    designation: str = "Software Engineer"
    address: str = "123 Koramangala 5th Block, Bangalore - 560034, Karnataka"


@dataclass
class DummyEmployer:
    """Dummy employer data for demos"""
    name: str = "TAXEDO TECHNOLOGIES PRIVATE LIMITED"
    tan: str = "DEMO1234E"
    pan: str = "DEMO12345F"
    address: str = "Taxedo IT Park, Tower 3, 4th Floor, Electronic City Phase 1, Bangalore - 560100, Karnataka"
    contact_number: str = "+91-XX-XXXXXXXX"
    email: str = "hr@taxedo.com"


class DummyDataGenerator:
    """Generates realistic dummy data for demo mode"""
    
    def __init__(self):
        self.employee = DummyEmployee()
        self.employer = DummyEmployer()
    
    def generate_form16_data(self) -> Dict[str, Any]:
        """Generate complete dummy Form16 data"""
        
        # Generate realistic salary figures (25 LPA example)
        gross_salary = 2500000
        basic = int(gross_salary * 0.4)  # 40% basic
        hra = int(gross_salary * 0.3)    # 30% HRA
        special_allowance = gross_salary - basic - hra
        
        # Generate realistic deductions
        section_80c = 150000  # Max 80C
        section_80d = 25000   # Health insurance
        section_80ccd_1b = 50000  # NPS
        
        return {
            "status": "success",
            "metadata": {
                "file_name": "demo_form16.pdf",
                "processing_time_seconds": 3.47,
                "extraction_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "extractor_version": "1.0.0",
                "demo_mode": True
            },
            "form16": {
                "part_a": {
                    "header": {
                        "form_number": "FORM NO. 16",
                        "certificate_number": "DEMO789123"
                    },
                    "employer": {
                        "name": self.employer.name,
                        "address": self.employer.address,
                        "tan": self.employer.tan,
                        "pan": self.employer.pan,
                        "contact_number": self.employer.contact_number,
                        "email": self.employer.email
                    },
                    "employee": {
                        "name": self.employee.name,
                        "pan": self.employee.pan,
                        "employee_id": self.employee.employee_id,
                        "designation": self.employee.designation,
                        "address": self.employee.address
                    },
                    "period": {
                        "assessment_year": "2024-25",
                        "financial_year": "2023-24"
                    },
                    "quarterly_tds_summary": {
                        "q1_apr_jun": {
                            "amount": 45000.0,
                            "deducted": 45000.0,
                            "deposited": 45000.0
                        },
                        "q2_jul_sep": {
                            "amount": 45000.0,
                            "deducted": 45000.0,
                            "deposited": 45000.0
                        },
                        "q3_oct_dec": {
                            "amount": 55000.0,
                            "deducted": 55000.0,
                            "deposited": 55000.0
                        },
                        "q4_jan_mar": {
                            "amount": 55000.0,
                            "deducted": 55000.0,
                            "deposited": 55000.0
                        },
                        "total": {
                            "amount": 200000.0,
                            "deducted": 200000.0,
                            "deposited": 200000.0
                        }
                    }
                },
                "part_b": {
                    "gross_salary": {
                        "section_17_1_salary": gross_salary * 0.85,
                        "section_17_2_perquisites": gross_salary * 0.15,
                        "section_17_3_profits_in_lieu": 0.0,
                        "total": float(gross_salary)
                    },
                    "allowances_exempt_under_section_10": {
                        "house_rent_allowance": hra * 0.6,  # 60% of HRA exempt
                        "leave_travel_allowance": 50000.0,
                        "other_exemptions": [
                            {"description": "Conveyance Allowance", "amount": 19200.0},
                            {"description": "Medical Reimbursement", "amount": 15000.0}
                        ],
                        "total_exemption": (hra * 0.6) + 50000 + 19200 + 15000
                    },
                    "deductions_under_section_16": {
                        "standard_deduction": 50000.0,
                        "professional_tax": 2500.0,
                        "total": 52500.0
                    },
                    "chapter_vi_a_deductions": {
                        "section_80C": {
                            "components": {
                                "ppf_contribution": 100000.0,
                                "life_insurance_premium": 25000.0,
                                "tuition_fees": 25000.0,
                                "nsc": 0.0,
                                "elss_investment": 0.0,
                                "others": 0.0
                            },
                            "total": float(section_80c)
                        },
                        "section_80CCD_1B": float(section_80ccd_1b),
                        "section_80D": {
                            "self_family": float(section_80d),
                            "parents": 0.0,
                            "total": float(section_80d)
                        },
                        "section_80G": 10000.0,
                        "total_chapter_via_deductions": float(section_80c + section_80ccd_1b + section_80d + 10000)
                    },
                    "tax_computation": {
                        "income_chargeable_under_head_salary": float(gross_salary - 655000),  # ₹18.45L after exemptions and deductions
                        "tax_on_total_income": 351000.0,  # Tax before cess
                        "health_and_education_cess": 14040.0,  # 4% cess
                        "total_tax_liability": 365040.0,
                        "tax_payable": 365040.0,
                        "less_tds": 400000.0,
                        "tax_due_refund": 34960.0  # Refund due
                    }
                }
            },
            "extraction_metrics": {
                "confidence_scores": {
                    "employee": {"name": 1.0, "pan": 1.0, "address": 1.0},
                    "employer": {"name": 1.0, "tan": 1.0, "address": 1.0},
                    "salary": {"gross_salary": 1.0, "allowances": 1.0},
                    "deductions": {"section_80c": 1.0, "section_80d": 1.0},
                    "tax": {"tax_computation": 1.0, "tds_summary": 1.0}
                },
                "extraction_summary": {
                    "total_fields": 250,
                    "extracted_fields": 235,
                    "extraction_rate": 94.0,
                    "quality_score": 95.5
                },
                "demo_mode": True
            }
        }
    
    def generate_tax_calculation_results(self) -> Dict[str, Any]:
        """Generate dummy tax calculation results for both regimes"""
        
        return {
            "status": "success",
            "assessment_year": "2024-25",
            "regimes_calculated": ["old", "new"],
            "recommendation": "OLD regime saves Rs 79,560 annually",
            "demo_mode": True,
            # Employee info for display
            "employee_info": {
                "name": self.employee.name,
                "pan": self.employee.pan,
                "employer": self.employer.name,
                "assessment_year": "2024-25"
            },
            # Financial data for calculations
            "financial_data": {
                "section_17_1_salary": 2000000.0,  # 20 LPA basic salary
                "section_17_2_perquisites": 500000.0,  # 5 LPA perquisites  
                "gross_salary": 2500000.0,         # 25 LPA total
                "section_80c": 150000.0,           # Max 80C deduction
                "section_80ccd_1b": 50000.0,       # NPS additional deduction
                "section_80d": 25000.0,            # Health insurance
                "total_tds": 400000.0               # TDS deducted
            },
            # Regime comparison in expected format
            "regime_comparison": {
                "old_regime": {
                    "taxable_income": 1795000.0,  # After all deductions (₹6.55L total deductions)
                    "tax_liability": 365040.0,    # Realistic tax: ₹3,51,000 + 4% cess
                    "tds_paid": 400000.0,         # 16% TDS deduction
                    "refund_due": 34960.0,        # Small refund
                    "tax_due": 0.0,
                    "effective_rate": 14.60,
                    "deductions_used": {
                        "80C": 150000.0,
                        "80CCD(1B)": 50000.0,
                        "80D": 25000.0
                    }
                },
                "new_regime": {
                    "taxable_income": 2425000.0,  # Only ₹75k standard deduction
                    "tax_liability": 444600.0,    # Realistic tax: ₹4,27,500 + 4% cess  
                    "tds_paid": 400000.0,
                    "refund_due": 0.0,
                    "tax_due": 44600.0,           # Additional tax due
                    "effective_rate": 17.78,
                    "deductions_used": {
                        "80C": 0.0,
                        "80CCD(1B)": 50000.0,  # Still allowed in new regime
                        "80D": 0.0
                    }
                }
            },
            "recommended_regime": "old",
            "tax_savings": 79560.0,
            # Legacy format for backward compatibility
            "results": {
                "old": {
                    "gross_income": 2500000.0,
                    "taxable_income": 1795000.0,
                    "tax_liability": 365040.0,
                    "tds_paid": 400000.0,
                    "balance": 34960.0,
                    "status": "refund_due",
                    "effective_tax_rate": 14.60
                },
                "new": {
                    "gross_income": 2500000.0,
                    "taxable_income": 2425000.0,
                    "tax_liability": 444600.0,
                    "tds_paid": 400000.0,
                    "balance": -44600.0,
                    "status": "additional_tax_due",
                    "effective_tax_rate": 17.78
                }
            },
            "comparison": {
                "old_regime_tax": 365040.0,
                "new_regime_tax": 444600.0,
                "savings_with_old": 79560.0,
                "savings_percentage": 17.89
            }
        }
    
    def get_dummy_progress_stages(self) -> List[str]:
        """Get dummy progress stage messages for realistic demo"""
        return [
            "Reading PDF document...",
            "Extracting tables from Form16...", 
            "Classifying table structures...",
            "Processing employee information...",
            "Processing salary details...",
            "Extracting tax deductions...",
            "Computing tax calculations...",
            "Finalizing results..."
        ]
    
    def generate_consolidated_results(self, num_employers: int = 2) -> Dict[str, Any]:
        """Generate dummy consolidated results for multiple employers"""
        
        employers = [
            "TAXEDO TECHNOLOGIES PRIVATE LIMITED",
            "TECH SOLUTIONS INDIA LIMITED", 
            "DIGITAL INNOVATIONS PVT LTD"
        ]
        
        total_gross = 0
        total_tds = 0
        forms_data = []
        
        for i in range(num_employers):
            employer_name = employers[i] if i < len(employers) else f"DEMO EMPLOYER {i+1} LTD"
            gross = 1200000 + (i * 100000)  # Varying salaries totaling ~25L
            tds = gross * 0.16  # 16% TDS (realistic for 25L salary)
            
            total_gross += gross
            total_tds += tds
            
            forms_data.append({
                "employer": employer_name,
                "gross_salary": gross,
                "tds_paid": tds,
                "period": f"Apr-{6+i*6} to Mar-{7+i*6}"  # Different periods
            })
        
        return {
            "status": "success",
            "demo_mode": True,
            "consolidated_summary": {
                "total_employers": num_employers,
                "total_gross_income": total_gross,
                "total_tds_paid": total_tds,
                "consolidated_taxable_income": total_gross - 200000,  # After deductions
                "forms_processed": forms_data
            },
            "tax_calculation": self.generate_tax_calculation_results()
        }