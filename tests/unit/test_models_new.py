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


def test_quarterly_tds_model():
    """Test QuarterlyTDS model with actual TDS data"""
    from form16_extractor.models.form16_models import QuarterlyTDS
    
    # Test with actual quarterly data from Form16
    q1_tds = QuarterlyTDS(
        quarter="Q1",
        receipt_number="QVSDURWF",
        amount_paid=Decimal("1370780.00"),
        tax_deducted=Decimal("334967.00"),
        tax_deposited=Decimal("334967.00")
    )
    
    assert q1_tds.quarter == "Q1"
    assert q1_tds.tax_deducted == Decimal("334967.00")
    assert q1_tds.amount_paid == Decimal("1370780.00")


def test_pan_validation():
    """Test PAN format validation"""
    from form16_extractor.models.form16_models import EmployeeInfo
    
    # Valid PAN should work
    employee = EmployeeInfo(
        name="Test Name",
        pan="BYHPR6078P"
    )
    assert employee.pan == "BYHPR6078P"
    
    # Invalid PAN should raise validation error
    with pytest.raises(ValidationError) as exc_info:
        EmployeeInfo(
            name="Test Name", 
            pan="INVALID123"
        )
    assert "PAN format" in str(exc_info.value)


def test_tan_validation():
    """Test TAN format validation"""
    from form16_extractor.models.form16_models import EmployerInfo
    
    # Valid TAN should work
    employer = EmployerInfo(
        name="Test Company",
        tan="BLRS20885E"
    )
    assert employer.tan == "BLRS20885E"
    
    # Invalid TAN should raise validation error
    with pytest.raises(ValidationError) as exc_info:
        EmployerInfo(
            name="Test Company",
            tan="INVALID123"
        )
    assert "TAN format" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])