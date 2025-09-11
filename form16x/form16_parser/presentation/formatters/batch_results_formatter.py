"""
Batch Results Formatter - Handles batch processing results display.

This formatter is responsible for displaying batch processing results
including progress, statistics, and individual file results.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.text import Text


class BatchResultsFormatter:
    """Formatter for batch processing results display."""
    
    def __init__(self):
        """Initialize the batch results formatter."""
        self.console = Console()
    
    def display_batch_header(self, input_dir: str, output_dir: str) -> None:
        """
        Display batch processing header information.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
        """
        header_text = Text()
        header_text.append("Batch Processing Demo", style="bold cyan")
        
        subtitle = Text()
        subtitle.append("Process multiple Form16 files in bulk", style="dim")
        
        self.console.print()
        self.console.print(header_text, justify="center")
        self.console.print(subtitle, justify="center")
        self.console.print("─" * 60, style="dim", justify="center")
        self.console.print()
        
        self.console.print(f"[DEMO MODE] Found {4} PDF files to process")
        self.console.print(f"Output directory: {output_dir}")
        self.console.print()
    
    def display_file_processing_progress(
        self,
        results: List[Dict[str, Any]],
        demo_mode: bool = False
    ) -> None:
        """
        Display individual file processing progress and results.
        
        Args:
            results: List of processing results for each file
            demo_mode: Whether this is demo mode
        """
        for i, result in enumerate(results, 1):
            file_name = result.get('file_name', 'Unknown')
            success = result.get('success', False)
            output_file = result.get('output_file', '')
            fields_extracted = result.get('fields_extracted', 0)
            total_fields = result.get('total_fields', 0)
            extraction_rate = result.get('extraction_rate', 0.0)
            error_message = result.get('error_message')
            
            # Display processing status
            status_icon = "✓" if success else "✗"
            status_color = "green" if success else "red"
            status_text = "Success" if success else "Failed"
            
            self.console.print(f"[{i}/{len(results)}] Processing: {file_name}")
            
            if success:
                self.console.print(f"  [{status_color}]{status_icon} {status_text}[/{status_color}]")
                self.console.print(f"    Output: {output_file}")
                self.console.print(f"    Extracted {fields_extracted}/{total_fields} fields ({extraction_rate:.1f}%)")
            else:
                self.console.print(f"  [{status_color}]{status_icon} {status_text}[/{status_color}]")
                if error_message:
                    self.console.print(f"    Error: {error_message}")
            
            self.console.print()
    
    def display_batch_summary(
        self,
        statistics: Dict[str, Any],
        demo_mode: bool = False
    ) -> None:
        """
        Display comprehensive batch processing summary.
        
        Args:
            statistics: Batch processing statistics
            demo_mode: Whether this is demo mode
        """
        total_files = statistics.get('total_files', 0)
        successful_files = statistics.get('successful_files', 0)
        failed_files = statistics.get('failed_files', 0)
        success_rate = statistics.get('success_rate', 0.0)
        total_time = statistics.get('total_processing_time', 0.0)
        
        # Create summary panel
        summary_lines = [
            "=" * 60,
            "BATCH PROCESSING SUMMARY",
            "=" * 60,
            f"Total files processed: {total_files}",
            f"Successful: {successful_files}",
            f"Failed: {failed_files}",
            f"Success rate: {success_rate}%",
            f"Total processing time: {total_time:.1f} seconds"
        ]
        
        if demo_mode:
            summary_lines.append("")
            summary_lines.append("[DEMO MODE] Batch processing completed successfully!")
        
        for line in summary_lines:
            if line.startswith("="):
                self.console.print(line, style="cyan")
            elif "SUMMARY" in line:
                self.console.print(line, style="bold cyan", justify="center")
            elif line.startswith("[DEMO MODE]"):
                self.console.print(line, style="bold green")
            else:
                self.console.print(line)
    
    def display_batch_results_table(
        self,
        results: List[Dict[str, Any]],
        show_details: bool = False
    ) -> None:
        """
        Display batch results in tabular format.
        
        Args:
            results: List of processing results
            show_details: Whether to show detailed information
        """
        table = Table(title="Batch Processing Results")
        
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("File Name", style="white", min_width=20)
        table.add_column("Status", style="white", width=10, justify="center")
        table.add_column("Fields", style="yellow", width=10, justify="right")
        table.add_column("Rate", style="cyan", width=8, justify="right")
        
        if show_details:
            table.add_column("Time", style="magenta", width=8, justify="right")
            table.add_column("Output File", style="dim", min_width=15)
        
        for i, result in enumerate(results, 1):
            file_name = result.get('file_name', 'Unknown')
            success = result.get('success', False)
            fields_extracted = result.get('fields_extracted', 0)
            total_fields = result.get('total_fields', 0)
            extraction_rate = result.get('extraction_rate', 0.0)
            processing_time = result.get('processing_time', 0.0)
            output_file = result.get('output_file', '')
            
            status = "[green]✓ Success[/green]" if success else "[red]✗ Failed[/red]"
            fields_text = f"{fields_extracted}/{total_fields}" if success else "0/0"
            rate_text = f"{extraction_rate:.1f}%" if success else "0.0%"
            
            row_data = [str(i), file_name, status, fields_text, rate_text]
            
            if show_details:
                time_text = f"{processing_time:.1f}s" if success else "0.0s"
                output_name = output_file.split('/')[-1] if output_file else ""
                row_data.extend([time_text, output_name])
            
            table.add_row(*row_data)
        
        self.console.print(table)
    
    def display_batch_errors(
        self,
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Display detailed error information for failed files.
        
        Args:
            results: List of processing results
        """
        failed_results = [r for r in results if not r.get('success', False)]
        
        if not failed_results:
            return
        
        self.console.print("\n[bold red]PROCESSING ERRORS[/bold red]")
        self.console.print("=" * 40)
        
        for result in failed_results:
            file_name = result.get('file_name', 'Unknown')
            error_message = result.get('error_message', 'Unknown error')
            
            error_panel = Panel(
                f"[red]{error_message}[/red]",
                title=f"[bold red]Error in {file_name}[/bold red]",
                border_style="red",
                padding=(0, 1)
            )
            
            self.console.print(error_panel)
    
    def display_processing_recommendations(
        self,
        statistics: Dict[str, Any]
    ) -> None:
        """
        Display recommendations based on processing results.
        
        Args:
            statistics: Batch processing statistics
        """
        success_rate = statistics.get('success_rate', 0.0)
        avg_extraction_rate = statistics.get('average_extraction_rate', 0.0)
        
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("Consider checking PDF quality and format consistency")
        
        if avg_extraction_rate < 80:
            recommendations.append("Review PDF structure - some files may have non-standard layouts")
        
        if success_rate == 100 and avg_extraction_rate > 90:
            recommendations.append("Excellent results! All files processed successfully")
        
        if recommendations:
            self.console.print("\n[bold yellow]RECOMMENDATIONS[/bold yellow]")
            for i, rec in enumerate(recommendations, 1):
                self.console.print(f"{i}. {rec}")
    
    def display_demo_batch_results(self) -> None:
        """Display demo batch processing results."""
        demo_results = [
            {
                'file_name': 'Company_A_Form16.pdf',
                'success': True,
                'fields_extracted': 235,
                'total_fields': 250,
                'extraction_rate': 94.0,
                'processing_time': 2.1,
                'output_file': 'output_test/Company_A_Form16.json'
            },
            {
                'file_name': 'Company_B_Form16.pdf',
                'success': True,
                'fields_extracted': 235,
                'total_fields': 250,
                'extraction_rate': 94.0,
                'processing_time': 2.4,
                'output_file': 'output_test/Company_B_Form16.json'
            },
            {
                'file_name': 'Employee_001_Form16.pdf',
                'success': True,
                'fields_extracted': 235,
                'total_fields': 250,
                'extraction_rate': 94.0,
                'processing_time': 2.7,
                'output_file': 'output_test/Employee_001_Form16.json'
            },
            {
                'file_name': 'Employee_002_Form16.pdf',
                'success': True,
                'fields_extracted': 235,
                'total_fields': 250,
                'extraction_rate': 94.0,
                'processing_time': 3.0,
                'output_file': 'output_test/Employee_002_Form16.json'
            }
        ]
        
        demo_stats = {
            'total_files': 4,
            'successful_files': 4,
            'failed_files': 0,
            'success_rate': 100.0,
            'total_processing_time': 8.2,
            'average_extraction_rate': 94.0
        }
        
        self.display_file_processing_progress(demo_results, demo_mode=True)
        self.display_batch_summary(demo_stats, demo_mode=True)
    
    def display_progress_bar(
        self,
        current: int,
        total: int,
        description: str = "Processing files"
    ) -> None:
        """
        Display a simple progress indicator.
        
        Args:
            current: Current file number
            total: Total number of files
            description: Description text
        """
        percentage = (current / total) * 100 if total > 0 else 0
        filled_length = int(40 * current // total) if total > 0 else 0
        bar = "█" * filled_length + "░" * (40 - filled_length)
        
        self.console.print(f"\r{description}: [{bar}] {percentage:.1f}% ({current}/{total})", end="")
        
        if current == total:
            self.console.print()  # New line when complete