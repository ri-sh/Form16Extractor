"""
Tax Optimization Command - Lightweight command controller for tax optimization.

This command handles only argument parsing and delegates all business logic
to the TaxOptimizationService and presentation to TaxOptimizationFormatter.
"""

from pathlib import Path
from typing import Any

from .base_command import BaseCommand
from ..services.tax_optimization_service import TaxOptimizationService
from ..presentation.formatters.tax_optimization_formatter import TaxOptimizationFormatter
from ..display.rich_ui_components import RichUIComponents


class OptimizeCommand(BaseCommand):
    """Command for tax optimization analysis."""
    
    def __init__(self):
        """Initialize the optimize command."""
        super().__init__()
        self.service = TaxOptimizationService()
        self.formatter = TaxOptimizationFormatter()
        self.ui = RichUIComponents()
        
        # Import dependencies lazily to avoid circular imports
        self._pdf_processor = None
        self._extractor = None
    
    @property
    def pdf_processor(self):
        """Lazy initialization of PDF processor."""
        if self._pdf_processor is None:
            from ..pdf.reader import RobustPDFProcessor
            self._pdf_processor = RobustPDFProcessor()
        return self._pdf_processor
    
    @property 
    def extractor(self):
        """Lazy initialization of Form16 extractor."""
        if self._extractor is None:
            from ..extractors.form16_extractor import ModularSimpleForm16Extractor
            self._extractor = ModularSimpleForm16Extractor()
        return self._extractor
    
    def execute(self, args) -> int:
        """
        Execute the tax optimization command.
        
        Args:
            args: Command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Setup common arguments
            self.setup_common_args(args)
            
            # Validate file path
            file_path = Path(args.file)
            use_dummy_mode = self.should_use_dummy_mode(file_path, self.dummy_mode)
            
            if use_dummy_mode and not self.dummy_mode:
                print(f"[AUTO DEMO MODE] File not found - using demo data: {file_path}")
            
            # Show loading animations
            self._show_loading_stages(use_dummy_mode)
            
            # Get analysis result
            if use_dummy_mode:
                analysis_result = self.service.create_demo_analysis("medium")
            else:
                analysis_result = self._analyze_real_form16(file_path, args)
            
            # Display results using formatter
            self.formatter.display_optimization_analysis(analysis_result)
            
            return 0
            
        except Exception as e:
            self.ui.display_error_message(f"Tax optimization failed: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _show_loading_stages(self, dummy_mode: bool) -> None:
        """Show loading animations for different stages."""
        if dummy_mode:
            self.ui.show_loading_animation("Step 1: Calculating tax from Form16", 2.0)
            self.ui.show_loading_animation("Step 2: Extracting structured JSON data", 1.5)
            self.ui.show_loading_animation("Step 3: Analyzing tax optimization opportunities", 2.0)
        else:
            self.ui.show_loading_animation("Processing Form16 and calculating taxes", 3.0)
    
    def _analyze_real_form16(self, file_path: Path, args) -> dict:
        """
        Analyze real Form16 file for tax optimization.
        
        Args:
            file_path: Path to Form16 PDF file
            args: Command line arguments
            
        Returns:
            dict: Analysis result
        """
        self.log_verbose(f"Processing Form16: {file_path}")
        
        # Extract Form16 data
        extraction_result = self.pdf_processor.extract_tables(file_path)
        form16_result = self.extractor.extract_all(extraction_result.tables)
        
        if not form16_result:
            raise Exception("Failed to extract data from Form16")
        
        # Perform optimization analysis
        return self.service.analyze_tax_optimization(
            form16_result, 
            file_path, 
            getattr(args, 'target_savings', None)
        )