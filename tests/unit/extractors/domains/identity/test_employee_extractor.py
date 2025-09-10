"""
Unit tests for Employee Information Extractor
=============================================

Tests for employee field extraction from Form16 tables.
"""

import pytest
import pandas as pd
from form16x.form16_parser.extractors.domains.identity.employee_extractor import EmployeeExtractor
from form16x.form16_parser.models.form16_models import EmployeeInfo


class TestEmployeeExtractor:
    """Test employee information extraction from Form16 tables"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = EmployeeExtractor()
        
        # Create test table based on actual Form16 structure
        self.sample_employee_table = pd.DataFrame([
            ["Form 16", "", "", ""],
            ["Assessment Year", ":", "2024-25", ""],
            ["Financial Year", ":", "2023-24", ""],
            ["Employee ID", ":", "123456", ""],
            ["Employee Name", ":", "JOHN DOE", ""],
            ["Employee PAN", ":", "ABCDE1234F", ""],
            ["Employee Designation", ":", "Software Engineer", ""],
            ["Employer Name", ":", "TEST COMPANY PRIVATE LIMITED", ""],
            ["Employer TAN", ":", "TEST12345E", ""]
        ])
        
        # Alternative table format
        self.alt_employee_table = pd.DataFrame([
            ["Name and address of the Employee/Specified senior citizen", ""],
            ["JOHN DOE", ""],
            ["123 Test Street, Test City - 100001", ""],
            ["Test State", ""],
            ["PAN of the Employee/Specified senior citizen", ""],
            ["ABCDE1234F", ""]
        ])
    
    def test_extract_employee_name_from_key_value_format(self):
        """Test extracting employee name from key-value table format"""
        result = self.extractor.extract_employee_info([self.sample_employee_table])
        
        assert result.name == "JOHN DOE"
        assert result.employee_id == "123456"
        assert result.designation == "Software Engineer"
    
    def test_extract_employee_pan_with_validation(self):
        """Test PAN extraction with format validation"""
        result = self.extractor.extract_employee_info([self.sample_employee_table])
        
        assert result.pan == "ABCDE1234F"
        # PAN should be validated format: AAAAA9999A
        assert len(result.pan) == 10
        assert result.pan[:5].isalpha()
        assert result.pan[5:9].isdigit()
        assert result.pan[9].isalpha()
    
    def test_extract_employee_from_address_block_format(self):
        """Test extraction from address block format"""
        result = self.extractor.extract_employee_info([self.alt_employee_table])
        
        assert result.name == "JOHN DOE"
        assert result.pan == "ABCDE1234F"
        assert "123 Test Street" in result.address
    
    def test_extract_with_multiple_tables(self):
        """Test extraction when employee info is spread across multiple tables"""
        table1 = pd.DataFrame([
            ["Employee Name", ":", "JOHN DOE", ""],
            ["Employee PAN", ":", "ABCDE1234F", ""]
        ])
        
        table2 = pd.DataFrame([
            ["Employee ID", ":", "123456", ""],
            ["Designation", ":", "Software Engineer", ""]
        ])
        
        result = self.extractor.extract_employee_info([table1, table2])
        
        assert result.name == "JOHN DOE"
        assert result.pan == "ABCDE1234F"
        assert result.employee_id == "123456"
        assert result.designation == "Software Engineer"
    
    def test_confidence_scoring(self):
        """Test confidence scoring for extraction quality"""
        result = self.extractor.extract_with_confidence([self.sample_employee_table])
        
        assert result.data is not None
        assert result.confidence_scores is not None
        
        employee_info = result.data
        confidences = result.confidence_scores
        
        # High confidence for clear key-value matches
        assert confidences.get('name', 0) > 0.8
        assert confidences.get('pan', 0) > 0.9  # PAN has strict format
        assert confidences.get('employee_id', 0) > 0.8
    
    def test_handle_invalid_pan_gracefully(self):
        """Test graceful handling of invalid PAN format"""
        invalid_pan_table = pd.DataFrame([
            ["Employee Name", ":", "TEST USER", ""],
            ["Employee PAN", ":", "INVALID123", ""]  # Invalid format
        ])
        
        result = self.extractor.extract_employee_info([invalid_pan_table])
        
        assert result.name == "TEST USER"
        assert result.pan is None  # Should be None for invalid PAN
    
    def test_extract_from_empty_or_malformed_tables(self):
        """Test robustness with empty or malformed input"""
        empty_table = pd.DataFrame()
        malformed_table = pd.DataFrame([["random", "data", "here"]])
        
        result = self.extractor.extract_employee_info([empty_table, malformed_table])
        
        # Should return empty EmployeeInfo, not crash
        assert isinstance(result, EmployeeInfo)
        assert result.name is None
        assert result.pan is None
    
    def test_prioritize_employee_pan_over_employer_pan(self):
        """Test that employee PAN is prioritized when both are present"""
        mixed_table = pd.DataFrame([
            ["Employer PAN", ":", "ABCDE1234R", ""],  # Employer PAN
            ["Employee Name", ":", "JOHN DOE", ""],
            ["Employee PAN", ":", "ABCDE1234F", ""],  # Employee PAN
        ])
        
        result = self.extractor.extract_employee_info([mixed_table])
        
        # Should extract employee PAN, not employer PAN
        assert result.pan == "ABCDE1234F"
        assert result.name == "JOHN DOE"
    
    def test_extract_employee_address_multiline(self):
        """Test extraction of multi-line employee address"""
        result = self.extractor.extract_employee_info([self.alt_employee_table])
        
        assert result.address is not None
        assert "Test City" in result.address
    
    def test_extraction_with_sample_form16_pattern(self):
        """Integration test with pattern from sample Form16"""
        real_sample = pd.DataFrame([
            ["Assessment Year", ":", "2024-25"],
            ["Financial Year", ":", "2023-24"], 
            ["Employee ID", ":", "123456"],
            ["Employee Name", ":", "JOHN DOE"],
            ["Employee PAN", ":", "ABCDE1234F"],
            ["Employee Designation", ":", "Software Engineer"]
        ])
        
        result = self.extractor.extract_employee_info([real_sample])
        
        # Should match exact data from our test documents
        assert result.name == "JOHN DOE"
        assert result.pan == "ABCDE1234F"
        assert result.employee_id == "123456"
        assert result.designation == "Software Engineer"
    
    def test_extraction_speed(self):
        """Test that extraction completes within reasonable time"""
        import time
        
        # Create larger test table
        large_table = pd.DataFrame([
            ["Employee Name", ":", "JOHN DOE"] + [""] * 20,
            ["Employee PAN", ":", "ABCDE1234F"] + [""] * 20
        ] * 50)  # 100 rows
        
        start_time = time.time()
        result = self.extractor.extract_employee_info([large_table])
        extraction_time = time.time() - start_time
        
        assert extraction_time < 1.0  # Should complete within 1 second
        assert result.name == "JOHN DOE"
    
    def test_extractor_interface_compliance(self):
        """Test that extractor implements IExtractor interface correctly"""
        assert self.extractor.get_extractor_name() == "Employee Information Extractor"
        supported_fields = self.extractor.get_supported_fields()
        assert "name" in supported_fields
        assert "pan" in supported_fields
        assert "employee_id" in supported_fields
    
    def test_valid_pan_format_validation(self):
        """Test PAN format validation method"""
        assert self.extractor._is_valid_pan_format("ABCDE1234F") is True
        assert self.extractor._is_valid_pan_format("INVALID") is False
        assert self.extractor._is_valid_pan_format("12345ABCDF") is False
        assert self.extractor._is_valid_pan_format("") is False
    
    def test_valid_employee_id_validation(self):
        """Test employee ID validation method"""
        assert self.extractor._is_valid_employee_id("123456") is True
        assert self.extractor._is_valid_employee_id("123456") is True  # Valid numeric ID
        assert self.extractor._is_valid_employee_id("12") is False  # Too short
        assert self.extractor._is_valid_employee_id("12345678901") is False  # Too long
    
    def test_person_name_identification(self):
        """Test person name vs company name identification"""
        assert self.extractor._is_person_name("JOHN DOE") is True
        assert self.extractor._is_person_name("TEST COMPANY LIMITED") is False
        assert self.extractor._is_person_name("ABC PRIVATE LIMITED") is False
        assert self.extractor._is_person_name("XYZ SOLUTIONS") is False