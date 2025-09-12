"""
Unit tests for TaxOptimizationService.

Tests tax optimization analysis, suggestion generation, and demo mode
functionality without breaking existing behavior.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from form16x.form16_parser.services.tax_optimization_service import TaxOptimizationService


class TestTaxOptimizationService(unittest.TestCase):
    """Test cases for TaxOptimizationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TaxOptimizationService()
        
        # Sample Form16 result
        self.sample_form16_result = {
            'employee_name': 'Test Employee',
            'gross_salary': 2500000.0,  # ₹25L
            'section_80c': 150000.0,
            'perquisites': 0.0,
            'total_tds': 400000.0
        }
        
        self.sample_file_path = Path('/test/form16.pdf')
    
    @patch('form16x.form16_parser.services.tax_optimization_service.TaxOptimizationEngine')
    @patch('form16x.form16_parser.services.tax_optimization_service.Form16JSONBuilder')
    def test_analyze_tax_optimization_success(self, mock_json_builder, mock_optimizer):
        """Test successful tax optimization analysis."""
        # Mock tax calculation results
        mock_tax_results = {
            'results': {
                'old': {'tax_liability': 468000, 'effective_tax_rate': 22.0},
                'new': {'tax_liability': 331250, 'effective_tax_rate': 15.6}
            },
            'comparison': {'recommended_regime': 'new', 'savings_with_new': 136750}
        }
        
        # Mock optimization analysis
        mock_optimization = {
            'suggestions': [
                {'category': 'Section 80C', 'potential_saving': 15000, 'description': 'Maximize ELSS investment'},
                {'category': 'Section 80D', 'potential_saving': 12500, 'description': 'Health insurance premium'}
            ],
            'total_potential_savings': 27500
        }
        
        # Mock Form16 JSON
        mock_form16_json = {'employee': {'name': 'Test Employee'}}
        
        with patch.object(self.service, '_calculate_tax_for_regimes', return_value=mock_tax_results):
            mock_json_builder.return_value.build_comprehensive_json.return_value = mock_form16_json
            mock_optimizer.return_value.analyze_optimization_opportunities.return_value = mock_optimization
            
            result = self.service.analyze_tax_optimization(
                self.sample_form16_result, 
                self.sample_file_path,
                target_savings=50000
            )
            
            self.assertIn('tax_calculations', result)
            self.assertIn('optimization_analysis', result)
            self.assertIn('form16_data', result)
            self.assertIn('file_info', result)
            
            self.assertEqual(result['tax_calculations']['comparison']['recommended_regime'], 'new')
            self.assertEqual(len(result['optimization_analysis']['suggestions']), 2)
            self.assertEqual(result['file_info']['name'], 'form16.pdf')
    
    @patch('form16x.form16_parser.services.tax_optimization_service.TaxOptimizationEngine')
    def test_analyze_tax_optimization_with_object_result(self, mock_optimizer):
        """Test optimization analysis when optimizer returns object instead of dict."""
        # Mock optimization analysis as object
        mock_optimization_obj = Mock()
        mock_optimization_obj.suggestions = [
            {'category': 'Section 80C', 'potential_saving': 10000}
        ]
        mock_optimization_obj.total_potential_savings = 10000
        
        with patch.object(self.service, '_calculate_tax_for_regimes'):
            with patch.object(self.service.json_builder, 'build_comprehensive_json'):
                mock_optimizer.return_value.analyze_optimization_opportunities.return_value = mock_optimization_obj
                
                result = self.service.analyze_tax_optimization(
                    self.sample_form16_result, 
                    self.sample_file_path
                )
                
                # Verify object was converted to dict
                self.assertIsInstance(result['optimization_analysis'], dict)
                self.assertIn('suggestions', result['optimization_analysis'])
                self.assertIn('total_potential_savings', result['optimization_analysis'])
                self.assertEqual(result['optimization_analysis']['total_potential_savings'], 10000)
    
    def test_create_demo_analysis_medium_complexity(self):
        """Test demo analysis creation with medium complexity."""
        result = self.service.create_demo_analysis(complexity_level="medium")
        
        self.assertIn('tax_calculations', result)
        self.assertIn('optimization_analysis', result)
        self.assertTrue(result['demo_mode'])
        
        # Verify realistic ₹25L salary calculations
        self.assertEqual(result['current_taxable_income'], 2125000)  # ₹21.25L
        self.assertEqual(result['tax_calculations']['results']['new']['tax_liability'], 331250)
        self.assertEqual(result['tax_calculations']['results']['old']['tax_liability'], 468000)
        self.assertEqual(result['tax_savings'], 136750)  # NEW saves ₹1.37L vs OLD
        self.assertEqual(result['recommended_regime'], 'new')
    
    def test_create_demo_analysis_high_complexity(self):
        """Test demo analysis creation with high complexity."""
        result = self.service.create_demo_analysis(complexity_level="high")
        
        self.assertIn('optimization_analysis', result)
        self.assertTrue(result['demo_mode'])
        
        # Verify consistent tax calculations regardless of complexity
        self.assertEqual(result['current_tax_liability'], 331250)
        self.assertEqual(result['tax_savings'], 136750)
    
    @patch('form16x.form16_parser.services.tax_optimization_service.TaxOptimizationEngine')
    def test_create_demo_analysis_with_object_optimization(self, mock_optimizer):
        """Test demo analysis when optimizer returns object."""
        mock_optimization_obj = Mock()
        mock_optimization_obj.suggestions = [
            {'category': 'Demo Section 80C', 'potential_saving': 25000}
        ]
        mock_optimization_obj.total_potential_savings = 25000
        
        mock_optimizer.return_value.create_dummy_optimization_analysis.return_value = mock_optimization_obj
        
        result = self.service.create_demo_analysis()
        
        # Verify object was converted to dict
        self.assertIsInstance(result['optimization_analysis'], dict)
        self.assertEqual(result['optimization_analysis']['total_potential_savings'], 25000)
    
    def test_calculate_tax_for_regimes_structure(self):
        """Test tax calculation structure for regimes."""
        result = self.service._calculate_tax_for_regimes(self.sample_form16_result)
        
        # Verify correct structure is returned
        self.assertIn('results', result)
        self.assertIn('old', result['results'])
        self.assertIn('new', result['results'])
        self.assertIn('comparison', result)
        self.assertIn('recommendation', result)
    
    def test_service_initialization(self):
        """Test that service initializes all required components."""
        self.assertIsNotNone(self.service.optimizer)
        self.assertIsNotNone(self.service.tax_calculator)
        self.assertIsNotNone(self.service.json_builder)
    
    def test_analyze_optimization_without_target_savings(self):
        """Test optimization analysis without target savings specified."""
        with patch.object(self.service, '_calculate_tax_for_regimes'):
            with patch.object(self.service.json_builder, 'build_comprehensive_json'):
                with patch.object(self.service.optimizer, 'analyze_optimization_opportunities') as mock_analyze:
                    mock_analyze.return_value = {'suggestions': [], 'total_potential_savings': 0}
                    
                    result = self.service.analyze_tax_optimization(
                        self.sample_form16_result, 
                        self.sample_file_path,
                        target_savings=None  # No target specified
                    )
                    
                    # Verify analyze was called with None target
                    call_args = mock_analyze.call_args[0]
                    self.assertIsNone(call_args[2])  # target_savings argument
    
    def test_realistic_demo_values_consistency(self):
        """Test that demo values are realistic and consistent."""
        result = self.service.create_demo_analysis()
        
        old_regime = result['tax_calculations']['results']['old']
        new_regime = result['tax_calculations']['results']['new']
        
        # Verify NEW regime has lower tax than OLD for ₹25L salary
        self.assertLess(new_regime['tax_liability'], old_regime['tax_liability'])
        
        # Verify effective tax rates are reasonable
        self.assertGreater(old_regime['effective_tax_rate'], 20.0)  # ~22% for OLD
        self.assertLess(new_regime['effective_tax_rate'], 18.0)     # ~15.6% for NEW
        
        # Verify savings calculation is correct
        expected_savings = old_regime['tax_liability'] - new_regime['tax_liability']
        self.assertEqual(result['tax_savings'], expected_savings)
    
    def test_form16_json_builder_integration(self):
        """Test integration with Form16JSONBuilder."""
        with patch.object(self.service, '_calculate_tax_for_regimes'):
            with patch.object(self.service.optimizer, 'analyze_optimization_opportunities') as mock_analyze:
                mock_analyze.return_value = {'suggestions': []}
                
                result = self.service.analyze_tax_optimization(
                    self.sample_form16_result, 
                    self.sample_file_path
                )
                
                # Verify JSON builder was called correctly
                self.service.json_builder.build_comprehensive_json.assert_called_once()
                call_args = self.service.json_builder.build_comprehensive_json.call_args
                
                self.assertEqual(call_args[0][0], self.sample_form16_result)  # form16_result
                self.assertEqual(call_args[0][1], 'form16.pdf')  # file name
                self.assertEqual(call_args[0][2], 0.0)  # processing time
                self.assertEqual(call_args[0][3], {})   # additional_data


if __name__ == '__main__':
    unittest.main()