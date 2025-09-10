"""
Progress Animation System for Form16 PDF Processing

This module provides beautiful terminal progress animations with changing status text
during PDF processing operations using the Rich library.
"""

import time
from typing import Optional, Callable, Any
from contextlib import contextmanager

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.console import Console
    from rich.status import Status
    from rich import print as rich_print
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Form16ProgressTracker:
    """Progress tracker for Form16 PDF processing with animated status updates."""
    
    def __init__(self, enable_animation: bool = True, dummy_mode: bool = False):
        """Initialize the progress tracker.
        
        Args:
            enable_animation: Whether to show animated progress (requires Rich library)
            dummy_mode: Whether to use faster dummy mode for demos
        """
        self.enable_animation = enable_animation and RICH_AVAILABLE
        self.dummy_mode = dummy_mode
        self.console = Console() if RICH_AVAILABLE else None
    
    @contextmanager
    def processing_pipeline(self, pdf_filename: str):
        """Context manager for the complete PDF processing pipeline.
        
        Args:
            pdf_filename: Name of the PDF file being processed
        """
        if not self.enable_animation:
            yield SimpleProgressContext()
            return
        
        # Create progress display with custom columns
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        )
        
        with progress:
            # Create main task
            main_task = progress.add_task(
                f"[cyan]Processing {pdf_filename}...",
                total=100
            )
            
            yield RichProgressContext(progress, main_task, self.dummy_mode)
    
    @contextmanager
    def status_spinner(self, message: str):
        """Context manager for simple status spinner.
        
        Args:
            message: Status message to display
        """
        if not self.enable_animation:
            print(f"Processing: {message}")
            yield
            return
        
        with Status(f"[bold green]{message}", spinner="dots", console=self.console):
            yield


class ProgressContext:
    """Base class for progress context."""
    
    def update_status(self, message: str, progress: int = None):
        """Update the current processing status."""
        pass
    
    def advance_stage(self, stage_name: str):
        """Advance to the next processing stage."""
        pass
    
    def complete(self, message: str = "Complete"):
        """Mark processing as complete."""
        pass


class SimpleProgressContext(ProgressContext):
    """Simple progress context for when Rich is not available."""
    
    def update_status(self, message: str, progress: int = None):
        """Update the current processing status."""
        status_indicator = "[IN PROGRESS]"
        if progress is not None and progress >= 100:
            status_indicator = "[COMPLETED]"
        
        print(f"{status_indicator} {message}")
    
    def advance_stage(self, stage_name: str):
        """Advance to the next processing stage (simple version)."""
        message = Form16ProcessingStages.get_stage_message(stage_name)
        self.update_status(message)
    
    def complete(self, message: str = "Complete"):
        """Mark processing as complete."""
        print(f"Completed: {message}")


class RichProgressContext(ProgressContext):
    """Rich-enabled progress context with animated progress bars."""
    
    def __init__(self, progress: 'Progress', task_id, dummy_mode: bool = False):
        self.progress = progress
        self.task_id = task_id
        self.dummy_mode = dummy_mode
        
        # Define the processing stages and their weights
        self.stages = [
            ("Reading PDF document...", 15),
            ("Extracting tables from PDF...", 25),
            ("Classifying table structures...", 20),
            ("Reading data from tables...", 20),
            ("Extracting Form16 JSON data...", 15),
            ("Computing tax calculations...", 5)
        ]
        
        self.current_progress = 0
    
    def update_status(self, message: str, progress: int = None):
        """Update the current processing status with animated progress."""
        if progress is not None:
            self.current_progress = min(progress, 100)
        
        # Update task description and progress
        self.progress.update(
            self.task_id,
            description=f"[cyan]{message}",
            completed=self.current_progress
        )
        
        # Faster animation in dummy mode for demos
        if self.dummy_mode:
            time.sleep(0.3)  # 300ms in dummy mode
        else:
            time.sleep(0.1)  # 100ms in normal mode
    
    def advance_stage(self, stage_name: str):
        """Advance to the next processing stage."""
        # Get the display message for this stage
        display_message = Form16ProcessingStages.get_stage_message(stage_name)
        
        # Find matching stage in our predefined stages for progress calculation
        stage_index = -1
        if stage_name == Form16ProcessingStages.READING_PDF:
            stage_index = 0
        elif stage_name == Form16ProcessingStages.EXTRACTING_TABLES:
            stage_index = 1
        elif stage_name == Form16ProcessingStages.CLASSIFYING_TABLES:
            stage_index = 2
        elif stage_name == Form16ProcessingStages.READING_DATA:
            stage_index = 3
        elif stage_name == Form16ProcessingStages.EXTRACTING_JSON:
            stage_index = 4
        elif stage_name == Form16ProcessingStages.COMPUTING_TAX:
            stage_index = 5
        
        if stage_index >= 0:
            # Calculate cumulative progress up to this stage
            total_weight = sum(w for _, w in self.stages[:stage_index])
            self.current_progress = min(total_weight + self.stages[stage_index][1] // 2, 100)
        else:
            # Fallback: just increment progress
            self.current_progress = min(self.current_progress + 15, 100)
        
        self.update_status(display_message, self.current_progress)
    
    def complete(self, message: str = "Processing complete"):
        """Mark processing as complete."""
        self.progress.update(
            self.task_id,
            description=f"[bold green]{message}",
            completed=100
        )


class Form16ProcessingStages:
    """Predefined processing stages for Form16 extraction."""
    
    READING_PDF = "reading_pdf"
    EXTRACTING_TABLES = "extracting_tables"
    CLASSIFYING_TABLES = "classifying_tables"
    READING_DATA = "reading_data"
    EXTRACTING_JSON = "extracting_json"
    COMPUTING_TAX = "computing_tax"
    
    @classmethod
    def get_stage_message(cls, stage: str) -> str:
        """Get display message for a processing stage."""
        stage_messages = {
            cls.READING_PDF: "Reading PDF document...",
            cls.EXTRACTING_TABLES: "Extracting tables from PDF...",
            cls.CLASSIFYING_TABLES: "Classifying table structures...",
            cls.READING_DATA: "Reading data from tables...",
            cls.EXTRACTING_JSON: "Extracting Form16 JSON data...",
            cls.COMPUTING_TAX: "Computing tax calculations..."
        }
        return stage_messages.get(stage, f"Processing: {stage.replace('_', ' ').title()}...")


# Convenience function for backward compatibility
def create_progress_tracker(enable_animation: bool = True) -> Form16ProgressTracker:
    """Create a Form16 progress tracker instance.
    
    Args:
        enable_animation: Whether to enable animated progress (requires Rich library)
        
    Returns:
        Form16ProgressTracker instance
    """
    return Form16ProgressTracker(enable_animation)