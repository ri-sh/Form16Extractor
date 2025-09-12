"""
Minimal unit tests for TaxCalculationService covering only working functionality.

Tests only the actual working code paths without mocking non-existent methods.
"""

import unittest
from unittest.mock import Mock, patch

from form16x.form16_parser.services.tax_calculation_service import TaxCalculationService


class TestTaxCalculationServiceMinimal(unittest.TestCase):
    """Test cases for TaxCalculationService covering only working functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TaxCalculationService()
        
        self.sample_tax_args = {
            'tax_regime': 'both',
            'city_type': 'metro',
            'age_category': 'below_60',
            'bank_interest': 0,
            'other_income': 0,
            'verbose': False
        }
    
    def test_service_initialization(self):
        """Test that service initializes without error."""
        service = TaxCalculationService()
        self.assertIsNotNone(service)
    
    def test_get_demo_tax_results(self):
        """Test generation of demo tax results."""
        result = self.service.get_demo_tax_results(self.sample_tax_args)
        
        self.assertIn('results', result)
        self.assertIn('comparison', result)
        self.assertTrue(result.get('demo_mode', False))
        self.assertIn('old', result['results'])
        self.assertIn('new', result['results'])
        
        # Verify structure
        old_regime = result['results']['old']
        new_regime = result['results']['new']
        
        self.assertIn('tax_liability', old_regime)
        self.assertIn('effective_tax_rate', old_regime)
        self.assertIn('tax_liability', new_regime)
        self.assertIn('effective_tax_rate', new_regime)
    
    def test_parse_tax_regime(self):
        """Test tax regime string parsing."""
        from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import TaxRegimeType
        
        # Test all regime types
        self.assertEqual(self.service._parse_tax_regime('old'), TaxRegimeType.OLD)
        self.assertEqual(self.service._parse_tax_regime('new'), TaxRegimeType.NEW)
        self.assertEqual(self.service._parse_tax_regime('both'), TaxRegimeType.BOTH)
        
        # Test case insensitivity
        self.assertEqual(self.service._parse_tax_regime('OLD'), TaxRegimeType.OLD)
        self.assertEqual(self.service._parse_tax_regime('BOTH'), TaxRegimeType.BOTH)
        
        # Test default fallback
        self.assertEqual(self.service._parse_tax_regime('invalid'), TaxRegimeType.BOTH)
    
    def test_parse_age_category(self):
        """Test age category string parsing."""
        from form16x.form16_parser.tax_calculators.interfaces.calculator_interface import AgeCategory
        
        # Test all age categories
        self.assertEqual(self.service._parse_age_category('below_60'), AgeCategory.BELOW_60)
        self.assertEqual(self.service._parse_age_category('senior_60_to_80'), AgeCategory.SENIOR_60_TO_80)
        self.assertEqual(self.service._parse_age_category('super_senior_above_80'), AgeCategory.SUPER_SENIOR_ABOVE_80)
        
        # Test default fallback
        self.assertEqual(self.service._parse_age_category('invalid'), AgeCategory.BELOW_60)
    
    def test_extract_assessment_year_from_form16(self):
        """Test assessment year extraction from Form16."""
        # Mock Form16 result with financial year
        mock_form16 = Mock()
        mock_form16.financial_year = '2023-24'
        
        result = self.service._extract_assessment_year_from_form16(mock_form16)
        self.assertEqual(result, '2024-25')
        
        # Test with no financial year
        mock_form16.financial_year = None
        result = self.service._extract_assessment_year_from_form16(mock_form16)
        self.assertEqual(result, '2024-25')  # Default fallback
        
        # Test with missing attribute
        mock_form16_no_fy = Mock(spec=[])  # No financial_year attribute
        result = self.service._extract_assessment_year_from_form16(mock_form16_no_fy)
        self.assertEqual(result, '2024-25')  # Default fallback
    
    def test_generate_demo_tax_results_from_extraction(self):
        """Test demo results generation from extraction data."""
        extraction_data = {
            'gross_salary': 800000,
            'section_80c': 50000,
            'total_tds': 75000
        }
        
        result = self.service._generate_demo_tax_results_from_extraction(extraction_data, self.sample_tax_args)
        
        self.assertIn('results', result)
        self.assertIn('comparison', result)
        self.assertTrue(result.get('demo_mode', False))
        self.assertIn('extraction_data', result)
        
        # Verify calculation logic
        old_regime = result['results']['old']
        new_regime = result['results']['new']
        
        self.assertEqual(old_regime['gross_salary'], 800000)
        self.assertEqual(new_regime['gross_salary'], 800000)
        self.assertIsInstance(old_regime['tax_liability'], int)
        self.assertIsInstance(new_regime['tax_liability'], int)
    
    def test_calculate_tax_with_consolidated_demo_data(self):
        """Test tax calculation with consolidated demo data."""
        consolidated_data = {
            'consolidated_summary': {
                'total_gross_income': 2500000,
                'total_tds_paid': 400000
            }
        }
        
        result = self.service.calculate_tax_with_consolidated_demo_data(consolidated_data, self.sample_tax_args)
        
        self.assertIn('results', result)
        self.assertIn('financial_data', result)
        self.assertTrue(result.get('demo_mode', False))
        
        # Verify consolidated amounts
        old_regime = result['results']['old']
        new_regime = result['results']['new']
        
        self.assertEqual(old_regime['gross_salary'], 2500000)
        self.assertEqual(new_regime['gross_salary'], 2500000)
        self.assertEqual(old_regime['tds_paid'], 400000)
        self.assertEqual(new_regime['tds_paid'], 400000)
        
        # Verify recommendation logic
        comparison = result['comparison']
        self.assertIn('recommended_regime', comparison)
        self.assertIn('savings_with_new', comparison)
    
    def test_extract_financial_data_with_complete_form16(self):
        """Test financial data extraction from complete Form16."""
        # Mock complete Form16 result
        mock_form16 = Mock()
        
        # Mock salary data
        mock_form16.salary = Mock()
        mock_form16.salary.gross_salary = 1000000
        mock_form16.salary.basic_salary = 800000
        mock_form16.salary.perquisites_value = 50000
        
        # Mock deductions
        mock_form16.chapter_via_deductions = Mock()
        mock_form16.chapter_via_deductions.section_80c_total = 100000
        mock_form16.chapter_via_deductions.section_80ccd_1b = 50000
        
        # Mock employee/employer
        mock_form16.employee = Mock()
        mock_form16.employee.name = 'Test Employee'
        mock_form16.employee.pan = 'ABCDE1234F'
        mock_form16.employer = Mock()
        mock_form16.employer.name = 'Test Company'
        
        # Mock quarterly TDS
        mock_quarter = Mock()
        mock_quarter.tax_deducted = 25000
        mock_form16.quarterly_tds = [mock_quarter]
        
        result = self.service._extract_financial_data(mock_form16)
        
        # Verify extracted data
        self.assertEqual(result['employee_name'], 'Test Employee')
        self.assertEqual(result['employee_pan'], 'ABCDE1234F')
        self.assertEqual(result['employer_name'], 'Test Company')
        self.assertEqual(result['gross_salary'], 1000000.0)
        self.assertEqual(result['section_17_1'], 800000.0)
        self.assertEqual(result['perquisites'], 50000.0)
        self.assertEqual(result['section_80c'], 100000.0)
        self.assertEqual(result['section_80ccd_1b'], 50000.0)
        self.assertEqual(result['total_tds'], 25000.0)
    
    def test_build_tax_calculation_result(self):
        """Test building comprehensive tax calculation result structure."""
        # Mock inputs for the method
        mock_results = {'old': {'tax_liability': 100000}, 'new': {'tax_liability': 80000}}
        mock_comparison = {'recommended_regime': 'new'}
        mock_extraction_data = {'employee_name': 'Test'}
        
        # Mock tax input object
        mock_tax_input = Mock()
        mock_tax_input.gross_salary = 1000000
        mock_tax_input.basic_salary = 800000
        mock_tax_input.hra_received = 100000
        mock_tax_input.other_income = 0
        mock_tax_input.bank_interest = 0
        mock_tax_input.assessment_year = '2024-25'
        mock_tax_input.age_category = Mock()
        mock_tax_input.age_category.value = 'below_60'
        mock_tax_input.city_type = 'metro'
        
        mock_tax_args = {'display_mode': 'colored', 'summary': True}
        
        result = self.service._build_tax_calculation_result(
            mock_results, mock_comparison, mock_extraction_data, mock_tax_input, mock_tax_args
        )
        
        # Verify structure
        self.assertIn('results', result)
        self.assertIn('comparison', result)
        self.assertIn('extraction_data', result)
        self.assertIn('calculation_input', result)
        self.assertIn('display_options', result)
        
        # Verify calculation input structure
        calc_input = result['calculation_input']
        self.assertEqual(calc_input['gross_salary'], 1000000.0)
        self.assertEqual(calc_input['assessment_year'], '2024-25')
        self.assertEqual(calc_input['age_category'], 'below_60')


if __name__ == '__main__':
    unittest.main()