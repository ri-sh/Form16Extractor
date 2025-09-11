"""
Extraction Service - Core business logic for PDF extraction.

This service handles the entire PDF extraction workflow including:
- PDF processing and table extraction
- Form16 data extraction
- JSON result building
- Tax calculation integration
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal

from ..extractors.enhanced_form16_extractor import EnhancedForm16Extractor, ProcessingLevel
from ..pdf.reader import RobustPDFProcessor
from ..utils.json_builder import Form16JSONBuilder
from ..progress import Form16ProgressTracker, Form16ProcessingStages
from ..dummy_generator import DummyDataGenerator


class ExtractionService:
    """Service for handling PDF extraction workflow."""
    
    def __init__(self):
        """Initialize the extraction service with required dependencies."""
        self.extractor = EnhancedForm16Extractor(ProcessingLevel.ENHANCED)
        self.pdf_processor = RobustPDFProcessor()
        self.dummy_generator = DummyDataGenerator()
    
    def extract_form16_data(
        self, 
        input_file: Path,
        verbose: bool = False,
        batch_mode: bool = False,
        calculate_tax: bool = False,
        tax_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract Form16 data from PDF file.
        
        Args:
            input_file: Path to PDF file
            verbose: Enable verbose logging
            batch_mode: Skip UI delays for batch processing
            calculate_tax: Whether to calculate tax
            tax_args: Additional arguments for tax calculation
            
        Returns:
            Dict containing extraction results and metadata
        """
        start_time = time.time()
        
        # Initialize progress tracker
        progress_tracker = Form16ProgressTracker(
            enable_animation=not verbose, 
            dummy_mode=False
        )
        
        # Process PDF with animated progress
        with progress_tracker.processing_pipeline(input_file.name) as progress:
            # Stage 1: Reading PDF
            progress.advance_stage(Form16ProcessingStages.READING_PDF)
            if not batch_mode:
                time.sleep(2.0)
            
            # Stage 2: Extract tables from PDF
            progress.advance_stage(Form16ProcessingStages.EXTRACTING_TABLES)
            if verbose:
                print(f"Processing PDF: {input_file}")
            
            extraction_result = self.pdf_processor.extract_tables(input_file)
            tables = extraction_result.tables
            text_data = getattr(extraction_result, 'text_data', None)
            
            # Stage 3: Classifying tables
            progress.advance_stage(Form16ProcessingStages.CLASSIFYING_TABLES)
            if verbose:
                print(f"Extracted {len(tables)} tables from PDF")
            if not batch_mode:
                time.sleep(2.0)
            
            # Stage 4: Reading data from tables
            progress.advance_stage(Form16ProcessingStages.READING_DATA)
            if not batch_mode:
                time.sleep(2.0)
            
            # Stage 5: Extract Form16 data
            progress.advance_stage(Form16ProcessingStages.EXTRACTING_JSON)
            form16_result = self.extractor.extract_all(tables, text_data=text_data)
            processing_time = time.time() - start_time
            
            # Build comprehensive JSON result
            result = Form16JSONBuilder.build_comprehensive_json(
                form16_doc=form16_result,
                pdf_file_name=input_file.name,
                processing_time=processing_time,
                extraction_metadata=getattr(form16_result, 'extraction_metadata', {})
            )
            if not batch_mode:
                time.sleep(2.0)
            
            # Add tax calculation if requested
            if calculate_tax and tax_args:
                from .tax_calculation_service import TaxCalculationService
                tax_service = TaxCalculationService()
                tax_results = tax_service.calculate_comprehensive_tax(
                    form16_result, tax_args
                )
                result['tax_calculation'] = tax_results
        
        return {
            'form16_data': result,
            'form16_result': form16_result,
            'processing_time': processing_time,
            'extraction_success': True
        }
    
    def extract_demo_data(
        self, 
        input_file: Path,
        output_format: str = 'json',
        calculate_tax: bool = False,
        tax_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate demo extraction data for demonstration purposes.
        
        Args:
            input_file: Original file path (for naming)
            output_format: Output format (json, csv, xlsx)
            calculate_tax: Whether to include tax calculation
            tax_args: Additional arguments for tax calculation
            
        Returns:
            Dict containing demo extraction results
        """
        start_time = time.time()
        
        # Generate demo data
        demo_data = self.dummy_generator.generate_form16_data()
        
        processing_time = time.time() - start_time
        
        # Build result structure
        result = {
            'form16_data': demo_data,
            'processing_time': processing_time,
            'extraction_success': True,
            'demo_mode': True
        }
        
        # Add tax calculation if requested
        if calculate_tax and tax_args:
            from .tax_calculation_service import TaxCalculationService
            tax_service = TaxCalculationService()
            tax_results = tax_service.get_demo_tax_results(tax_args)
            result['tax_calculation'] = tax_results
        
        return result
    
    def validate_extraction_input(self, input_file: Path) -> tuple[bool, str]:
        """
        Validate input file for extraction.
        
        Args:
            input_file: Path to input file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_file:
            return False, "File path is required"
        
        if not input_file.exists():
            return False, f"File not found: {input_file}"
        
        if not input_file.suffix.lower() == '.pdf':
            return False, f"Only PDF files are supported, got: {input_file.suffix}"
        
        return True, ""
    
    def determine_output_path(
        self, 
        input_file: Path, 
        output_file: Optional[Path], 
        output_dir: Optional[Path], 
        format: str
    ) -> Path:
        """
        Determine the output file path based on input parameters.
        
        Args:
            input_file: Input PDF file
            output_file: Explicit output file path
            output_dir: Output directory
            format: Output format (json, csv, xlsx)
            
        Returns:
            Path to output file
        """
        if output_file:
            return output_file
        
        # Auto-generate filename based on input file
        base_filename = input_file.stem + f'.{format}'
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir / base_filename
        else:
            return Path.cwd() / base_filename