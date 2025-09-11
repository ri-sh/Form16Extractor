"""
Validation Formatter - Handles validation results display.

This formatter is responsible for displaying data validation results
including error reports, warnings, and compliance status.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn


class ValidationFormatter:
    """Formatter for validation results display."""
    
    def __init__(self):
        """Initialize the validation formatter."""
        self.console = Console()
    
    def display_validation_results(
        self,
        validation_results: Dict[str, Any],
        show_details: bool = True
    ) -> None:
        """
        Display comprehensive validation results.
        
        Args:
            validation_results: Validation results dictionary
            show_details: Whether to show detailed breakdown
        """
        if not validation_results:
            self.console.print("[red]No validation results available[/red]")
            return
        
        self._display_validation_header(validation_results)
        self._display_validation_summary(validation_results)
        
        if show_details:
            self._display_detailed_results(validation_results)
        
        self._display_validation_footer(validation_results)
    
    def display_validation_header(self, file_path: str) -> None:
        """
        Display validation header information.
        
        Args:
            file_path: Path to file being validated
        """
        header_text = Text()
        header_text.append("Form16 Data Validation", style="bold cyan")
        
        subtitle = Text()
        subtitle.append("Validate extracted Form16 data for accuracy", style="dim")
        
        self.console.print()
        self.console.print(header_text, justify="center")
        self.console.print(subtitle, justify="center")
        self.console.print("─" * 60, style="dim", justify="center")
        self.console.print()
        
        self.console.print(f"Validating: {file_path}")
        self.console.print()
    
    def display_demo_validation_results(self, file_path: str) -> None:
        """
        Display demo validation results for demonstration purposes.
        
        Args:
            file_path: Original file path (for display)
        """
        demo_results = {
            'file_path': file_path,
            'overall_valid': True,
            'validation_score': 93.3,
            'validation_summary': {
                'total_checks': 45,
                'passed_checks': 42,
                'failed_checks': 1,
                'warnings': 2
            },
            'detailed_results': {
                'structure': {'status': 'PASSED', 'checks_passed': 8, 'checks_failed': 0},
                'employee_data': {'status': 'PASSED', 'checks_passed': 5, 'checks_failed': 0},
                'employer_data': {'status': 'PASSED', 'checks_passed': 6, 'checks_failed': 0},
                'salary_data': {'status': 'WARNING', 'checks_passed': 9, 'checks_failed': 0},
                'deductions': {'status': 'PASSED', 'checks_passed': 7, 'checks_failed': 0},
                'tax_calculations': {'status': 'FAILED', 'checks_passed': 4, 'checks_failed': 1},
                'financial_year': {'status': 'PASSED', 'checks_passed': 2, 'checks_failed': 0},
                'data_consistency': {'status': 'WARNING', 'checks_passed': 1, 'checks_failed': 0}
            },
            'errors': ['Tax calculation mismatch: TDS amount does not match quarterly totals'],
            'warnings': ['HRA amount seems unusually high', 'Some optional deduction fields are missing'],
            'recommendations': [
                'Verify HRA calculation with rent receipts',
                'Check TDS calculation with quarterly statements',
                'Consider adding health insurance premium data'
            ],
            'demo_mode': True
        }
        
        self.display_validation_results(demo_results, show_details=True)
    
    def _display_validation_header(self, validation_results: Dict[str, Any]) -> None:
        """Display validation header with file information."""
        file_path = validation_results.get('file_path', 'Unknown')
        timestamp = validation_results.get('validation_timestamp', 'Unknown')
        
        header_panel = Panel(
            f"[cyan]File:[/cyan] {file_path}\n[cyan]Validated at:[/cyan] {timestamp}",
            title="[bold cyan]Validation Report[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )
        
        self.console.print(header_panel)
        self.console.print()
    
    def _display_validation_summary(self, validation_results: Dict[str, Any]) -> None:
        """Display high-level validation summary."""
        overall_valid = validation_results.get('overall_valid', False)
        validation_score = validation_results.get('validation_score', 0.0)
        summary = validation_results.get('validation_summary', {})
        
        total_checks = summary.get('total_checks', 0)
        passed_checks = summary.get('passed_checks', 0)
        failed_checks = summary.get('failed_checks', 0)
        warnings = summary.get('warnings', 0)
        
        # Overall status
        status_color = "green" if overall_valid else "red"
        status_text = "VALID" if overall_valid else "INVALID"
        
        self.console.print(f"[bold {status_color}]Overall Status: {status_text}[/bold {status_color}]")
        self.console.print(f"[bold]Validation Score: {validation_score}%[/bold]")
        self.console.print()
        
        # Summary statistics
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_row("Total Checks:", f"[bold]{total_checks}[/bold]")
        summary_table.add_row("Passed:", f"[green]{passed_checks}[/green]")
        summary_table.add_row("Failed:", f"[red]{failed_checks}[/red]")
        summary_table.add_row("Warnings:", f"[yellow]{warnings}[/yellow]")
        
        summary_panel = Panel(
            summary_table,
            title="[bold]Validation Summary[/bold]",
            border_style="blue",
            padding=(0, 1)
        )
        
        self.console.print(summary_panel)
        self.console.print()
    
    def _display_detailed_results(self, validation_results: Dict[str, Any]) -> None:
        """Display detailed validation results by category."""
        detailed_results = validation_results.get('detailed_results', {})
        
        if not detailed_results:
            return
        
        self.console.print("[bold]Detailed Validation Results[/bold]")
        self.console.print("─" * 40)
        
        # Create detailed results table
        table = Table()
        table.add_column("Category", style="white", width=20)
        table.add_column("Status", style="white", width=10, justify="center")
        table.add_column("Passed", style="green", width=8, justify="center")
        table.add_column("Failed", style="red", width=8, justify="center")
        table.add_column("Details", style="dim", min_width=20)
        
        for category, result in detailed_results.items():
            status = result.get('status', 'UNKNOWN')
            passed = result.get('checks_passed', 0)
            failed = result.get('checks_failed', 0)
            
            # Format category name
            category_name = category.replace('_', ' ').title()
            
            # Status styling
            if status == 'PASSED':
                status_display = "[green]✓ PASSED[/green]"
            elif status == 'FAILED':
                status_display = "[red]✗ FAILED[/red]"
            elif status == 'WARNING':
                status_display = "[yellow]⚠ WARNING[/yellow]"
            else:
                status_display = "[dim]? UNKNOWN[/dim]"
            
            # Details
            details = ""
            if failed > 0:
                details = f"{failed} issue(s) found"
            elif status == 'WARNING':
                details = "Minor issues detected"
            else:
                details = "All checks passed"
            
            table.add_row(category_name, status_display, str(passed), str(failed), details)
        
        self.console.print(table)
        self.console.print()
    
    def _display_validation_footer(self, validation_results: Dict[str, Any]) -> None:
        """Display validation footer with errors, warnings, and recommendations."""
        errors = validation_results.get('errors', [])
        warnings = validation_results.get('warnings', [])
        recommendations = validation_results.get('recommendations', [])
        
        # Display errors
        if errors:
            self.console.print("[bold red]ERRORS FOUND[/bold red]")
            for i, error in enumerate(errors, 1):
                self.console.print(f"  {i}. [red]{error}[/red]")
            self.console.print()
        
        # Display warnings
        if warnings:
            self.console.print("[bold yellow]WARNINGS[/bold yellow]")
            for i, warning in enumerate(warnings, 1):
                self.console.print(f"  {i}. [yellow]{warning}[/yellow]")
            self.console.print()
        
        # Display recommendations
        if recommendations:
            self.console.print("[bold cyan]RECOMMENDATIONS[/bold cyan]")
            for i, recommendation in enumerate(recommendations, 1):
                self.console.print(f"  {i}. [cyan]{recommendation}[/cyan]")
            self.console.print()
        
        # Demo mode indicator
        if validation_results.get('demo_mode', False):
            demo_panel = Panel(
                "[bold green]Demo validation completed successfully![/bold green]",
                border_style="green"
            )
            self.console.print(demo_panel)
    
    def display_validation_progress(self, current_check: str, total_checks: int, completed: int) -> None:
        """
        Display validation progress information.
        
        Args:
            current_check: Name of current validation check
            total_checks: Total number of validation checks
            completed: Number of completed checks
        """
        percentage = (completed / total_checks * 100) if total_checks > 0 else 0
        
        self.console.print(f"[cyan]Running validation check:[/cyan] {current_check}")
        self.console.print(f"Progress: {completed}/{total_checks} ({percentage:.1f}%)")
    
    def display_validation_error(self, error_message: str) -> None:
        """
        Display validation error message.
        
        Args:
            error_message: Error message to display
        """
        error_panel = Panel(
            f"[red]Validation Error: {error_message}[/red]",
            title="[bold red]Validation Failed[/bold red]",
            border_style="red"
        )
        
        self.console.print(error_panel)
    
    def display_validation_score_badge(self, score: float) -> None:
        """
        Display validation score as a badge.
        
        Args:
            score: Validation score (0-100)
        """
        if score >= 90:
            badge_color = "green"
            grade = "A"
        elif score >= 80:
            badge_color = "yellow"
            grade = "B"
        elif score >= 70:
            badge_color = "orange"
            grade = "C"
        else:
            badge_color = "red"
            grade = "F"
        
        badge_text = f"[bold {badge_color}]Validation Score: {score:.1f}% (Grade: {grade})[/bold {badge_color}]"
        
        badge_panel = Panel(
            badge_text,
            border_style=badge_color,
            padding=(0, 2)
        )
        
        self.console.print(badge_panel)
    
    def display_quick_validation_summary(
        self,
        file_path: str,
        is_valid: bool,
        score: float,
        errors_count: int,
        warnings_count: int
    ) -> None:
        """
        Display a quick validation summary.
        
        Args:
            file_path: Path to validated file
            is_valid: Whether validation passed
            score: Validation score
            errors_count: Number of errors
            warnings_count: Number of warnings
        """
        status = "[green]✓ VALID[/green]" if is_valid else "[red]✗ INVALID[/red]"
        
        self.console.print(f"File: {file_path}")
        self.console.print(f"Status: {status}")
        self.console.print(f"Score: {score:.1f}%")
        self.console.print(f"Errors: {errors_count}, Warnings: {warnings_count}")
        self.console.print("─" * 50)