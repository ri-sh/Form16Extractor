"""
Unit tests for TaxCalculationService.

Tests tax calculation functionality, regime comparison, and fallback
behavior without breaking existing functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from form16x.form16_parser.services.tax_calculation_service import TaxCalculationService


class TestTaxCalculationService(unittest.TestCase):
    """Test cases for TaxCalculationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TaxCalculationService()
        
        # Sample extraction data
        self.sample_extraction_data = {
            'employee_name': 'Test Employee',
            'employee_pan': 'ABCDE1234F',
            'employer_name': 'Test Company',
            'gross_salary': 800000.0,
            'section_17_1': 800000.0,
            'perquisites': 0.0,
            'section_80c': 50000.0,
            'section_80ccd_1b': 25000.0,
            'total_tds': 75000.0
        }
        
        self.sample_tax_args = {
            'tax_regime': 'both',
            'city_type': 'metro',
            'age_category': 'below_60',
            'bank_interest': 0,
            'other_income': 0,
            'verbose': False
        }
    
    def test_calculate_comprehensive_tax_success(self):
        """Test successful comprehensive tax calculation."""
        # Mock Form16 result object
        mock_form16_result = Mock()
        mock_form16_result.salary = Mock()
        mock_form16_result.salary.gross_salary = 800000.0
        mock_form16_result.salary.basic_salary = 600000.0
        mock_form16_result.chapter_via_deductions = Mock()
        mock_form16_result.chapter_via_deductions.section_80c_total = 50000.0
        mock_form16_result.chapter_via_deductions.section_80ccd_1b = 25000.0
        mock_form16_result.employee = Mock()
        mock_form16_result.employee.name = 'Test Employee'
        mock_form16_result.employer = Mock()
        mock_form16_result.employer.name = 'Test Company'
        mock_form16_result.quarterly_tds = []
        
        result = self.service.calculate_comprehensive_tax(mock_form16_result, self.sample_tax_args)
        
        # Should fall back to simple calculation due to missing modules
        self.assertIsNotNone(result)
    
    def test_get_demo_tax_results(self):
        """Test generation of demo tax results."""
        result = self.service.get_demo_tax_results(self.sample_tax_args)
        
        self.assertIn('results', result)
        self.assertIn('comparison', result)
        self.assertTrue(result.get('demo_mode', False))
        self.assertIn('old', result['results'])
        self.assertIn('new', result['results'])
    
    def test_calculate_simple_tax(self):
        """Test simple tax calculation using SimpleTaxCalculator."""
        with patch('form16x.form16_parser.tax_calculators.simple_tax_calculator.SimpleTaxCalculator') as mock_calc_class:
            mock_calc = Mock()
            mock_calc_class.return_value = mock_calc
            
            mock_result = {
                'results': {
                    'old': {'tax_liability': 70000, 'effective_tax_rate': 8.75},
                    'new': {'tax_liability': 55000, 'effective_tax_rate': 6.875}
                },
                'comparison': {'recommended_regime': 'new'},
                'recommendation': 'NEW regime saves ₹15,000'
            }
            mock_calc.calculate_tax_both_regimes.return_value = mock_result
            
            result = self.service._calculate_simple_tax(self.sample_extraction_data, self.sample_tax_args)
            
            self.assertEqual(result['results']['old']['tax_liability'], 70000)
            self.assertEqual(result['results']['new']['tax_liability'], 55000)
            mock_calc.calculate_tax_both_regimes.assert_called_once()
    
    def test_calculate_tax_old_regime_only(self):
        """Test tax calculation for old regime only."""
        tax_args = self.sample_tax_args.copy()
        tax_args['tax_regime'] = 'old'
        
        with patch.object(self.service, 'comprehensive_calculator') as mock_calc:
            mock_result = {
                'results': {
                    'old': {
                        'tax_liability': 80000,
                        'effective_tax_rate': 10.0
                    }
                },
                'comparison': {'recommended_regime': 'old'},
                'recommendation': 'Using OLD regime'
            }
            mock_calc.calculate_comprehensive_tax.return_value = mock_result
            
            result = self.service.calculate_tax(self.sample_extraction_data, tax_args)
            
            self.assertIn('old', result['results'])
            self.assertNotIn('new', result['results'])
    
    def test_calculate_tax_new_regime_only(self):
        """Test tax calculation for new regime only."""
        tax_args = self.sample_tax_args.copy()
        tax_args['tax_regime'] = 'new'
        
        with patch.object(self.service, 'comprehensive_calculator') as mock_calc:
            mock_result = {
                'results': {
                    'new': {
                        'tax_liability': 65000,
                        'effective_tax_rate': 8.125
                    }
                },
                'comparison': {'recommended_regime': 'new'},
                'recommendation': 'Using NEW regime'
            }
            mock_calc.calculate_comprehensive_tax.return_value = mock_result
            
            result = self.service.calculate_tax(self.sample_extraction_data, tax_args)
            
            self.assertIn('new', result['results'])
            self.assertNotIn('old', result['results'])
    
    def test_calculate_tax_with_additional_income(self):
        """Test tax calculation with additional income sources."""
        tax_args = self.sample_tax_args.copy()
        tax_args['bank_interest'] = 30000
        tax_args['other_income'] = 50000
        
        with patch.object(self.service, 'comprehensive_calculator') as mock_calc:
            mock_result = {
                'results': {
                    'old': {'tax_liability': 95000, 'effective_tax_rate': 10.8},
                    'new': {'tax_liability': 80000, 'effective_tax_rate': 9.1}
                },
                'comparison': {'recommended_regime': 'new'},
                'recommendation': 'NEW regime saves ₹15,000'
            }
            mock_calc.calculate_comprehensive_tax.return_value = mock_result
            
            result = self.service.calculate_tax(self.sample_extraction_data, tax_args)
            
            # Verify additional income was considered
            call_args = mock_calc.calculate_comprehensive_tax.call_args[0][0]
            self.assertIn('other_income', call_args)
    
    def test_calculate_tax_verbose_mode(self):
        """Test tax calculation with verbose logging enabled."""
        tax_args = self.sample_tax_args.copy()
        tax_args['verbose'] = True
        
        with patch.object(self.service, 'comprehensive_calculator') as mock_calc:
            with patch('builtins.print') as mock_print:
                mock_calc.calculate_comprehensive_tax.side_effect = Exception("Test error")
                
                with patch.object(self.service, '_calculate_simple_tax') as mock_simple:
                    mock_simple.return_value = {'results': {}}
                    
                    self.service.calculate_tax(self.sample_extraction_data, tax_args)
                    
                    # Verify verbose logging occurred
                    mock_print.assert_called()
    
    def test_build_tax_request_comprehensive(self):
        """Test building comprehensive tax request."""
        request = self.service._build_tax_request(self.sample_extraction_data, self.sample_tax_args)
        
        self.assertEqual(request['gross_salary'], 800000.0)
        self.assertEqual(request['section_80c'], 50000.0)
        self.assertEqual(request['tax_regime'], 'both')
        self.assertEqual(request['city_type'], 'metro')
        self.assertIn('employee_name', request)
    
    def test_build_tax_request_with_defaults(self):
        """Test building tax request with default values."""
        minimal_extraction_data = {
            'gross_salary': 500000.0,
            'section_80c': 0.0
        }
        
        request = self.service._build_tax_request(minimal_extraction_data, self.sample_tax_args)
        
        self.assertEqual(request['gross_salary'], 500000.0)
        self.assertEqual(request['section_80c'], 0.0)
        self.assertEqual(request['section_80ccd_1b'], 0.0)  # Default value
        self.assertEqual(request['perquisites'], 0.0)  # Default value
    
    def test_comprehensive_calculator_initialization(self):
        """Test that comprehensive calculator is properly initialized."""
        self.assertIsNotNone(self.service.comprehensive_calculator)
    
    def test_no_demo_fallback_in_simple_calculation(self):
        """Test that simple calculation doesn't include demo_mode flag."""
        with patch('form16x.form16_parser.services.tax_calculation_service.SimpleTaxCalculator') as mock_calc_class:
            mock_calc = Mock()
            mock_calc_class.return_value = mock_calc
            
            mock_result = {
                'results': {'old': {}, 'new': {}},
                'comparison': {},
                'recommendation': ''
            }
            mock_calc.calculate_tax_both_regimes.return_value = mock_result
            
            result = self.service._calculate_simple_tax(self.sample_extraction_data, self.sample_tax_args)
            
            # Ensure no demo_mode flag is set in result
            self.assertNotIn('demo_mode', result)
            for regime_result in result.get('results', {}).values():
                self.assertNotIn('demo_mode', regime_result)


if __name__ == '__main__':
    unittest.main()