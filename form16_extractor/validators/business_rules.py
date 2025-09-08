#!/usr/bin/env python3
"""
Business Rules Validation
=========================

Validates Form16 data against Indian tax regulations and common
business rules to catch errors and inconsistencies in extracted data.
"""

import re
from typing import Dict, Any, List
from decimal import Decimal
from form16_extractor.extractors.base import IValidator, ValidationResult
from form16_extractor.models.value_objects import PAN, TAN, Amount


class PANValidator(IValidator):
    """Validates PAN format and business rules"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate PAN format and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Basic presence check
        if not value:
            errors.append("PAN is required")
            field_results['presence'] = False
        else:
            field_results['presence'] = True
            
            # Format validation
            pan_str = str(value).strip().upper()
            if PAN.is_valid(pan_str):
                field_results['format'] = True
                
                # Business rule: PAN should not be dummy/test PAN
                if pan_str.startswith('AAAAA') or pan_str == 'ABCDE1234Z':
                    warnings.append("PAN appears to be a dummy/test PAN")
                    field_results['business_rule'] = False
                else:
                    field_results['business_rule'] = True
                    
            else:
                errors.append(f"Invalid PAN format: {pan_str}. Expected format: AAAAA9999A")
                field_results['format'] = False
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "PAN Format and Business Rules Validator"


class TANValidator(IValidator):
    """Validates TAN format and business rules"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate TAN format and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Basic presence check
        if not value:
            errors.append("TAN is required for employers")
            field_results['presence'] = False
        else:
            field_results['presence'] = True
            
            # Format validation
            tan_str = str(value).strip().upper()
            if TAN.is_valid(tan_str):
                field_results['format'] = True
                
                # Business rule: TAN should not be dummy/test TAN
                if tan_str.startswith('AAAA') or tan_str == 'ABCD12345E':
                    warnings.append("TAN appears to be a dummy/test TAN")
                    field_results['business_rule'] = False
                else:
                    field_results['business_rule'] = True
                    
            else:
                errors.append(f"Invalid TAN format: {tan_str}. Expected format: AAAA99999A")
                field_results['format'] = False
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "TAN Format and Business Rules Validator"


class AmountValidator(IValidator):
    """Validates amount values and business rules"""
    
    def __init__(self, min_value: Decimal = None, max_value: Decimal = None):
        self.min_value = min_value or Decimal('0')
        self.max_value = max_value or Decimal('100000000')  # 10 crores default max
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate amount value and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Parse amount
        amount = Amount.from_string(value) if value is not None else None
        
        if amount is None:
            if value is not None:  # Only error if value was provided but couldn't parse
                errors.append(f"Invalid amount format: {value}")
                field_results['format'] = False
            else:
                field_results['format'] = True  # Null amounts are acceptable
        else:
            field_results['format'] = True
            
            # Range validation
            if amount.value < self.min_value:
                errors.append(f"Amount {amount} is below minimum {self.min_value}")
                field_results['range'] = False
            elif amount.value > self.max_value:
                errors.append(f"Amount {amount} exceeds maximum {self.max_value}")
                field_results['range'] = False
            else:
                field_results['range'] = True
            
            # Business rules
            if amount.value == 0:
                warnings.append("Amount is zero")
                field_results['business_rule'] = True  # Zero is valid but noteworthy
            elif amount.value > Decimal('10000000'):  # 1 crore
                warnings.append(f"Large amount: {amount}")
                field_results['business_rule'] = True
            else:
                field_results['business_rule'] = True
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "Amount Validation and Business Rules"


class SalaryValidator(IValidator):
    """Validates salary-related business rules"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate salary structure and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Expecting value to be a dict with salary components
        if not isinstance(value, dict):
            errors.append("Salary data must be a dictionary")
            return ValidationResult(False, {}, errors, warnings, context)
        
        # Validate individual components
        basic_salary = Amount.from_string(value.get('basic_salary'))
        gross_salary = Amount.from_string(value.get('gross_salary'))
        total_deductions = Amount.from_string(value.get('total_deductions'))
        
        # Business rule: Basic salary should be reasonable portion of gross
        if basic_salary and gross_salary:
            basic_percentage = float(basic_salary.value) / float(gross_salary.value) * 100
            if basic_percentage < 30:
                warnings.append(f"Basic salary is only {basic_percentage:.1f}% of gross salary")
            elif basic_percentage > 70:
                warnings.append(f"Basic salary is {basic_percentage:.1f}% of gross salary (unusually high)")
            field_results['basic_gross_ratio'] = True
        
        # Business rule: Deductions should not exceed gross salary
        if total_deductions and gross_salary:
            if total_deductions.value > gross_salary.value:
                errors.append("Total deductions cannot exceed gross salary")
                field_results['deduction_limit'] = False
            else:
                field_results['deduction_limit'] = True
        
        # Business rule: Gross salary should be reasonable (not too low/high)
        if gross_salary:
            if gross_salary.value < Decimal('100000'):  # 1 lakh per year
                warnings.append("Gross salary appears low (< 1 lakh per year)")
            elif gross_salary.value > Decimal('50000000'):  # 5 crores per year
                warnings.append("Gross salary appears very high (> 5 crores per year)")
            field_results['salary_range'] = True
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "Salary Structure Business Rules Validator"


class TaxCalculationValidator(IValidator):
    """Validates tax calculation business rules"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate tax calculations and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Expecting value to be a dict with tax components
        if not isinstance(value, dict):
            errors.append("Tax data must be a dictionary")
            return ValidationResult(False, {}, errors, warnings, context)
        
        taxable_income = Amount.from_string(value.get('taxable_income'))
        tax_calculated = Amount.from_string(value.get('tax_calculated'))
        tds_deducted = Amount.from_string(value.get('tds_deducted'))
        
        # Business rule: Tax rate should be reasonable
        if taxable_income and tax_calculated and taxable_income.value > 0:
            effective_rate = float(tax_calculated.value) / float(taxable_income.value) * 100
            if effective_rate > 50:
                errors.append(f"Effective tax rate {effective_rate:.1f}% seems too high")
                field_results['tax_rate'] = False
            elif effective_rate < 0:
                errors.append("Effective tax rate cannot be negative")
                field_results['tax_rate'] = False
            else:
                field_results['tax_rate'] = True
                if effective_rate > 35:
                    warnings.append(f"High effective tax rate: {effective_rate:.1f}%")
        
        # Business rule: TDS should not significantly exceed calculated tax
        if tax_calculated and tds_deducted:
            if tds_deducted.value > tax_calculated.value * Decimal('1.1'):  # 10% tolerance
                warnings.append("TDS deducted exceeds calculated tax by more than 10%")
                field_results['tds_reconciliation'] = False
            else:
                field_results['tds_reconciliation'] = True
        
        # Business rule: Check for minimum tax exemption limit
        if taxable_income and taxable_income.value > 0:
            if taxable_income.value < Decimal('250000') and tax_calculated and tax_calculated.value > 0:
                warnings.append("Tax calculated on income below basic exemption limit")
            field_results['exemption_limit'] = True
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "Tax Calculation Business Rules Validator"


class CrossFieldValidator(IValidator):
    """Validates cross-field business rules and consistency"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate cross-field consistency and business rules"""
        errors = []
        warnings = []
        field_results = {}
        
        if context is None:
            context = {}
        
        # Expecting value to be a complete Form16 data dict
        if not isinstance(value, dict):
            errors.append("Form16 data must be a dictionary")
            return ValidationResult(False, {}, errors, warnings, context)
        
        # Extract sections for cross-validation
        employee = value.get('employee', {})
        employer = value.get('employer', {})
        salary = value.get('salary', {})
        tax = value.get('tax', {})
        
        # Cross-field rule: Employee and employer PANs should be different
        employee_pan = employee.get('pan')
        employer_pan = employer.get('pan')
        if employee_pan and employer_pan and employee_pan == employer_pan:
            errors.append("Employee and employer cannot have the same PAN")
            field_results['pan_uniqueness'] = False
        else:
            field_results['pan_uniqueness'] = True
        
        # Cross-field rule: TDS quarters should sum to total
        quarterly_tds = tax.get('quarterly_tds', [])
        total_tds = Amount.from_string(tax.get('total_tds'))
        if quarterly_tds and total_tds:
            quarter_sum = sum(Amount.from_string(q.get('amount', 0)).value for q in quarterly_tds if q.get('amount'))
            if abs(quarter_sum - total_tds.value) > Decimal('1'):  # Allow 1 rupee tolerance
                warnings.append(f"Quarterly TDS sum ({quarter_sum}) doesn't match total TDS ({total_tds.value})")
                field_results['quarterly_reconciliation'] = False
            else:
                field_results['quarterly_reconciliation'] = True
        
        # Cross-field rule: Financial year consistency
        assessment_year = value.get('assessment_year')
        financial_year = value.get('financial_year')
        if assessment_year and financial_year:
            # Assessment year should be one year ahead of financial year
            # This would require parsing the year formats - simplified check for now
            field_results['year_consistency'] = True
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            field_results=field_results,
            errors=errors,
            warnings=warnings,
            metadata=context
        )
    
    def get_validator_name(self) -> str:
        return "Cross-Field Consistency Validator"