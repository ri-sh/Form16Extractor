#!/usr/bin/env python3
"""
Tests for Configuration Settings
=================================

Test coverage for application configuration settings.
"""

import unittest
import os
from pathlib import Path

from form16_extractor.config.settings import (
    Environment,
    ExtractionSettings,
    Settings,
    get_settings
)


class TestEnvironment(unittest.TestCase):
    """Test Environment enum."""
    
    def test_environment_values(self):
        """Test environment enum values."""
        self.assertEqual(Environment.DEVELOPMENT.value, "development")
        self.assertEqual(Environment.TESTING.value, "testing")
        self.assertEqual(Environment.PRODUCTION.value, "production")
    
    def test_environment_membership(self):
        """Test environment membership checks."""
        envs = [Environment.DEVELOPMENT, Environment.TESTING, Environment.PRODUCTION]
        self.assertEqual(len(envs), 3)
        
        for env in envs:
            self.assertIsInstance(env, Environment)


class TestExtractionSettings(unittest.TestCase):
    """Test extraction settings configuration."""
    
    def test_extraction_settings_defaults(self):
        """Test extraction settings default values."""
        settings = ExtractionSettings()
        
        self.assertEqual(settings.extraction_timeout_seconds, 120)
        self.assertEqual(settings.max_table_extraction_retries, 3) 
        self.assertEqual(settings.confidence_threshold, 0.5)
        self.assertEqual(settings.max_concurrent_extractions, 1)
        self.assertTrue(settings.enable_caching)
        self.assertEqual(settings.cache_ttl_seconds, 3600)
        
        # Check preferred strategies are set
        self.assertIsNotNone(settings.preferred_strategies)
        self.assertIsInstance(settings.preferred_strategies, list)
        self.assertIn("camelot_lattice", settings.preferred_strategies)
    
    def test_extraction_settings_custom(self):
        """Test custom extraction settings."""
        custom_strategies = ["tabula", "pdfplumber"]
        
        settings = ExtractionSettings(
            extraction_timeout_seconds=60,
            confidence_threshold=0.8,
            max_table_extraction_retries=5,
            preferred_strategies=custom_strategies,
            enable_caching=False
        )
        
        self.assertEqual(settings.extraction_timeout_seconds, 60)
        self.assertEqual(settings.confidence_threshold, 0.8)
        self.assertEqual(settings.max_table_extraction_retries, 5)
        self.assertEqual(settings.preferred_strategies, custom_strategies)
        self.assertFalse(settings.enable_caching)
    
    def test_extraction_settings_strategies_default(self):
        """Test that preferred strategies get default values."""
        settings = ExtractionSettings()
        
        expected_strategies = [
            "camelot_lattice",
            "camelot_stream", 
            "tabula_lattice",
            "pdfplumber",
            "fallback"
        ]
        
        self.assertEqual(settings.preferred_strategies, expected_strategies)


class TestSettingsFactory(unittest.TestCase):
    """Test settings factory functions."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance
        self.assertIs(settings1, settings2)
        
        # Should be Settings object
        self.assertIsInstance(settings1, Settings)
    
    def test_settings_directories_created(self):
        """Test that settings creates necessary directories."""
        settings = get_settings()
        
        # Directories should exist
        self.assertTrue(settings.data_dir.exists())
        self.assertTrue(settings.logs_dir.exists()) 
        self.assertTrue(settings.cache_dir.exists())
    
    def test_settings_environment_config(self):
        """Test settings environment configuration."""
        settings = get_settings()
        
        # Should have environment set
        self.assertIsInstance(settings.environment, Environment)
        
        # Should have extraction settings
        self.assertIsInstance(settings.extraction, ExtractionSettings)


if __name__ == '__main__':
    unittest.main()