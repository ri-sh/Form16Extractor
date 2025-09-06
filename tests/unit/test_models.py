"""
Test-Driven Development: Form16 Data Models Tests
================================================

These tests define the expected behavior of our Form16 data models
BEFORE implementing the actual models. This ensures we design the
models correctly based on real Form16 document analysis.

Based on analysis of actual Form16 documents from ~/Downloads/form16/
"""

import pytest
from decimal import Decimal
from datetime import date
from pydantic import ValidationError


def test_employee_info_model():
    """Test EmployeeInfo model with data from real Form16s"""
    from form16_extractor.models.form16_models import EmployeeInfo
    
    # Test with data from actual Salesforce Form16
    employee = EmployeeInfo(
        name="RISHABH ROY",
        pan="BYHPR6078P",
        address="MIG 1/937 HUDCO WARD NO, 57 BHILAI WEST, DURG - 490009",
        state="Chattisgarh",
        designation="Software Engineering SMTS",
        employee_id="870937"
    )
    
    assert employee.name == "RISHABH ROY"
    assert employee.pan == "BYHPR6078P" 
    assert employee.designation == "Software Engineering SMTS"
    assert employee.employee_id == "870937"


def test_employer_info_model():
    """Test EmployerInfo model with actual employer data"""
    from form16_extractor.models.form16_models import EmployerInfo
    
    # Test with Salesforce data
    employer = EmployerInfo(
        name="SALESFORCE.COM INDIA PRIVATE LIMITED",
        tan="BLRS20885E",
        pan="AAJCS3582R",
        address="Torrey Pines, 3rd Floor, Embassy Golflinks Software Business Park",
        city="Bengaluru",
        state="Karnataka",
        pincode="560071"
    )
    
    assert employer.name == "SALESFORCE.COM INDIA PRIVATE LIMITED"
    assert employer.tan == "BLRS20885E"
    assert employer.pan == "AAJCS3582R"


def test_salary_breakdown_model():
    """Test SalaryBreakdown model with actual salary data"""
    from form16_extractor.models.form16_models import SalaryBreakdown
    
    # Test with real salary data from Form16
    salary = SalaryBreakdown(
        basic_salary=Decimal("4958800.00"),
        perquisites_value=Decimal("302394.00"),
        gross_salary=Decimal("5261194.00"),
        standard_deduction=Decimal("50000.00"),
        professional_tax=Decimal("2400.00"),
        total_deductions_sec16=Decimal("52400.00"),
        income_chargeable_under_salaries=Decimal("5208794.00")
    )
    
    assert salary.basic_salary == Decimal("4958800.00")
    assert salary.gross_salary == Decimal("5261194.00")
    assert salary.income_chargeable_under_salaries == Decimal("5208794.00")


class TestTANValidation:
    """Test TAN validation logic"""
    
    def test_valid_tan_formats(self):
        """Test valid TAN formats are accepted"""
        valid_tans = [
            "BLRS20885E",
            "AAAA11111A",
            "ZZZZ99999Z"
        ]
        
        for tan_str in valid_tans:
            tan = TAN(value=tan_str)
            assert tan.value == tan_str.upper()
    
    def test_invalid_tan_formats(self):
        """Test invalid TAN formats are rejected"""
        with pytest.raises(ValueError):
            TAN(value="BLR20885E")  # Too short
        
        with pytest.raises(ValueError):
            TAN(value="1LRS20885E")  # Invalid format


class TestAmountHandling:
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
        with pytest.raises(ValueError):
            Amount(value=Decimal("-1000"))


class TestEmployeeInfo:
    """Test EmployeeInfo model"""
    
    def test_employee_creation_with_valid_data(self):
        """Test creating employee with valid data"""
        employee = EmployeeInfo(
            name="Rishabh Roy",
            pan="BYHPR6078P",
            designation="Software Engineering SMTS"
        )
        
        assert employee.name == "Rishabh Roy"
        assert employee.pan == "BYHPR6078P"
        assert employee.designation == "Software Engineering SMTS"
    
    def test_employee_with_invalid_pan_handled_gracefully(self):
        """Test invalid PAN doesn't break the model"""
        employee = EmployeeInfo(
            name="Test User",
            pan="INVALID_PAN"  # This should not raise exception
        )
        
        # Invalid PAN should be set to None, not raise exception
        assert employee.name == "Test User"
        assert employee.pan is None


class TestSalaryBreakdown:
    """Test SalaryBreakdown comprehensive field handling"""
    
    def test_salary_breakdown_creation(self):
        """Test creating salary breakdown with various fields"""
        salary = SalaryBreakdown(
            basic_salary=Decimal("500000"),
            hra_received=Decimal("250000"),
            special_allowance=Decimal("100000")
        )
        
        assert salary.basic_salary == Decimal("500000")
        assert salary.hra_received == Decimal("250000")
        assert salary.special_allowance == Decimal("100000")
    
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
            basic_salary=Decimal("500000"),
            hra_received=Decimal("0"),  # Zero value
            transport_allowance=Decimal("25000")
        )
        
        non_zero = salary.get_non_zero_fields()
        
        assert "basic_salary" in non_zero
        assert "transport_allowance" in non_zero
        assert "hra_received" not in non_zero  # Zero value excluded


class TestForm16Document:
    """Test complete Form16Document model"""
    
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
        form16.salary.basic_salary = Decimal("500000")
        
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
        assert summary["quality_score"] > 0
    
    def test_json_output_format(self):
        """Test JSON output format for CLI"""
        form16 = Form16Document()
        form16.employee.name = "Test Employee"
        form16.salary.basic_salary = Decimal("500000")
        
        json_output = form16.to_json_output()
        
        # Should have required structure for CLI
        assert "form16_data" in json_output
        assert "extraction_summary" in json_output
        assert "processing_info" in json_output
        
        # Form16 data should have all sections
        form16_data = json_output["form16_data"]
        assert "employee_info" in form16_data
        assert "salary_breakdown" in form16_data
        assert "quarterly_tds" in form16_data


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
        assert "form16_data" in cli_output
    
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


# Integration test placeholder
class TestModelIntegration:
    """Integration tests for model interactions"""
    
    def test_complete_form16_workflow(self):
        """Test complete Form16 creation and validation workflow"""
        # Create a complete Form16 document
        form16 = Form16Document()
        
        # Employee information
        form16.employee.name = "Rishabh Roy"
        form16.employee.pan = "BYHPR6078P"
        form16.employee.designation = "Software Engineering SMTS"
        
        # Employer information  
        form16.employer.name = "SALESFORCE.COM INDIA PRIVATE LIMITED"
        form16.employer.tan = "BLRS20885E"
        
        # Salary breakdown
        form16.salary.basic_salary = Decimal("500000")
        form16.salary.hra_received = Decimal("250000")
        form16.salary.special_allowance = Decimal("100000")
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
        assert form16.employee.pan == "BYHPR6078P"
        assert form16.employer.tan == "BLRS20885E"
        assert form16.salary.total_allowances > 0
        
        # Test summary generation
        summary = form16.get_extraction_summary()
        assert summary["extraction_rate"] > 0
        
        # Test JSON output
        json_output = form16.to_json_output()
        assert json_output["form16_data"]["employee_info"]["name"] == "Rishabh Roy"