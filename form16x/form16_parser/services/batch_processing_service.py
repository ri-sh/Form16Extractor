"""
Batch Processing Service - Business logic for processing multiple Form16 files in parallel.

This service handles the complex workflow of:
- Discovering PDF files in directories
- Parallel processing of multiple files
- Progress tracking and error handling
- Results aggregation and reporting
"""

import os
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .extraction_service import ExtractionService
from ..progress import Form16ProgressTracker
from ..dummy_generator import DummyDataGenerator


class BatchProcessingService:
    """Service for handling batch processing of Form16 files."""
    
    def __init__(self):
        """Initialize the batch processing service with required dependencies."""
        self.extraction_service = ExtractionService()
        self.dummy_generator = DummyDataGenerator()
    
    def process_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        pattern: str = "*.pdf",
        parallel_workers: int = 4,
        continue_on_error: bool = False,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple Form16 files in parallel.
        
        Args:
            input_dir: Directory containing Form16 PDF files
            output_dir: Directory to save extraction results
            pattern: File pattern to match (default: *.pdf)
            parallel_workers: Number of parallel processing workers
            continue_on_error: Continue processing even if some files fail
            verbose: Enable verbose logging
            
        Returns:
            Dictionary containing batch processing results and statistics
        """
        start_time = time.time()
        
        # Discover files to process
        discovery_result = self._discover_files(input_dir, pattern)
        if not discovery_result['success']:
            return discovery_result
        
        pdf_files = discovery_result['files']
        
        if not pdf_files:
            return {
                'success': False,
                'error': f'No PDF files found in {input_dir} matching pattern {pattern}',
                'processing_time': time.time() - start_time
            }
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files in parallel
        processing_results = self._process_files_parallel(
            pdf_files, output_dir, parallel_workers, continue_on_error, verbose
        )
        
        # Aggregate results
        total_processing_time = time.time() - start_time
        batch_stats = self._calculate_batch_statistics(processing_results, total_processing_time)
        
        return {
            'success': True,
            'results': processing_results,
            'statistics': batch_stats,
            'input_directory': str(input_dir),
            'output_directory': str(output_dir),
            'processing_time': total_processing_time
        }
    
    def process_batch_demo(
        self,
        input_dir: Path,
        output_dir: Path,
        file_count: int = 4,
        pattern: str = "*.pdf"
    ) -> Dict[str, Any]:
        """
        Generate demo batch processing results for demonstration purposes.
        
        Args:
            input_dir: Original input directory (for display)
            output_dir: Output directory (for display)
            file_count: Number of demo files to simulate
            pattern: File pattern (for display)
            
        Returns:
            Dictionary containing demo batch processing results
        """
        from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
        from rich.console import Console
        
        start_time = time.time()
        console = Console()
        
        # Generate demo results
        demo_files = [
            f"Company_A_Form16.pdf",
            f"Company_B_Form16.pdf", 
            f"Employee_001_Form16.pdf",
            f"Employee_002_Form16.pdf"
        ][:file_count]
        
        processing_results = []
        
        # Create progress bar for demo mode
        with Progress(
            TextColumn("[bold green]Demo: Processing files..."),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Add demo task
            demo_task = progress.add_task("Demo processing", total=len(demo_files))
            
            for i, filename in enumerate(demo_files, 1):
                # Simulate processing time with longer delay for demo
                time.sleep(1.2)  # Increased from 0.5 to 1.2 seconds
                
                result = {
                    'file_name': filename,
                    'file_path': str(input_dir / filename),
                    'output_file': str(output_dir / filename.replace('.pdf', '.json')),
                    'success': True,
                    'processing_time': 2.0 + (i * 0.3),  # Simulated processing time
                    'fields_extracted': 235,
                    'total_fields': 250,
                    'extraction_rate': 94.0,
                    'error_message': None
                }
                processing_results.append(result)
                
                # Update progress
                progress.advance(demo_task)
            
            # Keep the completed progress bar visible for a moment
            time.sleep(1.0)
        
        total_processing_time = time.time() - start_time
        batch_stats = self._calculate_batch_statistics(processing_results, total_processing_time)
        
        return {
            'success': True,
            'results': processing_results,
            'statistics': batch_stats,
            'input_directory': str(input_dir),
            'output_directory': str(output_dir),
            'processing_time': total_processing_time,
            'demo_mode': True
        }
    
    def _discover_files(self, input_dir: Path, pattern: str) -> Dict[str, Any]:
        """
        Discover PDF files in the input directory.
        
        Args:
            input_dir: Directory to search for files
            pattern: File pattern to match
            
        Returns:
            Dictionary containing discovery results
        """
        if not input_dir.exists():
            return {
                'success': False,
                'error': f'Input directory not found: {input_dir}'
            }
        
        if not input_dir.is_dir():
            return {
                'success': False,
                'error': f'Input path is not a directory: {input_dir}'
            }
        
        try:
            # Find all PDF files matching the pattern
            pdf_files = list(input_dir.glob(pattern))
            pdf_files.sort()  # Sort for consistent processing order
            
            return {
                'success': True,
                'files': pdf_files,
                'file_count': len(pdf_files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error discovering files: {str(e)}'
            }
    
    def _process_files_parallel(
        self,
        pdf_files: List[Path],
        output_dir: Path,
        parallel_workers: int,
        continue_on_error: bool,
        verbose: bool
    ) -> List[Dict[str, Any]]:
        """
        Process files in parallel using ThreadPoolExecutor.
        
        Args:
            pdf_files: List of PDF files to process
            output_dir: Output directory for results
            parallel_workers: Number of parallel workers
            continue_on_error: Continue processing on errors
            verbose: Enable verbose logging
            
        Returns:
            List of processing results for each file
        """
        from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
        from rich.console import Console
        
        processing_results = []
        console = Console()
        
        # Limit workers to reasonable number
        max_workers = min(parallel_workers, len(pdf_files), os.cpu_count() or 4)
        
        # Create progress bar
        with Progress(
            TextColumn("[bold blue]Processing files..."),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Add main task for batch progress
            batch_task = progress.add_task("Batch processing", total=len(pdf_files))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(
                        self._process_single_file_for_batch,
                        pdf_file,
                        output_dir,
                        verbose
                    ): pdf_file
                    for pdf_file in pdf_files
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_file):
                    pdf_file = future_to_file[future]
                    
                    try:
                        result = future.result()
                        processing_results.append(result)
                        
                    except Exception as e:
                        error_result = {
                            'file_name': pdf_file.name,
                            'file_path': str(pdf_file),
                            'output_file': str(output_dir / pdf_file.stem) + '.json',
                            'success': False,
                            'processing_time': 0.0,
                            'fields_extracted': 0,
                            'total_fields': 0,
                            'extraction_rate': 0.0,
                            'error_message': str(e)
                        }
                        processing_results.append(error_result)
                        
                        if not continue_on_error:
                            # Cancel remaining tasks
                            for remaining_future in future_to_file:
                                remaining_future.cancel()
                            break
                    
                    # Update progress
                    progress.advance(batch_task)
        
        # Sort results by file name for consistent output
        processing_results.sort(key=lambda x: x['file_name'])
        return processing_results
    
    def _process_single_file_for_batch(
        self,
        pdf_file: Path,
        output_dir: Path,
        verbose: bool
    ) -> Dict[str, Any]:
        """
        Process a single file for batch processing.
        
        Args:
            pdf_file: Path to PDF file to process
            output_dir: Output directory for results
            verbose: Enable verbose logging
            
        Returns:
            Dictionary containing processing results for the file
        """
        start_time = time.time()
        
        try:
            # Determine output file path
            output_file = output_dir / (pdf_file.stem + '.json')
            
            # Use extraction service with batch mode enabled
            extraction_result = self.extraction_service.extract_form16_data(
                input_file=pdf_file,
                verbose=verbose,
                batch_mode=True,  # Skip UI delays
                calculate_tax=False  # Don't calculate tax in batch mode by default
            )
            
            if extraction_result['extraction_success']:
                # Save result to file
                import json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(extraction_result['form16_data'], f, indent=2, ensure_ascii=False, default=str)
                
                # Calculate extraction statistics
                fields_extracted = self._count_extracted_fields(extraction_result['form16_data'])
                total_fields = 250  # Estimated total possible fields
                extraction_rate = (fields_extracted / total_fields) * 100
                
                return {
                    'file_name': pdf_file.name,
                    'file_path': str(pdf_file),
                    'output_file': str(output_file),
                    'success': True,
                    'processing_time': extraction_result['processing_time'],
                    'fields_extracted': fields_extracted,
                    'total_fields': total_fields,
                    'extraction_rate': extraction_rate,
                    'error_message': None
                }
            else:
                return {
                    'file_name': pdf_file.name,
                    'file_path': str(pdf_file),
                    'output_file': str(output_file),
                    'success': False,
                    'processing_time': extraction_result['processing_time'],
                    'fields_extracted': 0,
                    'total_fields': 0,
                    'extraction_rate': 0.0,
                    'error_message': 'Extraction failed'
                }
                
        except Exception as e:
            return {
                'file_name': pdf_file.name,
                'file_path': str(pdf_file),
                'output_file': str(output_dir / (pdf_file.stem + '.json')),
                'success': False,
                'processing_time': time.time() - start_time,
                'fields_extracted': 0,
                'total_fields': 0,
                'extraction_rate': 0.0,
                'error_message': str(e)
            }
    
    def _count_extracted_fields(self, form16_data: Dict[str, Any]) -> int:
        """
        Count the number of successfully extracted fields.
        
        Args:
            form16_data: Extracted Form16 data dictionary
            
        Returns:
            Number of non-null, non-empty extracted fields
        """
        def count_fields(obj, path=""):
            """Recursively count non-empty fields."""
            count = 0
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if value is not None and value != "" and value != 0:
                        if isinstance(value, (dict, list)):
                            count += count_fields(value, f"{path}.{key}")
                        else:
                            count += 1
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    count += count_fields(item, f"{path}[{i}]")
            
            return count
        
        return count_fields(form16_data)
    
    def _calculate_batch_statistics(
        self,
        processing_results: List[Dict[str, Any]],
        total_processing_time: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive batch processing statistics.
        
        Args:
            processing_results: List of individual file processing results
            total_processing_time: Total time for batch processing
            
        Returns:
            Dictionary containing batch processing statistics
        """
        total_files = len(processing_results)
        successful_files = sum(1 for result in processing_results if result['success'])
        failed_files = total_files - successful_files
        
        success_rate = (successful_files / total_files * 100) if total_files > 0 else 0
        
        # Calculate average processing time for successful files
        successful_times = [
            result['processing_time'] 
            for result in processing_results 
            if result['success'] and result['processing_time'] > 0
        ]
        avg_processing_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        # Calculate average extraction rate for successful files
        successful_rates = [
            result['extraction_rate']
            for result in processing_results
            if result['success']
        ]
        avg_extraction_rate = sum(successful_rates) / len(successful_rates) if successful_rates else 0
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': round(success_rate, 1),
            'total_processing_time': round(total_processing_time, 2),
            'average_processing_time': round(avg_processing_time, 2),
            'average_extraction_rate': round(avg_extraction_rate, 1),
            'timestamp': datetime.now().isoformat()
        }