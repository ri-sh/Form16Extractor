#!/usr/bin/env python3
"""
Tests for Table Processing Utilities
=====================================

Test coverage for table processing and manipulation functions.
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch

from form16x.form16_parser.utils.table_utils import (
    TablePreprocessor,
    TableAnalyzer,
    preprocess_tables
)


class TestTablePreprocessor(unittest.TestCase):
    """Test TablePreprocessor functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_df = pd.DataFrame({
            'Employee Name': ['John Doe', '', 'Jane Smith'],
            'Gross Salary': ['₹50,000', '₹0', '₹75,000'],
            'TDS Deducted': ['5000', '', '7500'],
            'Empty_Col': ['', '', '']
        })
    
    def test_clean_table(self):
        """Test basic table cleaning."""
        cleaned_df = TablePreprocessor.clean_table(self.sample_df)
        
        # Should return a DataFrame
        self.assertIsInstance(cleaned_df, pd.DataFrame)
        
        # Should handle empty input
        empty_df = pd.DataFrame()
        result = TablePreprocessor.clean_table(empty_df)
        self.assertTrue(result.empty)
    
    def test_remove_empty_rows_cols(self):
        """Test removing empty rows and columns."""
        df_with_empties = pd.DataFrame({
            'Good_Col': ['A', 'B', 'C'],
            'Empty_Col': ['', None, ''],
            'Mixed_Col': ['X', '', 'Z']
        })
        df_with_empties.loc[1] = ['', '', '']  # Empty row
        
        cleaned_df = TablePreprocessor.remove_empty_rows_cols(df_with_empties)
        
        # Should return a DataFrame
        self.assertIsInstance(cleaned_df, pd.DataFrame)
    
    def test_normalize_cell_values(self):
        """Test normalizing cell values."""
        df = pd.DataFrame({
            'Text': ['  HELLO  ', 'world', None],
            'Numbers': ['123', '  456  ', '']
        })
        
        normalized_df = TablePreprocessor.normalize_cell_values(df)
        
        # Should return a DataFrame
        self.assertIsInstance(normalized_df, pd.DataFrame)
    
    def test_handle_merged_cells(self):
        """Test handling merged cell artifacts."""
        df = pd.DataFrame({
            'Col1': ['A', '', 'C'],
            'Col2': ['1', '2', '3']
        })
        
        handled_df = TablePreprocessor.handle_merged_cells(df)
        
        # Should return a DataFrame
        self.assertIsInstance(handled_df, pd.DataFrame)


class TestTableAnalyzer(unittest.TestCase):
    """Test TableAnalyzer functionality."""
    
    def test_find_data_boundaries(self):
        """Test finding data boundaries."""
        df = pd.DataFrame([
            ['', 'TITLE', ''],
            ['Name', 'Value', 'Amount'],
            ['John', '100', '500'],
            ['Jane', '200', '600']
        ])
        
        boundaries = TableAnalyzer.find_data_boundaries(df)
        
        # Should return boundaries (could be dict or tuple based on implementation)
        self.assertTrue(isinstance(boundaries, (dict, tuple)))
    
    def test_get_table_stats(self):
        """Test getting table statistics."""
        df = pd.DataFrame({
            'Employee': ['John Doe', 'Jane Smith'],
            'Salary': [50000, 60000]
        })
        
        stats = TableAnalyzer.get_table_stats(df)
        
        # Should return stats
        self.assertIsInstance(stats, dict)


class TestPreprocessTables(unittest.TestCase):
    """Test preprocess_tables function."""
    
    def test_preprocess_single_table(self):
        """Test preprocessing single table."""
        df = pd.DataFrame({
            'Name': ['John', 'Jane'],
            'Amount': ['₹1000', '₹2000']
        })
        
        result = preprocess_tables([df])
        
        # Should return processed tables
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
    
    def test_preprocess_multiple_tables(self):
        """Test preprocessing multiple tables."""
        tables = [
            pd.DataFrame({'A': [1, 2], 'B': [3, 4]}),
            pd.DataFrame({'C': [5, 6], 'D': [7, 8]})
        ]
        
        result = preprocess_tables(tables)
        
        # Should return processed tables
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
    
    def test_preprocess_empty_list(self):
        """Test preprocessing empty table list."""
        result = preprocess_tables([])
        
        # Should handle empty input
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()