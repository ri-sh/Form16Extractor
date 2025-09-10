#!/usr/bin/env python3
"""
Tests for Progress Tracker
===========================

Test coverage for progress tracking and animation utilities.
"""

import unittest
import time
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

from form16_extractor.progress.progress_tracker import (
    Form16ProgressTracker,
    Form16ProcessingStages,
    ProgressContext,
    SimpleProgressContext,
    RichProgressContext,
    create_progress_tracker
)


class TestForm16ProcessingStages(unittest.TestCase):
    """Test Form16ProcessingStages enum."""
    
    def test_stage_constants(self):
        """Test processing stage constants."""
        # Should have standard extraction stages
        stages = [
            Form16ProcessingStages.READING_PDF,
            Form16ProcessingStages.EXTRACTING_TABLES,
            Form16ProcessingStages.CLASSIFYING_TABLES,
            Form16ProcessingStages.READING_DATA,
            Form16ProcessingStages.EXTRACTING_JSON,
            Form16ProcessingStages.COMPUTING_TAX
        ]
        
        for stage in stages:
            self.assertIsInstance(stage, str)
    
    def test_get_stage_message(self):
        """Test getting stage messages."""
        # Test known stages
        message = Form16ProcessingStages.get_stage_message(Form16ProcessingStages.READING_PDF)
        self.assertEqual(message, "Reading PDF document...")
        
        message = Form16ProcessingStages.get_stage_message(Form16ProcessingStages.EXTRACTING_TABLES)
        self.assertEqual(message, "Extracting tables from PDF...")
        
        # Test unknown stage
        message = Form16ProcessingStages.get_stage_message("unknown_stage")
        self.assertIn("Processing:", message)


class TestForm16ProgressTracker(unittest.TestCase):
    """Test Form16ProgressTracker functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = Form16ProgressTracker(enable_animation=False)  # Disable animation for testing
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = Form16ProgressTracker()
        self.assertIsInstance(tracker, Form16ProgressTracker)
        
        # Test with animation disabled
        tracker_no_anim = Form16ProgressTracker(enable_animation=False)
        self.assertFalse(tracker_no_anim.enable_animation)
    
    @patch('form16_extractor.progress.progress_tracker.RICH_AVAILABLE', False)
    def test_processing_pipeline_no_rich(self):
        """Test processing pipeline without Rich library."""
        tracker = Form16ProgressTracker(enable_animation=True)  # Should fallback to simple
        
        with tracker.processing_pipeline("test.pdf") as context:
            self.assertIsInstance(context, SimpleProgressContext)
    
    def test_processing_pipeline_simple(self):
        """Test processing pipeline with simple context."""
        with self.tracker.processing_pipeline("test.pdf") as context:
            self.assertIsInstance(context, SimpleProgressContext)
            
            # Test context methods
            context.update_status("Test message")
            context.advance_stage(Form16ProcessingStages.READING_PDF)
            context.complete()
    
    @patch('form16_extractor.progress.progress_tracker.RICH_AVAILABLE', False)
    def test_status_spinner_no_rich(self):
        """Test status spinner without Rich library."""
        tracker = Form16ProgressTracker(enable_animation=True)  # Should fallback
        
        with patch('builtins.print') as mock_print:
            with tracker.status_spinner("Testing..."):
                pass
            mock_print.assert_called_with("Processing: Testing...")
    
    def test_status_spinner_simple(self):
        """Test status spinner with simple implementation."""
        with patch('builtins.print') as mock_print:
            with self.tracker.status_spinner("Testing..."):
                pass
            mock_print.assert_called_with("Processing: Testing...")


class TestProgressContext(unittest.TestCase):
    """Test ProgressContext base class."""
    
    def test_base_context_methods(self):
        """Test base context methods."""
        context = ProgressContext()
        
        # Should not raise errors (default implementations)
        context.update_status("Test")
        context.advance_stage("test_stage")
        context.complete()


class TestSimpleProgressContext(unittest.TestCase):
    """Test SimpleProgressContext functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context = SimpleProgressContext()
    
    @patch('builtins.print')
    def test_update_status(self, mock_print):
        """Test updating status."""
        self.context.update_status("Test message")
        mock_print.assert_called_with("[IN PROGRESS] Test message")
        
        # Test with progress completion
        self.context.update_status("Complete message", progress=100)
        mock_print.assert_called_with("[COMPLETED] Complete message")
    
    @patch('builtins.print')
    def test_advance_stage(self, mock_print):
        """Test advancing stage."""
        self.context.advance_stage(Form16ProcessingStages.READING_PDF)
        expected_message = Form16ProcessingStages.get_stage_message(Form16ProcessingStages.READING_PDF)
        mock_print.assert_called_with(f"[IN PROGRESS] {expected_message}")
    
    @patch('builtins.print')
    def test_complete(self, mock_print):
        """Test completion."""
        self.context.complete("All done")
        mock_print.assert_called_with("Completed: All done")
        
        # Test default message
        self.context.complete()
        mock_print.assert_called_with("Completed: Complete")


class TestRichProgressContext(unittest.TestCase):
    """Test RichProgressContext functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Progress and task_id
        self.mock_progress = Mock()
        self.task_id = "test_task_id"
        self.context = RichProgressContext(self.mock_progress, self.task_id)
    
    def test_initialization(self):
        """Test context initialization."""
        self.assertEqual(self.context.progress, self.mock_progress)
        self.assertEqual(self.context.task_id, self.task_id)
        self.assertEqual(self.context.current_progress, 0)
        
        # Should have predefined stages
        self.assertGreater(len(self.context.stages), 0)
    
    @patch('time.sleep')
    def test_update_status(self, mock_sleep):
        """Test updating status."""
        self.context.update_status("Test message", progress=50)
        
        # Should update progress
        self.mock_progress.update.assert_called_with(
            self.task_id,
            description="[cyan]Test message",
            completed=50
        )
        self.assertEqual(self.context.current_progress, 50)
        
        # Should have small delay
        mock_sleep.assert_called_with(0.1)
    
    @patch('time.sleep')
    def test_advance_stage(self, mock_sleep):
        """Test advancing to next stage."""
        # Test known stage
        self.context.advance_stage(Form16ProcessingStages.READING_PDF)
        
        # Should update with proper message
        expected_message = Form16ProcessingStages.get_stage_message(Form16ProcessingStages.READING_PDF)
        self.mock_progress.update.assert_called()
        
        # Should have updated progress
        self.assertGreater(self.context.current_progress, 0)
    
    def test_advance_stage_unknown(self):
        """Test advancing with unknown stage."""
        initial_progress = self.context.current_progress
        
        self.context.advance_stage("unknown_stage")
        
        # Should still update progress (fallback)
        self.assertGreaterEqual(self.context.current_progress, initial_progress)
    
    def test_complete(self):
        """Test completion."""
        self.context.complete("Processing done")
        
        # Should update to 100% with completion message
        self.mock_progress.update.assert_called_with(
            self.task_id,
            description="[bold green]Processing done",
            completed=100
        )


class TestCreateProgressTracker(unittest.TestCase):
    """Test create_progress_tracker function."""
    
    def test_create_tracker_default(self):
        """Test creating tracker with defaults."""
        tracker = create_progress_tracker()
        
        self.assertIsInstance(tracker, Form16ProgressTracker)
        self.assertTrue(tracker.enable_animation)  # Default should be True
    
    def test_create_tracker_no_animation(self):
        """Test creating tracker without animation."""
        tracker = create_progress_tracker(enable_animation=False)
        
        self.assertIsInstance(tracker, Form16ProgressTracker)
        self.assertFalse(tracker.enable_animation)


class TestProgressIntegration(unittest.TestCase):
    """Test progress tracking integration scenarios."""
    
    def test_full_processing_simulation(self):
        """Test full processing progress simulation."""
        tracker = Form16ProgressTracker(enable_animation=False)
        
        with tracker.processing_pipeline("test_form16.pdf") as context:
            # Simulate processing stages
            stages = [
                Form16ProcessingStages.READING_PDF,
                Form16ProcessingStages.EXTRACTING_TABLES,
                Form16ProcessingStages.CLASSIFYING_TABLES,
                Form16ProcessingStages.READING_DATA,
                Form16ProcessingStages.EXTRACTING_JSON,
                Form16ProcessingStages.COMPUTING_TAX
            ]
            
            for stage in stages:
                context.advance_stage(stage)
            
            context.complete("Processing complete")
    
    def test_status_spinner_with_work(self):
        """Test status spinner during work."""
        tracker = Form16ProgressTracker(enable_animation=False)
        
        with tracker.status_spinner("Processing data..."):
            # Simulate some work
            time.sleep(0.01)
    
    @patch('form16_extractor.progress.progress_tracker.RICH_AVAILABLE', True)
    @patch('form16_extractor.progress.progress_tracker.Progress')
    @patch('form16_extractor.progress.progress_tracker.Console')
    def test_rich_integration(self, mock_console, mock_progress_class):
        """Test Rich library integration."""
        # Mock Rich components
        mock_progress = Mock()
        mock_progress_class.return_value = mock_progress
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        
        # Create tracker with animation enabled
        tracker = Form16ProgressTracker(enable_animation=True)
        self.assertTrue(tracker.enable_animation)
        
        # Test that Rich components are used
        mock_console.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling in progress tracking."""
        tracker = Form16ProgressTracker(enable_animation=False)
        
        try:
            with tracker.processing_pipeline("test.pdf") as context:
                context.advance_stage(Form16ProcessingStages.READING_PDF)
                # Simulate error
                raise Exception("Test error")
        except Exception as e:
            self.assertEqual(str(e), "Test error")
        
        # Should not crash the progress system


if __name__ == '__main__':
    unittest.main()