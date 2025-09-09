"""
Unit tests for Employer Information Extractor
============================================

Tests for employer name, TAN, and address extraction from Form16 documents.
"""

import pytest
import pandas as pd
from form16_extractor.extractors.domains.identity.employer_extractor import EmployerExtractor
from form16_extractor.models.form16_models import EmployerInfo


class TestEmployerExtractor:
    """Test employer information extraction from Form16 tables"""
    
    def setup_method(self):
        """Setup test data based on real Form16 structure"""
        
        # Sample table with employer info (Part A format)
        self.sample_employer_table = pd.DataFrame([
            ["", "", "", "", "", "", "", "Name and address of the Employer/Specified Bank", "", "", "", "", "", "", "", "", "Name and address of the Employee"],
            ["", "", "", "", "", "", "", "TEST TECH COMPANY LIMITED\nTest Building, 5th Floor,\nTest Business Park, TEST CITY - 100001\nTest State\n+91-99-12345678\nhr@example.com", "", "", "", "", "", "", "", "", "Test User\n123 Test Street, Test City - 100001"],
            ["", "", "PAN of the Deductor", "", "", "", "", "TAN of the Deductor", "", "", "PAN of the Employee", "", "", "", "", "", "Employee Reference No."],
            ["", "", "TEST11919K", "", "", "", "", "TEST25952D", "", "", "TEST12345F", "", "", "", "", "", "TEST001"]
        ])
        
        # Another format with key-value pairs
        self.sample_kv_table = pd.DataFrame([
            ["Employer Name", "TEST TECH COMPANY LIMITED"],
            ["Employer TAN", "TEST25952D"],
            ["Employer PAN", "ABCDE1919K"],
            ["Employer Address", "Test Building, 5th Floor, Test Business Park, TEST CITY - 100001"]
        ])
        
        # Part B format table
        self.sample_partb_table = pd.DataFrame([
            ["PAN of the Deductor", "", "TAN of the Deductor", "", "", "PAN of the Employee"],
            ["ABCDE1919K", "", "TEST25952D", "", "", "ABCDE1234F"]
        ])
    
    def test_extract_employer_name_from_address_block(self):
        """Test extracting employer name from address block format"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([self.sample_employer_table])
        
        assert result.name == "TEST TECH COMPANY LIMITED"
        assert result.name is not None
    
    def test_extract_employer_tan(self):
        """Test extracting employer TAN with format validation"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([self.sample_employer_table])
        
        assert result.tan == "TEST25952D"
        # TAN format: 4 letters + 5 digits + 1 letter
        assert len(result.tan) == 10
        assert result.tan[:4].isalpha()
        assert result.tan[4:9].isdigit()
        assert result.tan[9].isalpha()
    
    def test_extract_employer_address(self):
        """Test extracting and cleaning employer address"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([self.sample_employer_table])
        
        assert result.address is not None
        assert "Test Building" in result.address
        assert "TEST CITY - 100001" in result.address
        assert "Test State" in result.address
    
    def test_extract_from_key_value_format(self):
        """Test extraction from key-value pair format"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([self.sample_kv_table])
        
        assert result.name == "TEST TECH COMPANY LIMITED"
        assert result.tan == "TEST25952D"
        assert result.address is not None
    
    def test_extract_from_partb_format(self):
        """Test extraction from Part B format with PAN/TAN headers"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([self.sample_partb_table, self.sample_employer_table])
        
        assert result.tan == "TEST25952D"
    
    def test_confidence_scoring(self):
        """Test confidence scoring for extracted employer data"""
        extractor = EmployerExtractor()
        result = extractor.extract_with_confidence([self.sample_employer_table])
        
        employer_info = result.data
        confidence_scores = result.confidence_scores
        
        assert isinstance(employer_info, EmployerInfo)
        assert 'name' in confidence_scores
        assert 'tan' in confidence_scores
        assert 'address' in confidence_scores
        
        # Should have high confidence for clear data
        assert confidence_scores['name'] > 0.5
        assert confidence_scores['tan'] > 0.8
    
    def test_handle_missing_data(self):
        """Test handling of missing employer data gracefully"""
        extractor = EmployerExtractor()
        empty_table = pd.DataFrame()
        result = extractor.extract_employer_info([empty_table])
        
        # Should return empty EmployerInfo without errors
        assert isinstance(result, EmployerInfo)
        assert result.name is None
        assert result.tan is None
    
    def test_multiple_table_extraction(self):
        """Test extraction from multiple tables with employer data"""
        extractor = EmployerExtractor()
        result = extractor.extract_employer_info([
            self.sample_partb_table,
            self.sample_employer_table,
            self.sample_kv_table
        ])
        
        # Should combine data from all tables
        assert result.name == "TEST TECH COMPANY LIMITED"
        assert result.tan == "TEST25952D"
        assert result.address is not None
    
    def test_clean_company_name(self):
        """Test cleaning of company names"""
        extractor = EmployerExtractor()
        
        # Table with messy company name
        messy_table = pd.DataFrame([
            ["Employer Name", "  TEST TECH COMPANY LIMITED  \n\n"]
        ])
        
        result = extractor.extract_employer_info([messy_table])
        
        # Should be cleaned
        assert result.name == "TEST TECH COMPANY LIMITED"
        assert "\n" not in result.name
        assert "  " not in result.name
    
    def test_is_company_name_validation(self):
        """Test company name identification method"""
        extractor = EmployerExtractor()
        
        assert extractor._is_company_name("TEST COMPANY LIMITED") is True
        assert extractor._is_company_name("ABC PRIVATE LIMITED") is True
        assert extractor._is_company_name("XYZ SOLUTIONS") is True
        assert extractor._is_company_name("John Doe") is False
        assert extractor._is_company_name("") is False
        assert extractor._is_company_name("nan") is False
    
    def test_tan_pattern_validation(self):
        """Test TAN pattern validation"""
        extractor = EmployerExtractor()
        
        assert extractor.tan_pattern.match("TEST12345D") is not None
        assert extractor.tan_pattern.match("ABCD99999Z") is not None
        assert extractor.tan_pattern.match("INVALID") is None
        assert extractor.tan_pattern.match("123456789") is None
        assert extractor.tan_pattern.match("ABCDE1234F") is None  # PAN format, not TAN
    
    def test_clean_company_name_method(self):
        """Test company name cleaning method"""
        extractor = EmployerExtractor()
        
        assert extractor._clean_company_name("  TEST COMPANY LIMITED  ") == "TEST COMPANY LIMITED"
        assert extractor._clean_company_name("Test Company ltd") == "Test Company LTD"
        assert extractor._clean_company_name("ABC Private Limited.,") == "ABC PRIVATE LIMITED"
    
    def test_clean_address_method(self):
        """Test address cleaning method"""
        extractor = EmployerExtractor()
        
        cleaned = extractor._clean_address("Test Building,, 5th Floor,  Test City")
        assert ",," not in cleaned
        assert "  " not in cleaned
        assert cleaned == "Test Building, 5th Floor, Test City"
    
    def test_confidence_calculation_methods(self):
        """Test individual confidence calculation methods"""
        extractor = EmployerExtractor()
        
        # Test name confidence
        assert extractor._calculate_name_confidence("TEST COMPANY LIMITED") > 0.5
        assert extractor._calculate_name_confidence(None) == 0.0
        
        # Test TAN confidence
        assert extractor._calculate_tan_confidence("TEST12345D") > 0.9
        assert extractor._calculate_tan_confidence("INVALID") < 0.5
        assert extractor._calculate_tan_confidence(None) == 0.0
        
        # Test address confidence
        assert extractor._calculate_address_confidence("Test Building, Test City - 100001") > 0.5
        assert extractor._calculate_address_confidence(None) == 0.0
    
    def test_extractor_interface_compliance(self):
        """Test that extractor implements IExtractor interface correctly"""
        extractor = EmployerExtractor()
        
        assert extractor.get_extractor_name() == "Employer Information Extractor"
        supported_fields = extractor.get_supported_fields()
        assert "name" in supported_fields
        assert "tan" in supported_fields
        assert "address" in supported_fields
    
    def test_dual_interface_support(self):
        """Test that extractor supports both interfaces"""
        extractor = EmployerExtractor()
        
        # Test with List[pd.DataFrame] (domain interface)
        result1 = extractor.extract([self.sample_employer_table])
        assert isinstance(result1, EmployerInfo)
        
        # Test legacy method
        result2 = extractor.extract_with_confidence_legacy([self.sample_employer_table])
        assert 'employer_info' in result2
        assert 'confidence_scores' in result2