"""
Form 16 Extractor Service - ROBUST for ANY Form 16
==================================================

Main application service that orchestrates the complete extraction process.
Designed to work with ANY Form 16 document and extract ALL possible fields.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..domain.models import Form16Document, ExtractionResult, EmployeeInfo, EmployerInfo, SalaryBreakdown
from ..infrastructure.pdf_processor import create_pdf_processor, TableExtractionResult
from .extractors.identity_extractor import IdentityExtractor
from .extractors.salary_extractor import SalaryExtractor
from .extractors.tax_extractor import TaxExtractor
from .extractors.metadata_extractor import MetadataExtractor


@dataclass
class ExtractionConfig:
    """Configuration for extraction process"""
    # Confidence thresholds
    min_confidence_threshold: float = 0.3
    high_confidence_threshold: float = 0.8
    
    # Processing options
    enable_aggressive_extraction: bool = True
    enable_cross_validation: bool = True
    max_processing_time: float = 60.0  # seconds
    
    # Output options
    include_raw_tables: bool = True
    include_processing_metadata: bool = True
    
    # Field selection (empty list = extract all)
    target_fields: List[str] = None


class Form16ExtractorService:
    """
    Main service for extracting data from Form 16 documents.
    
    This service is designed to be ROBUST and work with ANY Form 16 document:
    - Handles multiple PDF layouts and formats
    - Uses multiple extraction strategies
    - Provides comprehensive field extraction
    - Includes validation and error handling
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or ExtractionConfig()
        
        # Initialize components
        self.pdf_processor = create_pdf_processor()
        self.identity_extractor = IdentityExtractor()
        self.salary_extractor = SalaryExtractor()
        self.tax_extractor = TaxExtractor()
        self.metadata_extractor = MetadataExtractor()
        
        self.logger.info("✅ Form16ExtractorService initialized")
    
    def extract_from_file(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract all data from a Form 16 PDF file.
        
        This is the main entry point for the CLI tool.
        """
        start_time = time.time()
        warnings = []
        
        try:
            self.logger.info(f"🚀 Starting Form 16 extraction: {pdf_path.name}")
            
            # Step 1: Extract tables from PDF
            table_result = self._extract_tables_from_pdf(pdf_path)
            if not table_result.tables:
                return ExtractionResult(
                    success=False,
                    error_message="No tables could be extracted from the PDF",
                    processing_time=time.time() - start_time,
                    warnings=table_result.warnings
                )
            
            warnings.extend(table_result.warnings)
            
            # Step 2: Create Form16 document and extract all fields
            form16_doc = self._extract_all_fields(table_result, pdf_path)
            
            # Step 3: Post-process and validate
            self._post_process_extraction(form16_doc)
            
            # Step 4: Calculate quality metrics
            extraction_summary = form16_doc.get_extraction_summary()
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"✅ Extraction completed in {processing_time:.2f}s")
            self.logger.info(f"📊 Extracted {extraction_summary['extracted_fields']}/{extraction_summary['total_possible_fields']} fields "
                           f"({extraction_summary['extraction_rate']:.1f}%)")
            
            return ExtractionResult(
                success=True,
                form16_document=form16_doc,
                processing_time=processing_time,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ExtractionResult(
                success=False,
                error_message=error_msg,
                processing_time=time.time() - start_time,
                warnings=warnings
            )
    
    def _extract_tables_from_pdf(self, pdf_path: Path) -> TableExtractionResult:
        """Extract tables from PDF using robust processing"""
        self.logger.info("📄 Extracting tables from PDF...")
        
        try:
            table_result = self.pdf_processor.extract_tables(pdf_path)
            
            if table_result.tables:
                self.logger.info(f"✅ Extracted {len(table_result.tables)} tables using {table_result.strategy_used.value}")
                self.logger.debug(f"Confidence: {table_result.confidence_score:.2f}")
                
                # Log table shapes for debugging
                for i, table in enumerate(table_result.tables):
                    self.logger.debug(f"Table {i}: {table.shape} ({table.shape[0]} rows, {table.shape[1]} cols)")
            
            return table_result
            
        except Exception as e:
            self.logger.error(f"❌ PDF table extraction failed: {str(e)}")
            raise
    
    def _extract_all_fields(self, table_result: TableExtractionResult, pdf_path: Path) -> Form16Document:
        """Extract all fields from the extracted tables"""
        self.logger.info("🔍 Extracting all fields from tables...")
        
        # Initialize Form16 document
        form16_doc = Form16Document()
        
        # Store raw tables if requested
        if self.config.include_raw_tables:
            form16_doc.raw_tables = [table.to_dict() for table in table_result.tables]
        
        # Store processing metadata
        if self.config.include_processing_metadata:
            form16_doc.processing_metadata = {
                'pdf_file': str(pdf_path),
                'extraction_strategy': table_result.strategy_used.value,
                'extraction_confidence': table_result.confidence_score,
                'table_count': len(table_result.tables),
                'page_numbers': table_result.page_numbers
            }
        
        # Extract using specialized extractors
        try:
            # Identity information (employee, employer)
            identity_result = self.identity_extractor.extract(table_result.tables)
            self._merge_identity_data(form16_doc, identity_result)
            
            # Salary breakdown
            salary_result = self.salary_extractor.extract(table_result.tables)
            self._merge_salary_data(form16_doc, salary_result)
            
            # Tax and deduction data
            tax_result = self.tax_extractor.extract(table_result.tables)
            self._merge_tax_data(form16_doc, tax_result)
            
            # Metadata (dates, certificate info)
            metadata_result = self.metadata_extractor.extract(table_result.tables)
            self._merge_metadata(form16_doc, metadata_result)
            
        except Exception as e:
            self.logger.error(f"❌ Field extraction error: {str(e)}")
            form16_doc.extraction_errors.append(f"Field extraction error: {str(e)}")
        
        return form16_doc
    
    def _merge_identity_data(self, form16_doc: Form16Document, identity_result: Dict[str, Any]):
        """Merge identity extraction results into Form16 document"""
        try:
            # Employee information
            if 'employee' in identity_result:
                employee_data = identity_result['employee']
                for field, value in employee_data.items():
                    if value and hasattr(form16_doc.employee, field):
                        setattr(form16_doc.employee, field, value)
                        if 'confidence' in identity_result:
                            form16_doc.extraction_confidence[f'employee_{field}'] = identity_result['confidence'].get(field, 0.5)
            
            # Employer information
            if 'employer' in identity_result:
                employer_data = identity_result['employer']
                for field, value in employer_data.items():
                    if value and hasattr(form16_doc.employer, field):
                        setattr(form16_doc.employer, field, value)
                        if 'confidence' in identity_result:
                            form16_doc.extraction_confidence[f'employer_{field}'] = identity_result['confidence'].get(field, 0.5)
            
        except Exception as e:
            self.logger.warning(f"Error merging identity data: {str(e)}")
            form16_doc.extraction_errors.append(f"Identity merge error: {str(e)}")
    
    def _merge_salary_data(self, form16_doc: Form16Document, salary_result: Dict[str, Any]):
        """Merge salary extraction results into Form16 document"""
        try:
            if 'salary_breakdown' in salary_result:
                salary_data = salary_result['salary_breakdown']
                
                for field, value in salary_data.items():
                    if value is not None and hasattr(form16_doc.salary, field):
                        setattr(form16_doc.salary, field, value)
                        if 'confidence' in salary_result:
                            form16_doc.extraction_confidence[f'salary_{field}'] = salary_result['confidence'].get(field, 0.5)
                
                # Calculate derived totals
                form16_doc.salary.calculate_totals()
            
        except Exception as e:
            self.logger.warning(f"Error merging salary data: {str(e)}")
            form16_doc.extraction_errors.append(f"Salary merge error: {str(e)}")
    
    def _merge_tax_data(self, form16_doc: Form16Document, tax_result: Dict[str, Any]):
        """Merge tax and deduction results into Form16 document"""
        try:
            # Quarterly TDS
            if 'quarterly_tds' in tax_result:
                form16_doc.quarterly_tds = tax_result['quarterly_tds']
            
            # Chapter VI-A deductions
            if 'chapter_via_deductions' in tax_result:
                deduction_data = tax_result['chapter_via_deductions']
                for field, value in deduction_data.items():
                    if value is not None and hasattr(form16_doc.chapter_via_deductions, field):
                        setattr(form16_doc.chapter_via_deductions, field, value)
            
            # Tax computation
            if 'tax_computation' in tax_result:
                tax_comp_data = tax_result['tax_computation']
                for field, value in tax_comp_data.items():
                    if value is not None and hasattr(form16_doc.tax_computation, field):
                        setattr(form16_doc.tax_computation, field, value)
            
        except Exception as e:
            self.logger.warning(f"Error merging tax data: {str(e)}")
            form16_doc.extraction_errors.append(f"Tax merge error: {str(e)}")
    
    def _merge_metadata(self, form16_doc: Form16Document, metadata_result: Dict[str, Any]):
        """Merge metadata into Form16 document"""
        try:
            if 'metadata' in metadata_result:
                metadata = metadata_result['metadata']
                for field, value in metadata.items():
                    if value is not None and hasattr(form16_doc.metadata, field):
                        setattr(form16_doc.metadata, field, value)
            
        except Exception as e:
            self.logger.warning(f"Error merging metadata: {str(e)}")
            form16_doc.extraction_errors.append(f"Metadata merge error: {str(e)}")
    
    def _post_process_extraction(self, form16_doc: Form16Document):
        """Post-process and validate extraction results"""
        try:
            # Validate critical fields
            self._validate_critical_fields(form16_doc)
            
            # Cross-validate fields
            if self.config.enable_cross_validation:
                self._cross_validate_fields(form16_doc)
            
            # Identify missing fields
            self._identify_missing_fields(form16_doc)
            
        except Exception as e:
            self.logger.warning(f"Post-processing error: {str(e)}")
            form16_doc.extraction_errors.append(f"Post-processing error: {str(e)}")
    
    def _validate_critical_fields(self, form16_doc: Form16Document):
        """Validate critical fields like PAN, TAN format"""
        # Employee PAN validation
        if form16_doc.employee.pan:
            try:
                from ..domain.models import PAN
                PAN(value=form16_doc.employee.pan)  # Will validate format
            except ValueError as e:
                form16_doc.extraction_errors.append(f"Invalid employee PAN: {form16_doc.employee.pan}")
                form16_doc.employee.pan = None
        
        # Employer TAN validation
        if form16_doc.employer.tan:
            try:
                from ..domain.models import TAN
                TAN(value=form16_doc.employer.tan)  # Will validate format
            except ValueError as e:
                form16_doc.extraction_errors.append(f"Invalid employer TAN: {form16_doc.employer.tan}")
                form16_doc.employer.tan = None
    
    def _cross_validate_fields(self, form16_doc: Form16Document):
        """Cross-validate fields for consistency"""
        # Example: Gross salary should match sum of components
        salary = form16_doc.salary
        
        if salary.gross_salary and salary.total_allowances:
            expected_gross = (salary.total_allowances or 0) + (salary.perquisites_value or 0)
            if abs(float(salary.gross_salary) - float(expected_gross)) > 1000:  # Allow small differences
                form16_doc.extraction_errors.append(
                    f"Gross salary mismatch: {salary.gross_salary} vs calculated {expected_gross}"
                )
    
    def _identify_missing_fields(self, form16_doc: Form16Document):
        """Identify critical missing fields"""
        missing_critical = []
        
        # Critical employee fields
        if not form16_doc.employee.name:
            missing_critical.append("employee_name")
        if not form16_doc.employee.pan:
            missing_critical.append("employee_pan")
        
        # Critical salary fields
        if not form16_doc.salary.gross_salary and not form16_doc.salary.basic_salary:
            missing_critical.append("basic_salary_or_gross_salary")
        
        # Critical tax fields
        if not form16_doc.quarterly_tds and not form16_doc.tax_computation.total_tds:
            missing_critical.append("tax_deduction_data")
        
        form16_doc.missing_fields = missing_critical
    
    def batch_extract(self, pdf_files: List[Path]) -> List[ExtractionResult]:
        """Extract data from multiple Form 16 files"""
        self.logger.info(f"🔄 Starting batch extraction of {len(pdf_files)} files")
        
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            self.logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            result = self.extract_from_file(pdf_file)
            results.append(result)
            
            if result.success:
                self.logger.info(f"  ✅ Success")
            else:
                self.logger.warning(f"  ❌ Failed: {result.error_message}")
        
        successful = sum(1 for r in results if r.success)
        self.logger.info(f"📊 Batch complete: {successful}/{len(pdf_files)} successful")
        
        return results


# Factory function for easy CLI integration
def create_form16_extractor(config: Optional[ExtractionConfig] = None) -> Form16ExtractorService:
    """Create a Form16ExtractorService instance"""
    return Form16ExtractorService(config)