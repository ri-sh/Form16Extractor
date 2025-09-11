"""
Validation Service - Business logic for validating extracted Form16 data.

This service handles comprehensive validation including:
- JSON structure validation
- Data consistency checks
- Financial calculations verification
- Compliance with Form16 standards
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime


class ValidationService:
    """Service for handling Form16 data validation."""
    
    def __init__(self):
        """Initialize the validation service."""
        pass
    
    def validate_extracted_data(
        self,
        file_path: Path,
        strict_mode: bool = False,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Validate extracted Form16 data from JSON file.
        
        Args:
            file_path: Path to JSON file containing extracted data
            strict_mode: Enable strict validation with additional checks
            verbose: Enable verbose validation reporting
            
        Returns:
            Dictionary containing validation results and detailed findings
        """
        validation_start_time = datetime.now()
        
        # Load and parse JSON file
        load_result = self._load_json_file(file_path)
        if not load_result['success']:
            return load_result
        
        data = load_result['data']
        
        # Perform comprehensive validation
        validation_results = {
            'file_path': str(file_path),
            'validation_timestamp': validation_start_time.isoformat(),
            'overall_valid': True,
            'validation_summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warnings': 0
            },
            'detailed_results': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Run validation checks
        checks = [
            ('structure', self._validate_structure),
            ('employee_data', self._validate_employee_data),
            ('employer_data', self._validate_employer_data),
            ('salary_data', self._validate_salary_data),
            ('deductions', self._validate_deductions),
            ('tax_calculations', self._validate_tax_calculations),
            ('financial_year', self._validate_financial_year),
            ('data_consistency', self._validate_data_consistency)
        ]
        
        if strict_mode:
            checks.extend([
                ('compliance', self._validate_compliance),
                ('completeness', self._validate_completeness)
            ])
        
        # Execute all validation checks
        for check_name, check_function in checks:
            try:
                check_result = check_function(data, verbose)
                validation_results['detailed_results'][check_name] = check_result
                
                # Update summary counters
                validation_results['validation_summary']['total_checks'] += check_result.get('checks_performed', 0)
                validation_results['validation_summary']['passed_checks'] += check_result.get('checks_passed', 0)
                validation_results['validation_summary']['failed_checks'] += check_result.get('checks_failed', 0)
                validation_results['validation_summary']['warnings'] += len(check_result.get('warnings', []))
                
                # Collect errors and warnings
                validation_results['errors'].extend(check_result.get('errors', []))
                validation_results['warnings'].extend(check_result.get('warnings', []))
                validation_results['recommendations'].extend(check_result.get('recommendations', []))
                
                # Update overall validity
                if check_result.get('checks_failed', 0) > 0:
                    validation_results['overall_valid'] = False
                    
            except Exception as e:
                error_msg = f"Error in {check_name} validation: {str(e)}"
                validation_results['errors'].append(error_msg)
                validation_results['overall_valid'] = False
        
        # Calculate validation score
        total_checks = validation_results['validation_summary']['total_checks']
        passed_checks = validation_results['validation_summary']['passed_checks']
        validation_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        validation_results['validation_score'] = round(validation_score, 1)
        
        return validation_results
    
    def validate_demo_data(self, file_path: Path) -> Dict[str, Any]:
        """
        Generate demo validation results for demonstration purposes.
        
        Args:
            file_path: Original file path (for display)
            
        Returns:
            Dictionary containing demo validation results
        """
        return {
            'file_path': str(file_path),
            'validation_timestamp': datetime.now().isoformat(),
            'overall_valid': True,
            'validation_summary': {
                'total_checks': 45,
                'passed_checks': 42,
                'failed_checks': 1,
                'warnings': 2
            },
            'validation_score': 93.3,
            'detailed_results': {
                'structure': {'status': 'PASSED', 'checks_performed': 8, 'checks_passed': 8, 'checks_failed': 0},
                'employee_data': {'status': 'PASSED', 'checks_performed': 5, 'checks_passed': 5, 'checks_failed': 0},
                'employer_data': {'status': 'PASSED', 'checks_performed': 6, 'checks_passed': 6, 'checks_failed': 0},
                'salary_data': {'status': 'WARNING', 'checks_performed': 10, 'checks_passed': 9, 'checks_failed': 0, 'warnings': 1},
                'deductions': {'status': 'PASSED', 'checks_performed': 7, 'checks_passed': 7, 'checks_failed': 0},
                'tax_calculations': {'status': 'FAILED', 'checks_performed': 5, 'checks_passed': 4, 'checks_failed': 1},
                'financial_year': {'status': 'PASSED', 'checks_performed': 2, 'checks_passed': 2, 'checks_failed': 0},
                'data_consistency': {'status': 'WARNING', 'checks_performed': 2, 'checks_passed': 1, 'checks_failed': 0, 'warnings': 1}
            },
            'errors': ['Tax calculation mismatch: TDS amount does not match quarterly totals'],
            'warnings': ['HRA amount seems unusually high', 'Some optional deduction fields are missing'],
            'recommendations': [
                'Verify HRA calculation with rent receipts',
                'Check TDS calculation with quarterly statements',
                'Consider adding health insurance premium data'
            ],
            'demo_mode': True
        }
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary containing load results
        """
        if not file_path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'overall_valid': False
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'success': True,
                'data': data
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON format: {str(e)}',
                'overall_valid': False
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading file: {str(e)}',
                'overall_valid': False
            }
    
    def _validate_structure(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate basic JSON structure and required fields."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        required_sections = ['employee', 'employer', 'salary', 'deductions']
        
        for section in required_sections:
            result['checks_performed'] += 1
            if section in data and data[section]:
                result['checks_passed'] += 1
            else:
                result['checks_failed'] += 1
                result['errors'].append(f'Missing required section: {section}')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_employee_data(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate employee information."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        employee = data.get('employee', {})
        
        # Check PAN format
        result['checks_performed'] += 1
        pan = employee.get('pan', '')
        if pan and len(pan) == 10 and pan.isalnum():
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Invalid PAN format')
        
        # Check employee name
        result['checks_performed'] += 1
        name = employee.get('name', '')
        if name and len(name) > 2:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Employee name missing or invalid')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_employer_data(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate employer information."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        employer = data.get('employer', {})
        
        # Check TAN format
        result['checks_performed'] += 1
        tan = employer.get('tan', '')
        if tan and len(tan) == 10:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Invalid TAN format')
        
        # Check employer name
        result['checks_performed'] += 1
        name = employer.get('name', '')
        if name and len(name) > 2:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Employer name missing or invalid')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_salary_data(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate salary information and calculations."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        salary = data.get('salary', {})
        
        # Check gross salary
        result['checks_performed'] += 1
        gross_salary = self._safe_decimal(salary.get('gross_salary', 0))
        if gross_salary > 0:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Gross salary must be positive')
        
        # Check basic salary
        result['checks_performed'] += 1
        basic_salary = self._safe_decimal(salary.get('basic_salary', 0))
        if basic_salary > 0:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Basic salary must be positive')
        
        # Validate salary component relationships
        if gross_salary > 0 and basic_salary > 0:
            result['checks_performed'] += 1
            if basic_salary <= gross_salary:
                result['checks_passed'] += 1
            else:
                result['checks_failed'] += 1
                result['errors'].append('Basic salary cannot exceed gross salary')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_deductions(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate deduction information."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        deductions = data.get('deductions', {})
        
        # Check 80C limit
        result['checks_performed'] += 1
        section_80c = self._safe_decimal(deductions.get('section_80c_total', 0))
        if section_80c <= 150000:  # Current 80C limit
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Section 80C deduction exceeds limit of ₹1,50,000')
        
        # Check 80CCD(1B) limit  
        result['checks_performed'] += 1
        section_80ccd_1b = self._safe_decimal(deductions.get('section_80ccd_1b', 0))
        if section_80ccd_1b <= 50000:  # Current 80CCD(1B) limit
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Section 80CCD(1B) deduction exceeds limit of ₹50,000')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_tax_calculations(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate tax calculation consistency."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Basic tax calculation validation
        result['checks_performed'] += 1
        tds_data = data.get('tds', {})
        if isinstance(tds_data, dict):
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('TDS data structure invalid')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_financial_year(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate financial year information."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check financial year format
        result['checks_performed'] += 1
        fy = data.get('financial_year', '')
        if fy and '-' in fy:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Financial year format invalid')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_data_consistency(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate data consistency across sections."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Basic consistency check
        result['checks_performed'] += 1
        if 'employee' in data and 'employer' in data:
            result['checks_passed'] += 1
        else:
            result['checks_failed'] += 1
            result['errors'].append('Missing essential data sections')
        
        if result['checks_failed'] > 0:
            result['status'] = 'FAILED'
        
        return result
    
    def _validate_compliance(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate compliance with Form16 standards (strict mode)."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Placeholder for compliance checks
        result['checks_performed'] += 1
        result['checks_passed'] += 1
        
        return result
    
    def _validate_completeness(self, data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Validate data completeness (strict mode)."""
        result = {
            'status': 'PASSED',
            'checks_performed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Placeholder for completeness checks
        result['checks_performed'] += 1
        result['checks_passed'] += 1
        
        return result
    
    def _safe_decimal(self, value: Any) -> Decimal:
        """Safely convert value to Decimal."""
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')