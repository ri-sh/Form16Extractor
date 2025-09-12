"""
Unit tests for PDF Reader performance optimizations.

Tests the lazy loading infrastructure and performance improvements
without breaking existing PDF processing functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

from form16x.form16_parser.pdf.reader import RobustPDFProcessor, _lazy_import, _check_module_availability


class TestPDFReaderPerformance(unittest.TestCase):
    """Test cases for PDF Reader performance optimizations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = RobustPDFProcessor()
        self.test_pdf_path = Path('/test/form16.pdf')
    
    def test_lazy_import_success(self):
        """Test successful lazy import with caching."""
        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module
            
            # First import
            result1 = _lazy_import('test_module')
            self.assertEqual(result1, mock_module)
            mock_import.assert_called_once_with('test_module')
            
            # Second import should use cache
            mock_import.reset_mock()
            result2 = _lazy_import('test_module')
            self.assertEqual(result2, mock_module)
            mock_import.assert_not_called()  # Should not import again
    
    def test_lazy_import_failure(self):
        """Test lazy import failure handling."""
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            with self.assertRaises(ImportError) as context:
                _lazy_import('nonexistent_module')
            
            self.assertIn("nonexistent_module not available", str(context.exception))
    
    def test_lazy_import_cached_failure(self):
        """Test that failed imports are cached to avoid repeated attempts."""
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            # First failed import
            with self.assertRaises(ImportError):
                _lazy_import('failing_module')
            
            # Second attempt should also raise but without calling __import__ again
            mock_import.reset_mock()
            with self.assertRaises(ImportError):
                _lazy_import('failing_module')
            
            mock_import.assert_not_called()  # Should use cached None
    
    def test_check_module_availability_available(self):
        """Test module availability check for available module."""
        with patch('form16x.form16_parser.pdf.reader._lazy_import') as mock_lazy_import:
            mock_lazy_import.return_value = Mock()
            
            result = _check_module_availability('available_module')
            self.assertTrue(result)
            mock_lazy_import.assert_called_once_with('available_module')
    
    def test_check_module_availability_unavailable(self):
        """Test module availability check for unavailable module."""
        with patch('form16x.form16_parser.pdf.reader._lazy_import') as mock_lazy_import:
            mock_lazy_import.side_effect = ImportError("Not available")
            
            result = _check_module_availability('unavailable_module')
            self.assertFalse(result)
    
    @patch('form16x.form16_parser.pdf.reader._lazy_import')
    def test_camelot_extraction_lazy_loading(self, mock_lazy_import):
        """Test that camelot is loaded lazily during extraction."""
        mock_camelot = Mock()
        mock_camelot.read_pdf.return_value = [Mock(df=Mock())]
        mock_lazy_import.return_value = mock_camelot
        
        with patch('pathlib.Path.exists', return_value=True):
            # This should trigger lazy loading of camelot
            result = self.processor.extract_with_camelot(self.test_pdf_path)
            
            # Verify camelot was lazily imported
            mock_lazy_import.assert_called_with('camelot')
            mock_camelot.read_pdf.assert_called()
    
    @patch('form16x.form16_parser.pdf.reader._lazy_import')
    def test_tabula_extraction_lazy_loading(self, mock_lazy_import):
        """Test that tabula is loaded lazily during extraction."""
        mock_tabula = Mock()
        mock_tabula.read_pdf.return_value = [Mock()]
        mock_lazy_import.return_value = mock_tabula
        
        with patch('pathlib.Path.exists', return_value=True):
            # This should trigger lazy loading of tabula
            result = self.processor.extract_with_tabula(self.test_pdf_path)
            
            # Verify tabula was lazily imported
            mock_lazy_import.assert_called_with('tabula')
            mock_tabula.read_pdf.assert_called()
    
    def test_processor_initialization_no_immediate_imports(self):
        """Test that processor initialization doesn't import heavy libraries."""
        with patch('builtins.__import__') as mock_import:
            processor = RobustPDFProcessor()
            
            # Verify no heavy libraries were imported during init
            import_calls = [call[0][0] for call in mock_import.call_args_list]
            heavy_libraries = ['camelot', 'tabula', 'pdfplumber']
            
            for lib in heavy_libraries:
                self.assertNotIn(lib, import_calls)
    
    @patch('form16x.form16_parser.pdf.reader._check_module_availability')
    def test_get_available_strategies_performance(self, mock_check_availability):
        """Test strategy availability checking uses lazy loading."""
        # Mock availability checks
        availability_map = {
            'camelot': True,
            'tabula': True,
            'pdfplumber': True
        }
        mock_check_availability.side_effect = lambda module: availability_map.get(module, False)
        
        strategies = self.processor.get_available_strategies()
        
        # Verify all strategies were checked
        self.assertEqual(mock_check_availability.call_count, 3)
        
        # Verify correct strategies are available
        expected_strategies = ['camelot', 'tabula', 'pdfplumber']
        self.assertEqual(sorted(strategies), sorted(expected_strategies))
    
    @patch('form16x.form16_parser.pdf.reader._check_module_availability')
    def test_get_available_strategies_partial_availability(self, mock_check_availability):
        """Test strategy detection with some libraries missing."""
        # Only camelot available
        availability_map = {
            'camelot': True,
            'tabula': False,
            'pdfplumber': False
        }
        mock_check_availability.side_effect = lambda module: availability_map.get(module, False)
        
        strategies = self.processor.get_available_strategies()
        
        self.assertEqual(strategies, ['camelot'])
    
    def test_module_cache_isolation(self):
        """Test that module cache doesn't leak between tests."""
        # Import the module cache directly
        from form16x.form16_parser.pdf.reader import _module_cache
        
        # Clear cache for clean test
        _module_cache.clear()
        
        with patch('builtins.__import__') as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module
            
            _lazy_import('test_isolation_module')
            
            # Verify module is cached
            self.assertIn('test_isolation_module', _module_cache)
            self.assertEqual(_module_cache['test_isolation_module'], mock_module)
    
    @patch('form16x.form16_parser.pdf.reader._lazy_import')
    def test_extraction_error_handling_with_lazy_loading(self, mock_lazy_import):
        """Test error handling when lazy-loaded modules fail."""
        mock_lazy_import.side_effect = ImportError("Camelot not available")
        
        with patch('pathlib.Path.exists', return_value=True):
            with self.assertRaises(ImportError):
                self.processor.extract_with_camelot(self.test_pdf_path)
    
    def test_processor_memory_efficiency(self):
        """Test that processor doesn't hold references to heavy modules unnecessarily."""
        processor = RobustPDFProcessor()
        
        # Check that processor doesn't have direct references to heavy libraries
        processor_dict = processor.__dict__
        heavy_libraries = ['camelot', 'tabula', 'pdfplumber']
        
        for lib in heavy_libraries:
            self.assertNotIn(lib, processor_dict)
    
    @patch('form16x.form16_parser.pdf.reader._lazy_import')
    def test_multiple_extraction_methods_independence(self, mock_lazy_import):
        """Test that different extraction methods load their modules independently."""
        mock_modules = {
            'camelot': Mock(),
            'tabula': Mock()
        }
        
        def import_side_effect(module_name):
            return mock_modules.get(module_name, Mock())
        
        mock_lazy_import.side_effect = import_side_effect
        
        with patch('pathlib.Path.exists', return_value=True):
            # Use different extraction methods
            self.processor.extract_with_camelot(self.test_pdf_path)
            self.processor.extract_with_tabula(self.test_pdf_path)
            
            # Verify both modules were imported independently
            import_calls = [call[0][0] for call in mock_lazy_import.call_args_list]
            self.assertIn('camelot', import_calls)
            self.assertIn('tabula', import_calls)


if __name__ == '__main__':
    unittest.main()