"""
Consolidation Service - Business logic for consolidating multiple Form16 files.

This service handles the complex workflow of:
- Validating multiple Form16 files
- Extracting data from each file
- Financial year validation and consolidation
- Merging employee data across multiple employers
- Tax calculation for consolidated income
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from ..extractors.enhanced_form16_extractor import EnhancedForm16Extractor, ProcessingLevel
from ..pdf.reader import RobustPDFProcessor
from ..utils.json_builder import Form16JSONBuilder
from ..progress import Form16ProgressTracker
from ..dummy_generator import DummyDataGenerator


class ConsolidationService:
    """Service for handling Form16 consolidation workflow."""
    
    def __init__(self):
        """Initialize the consolidation service with required dependencies."""
        self.extractor = EnhancedForm16Extractor(ProcessingLevel.ENHANCED)
        self.pdf_processor = RobustPDFProcessor()
        self.dummy_generator = DummyDataGenerator()
    
    def consolidate_form16_files(
        self,
        form16_files: List[Path],
        output_file: Path,
        verbose: bool = False,
        calculate_tax: bool = False,
        tax_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Consolidate multiple Form16 files into a single comprehensive document.
        
        Args:
            form16_files: List of paths to Form16 PDF files
            output_file: Path for consolidated output file
            verbose: Enable verbose logging
            calculate_tax: Whether to calculate consolidated tax
            tax_args: Additional arguments for tax calculation
            
        Returns:
            Dictionary containing consolidation results and metadata
        """
        start_time = time.time()
        
        # Validate inputs
        validation_result = self._validate_consolidation_inputs(form16_files)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'processing_time': time.time() - start_time
            }
        
        # Initialize progress tracker
        progress_tracker = Form16ProgressTracker(enable_animation=not verbose)
        
        # Extract data from all Form16 files
        with progress_tracker.status_spinner(f"Consolidating {len(form16_files)} Form16 files..."):
            extraction_results = self._extract_all_form16_data(
                form16_files, verbose, progress_tracker
            )
        
        if not extraction_results['success']:
            return extraction_results
        
        extracted_forms = extraction_results['extracted_forms']
        financial_years = extraction_results['financial_years']
        
        # Validate financial year consistency
        fy_validation = self._validate_financial_years(financial_years)
        if not fy_validation['valid']:
            return {
                'success': False,
                'error': fy_validation['error'],
                'processing_time': time.time() - start_time
            }
        
        common_fy = fy_validation['common_fy']
        
        # Build consolidated Form16
        consolidated_result = self._build_consolidated_form16(extracted_forms, common_fy)
        
        # Calculate consolidated tax if requested
        tax_results = None
        if calculate_tax and tax_args:
            from .tax_calculation_service import TaxCalculationService
            tax_service = TaxCalculationService()
            tax_results = tax_service.calculate_comprehensive_tax(
                consolidated_result, tax_args
            )
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'consolidated_data': consolidated_result,
            'tax_calculation': tax_results,
            'financial_year': common_fy,
            'employers_count': len(extracted_forms),
            'processing_time': processing_time,
            'output_file': str(output_file)
        }
    
    def consolidate_demo_data(
        self,
        form16_files: List[Path],
        output_file: Path,
        calculate_tax: bool = False,
        tax_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate demo consolidation data for demonstration purposes.
        
        Args:
            form16_files: Original file paths (for naming)
            output_file: Path for consolidated output file
            calculate_tax: Whether to include tax calculation
            tax_args: Additional arguments for tax calculation
            
        Returns:
            Dictionary containing demo consolidation results
        """
        start_time = time.time()
        
        # Import UI components for progress display (user requested 5+ second progress bar)
        from ..display.rich_ui_components import RichUIComponents
        ui = RichUIComponents()
        
        # Show progress for demo processing (minimum 5 seconds as requested)
        ui.show_loading_animation("Processing and consolidating Form16 documents", 2.0)
        ui.show_loading_animation("Extracting income and tax data from multiple employers", 2.0)
        ui.show_loading_animation("Validating and consolidating tax information", 1.5)
        
        # Generate demo consolidated data  
        demo_data = self.dummy_generator.generate_consolidated_results(len(form16_files))
        
        # Calculate demo tax if requested
        tax_results = None
        if calculate_tax and tax_args:
            from .tax_calculation_service import TaxCalculationService
            tax_service = TaxCalculationService()
            # Use consolidated data for proper tax calculation instead of generic demo data
            tax_results = tax_service.calculate_tax_with_consolidated_demo_data(demo_data, tax_args)
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'consolidated_data': demo_data,
            'tax_calculation': tax_results,
            'financial_year': '2023-24',
            'employers_count': len(form16_files),
            'processing_time': processing_time,
            'output_file': str(output_file),
            'demo_mode': True
        }
    
    def _validate_consolidation_inputs(self, form16_files: List[Path]) -> Dict[str, Any]:
        """
        Validate consolidation input parameters.
        
        Args:
            form16_files: List of Form16 file paths
            
        Returns:
            Dictionary containing validation results
        """
        if len(form16_files) < 2:
            return {
                'valid': False,
                'error': 'At least 2 Form16 files required for consolidation'
            }
        
        # Validate all files exist and are PDFs
        for file_path in form16_files:
            if not file_path.exists():
                return {
                    'valid': False,
                    'error': f'File not found: {file_path}'
                }
            
            if not file_path.suffix.lower() == '.pdf':
                return {
                    'valid': False,
                    'error': f'Only PDF files supported: {file_path}'
                }
        
        return {'valid': True}
    
    def _extract_all_form16_data(
        self,
        form16_files: List[Path],
        verbose: bool,
        progress_tracker: Form16ProgressTracker
    ) -> Dict[str, Any]:
        """
        Extract data from all Form16 files.
        
        Args:
            form16_files: List of Form16 file paths
            verbose: Enable verbose logging
            progress_tracker: Progress tracking instance
            
        Returns:
            Dictionary containing extraction results for all files
        """
        extracted_forms = []
        financial_years = set()
        
        if verbose:
            print(f"\nExtracting data from {len(form16_files)} Form16 files...")
        
        for i, form16_file in enumerate(form16_files, 1):
            with progress_tracker.status_spinner(f"Processing {form16_file.name} ({i}/{len(form16_files)})"):
                if verbose:
                    print(f"[{i}/{len(form16_files)}] Processing: {form16_file.name}")
                
                try:
                    # Extract tables and Form16 data
                    extraction_result = self.pdf_processor.extract_tables(form16_file)
                    text_data = getattr(extraction_result, 'text_data', None)
                    form16_result = self.extractor.extract_all(extraction_result.tables, text_data=text_data)
                    
                    # Build comprehensive JSON
                    form16_json = Form16JSONBuilder.build_comprehensive_json(
                        form16_doc=form16_result,
                        pdf_file_name=form16_file.name,
                        processing_time=0.0,  # Individual processing time not tracked in consolidation
                        extraction_metadata=getattr(form16_result, 'extraction_metadata', {})
                    )
                    
                    # Extract and validate financial year
                    fy_info = self._extract_financial_year_info(form16_result, form16_file)
                    financial_years.add(fy_info['financial_year'])
                    
                    extracted_forms.append({
                        'file_name': form16_file.name,
                        'file_path': str(form16_file),
                        'form16_result': form16_result,
                        'form16_json': form16_json,
                        'financial_year': fy_info['financial_year'],
                        'assessment_year': fy_info['assessment_year']
                    })
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to process {form16_file.name}: {str(e)}'
                    }
        
        return {
            'success': True,
            'extracted_forms': extracted_forms,
            'financial_years': financial_years
        }
    
    def _validate_financial_years(self, financial_years: set) -> Dict[str, Any]:
        """
        Validate that all Form16s are from the same financial year.
        
        Args:
            financial_years: Set of financial years from all Form16s
            
        Returns:
            Dictionary containing validation results
        """
        if len(financial_years) > 1:
            return {
                'valid': False,
                'error': f'All Form16s must be from the same financial year. Found: {sorted(financial_years)}'
            }
        
        if not financial_years:
            # Use default if no FY found
            common_fy = "2023-24"
        else:
            common_fy = list(financial_years)[0]
        
        return {
            'valid': True,
            'common_fy': common_fy
        }
    
    def _extract_financial_year_info(self, form16_result: Any, file_path: Path) -> Dict[str, str]:
        """
        Extract financial year information from Form16 result.
        
        Args:
            form16_result: Extracted Form16 document data
            file_path: Path to the original PDF file
            
        Returns:
            Dictionary containing financial year and assessment year
        """
        # Try to extract from Form16 data
        financial_year = "2023-24"  # Default fallback
        
        if hasattr(form16_result, 'financial_year') and form16_result.financial_year:
            financial_year = str(form16_result.financial_year)
        elif hasattr(form16_result, 'deductor') and hasattr(form16_result.deductor, 'financial_year'):
            financial_year = str(form16_result.deductor.financial_year)
        
        # Calculate assessment year from financial year
        try:
            if '-' in financial_year:
                start_year = int(financial_year.split('-')[0])
                assessment_year = f"{start_year + 1}-{str(start_year + 2)[-2:]}"
            else:
                assessment_year = "2024-25"  # Default fallback
        except (ValueError, IndexError):
            assessment_year = "2024-25"  # Default fallback
        
        return {
            'financial_year': financial_year,
            'assessment_year': assessment_year
        }
    
    def _build_consolidated_form16(
        self,
        extracted_forms: List[Dict[str, Any]],
        common_fy: str
    ) -> Dict[str, Any]:
        """
        Build consolidated Form16 from multiple extracted forms.
        
        Args:
            extracted_forms: List of extracted Form16 data
            common_fy: Common financial year for all forms
            
        Returns:
            Consolidated Form16 data structure
        """
        if not extracted_forms:
            return {}
        
        # Start with the first form as base
        base_form = extracted_forms[0]['form16_result']
        
        # Initialize consolidated data structure
        consolidated_data = {
            'employee': {
                'name': getattr(base_form.employee, 'name', 'N/A') if hasattr(base_form, 'employee') else 'N/A',
                'pan': getattr(base_form.employee, 'pan', 'N/A') if hasattr(base_form, 'employee') else 'N/A',
                'address': getattr(base_form.employee, 'address', 'N/A') if hasattr(base_form, 'employee') else 'N/A'
            },
            'financial_year': common_fy,
            'employers': [],
            'consolidated_salary': {
                'gross_salary': Decimal('0'),
                'basic_salary': Decimal('0'),
                'hra': Decimal('0'),
                'other_allowances': Decimal('0'),
                'perquisites_value': Decimal('0')
            },
            'consolidated_deductions': {
                'section_80c_total': Decimal('0'),
                'section_80ccd_1b': Decimal('0'),
                'section_80d': Decimal('0'),
                'section_80tta': Decimal('0')
            },
            'consolidated_tds': Decimal('0'),
            'source_files': []
        }
        
        # Consolidate data from all forms
        for form_data in extracted_forms:
            form16_result = form_data['form16_result']
            
            # Add employer information
            if hasattr(form16_result, 'employer'):
                employer_info = {
                    'name': getattr(form16_result.employer, 'name', 'N/A'),
                    'tan': getattr(form16_result.employer, 'tan', 'N/A'),
                    'address': getattr(form16_result.employer, 'address', 'N/A'),
                    'file_name': form_data['file_name']
                }
                consolidated_data['employers'].append(employer_info)
            
            # Consolidate salary data
            if hasattr(form16_result, 'salary'):
                salary = form16_result.salary
                consolidated_data['consolidated_salary']['gross_salary'] += Decimal(str(salary.gross_salary or 0))
                consolidated_data['consolidated_salary']['basic_salary'] += Decimal(str(salary.basic_salary or 0))
                consolidated_data['consolidated_salary']['hra'] += Decimal(str(getattr(salary, 'hra', 0) or 0))
                consolidated_data['consolidated_salary']['other_allowances'] += Decimal(str(getattr(salary, 'other_allowances', 0) or 0))
                consolidated_data['consolidated_salary']['perquisites_value'] += Decimal(str(getattr(salary, 'perquisites_value', 0) or 0))
            
            # Consolidate deductions (take maximum for each section to avoid double counting)
            if hasattr(form16_result, 'chapter_via_deductions'):
                deductions = form16_result.chapter_via_deductions
                consolidated_data['consolidated_deductions']['section_80c_total'] = max(
                    consolidated_data['consolidated_deductions']['section_80c_total'],
                    Decimal(str(deductions.section_80c_total or 0))
                )
                consolidated_data['consolidated_deductions']['section_80ccd_1b'] = max(
                    consolidated_data['consolidated_deductions']['section_80ccd_1b'],
                    Decimal(str(deductions.section_80ccd_1b or 0))
                )
            
            # Consolidate TDS
            if hasattr(form16_result, 'quarterly_tds') and form16_result.quarterly_tds:
                for quarter_data in form16_result.quarterly_tds:
                    if hasattr(quarter_data, 'tax_deducted') and quarter_data.tax_deducted:
                        consolidated_data['consolidated_tds'] += Decimal(str(quarter_data.tax_deducted))
            
            # Track source files
            consolidated_data['source_files'].append({
                'file_name': form_data['file_name'],
                'file_path': form_data['file_path']
            })
        
        # Convert Decimal values to float for JSON serialization
        for key, value in consolidated_data['consolidated_salary'].items():
            consolidated_data['consolidated_salary'][key] = float(value)
        
        for key, value in consolidated_data['consolidated_deductions'].items():
            consolidated_data['consolidated_deductions'][key] = float(value)
        
        consolidated_data['consolidated_tds'] = float(consolidated_data['consolidated_tds'])
        
        return consolidated_data