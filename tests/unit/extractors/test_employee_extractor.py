"""
TDD: Employee Information Extractor Tests
=========================================

Test-driven development for employee field extraction from Form16 tables.
These tests define expected behavior BEFORE implementing the extractor.

Based on actual data from Form16.pdf (Salesforce document analysis)
"""

import pytest
import pandas as pd
from decimal import Decimal
from form16_extractor.extractors.employee import EmployeeExtractor
from form16_extractor.models.form16_models import EmployeeInfo


class TestEmployeeExtractor:
    """Test employee information extraction from Form16 tables"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = EmployeeExtractor()
        
        # Create test table based on actual Form16 structure
        self.sample_employee_table = pd.DataFrame([
            ["Form 16", "", "", ""],
            ["Assessment Year", ":", "2025-26", ""],
            ["Financial Year", ":", "2024-25", ""],
            ["Employee ID", ":", "870937", ""],
            ["Employee Name", ":", "RISHABH ROY", ""],
            ["Employee PAN", ":", "BYHPR6078P", ""],
            ["Employee Designation", ":", "Software Engineering SMTS", ""],
            ["Employer Name", ":", "SALESFORCE.COM INDIA PRIVATE LIMITED", ""],
            ["Employer TAN", ":", "BLRS20885E", ""]
        ])
        
        # Alternative table format (some Form16s use different layouts)
        self.alt_employee_table = pd.DataFrame([
            ["Name and address of the Employee/Specified senior citizen", ""],
            ["RISHABH ROY", ""],
            ["MIG 1/937 HUDCO WARD NO, 57 BHILAI WEST, DURG - 490009", ""],
            ["Chattisgarh", ""],
            ["PAN of the Employee/Specified senior citizen", ""],
            ["BYHPR6078P", ""]
        ])
    
    def test_extract_employee_name_from_key_value_format(self):
        """Test extracting employee name from key-value table format"""
        result = self.extractor.extract_employee_info([self.sample_employee_table])
        
        assert result.name == "RISHABH ROY"
        assert result.employee_id == "870937"
        assert result.designation == "Software Engineering SMTS"
    
    def test_extract_employee_pan_with_validation(self):
        """Test PAN extraction with format validation"""
        result = self.extractor.extract_employee_info([self.sample_employee_table])
        
        assert result.pan == "BYHPR6078P"
        # PAN should be validated format: AAAAA9999A
        assert len(result.pan) == 10
        assert result.pan[:5].isalpha()
        assert result.pan[5:9].isdigit()
        assert result.pan[9].isalpha()
    
    def test_extract_employee_from_address_block_format(self):
        """Test extraction from address block format (alternative layout)"""
        result = self.extractor.extract_employee_info([self.alt_employee_table])
        
        assert result.name == "RISHABH ROY"
        assert result.pan == "BYHPR6078P"
        assert "MIG 1/937 HUDCO WARD NO, 57" in result.address
    
    def test_extract_with_multiple_tables(self):
        """Test extraction when employee info is spread across multiple tables"""
        # Split info across tables (common in complex Form16s)
        table1 = pd.DataFrame([
            ["Employee Name", ":", "RISHABH ROY", ""],
            ["Employee PAN", ":", "BYHPR6078P", ""]
        ])
        
        table2 = pd.DataFrame([
            ["Employee ID", ":", "870937", ""],
            ["Designation", ":", "Software Engineering SMTS", ""]
        ])
        
        result = self.extractor.extract_employee_info([table1, table2])
        
        assert result.name == "RISHABH ROY"
        assert result.pan == "BYHPR6078P"
        assert result.employee_id == "870937"
        assert result.designation == "Software Engineering SMTS"
    
    def test_confidence_scoring(self):
        """Test confidence scoring for extraction quality"""
        result_with_confidence = self.extractor.extract_with_confidence([self.sample_employee_table])
        
        assert 'employee_info' in result_with_confidence
        assert 'confidence_scores' in result_with_confidence
        
        employee_info = result_with_confidence['employee_info']
        confidences = result_with_confidence['confidence_scores']
        
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
            ["Employer PAN", ":", "AAJCS3582R", ""],  # Employer PAN
            ["Employee Name", ":", "RISHABH ROY", ""],
            ["Employee PAN", ":", "BYHPR6078P", ""],  # Employee PAN
        ])
        
        result = self.extractor.extract_employee_info([mixed_table])
        
        # Should extract employee PAN, not employer PAN
        assert result.pan == "BYHPR6078P"
        assert result.name == "RISHABH ROY"
    
    def test_extract_employee_address_multiline(self):
        """Test extraction of multi-line employee address"""
        result = self.extractor.extract_employee_info([self.alt_employee_table])
        
        assert result.address is not None
        assert "DURG" in result.address
        assert "Chattisgarh" in result.address or "Chattisgarh" in result.state
    
    def test_extraction_with_real_form16_sample(self):
        """Integration test with pattern from actual Form16.pdf"""
        # This matches the exact structure from our Form16.pdf analysis
        real_sample = pd.DataFrame([
            ["Assessment Year", ":", "2025-26"],
            ["Financial Year", ":", "2024-25"], 
            ["Employee ID", ":", "870937"],
            ["Employee Name", ":", "RISHABH ROY"],
            ["Employee PAN", ":", "BYHPR6078P"],
            ["Employee Designation", ":", "Software Engineering SMTS"]
        ])
        
        result = self.extractor.extract_employee_info([real_sample])
        
        # Should match exact data from our test documents
        assert result.name == "RISHABH ROY"
        assert result.pan == "BYHPR6078P"
        assert result.employee_id == "870937"
        assert result.designation == "Software Engineering SMTS"


class TestEmployeeExtractionPatterns:
    """Test various Form16 layout patterns for employee data"""
    
    def test_google_form16_pattern(self):
        """Test pattern similar to google-form16.pdf"""
        # Google Form16s often have different layouts
        pass  # Will implement after analyzing google-form16.pdf structure
    
    def test_musigma_form16_pattern(self):
        """Test pattern from Form16_9840.pdf_musigma_FFS.pdf"""
        pass  # Will implement after analyzing structure
    
    def test_generic_form16_pattern(self):
        """Test generic government Form16 pattern"""
        pass  # Will implement for broader compatibility


# Performance and integration tests
class TestEmployeeExtractionPerformance:
    """Test performance and edge cases"""
    
    def test_extraction_speed(self):
        """Test that extraction completes within reasonable time"""
        import time
        extractor = EmployeeExtractor()
        
        # Create larger test table
        large_table = pd.DataFrame([
            ["Employee Name", ":", "RISHABH ROY"] + [""] * 20,
            ["Employee PAN", ":", "BYHPR6078P"] + [""] * 20
        ] * 50)  # 100 rows
        
        start_time = time.time()
        result = extractor.extract_employee_info([large_table])
        extraction_time = time.time() - start_time
        
        assert extraction_time < 1.0  # Should complete within 1 second
        assert result.name == "RISHABH ROY"
    
    def test_memory_usage(self):
        """Test memory efficiency with large tables"""
        # Will implement memory usage testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])