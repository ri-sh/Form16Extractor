"""
Batch Command Controller - Handles batch processing command.

This controller handles the batch processing command workflow using the modular architecture.
"""

from pathlib import Path

from .base_command import BaseCommand
from ..services.batch_processing_service import BatchProcessingService
from ..presentation.formatters.batch_results_formatter import BatchResultsFormatter
from ..display.rich_ui_components import RichUIComponents


class BatchCommand(BaseCommand):
    """Command controller for batch processing."""
    
    def __init__(self):
        """Initialize the batch command with required services."""
        self.batch_service = BatchProcessingService()
        self.batch_formatter = BatchResultsFormatter()
        self.ui = RichUIComponents()
    
    def execute(self, args) -> int:
        """
        Execute the batch command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Display command header
            self._display_command_header()
            
            # Get input and output directories
            input_dir = Path(args.input_dir)
            output_dir = Path(args.output_dir)
            
            # Check for demo mode
            if self._should_use_demo_mode(args, input_dir):
                return self._handle_demo_mode(args, input_dir, output_dir)
            
            # Process batch
            batch_result = self.batch_service.process_batch(
                input_dir=input_dir,
                output_dir=output_dir,
                pattern=getattr(args, 'pattern', '*.pdf'),
                parallel_workers=getattr(args, 'parallel', 4),
                continue_on_error=getattr(args, 'continue_on_error', False),
                verbose=getattr(args, 'verbose', False)
            )
            
            if not batch_result['success']:
                print(f"Error: {batch_result['error']}")
                return 1
            
            # Display results
            self._display_batch_results(batch_result)
            
            return 0
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return 1
    
    def _display_command_header(self) -> None:
        """Display the command header."""
        self.ui.show_animated_header("BATCH", "Process multiple Form16 files in parallel")
    
    def _should_use_demo_mode(self, args, input_dir: Path) -> bool:
        """Check if demo mode should be used."""
        explicit_demo = hasattr(args, 'dummy') and args.dummy
        auto_demo = not input_dir.exists()
        return explicit_demo or auto_demo
    
    def _handle_demo_mode(self, args, input_dir: Path, output_dir: Path) -> int:
        """Handle batch processing in demo mode."""
        # Display demo header
        self.batch_formatter.display_batch_header(str(input_dir), str(output_dir))
        
        # Get demo batch processing data
        demo_result = self.batch_service.process_batch_demo(
            input_dir=input_dir,
            output_dir=output_dir,
            file_count=4,
            pattern=getattr(args, 'pattern', '*.pdf')
        )
        
        # Display demo results
        self._display_batch_results(demo_result)
        
        return 0
    
    def _display_batch_results(self, batch_result) -> None:
        """Display batch processing results."""
        results = batch_result.get('results', [])
        statistics = batch_result.get('statistics', {})
        demo_mode = batch_result.get('demo_mode', False)
        
        # Display individual file results
        self.batch_formatter.display_file_processing_progress(results, demo_mode)
        
        # Display summary
        self.batch_formatter.display_batch_summary(statistics, demo_mode)