"""
Unit tests for Form16 Models
============================

Tests for all Form16 domain models including validation and functionality.
"""

import pytest
from decimal import Decimal
from datetime import date
from pydantic import ValidationError
from form16x.form16_parser.models.form16_models import (
    PAN, TAN, Amount, EmployeeInfo, EmployerInfo, SalaryBreakdown,
    TaxDeductionQuarterly, ChapterVIADeductions, Section16Deductions,
    TaxComputation, Form16Metadata, Form16Document, ExtractionResult
)


class TestPANValidation:
    """Test PAN value object validation"""
    
    def test_valid_pan_format(self):
        """Test valid PAN formats are accepted"""
        valid_pans = [
            "ABCDE1234F",
            "ZZZZZ9999A",
            "AAAAA1111A"
        ]
        
        for pan_str in valid_pans:
            pan = PAN(value=pan_str)
            assert pan.value == pan_str.upper()
    
    def test_invalid_pan_format(self):
        """Test invalid PAN formats are rejected"""
        with pytest.raises(ValueError):
            PAN(value="ABC12345E")  # Too short
        
        with pytest.raises(ValueError):
            PAN(value="1ABCD1234F")  # Invalid format
        
        with pytest.raises(ValueError):
            PAN(value="ABCD11234F")  # Wrong length


class TestTANValidation:
    """Test TAN value object validation"""
    
    def test_valid_tan_format(self):
        """Test valid TAN formats are accepted"""
        valid_tans = [
            "ABCD12345E",
            "ZZZZ99999A",
            "AAAA11111A"
        ]
        
        for tan_str in valid_tans:
            tan = TAN(value=tan_str)
            assert tan.value == tan_str.upper()
    
    def test_invalid_tan_format(self):
        """Test invalid TAN formats are rejected"""
        with pytest.raises(ValueError):
            TAN(value="ABC12345E")  # Too short
        
        with pytest.raises(ValueError):
            TAN(value="1ABC12345E")  # Invalid format


class TestAmountValueObject:
    """Test Amount value object"""
    
    def test_amount_creation(self):
        """Test Amount object creation and validation"""
        amount = Amount(value=Decimal("50000.00"))
        assert amount.value == Decimal("50000.00")
        assert amount.currency == "INR"
        assert float(amount) == 50000.0
    
    def test_amount_addition(self):
        """Test Amount arithmetic operations"""
        amount1 = Amount(value=Decimal("25000"))
        amount2 = Amount(value=Decimal("35000"))
        
        result = amount1 + amount2
        assert result.value == Decimal("60000")
    
    def test_negative_amount_rejected(self):
        """Test negative amounts are rejected"""
        with pytest.raises(ValidationError):
            Amount(value=Decimal("-1000"))


class TestEmployeeInfo:
    """Test EmployeeInfo model"""
    
    def test_employee_creation_with_valid_data(self):
        """Test creating employee with valid data"""
        employee = EmployeeInfo(
            name="John Doe",
            pan="ABCDE1234F",
            designation="Software Engineering SMTS",
            employee_id="EMP123"
        )
        
        assert employee.name == "John Doe"
        assert employee.pan == "ABCDE1234F"
        assert employee.designation == "Software Engineering SMTS"
        assert employee.employee_id == "EMP123"
    
    def test_employee_with_invalid_pan_handled_gracefully(self):
        """Test invalid PAN doesn't break the model"""
        employee = EmployeeInfo(
            name="Test User",
            pan="INVALID_PAN"  # This should not raise exception
        )
        
        # Invalid PAN should be set to None, not raise exception
        assert employee.name == "Test User"
        assert employee.pan is None
    
    def test_employee_creation_with_minimal_data(self):
        """Test creating employee with minimal required data"""
        employee = EmployeeInfo()
        
        assert employee.name is None
        assert employee.pan is None
        assert employee.designation is None


class TestEmployerInfo:
    """Test EmployerInfo model"""
    
    def test_employer_creation_with_valid_data(self):
        """Test creating employer with valid data"""
        employer = EmployerInfo(
            name="SAMPLE COMPANY PRIVATE LIMITED",
            tan="ABCD12345E",
            pan="ABCDE1234F",
            address="Sample Building, 3rd Floor, Sample Business Park"
        )
        
        assert employer.name == "SAMPLE COMPANY PRIVATE LIMITED"
        assert employer.tan == "ABCD12345E"
        assert employer.pan == "ABCDE1234F"
        assert employer.address == "Sample Building, 3rd Floor, Sample Business Park"
    
    def test_employer_with_invalid_tan_handled_gracefully(self):
        """Test invalid TAN doesn't break the model"""
        employer = EmployerInfo(
            name="Test Company",
            tan="INVALID_TAN"  # This should not raise exception
        )
        
        # Invalid TAN should be set to None
        assert employer.name == "Test Company"
        assert employer.tan is None


class TestSalaryBreakdown:
    """Test SalaryBreakdown model functionality"""
    
    def test_salary_breakdown_creation(self):
        """Test creating salary breakdown with various fields"""
        salary = SalaryBreakdown(
            basic_salary=Decimal("1500000"),
            hra_received=Decimal("400000"),
            special_allowance=Decimal("200000"),
            perquisites_value=Decimal("300000")
        )
        
        assert salary.basic_salary == Decimal("1500000")
        assert salary.hra_received == Decimal("400000")
        assert salary.special_allowance == Decimal("200000")
        assert salary.perquisites_value == Decimal("300000")
    
    def test_salary_total_calculation(self):
        """Test automatic calculation of salary totals"""
        salary = SalaryBreakdown(
            basic_salary=Decimal("400000"),
            hra_received=Decimal("200000"),
            transport_allowance=Decimal("25000"),
            medical_allowance=Decimal("15000")
        )
        
        salary.calculate_totals()
        
        # Total allowances should be sum of all allowance components
        expected_total = Decimal("640000")  # Sum of all above
        assert salary.total_allowances == expected_total
    
    def test_get_non_zero_fields(self):
        """Test getting only fields with values"""
        salary = SalaryBreakdown(
            basic_salary=Decimal("1500000"),
            hra_received=Decimal("0"),  # Zero value
            transport_allowance=Decimal("25000")
        )
        
        non_zero = salary.get_non_zero_fields()
        
        assert "basic_salary" in non_zero
        assert "transport_allowance" in non_zero
        assert "hra_received" not in non_zero  # Zero value excluded


class TestTaxDeductionQuarterly:
    """Test quarterly TDS model"""
    
    def test_quarterly_tds_creation(self):
        """Test creating quarterly TDS record"""
        q1_tds = TaxDeductionQuarterly(
            quarter="Q1",
            receipt_number="SAMPLE123",
            amount_paid=Decimal("500000.00"),
            tax_deducted=Decimal("100000.00"),
            tax_deposited=Decimal("100000.00")
        )
        
        assert q1_tds.quarter == "Q1"
        assert q1_tds.tax_deducted == Decimal("100000.00")
        assert q1_tds.amount_paid == Decimal("500000.00")
        assert q1_tds.receipt_number == "SAMPLE123"


class TestChapterVIADeductions:
    """Test Chapter VI-A deductions model"""
    
    def test_chapter_via_deductions_creation(self):
        """Test creating Chapter VI-A deductions"""
        deductions = ChapterVIADeductions(
            section_80c_total=Decimal("150000"),
            ppf_contribution=Decimal("100000"),
            section_80d_total=Decimal("25000"),
            section_80e=Decimal("50000")
        )
        
        assert deductions.section_80c_total == Decimal("150000")
        assert deductions.ppf_contribution == Decimal("100000")
        assert deductions.section_80d_total == Decimal("25000")
        assert deductions.section_80e == Decimal("50000")


class TestForm16Document:
    """Test complete Form16 document model"""
    
    def test_form16_document_creation(self):
        """Test creating a complete Form16 document"""
        form16 = Form16Document()
        
        # Should have all required sections
        assert form16.employee is not None
        assert form16.employer is not None
        assert form16.salary is not None
        assert form16.metadata is not None
        
        # Should have empty collections
        assert isinstance(form16.quarterly_tds, list)
        assert isinstance(form16.extraction_confidence, dict)
        assert isinstance(form16.extraction_errors, list)
    
    def test_extraction_summary_calculation(self):
        """Test extraction summary calculation"""
        form16 = Form16Document()
        
        # Add some data
        form16.employee.name = "Test Employee"
        form16.employee.pan = "AAAAA1111A"
        form16.salary.basic_salary = Decimal("1500000")
        
        # Update confidence scores
        form16.extraction_confidence = {
            "employee_name": 0.95,
            "employee_pan": 0.98,
            "basic_salary": 0.90
        }
        
        summary = form16.get_extraction_summary()
        
        assert summary["total_possible_fields"] > 0
        assert summary["extracted_fields"] > 0
        assert 0 <= summary["extraction_rate"] <= 100
        assert summary["quality_score"] >= 0
    
    def test_json_output_format(self):
        """Test JSON output format for CLI"""
        form16 = Form16Document()
        form16.employee.name = "Test Employee"
        form16.salary.basic_salary = Decimal("1500000")
        
        json_output = form16.to_json_output()
        
        # Should have required structure for CLI
        assert "status" in json_output
        assert "form16" in json_output
        assert "extraction_metrics" in json_output
        
        # Form16 data should have all sections
        form16_data = json_output["form16"]
        assert "part_a" in form16_data
        assert "part_b" in form16_data


class TestExtractionResult:
    """Test ExtractionResult for CLI output"""
    
    def test_successful_result(self):
        """Test successful extraction result"""
        form16 = Form16Document()
        form16.employee.name = "Test Employee"
        
        result = ExtractionResult(
            success=True,
            form16_document=form16,
            processing_time=2.5
        )
        
        cli_output = result.to_cli_output()
        
        assert cli_output["status"] == "success"
        assert cli_output["processing_time_seconds"] == 2.5
        assert "form16" in cli_output
    
    def test_failed_result(self):
        """Test failed extraction result"""
        result = ExtractionResult(
            success=False,
            error_message="PDF parsing failed",
            processing_time=1.2
        )
        
        cli_output = result.to_cli_output()
        
        assert cli_output["status"] == "error"
        assert cli_output["error"] == "PDF parsing failed"
        assert cli_output["processing_time_seconds"] == 1.2


class TestModelIntegration:
    """Integration tests for model interactions"""
    
    def test_complete_form16_workflow(self):
        """Test complete Form16 creation and validation workflow"""
        # Create a complete Form16 document
        form16 = Form16Document()
        
        # Employee information
        form16.employee.name = "John Doe"
        form16.employee.pan = "ABCDE1234F"
        form16.employee.designation = "Software Engineering SMTS"
        
        # Employer information  
        form16.employer.name = "SAMPLE COMPANY PRIVATE LIMITED"
        form16.employer.tan = "ABCD12345E"
        
        # Salary breakdown
        form16.salary.basic_salary = Decimal("1500000")
        form16.salary.hra_received = Decimal("400000")
        form16.salary.special_allowance = Decimal("200000")
        form16.salary.calculate_totals()
        
        # Add confidence scores
        form16.extraction_confidence = {
            "employee_name": 0.95,
            "employee_pan": 0.98,
            "employer_name": 0.90,
            "basic_salary": 0.88
        }
        
        # Validate the complete document
        assert form16.employee.name is not None
        assert form16.employee.pan == "ABCDE1234F"
        assert form16.employer.tan == "ABCD12345E"
        assert form16.salary.total_allowances > 0
        
        # Test summary generation
        summary = form16.get_extraction_summary()
        assert summary["extraction_rate"] >= 0
        
        # Test JSON output
        json_output = form16.to_json_output()
        assert json_output["form16"]["part_a"]["employee"]["name"] == "John Doe"