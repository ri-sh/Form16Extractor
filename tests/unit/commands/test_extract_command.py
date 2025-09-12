"""
Unit tests for ExtractCommand.

Tests the command layer logic, argument validation, and proper delegation
to service layer components without breaking functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from argparse import Namespace

from form16x.form16_parser.commands.extract_command import ExtractCommand


class TestExtractCommand(unittest.TestCase):
    """Test cases for ExtractCommand."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.command = ExtractCommand()
        
        # Create mock args with all required attributes
        self.mock_args = Namespace(
            format='json',
            file=Path('/test/form16.pdf'),
            file_flag=None,
            output=None,
            out_dir=None,
            pretty=False,
            calculate_tax=False,
            tax_regime='both',
            city_type='metro',
            age_category='below_60',
            summary=False,
            display_mode='colored',
            bank_interest=None,
            other_income=None,
            verbose=False,
            dummy=False,
            config=None
        )
    
    def test_validate_args_valid_file(self):
        """Test argument validation with valid file."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command._validate_args(self.mock_args)
                self.assertTrue(result)
    
    def test_validate_args_missing_file(self):
        """Test argument validation with missing file."""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.command._validate_args(self.mock_args)
            self.assertFalse(result)
    
    def test_validate_args_file_flag_fallback(self):
        """Test file_flag fallback when file is None."""
        self.mock_args.file = None
        self.mock_args.file_flag = Path('/test/form16.pdf')
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command._validate_args(self.mock_args)
                self.assertTrue(result)
                self.assertEqual(self.mock_args.file, self.mock_args.file_flag)
    
    @patch('form16x.form16_parser.commands.extract_command.ExtractionService')
    @patch('form16x.form16_parser.commands.extract_command.OutputService')
    def test_execute_successful_extraction(self, mock_output_service, mock_extraction_service):
        """Test successful extraction execution."""
        # Mock successful extraction
        mock_extraction_result = {
            'status': 'success',
            'form16_data': {
                'form16': {'part_a': {}, 'part_b': {}},
                'tax_calculation': None
            },
            'metadata': {'processing_time_seconds': 1.5}
        }
        
        mock_extraction_service.return_value.extract_form16_data.return_value = mock_extraction_result
        mock_output_service.return_value.save_extraction_result.return_value = '/test/output.json'
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command.execute(self.mock_args)
                
                self.assertEqual(result, 0)
                mock_extraction_service.return_value.extract_form16_data.assert_called_once()
                mock_output_service.return_value.save_extraction_result.assert_called_once()
    
    @patch('form16x.form16_parser.commands.extract_command.ExtractionService')
    def test_execute_extraction_failure(self, mock_extraction_service):
        """Test extraction failure handling."""
        # Mock extraction failure
        mock_extraction_result = {
            'status': 'error',
            'error_message': 'PDF parsing failed'
        }
        
        mock_extraction_service.return_value.extract_form16_data.return_value = mock_extraction_result
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command.execute(self.mock_args)
                
                self.assertEqual(result, 1)
    
    @patch('form16x.form16_parser.commands.extract_command.ExtractionService')
    @patch('form16x.form16_parser.commands.extract_command.OutputService')
    def test_execute_with_tax_calculation(self, mock_output_service, mock_extraction_service):
        """Test execution with tax calculation enabled."""
        self.mock_args.calculate_tax = True
        
        # Mock successful extraction with tax calculation
        mock_extraction_result = {
            'status': 'success',
            'form16_data': {
                'form16': {'part_a': {}, 'part_b': {}},
                'tax_calculation': {
                    'results': {
                        'old': {'tax_liability': 50000, 'effective_tax_rate': 10.0},
                        'new': {'tax_liability': 40000, 'effective_tax_rate': 8.0}
                    },
                    'comparison': {'recommended_regime': 'new'},
                    'recommendation': 'NEW regime saves ₹10,000'
                }
            },
            'metadata': {'processing_time_seconds': 2.5}
        }
        
        mock_extraction_service.return_value.extract_form16_data.return_value = mock_extraction_result
        mock_output_service.return_value.save_extraction_result.return_value = '/test/output.json'
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command.execute(self.mock_args)
                
                self.assertEqual(result, 0)
                # Verify tax calculation was requested
                call_args = mock_extraction_service.return_value.extract_form16_data.call_args
                self.assertTrue(call_args[1]['calculate_tax'])
    
    @patch('form16x.form16_parser.commands.extract_command.ExtractionService')
    def test_execute_exception_handling(self, mock_extraction_service):
        """Test exception handling during execution."""
        mock_extraction_service.return_value.extract_form16_data.side_effect = Exception("Unexpected error")
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = self.command.execute(self.mock_args)
                
                self.assertEqual(result, 1)
    
    def test_display_tax_results_comprehensive(self):
        """Test comprehensive tax results display."""
        tax_results = {
            'results': {
                'old': {
                    'tax_liability': 50000,
                    'effective_tax_rate': 10.0,
                    'taxable_income': 500000
                },
                'new': {
                    'tax_liability': 40000,
                    'effective_tax_rate': 8.0,
                    'taxable_income': 500000
                }
            },
            'comparison': {
                'recommended_regime': 'new',
                'savings_with_new': 10000
            },
            'recommendation': 'NEW regime saves ₹10,000'
        }
        
        form16_data = {
            'tax_calculation': {
                'extraction_data': {
                    'employee_name': 'Test Employee',
                    'gross_salary': 600000
                }
            }
        }
        
        with patch('builtins.print') as mock_print:
            self.command._display_tax_results(tax_results, self.mock_args, form16_data)
            mock_print.assert_called()
    
    def test_get_output_path_default(self):
        """Test default output path generation."""
        input_file = Path('/test/form16.pdf')
        result = self.command._get_output_path(input_file, 'json', None, None)
        
        expected = Path('/test/form16_extracted.json')
        self.assertEqual(result, expected)
    
    def test_get_output_path_custom_dir(self):
        """Test output path with custom directory."""
        input_file = Path('/test/form16.pdf')
        out_dir = Path('/custom/output')
        result = self.command._get_output_path(input_file, 'json', None, out_dir)
        
        expected = Path('/custom/output/form16_extracted.json')
        self.assertEqual(result, expected)
    
    def test_get_output_path_explicit(self):
        """Test explicit output path."""
        input_file = Path('/test/form16.pdf')
        output_path = Path('/custom/my_output.json')
        result = self.command._get_output_path(input_file, 'json', output_path, None)
        
        self.assertEqual(result, output_path)


if __name__ == '__main__':
    unittest.main()