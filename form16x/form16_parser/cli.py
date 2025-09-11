"""
Form16x CLI - Professional Form16 Processing & Tax Calculation Tool

This is the main CLI entry point that routes commands to their respective
controllers. The optimize command uses the new modular architecture,
while other commands use the legacy implementation until refactored.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Type

from .commands.base_command import BaseCommand
from .commands.optimize_command import OptimizeCommand
from .commands.extract_command import ExtractCommand
from .commands.consolidate_command import ConsolidateCommand
from .commands.batch_command import BatchCommand
from .display.rich_ui_components import RichUIComponents


class CLIRouter:
    """Lightweight CLI router that delegates to command controllers."""
    
    def __init__(self):
        """Initialize the CLI router."""
        self.ui = RichUIComponents()
        self.commands: Dict[str, Type[BaseCommand]] = {
            'optimize': OptimizeCommand,
            'extract': ExtractCommand,
            'consolidate': ConsolidateCommand,
            'batch': BatchCommand,
            # Add other commands as they are refactored
        }
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog="form16x",
            description="Professional Form16 Processing & Tax Calculation Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add version
        parser.add_argument(
            "--version", "-V", action="version", version="form16x 1.0.0"
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(
            dest="command", 
            help="Available commands",
            metavar="COMMAND"
        )
        
        # Add optimize command (new modular architecture)
        self._add_optimize_parser(subparsers)
        
        # Add extract command (new modular architecture)
        self._add_extract_parser(subparsers)
        
        # Add consolidate command (new modular architecture)
        self._add_consolidate_parser(subparsers)
        
        # Add batch command (new modular architecture)
        self._add_batch_parser(subparsers)
        
        # Legacy commands removed - all core functionality now uses modular architecture
        
        return parser
    
    def _add_optimize_parser(self, subparsers) -> None:
        """Add the optimize command parser."""
        optimize_parser = subparsers.add_parser(
            "optimize", 
            help="Analyze tax optimization opportunities"
        )
        optimize_parser.add_argument(
            "file", 
            help="Path to Form16 PDF file"
        )
        optimize_parser.add_argument(
            "--suggestions-only", 
            action="store_true",
            help="Show only optimization suggestions without current breakdown"
        )
        optimize_parser.add_argument(
            "--target-savings", 
            type=int,
            help="Target tax savings amount to achieve (in rupees)"
        )
        optimize_parser.add_argument(
            "--interactive", "-i", 
            action="store_true",
            help="Interactive mode with step-by-step recommendations"
        )
        
        # Common arguments
        self._add_common_arguments(optimize_parser)
    
    def _add_extract_parser(self, subparsers) -> None:
        """Add the extract command parser."""
        extract_parser = subparsers.add_parser(
            "extract", 
            help="Extract data from a single Form 16 PDF"
        )
        
        # Format selection (positional argument)
        extract_parser.add_argument(
            "format",
            choices=["json", "csv", "xlsx"],
            help="Output format (json, csv, xlsx)"
        )
        
        # File argument (positional)
        extract_parser.add_argument(
            "file",
            type=Path,
            help="Path to Form 16 PDF file"
        )
        
        # Legacy support for --file flag
        extract_parser.add_argument(
            "--file", "-f",
            dest="file_flag",
            type=Path,
            help="Path to Form 16 PDF file (legacy option)"
        )
        
        # Output options
        extract_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Output file path (default: auto-generated)"
        )
        extract_parser.add_argument(
            "--out-dir",
            type=Path,
            help="Output directory path (default: current directory)"
        )
        
        # Format options
        extract_parser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print JSON output"
        )
        
        # Tax calculation options
        extract_parser.add_argument(
            "--calculate-tax",
            action="store_true",
            help="Calculate comprehensive tax liability with regime comparison"
        )
        extract_parser.add_argument(
            "--tax-regime",
            choices=["old", "new", "both"],
            default="both",
            help="Tax regime for calculation (default: both)"
        )
        extract_parser.add_argument(
            "--city-type",
            choices=["metro", "non_metro"],
            default="metro",
            help="City type for HRA calculation (default: metro)"
        )
        extract_parser.add_argument(
            "--age-category",
            choices=["below_60", "senior_60_to_80", "super_senior_above_80"],
            default="below_60",
            help="Age category for tax calculation (default: below_60)"
        )
        extract_parser.add_argument(
            "--summary",
            action="store_true",
            help="Show detailed tax calculation breakdown"
        )
        extract_parser.add_argument(
            "--display-mode",
            choices=["table", "colored"],
            default="colored",
            help="Display mode for tax regime comparison"
        )
        extract_parser.add_argument(
            "--bank-interest",
            type=int,
            help="Annual bank/FD interest income"
        )
        extract_parser.add_argument(
            "--other-income",
            type=int,
            help="Other income sources not covered in Form16"
        )
        
        # Common arguments
        self._add_common_arguments(extract_parser)
    
    def _add_consolidate_parser(self, subparsers) -> None:
        """Add the consolidate command parser."""
        consolidate_parser = subparsers.add_parser(
            "consolidate", 
            help="Consolidate multiple Form16s from different employers"
        )
        
        # Files argument (required)
        consolidate_parser.add_argument(
            "--files", "-f",
            dest="files",
            nargs="+",
            required=True,
            help="List of Form 16 PDF files to consolidate"
        )
        
        # Output options
        consolidate_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Output JSON file path (default: consolidated_form16.json)"
        )
        
        # Tax calculation options
        consolidate_parser.add_argument(
            "--calculate-tax",
            action="store_true",
            help="Calculate comprehensive tax liability for consolidated income"
        )
        consolidate_parser.add_argument(
            "--tax-regime",
            choices=["old", "new", "both"],
            default="both",
            help="Tax regime for calculation (default: both)"
        )
        
        # Common arguments
        self._add_common_arguments(consolidate_parser)
    
    def _add_batch_parser(self, subparsers) -> None:
        """Add the batch command parser."""
        batch_parser = subparsers.add_parser(
            "batch", 
            help="Process multiple Form16 files in parallel"
        )
        
        # Input and output directories (required)
        batch_parser.add_argument(
            "--input-dir", "-i",
            type=Path,
            required=True,
            help="Directory containing Form 16 PDF files"
        )
        batch_parser.add_argument(
            "--output-dir", "-o",
            type=Path,
            required=True,
            help="Directory to save extraction results"
        )
        
        # Processing options
        batch_parser.add_argument(
            "--pattern",
            default="*.pdf",
            help="File pattern to match (default: *.pdf)"
        )
        batch_parser.add_argument(
            "--parallel",
            type=int,
            default=4,
            help="Number of parallel processes (default: 4)"
        )
        batch_parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue processing even if some files fail"
        )
        
        # Common arguments
        self._add_common_arguments(batch_parser)
    
    def _add_common_arguments(self, parser) -> None:
        """Add common arguments to a parser."""
        parser.add_argument(
            "--verbose", "-v", 
            action="store_true",
            help="Enable verbose logging"
        )
        parser.add_argument(
            "--dummy", "--demo", 
            action="store_true",
            help="Demo mode - use realistic dummy data for recordings (no real PDF processing)"
        )
        parser.add_argument(
            "--config", 
            type=Path,
            help="Configuration file path"
        )
    
    
    def route_command(self, args) -> int:
        """
        Route the command to the appropriate command controller.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code from the command
        """
        if not args.command:
            self.ui.console.print("[bold red]Error:[/bold red] No command specified")
            self.ui.console.print("Use --help to see available commands")
            return 1
        
        # Check if it's a new modular command
        if args.command in self.commands:
            command_class = self.commands[args.command]
            command = command_class()
            return command.execute(args)
        
        # All legacy functionality has been migrated to modular architecture
        
        # Show available commands
        self.ui.console.print(f"[bold red]Error:[/bold red] Unknown command: {args.command}")
        return 1
    
    def run(self, argv: list = None) -> int:
        """
        Main entry point for the CLI router.
        
        Args:
            argv: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            int: Exit code
        """
        if argv is None:
            argv = sys.argv[1:]
        
        try:
            parser = self.create_parser()
            
            # Parse all commands using the new modular architecture
            args = parser.parse_args(argv)
            return self.route_command(args)
        
        except KeyboardInterrupt:
            self.ui.console.print("\n[dim]Operation cancelled by user[/dim]")
            return 130
        
        except Exception as e:
            self.ui.console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
            return 1


def main():
    """Main entry point for Form16x CLI."""
    router = CLIRouter()
    exit_code = router.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()