"""
Consolidate Command Controller - Handles Form16 consolidation command.

This controller handles the consolidate command workflow using the modular architecture.
"""

import json
from pathlib import Path
from typing import List

from .base_command import BaseCommand
from ..services.consolidation_service import ConsolidationService
from ..services.tax_calculation_service import TaxCalculationService
from ..presentation.formatters.tax_display_formatter import TaxDisplayFormatter
from ..display.rich_ui_components import RichUIComponents


class ConsolidateCommand(BaseCommand):
    """Command controller for Form16 consolidation."""
    
    def __init__(self):
        """Initialize the consolidate command with required services."""
        self.consolidation_service = ConsolidationService()
        self.tax_service = TaxCalculationService()
        self.tax_formatter = TaxDisplayFormatter()
        self.ui = RichUIComponents()
    
    def execute(self, args) -> int:
        """
        Execute the consolidate command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Display command header
            self._display_command_header()
            
            # Get file list and output path
            form16_files = [Path(f) for f in args.files]
            output_file = Path(args.output) if args.output else Path("consolidated_form16.json")
            
            # Check for demo mode
            if self._should_use_demo_mode(args, form16_files):
                return self._handle_demo_mode(args, form16_files, output_file)
            
            # Prepare tax arguments if requested
            tax_args = None
            if getattr(args, 'calculate_tax', False):
                tax_args = self._build_tax_args(args)
            
            # Consolidate Form16 files
            consolidation_result = self.consolidation_service.consolidate_form16_files(
                form16_files=form16_files,
                output_file=output_file,
                verbose=getattr(args, 'verbose', False),
                calculate_tax=getattr(args, 'calculate_tax', False),
                tax_args=tax_args
            )
            
            if not consolidation_result['success']:
                print(f"Error: {consolidation_result['error']}")
                return 1
            
            # Save consolidated result
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(consolidation_result['consolidated_data'], f, indent=2, ensure_ascii=False, default=str)
            
            # Display tax results if calculated
            if consolidation_result['tax_calculation']:
                self._display_tax_results(consolidation_result['tax_calculation'], args)
            
            # Display completion message
            self._display_completion_message(consolidation_result, output_file)
            
            return 0
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return 1
    
    def _display_command_header(self) -> None:
        """Display the command header."""
        self.ui.show_animated_header("CONSOLIDATE", "Combine multiple Form16s from different employers")
    
    def _should_use_demo_mode(self, args, form16_files: List[Path]) -> bool:
        """Check if demo mode should be used."""
        explicit_demo = hasattr(args, 'dummy') and args.dummy
        auto_demo = any(not f.exists() for f in form16_files)
        return explicit_demo or auto_demo
    
    def _handle_demo_mode(self, args, form16_files: List[Path], output_file: Path) -> int:
        """Handle consolidation in demo mode."""
        print(f"[DEMO MODE] Consolidating {len(form16_files)} Form16 files...")
        
        # Prepare tax arguments if requested
        tax_args = None
        if getattr(args, 'calculate_tax', False):
            tax_args = self._build_tax_args(args)
        
        # Get demo consolidation data
        demo_result = self.consolidation_service.consolidate_demo_data(
            form16_files=form16_files,
            output_file=output_file,
            calculate_tax=getattr(args, 'calculate_tax', False),
            tax_args=tax_args
        )
        
        # Display tax results if available
        if demo_result['tax_calculation']:
            self._display_tax_results(demo_result['tax_calculation'], args)
        
        # Display demo completion message
        print(f"\n[DEMO MODE] Consolidation completed successfully!")
        print(f"Employers processed: {demo_result['employers_count']}")
        print(f"Total gross income: Rs 2,500,000")
        print(f"Output file: {output_file}")
        
        return 0
    
    def _build_tax_args(self, args):
        """Build tax calculation arguments from command line args."""
        return {
            'tax_regime': getattr(args, 'tax_regime', 'both'),
            'city_type': 'metro',
            'age_category': 'below_60',
            'bank_interest': 0,
            'other_income': 0,
            'display_mode': 'colored',
            'summary': False,
            'verbose': getattr(args, 'verbose', False)
        }
    
    def _display_tax_results(self, tax_results, args) -> None:
        """Display tax calculation results."""
        tax_regime = getattr(args, 'tax_regime', 'both')
        self.tax_formatter.display_tax_results(tax_results, tax_regime, 'colored')
    
    def _display_completion_message(self, consolidation_result, output_file: Path) -> None:
        """Display consolidation completion message."""
        employers_count = consolidation_result.get('employers_count', 0)
        processing_time = consolidation_result.get('processing_time', 0)
        
        print(f"\nConsolidation completed successfully!")
        print(f"Employers processed: {employers_count}")
        print(f"Output file: {output_file}")
        print(f"Processing time: {processing_time:.2f} seconds")