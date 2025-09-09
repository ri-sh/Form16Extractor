#!/usr/bin/env python3
"""
Form 16 Extractor CLI Tool
=========================

Command-line interface for extracting data from Form 16 PDF documents.
Supports single file processing and batch processing.

Usage:
    python cli.py extract --file form16.pdf --output result.json
    python cli.py batch --input-dir ./form16s/ --output-dir ./results/
    python cli.py validate --file result.json
"""

import warnings
import logging
import sys
import io
from contextlib import redirect_stderr

# Suppress all cryptography deprecation warnings early
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pypdf")
warnings.filterwarnings("ignore", message="ARC4 has been moved to cryptography.hazmat.decrepit")

# Suppress jpype warning by temporarily redirecting stderr during tabula import
original_stderr = sys.stderr
sys.stderr = io.StringIO()
try:
    # This will trigger the jpype import warning, which we suppress
    import tabula
except:
    pass
finally:
    sys.stderr = original_stderr

# Suppress debug logging from extraction modules unless verbose mode is enabled
logging.getLogger('form16_extractor').setLevel(logging.WARNING)

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from datetime import datetime

# Import our extraction modules  
from form16_extractor.extractors.enhanced_form16_extractor import EnhancedForm16Extractor, ProcessingLevel
from form16_extractor.pdf.reader import RobustPDFProcessor
from form16_extractor.utils.json_builder import Form16JSONBuilder
from form16_extractor.models.form16_models import Form16Document
from decimal import Decimal
# from src.domain.models import ExtractionResult


class Form16CLI:
    """Command-line interface for Form 16 extraction"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.extractor = EnhancedForm16Extractor(ProcessingLevel.ENHANCED)  # Enhanced level with zero value recognition
        self.pdf_processor = RobustPDFProcessor()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the command-line argument parser"""
        parser = argparse.ArgumentParser(
            description="Extract data from Form 16 PDF documents",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  Extract single Form 16:
    python cli.py extract --file form16.pdf --output result.json

  Batch process multiple Form 16s:
    python cli.py batch --input-dir ./pdfs/ --output-dir ./results/

  Extract with verbose logging:
    python cli.py extract --file form16.pdf --output result.json --verbose

  Extract specific fields only:
    python cli.py extract --file form16.pdf --fields employee_info,salary_breakdown

  Validate extraction results:
    python cli.py validate --file result.json
            """
        )
        
        parser.add_argument(
            "--version", action="version", version=f"Form16 Extractor {self.version}"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Extract command
        extract_parser = subparsers.add_parser(
            "extract", help="Extract data from a single Form 16 PDF"
        )
        extract_parser.add_argument(
            "--file", "-f", required=True, type=Path,
            help="Path to Form 16 PDF file"
        )
        extract_parser.add_argument(
            "--output", "-o", type=Path,
            help="Output JSON file path (default: auto-generated in current directory)"
        )
        extract_parser.add_argument(
            "--out-dir", type=Path,
            help="Output directory path (default: current directory)"
        )
        extract_parser.add_argument(
            "--fields", type=str,
            help="Comma-separated list of fields to extract (default: all)"
        )
        extract_parser.add_argument(
            "--format", choices=["json", "csv", "xlsx"], default="json",
            help="Output format (default: json)"
        )
        extract_parser.add_argument(
            "--pretty", action="store_true",
            help="Pretty-print JSON output"
        )
        extract_parser.add_argument(
            "--calculate-tax", action="store_true",
            help="Calculate comprehensive tax liability with regime comparison"
        )
        extract_parser.add_argument(
            "--tax-regime", choices=["old", "new", "both"], default="both",
            help="Tax regime for calculation (default: both - shows comparison)"
        )
        extract_parser.add_argument(
            "--city-type", choices=["metro", "non_metro"], default="metro",
            help="City type for HRA calculation (default: metro)"
        )
        extract_parser.add_argument(
            "--age-category", choices=["below_60", "senior_60_to_80", "super_senior_above_80"], default="below_60",
            help="Age category for tax calculation (default: below_60)"
        )
        extract_parser.add_argument(
            "--summary", action="store_true",
            help="Show detailed tax calculation breakdown (when using --calculate-tax)"
        )
        extract_parser.add_argument(
            "--display-mode", choices=["table", "colored"], default="table",
            help="Display mode for tax regime comparison (default: table, colored: regime components with background colors)"
        )
        
        # Batch command
        batch_parser = subparsers.add_parser(
            "batch", help="Batch process multiple Form 16 PDFs"
        )
        batch_parser.add_argument(
            "--input-dir", "-i", required=True, type=Path,
            help="Directory containing Form 16 PDF files"
        )
        batch_parser.add_argument(
            "--output-dir", "-o", required=True, type=Path,
            help="Directory to save extraction results"
        )
        batch_parser.add_argument(
            "--pattern", default="*.pdf",
            help="File pattern to match (default: *.pdf)"
        )
        batch_parser.add_argument(
            "--parallel", type=int, default=4,
            help="Number of parallel processes (default: 4)"
        )
        batch_parser.add_argument(
            "--continue-on-error", action="store_true",
            help="Continue processing even if some files fail"
        )
        
        # Consolidate command
        consolidate_parser = subparsers.add_parser(
            "consolidate", help="Consolidate multiple Form 16 PDFs from different employers"
        )
        consolidate_parser.add_argument(
            "--files", "-f", required=True, nargs='+', type=Path,
            help="List of Form 16 PDF files to consolidate"
        )
        consolidate_parser.add_argument(
            "--output", "-o", type=Path,
            help="Output JSON file path (default: consolidated_form16.json)"
        )
        consolidate_parser.add_argument(
            "--calculate-tax", action="store_true",
            help="Calculate comprehensive tax liability for consolidated income"
        )
        consolidate_parser.add_argument(
            "--tax-regime", choices=["old", "new", "both"], default="both",
            help="Tax regime for calculation (default: both)"
        )
        
        # Validate command
        validate_parser = subparsers.add_parser(
            "validate", help="Validate extraction results"
        )
        validate_parser.add_argument(
            "--file", "-f", required=True, type=Path,
            help="Path to extraction result JSON file"
        )
        validate_parser.add_argument(
            "--strict", action="store_true",
            help="Strict validation mode"
        )
        
        # Test command
        test_parser = subparsers.add_parser(
            "test", help="Test extractor with sample files"
        )
        test_parser.add_argument(
            "--sample-dir", type=Path,
            help="Directory with sample Form 16 files"
        )
        test_parser.add_argument(
            "--benchmark", action="store_true",
            help="Run performance benchmarks"
        )
        
        # Common arguments
        for subparser in [extract_parser, batch_parser, consolidate_parser, validate_parser, test_parser]:
            subparser.add_argument(
                "--verbose", "-v", action="store_true",
                help="Enable verbose logging"
            )
            subparser.add_argument(
                "--config", type=Path,
                help="Path to configuration file"
            )
            subparser.add_argument(
                "--log-file", type=Path,
                help="Path to log file"
            )
        
        return parser
    
    def extract_single_file(self, args) -> int:
        """Extract data from a single Form 16 file"""
        try:
            input_file = args.file
            if not input_file.exists():
                print(f"Error: File not found: {input_file}")
                return 1
            
            if not input_file.suffix.lower() == '.pdf':
                print(f"Error: Only PDF files are supported, got: {input_file.suffix}")
                return 1
            
            print(f"Processing: {input_file}")
            
            # Determine output file and directory
            if args.output:
                # If specific output file provided, use it as-is
                output_file = args.output
            else:
                # Auto-generate filename based on input file
                base_filename = input_file.stem + f'.{args.format}'
                
                # Determine output directory
                if args.out_dir:
                    # Use specified output directory
                    output_dir = args.out_dir
                    output_dir.mkdir(parents=True, exist_ok=True)  # Create directory if needed
                    output_file = output_dir / base_filename
                else:
                    # Use current directory (default behavior)
                    output_file = Path.cwd() / base_filename
            
            start_time = time.time()
            
            # Extract tables from PDF
            if args.verbose:
                print(f"Processing PDF: {input_file}")
            
            extraction_result = self.pdf_processor.extract_tables(input_file)
            tables = extraction_result.tables
            
            if args.verbose:
                print(f"Extracted {len(tables)} tables from PDF")
            
            # Extract Form16 data
            form16_result = self.extractor.extract_all(tables)
            processing_time = time.time() - start_time
            
            # Use proper Form16 JSON builder for correct Part A/Part B structure
            result = Form16JSONBuilder.build_comprehensive_json(
                form16_doc=form16_result,
                pdf_file_name=input_file.name,
                processing_time=processing_time,
                extraction_metadata=getattr(form16_result, 'extraction_metadata', {})
            )
            
            # Comprehensive tax calculation if requested
            if args.calculate_tax:
                if args.verbose:
                    print(f"Calculating comprehensive tax liability...")
                
                # Use the correct Form16-based tax computation
                tax_results = self._calculate_form16_based_tax(form16_result, args)
                if tax_results:
                    result['tax_calculations'] = tax_results
                    
                    # Always display tax results on terminal when --calculate-tax is used
                    if hasattr(args, 'display_mode') and args.display_mode == 'colored':
                        self._display_colored_regime_components(tax_results, args.tax_regime)
                    elif hasattr(args, 'summary') and args.summary:
                        self._display_detailed_tax_breakdown(tax_results, args.tax_regime)
                    else:
                        self._display_tax_summary(tax_results, args.tax_regime)
                else:
                    print(f"Warning: Tax calculation failed - continuing with extraction only")
            
            # Save result with proper formatting (only if output specified)
            if args.output or args.out_dir:
                if args.format == "json":
                    with open(output_file, 'w') as f:
                        # Always use pretty formatting to match specification
                        json.dump(result, f, indent=2, default=str)
                
                print(f"\nExtraction completed successfully!")
                print(f"Input: {input_file}")
                print(f"Output: {output_file}")
            else:
                print(f"\nExtraction completed successfully!")
                print(f"Input: {input_file}")
                if not args.calculate_tax:
                    print(f" Tip: Use --output to save results to file, or --calculate-tax for tax computation")
            
            print(f"Processing time: {result['metadata']['processing_time_seconds']:.2f} seconds")
            
            if 'extraction_metrics' in result and 'extraction_summary' in result['extraction_metrics']:
                summary = result['extraction_metrics']['extraction_summary']
                print(f"Extracted {summary['extracted_fields']}/{summary['total_fields']} fields ({summary['extraction_rate']:.1f}%)")
            
            return 0
            
        except Exception as e:
            print(f"Error processing file: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def batch_process(self, args) -> int:
        """Batch process multiple Form 16 files"""
        try:
            input_dir = args.input_dir
            output_dir = args.output_dir
            
            if not input_dir.exists():
                print(f"Error: Input directory not found: {input_dir}")
                return 1
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all PDF files
            pdf_files = list(input_dir.glob(args.pattern))
            if not pdf_files:
                print(f"No PDF files found in {input_dir} matching pattern {args.pattern}")
                return 1
            
            print(f"Found {len(pdf_files)} PDF files to process")
            print(f"Output directory: {output_dir}")
            
            successful = 0
            failed = 0
            start_time = time.time()
            
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
                
                try:
                    # Create mock args for single file processing
                    class MockArgs:
                        file = pdf_file
                        output = output_dir / f"{pdf_file.stem}.json"
                        format = "json"
                        pretty = True
                        verbose = args.verbose
                    
                    result = self.extract_single_file(MockArgs())
                    if result == 0:
                        successful += 1
                        print(f"  Success")
                    else:
                        failed += 1
                        print(f"  Failed")
                        if not args.continue_on_error:
                            break
                            
                except Exception as e:
                    failed += 1
                    print(f"  Error: {e}")
                    if not args.continue_on_error:
                        break
            
            total_time = time.time() - start_time
            
            print(f"\nBatch Processing Summary:")
            print(f"   Total files: {len(pdf_files)}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            print(f"   Total time: {total_time:.2f} seconds")
            print(f"   Average time per file: {total_time/len(pdf_files):.2f} seconds")
            
            return 0 if failed == 0 else 1
            
        except Exception as e:
            print(f"Batch processing error: {e}")
            return 1
    
    def validate_results(self, args) -> int:
        """Validate extraction results"""
        try:
            result_file = args.file
            if not result_file.exists():
                print(f"Error: Result file not found: {result_file}")
                return 1
            
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            print(f"Validating: {result_file}")
            
            # Basic validation
            if 'status' not in data:
                print("Missing 'status' field")
                return 1
            
            if data['status'] != 'success':
                print(f"Extraction was not successful: {data.get('error', 'Unknown error')}")
                return 1
            
            # Validate form16_data structure
            if 'form16_data' not in data:
                print("Missing 'form16_data' field")
                return 1
            
            form16_data = data['form16_data']
            required_sections = ['employee_info', 'employer_info', 'salary_breakdown']
            
            for section in required_sections:
                if section not in form16_data:
                    print(f"Missing required section: {section}")
                    if args.strict:
                        return 1
                else:
                    print(f"Found section: {section}")
            
            # Check extraction summary
            if 'extraction_summary' in data:
                summary = data['extraction_summary']
                rate = summary.get('extraction_rate', 0)
                print(f"Extraction rate: {rate:.1f}%")
                
                if rate < 50 and args.strict:
                    print("Extraction rate too low for strict mode")
                    return 1
            
            print("Validation passed!")
            return 0
            
        except Exception as e:
            print(f"Validation error: {e}")
            return 1
    
    def run_tests(self, args) -> int:
        """Run tests with sample files"""
        print("Running Form 16 extractor tests...")
        
        if args.sample_dir:
            sample_dir = args.sample_dir
        else:
            # Use default test samples directory
            sample_dir = Path("~/Downloads/form16/").expanduser()
        
        if not sample_dir.exists():
            print(f"Sample directory not found: {sample_dir}")
            return 1
        
        # Find sample files
        sample_files = list(sample_dir.glob("*.pdf"))
        if not sample_files:
            print(f"No PDF files found in {sample_dir}")
            return 1
        
        print(f"Found {len(sample_files)} test files")
        
        # Run basic extraction test on each file
        for pdf_file in sample_files[:3]:  # Test first 3 files
            print(f"\nTesting: {pdf_file.name}")
            
            class MockArgs:
                file = pdf_file
                output = None
                format = "json"
                pretty = False
                verbose = args.verbose
            
            result = self.extract_single_file(MockArgs())
            if result == 0:
                print("  Test passed")
            else:
                print("  Test failed")
        
        print("\nTest suite completed!")
        return 0
    
    def _calculate_comprehensive_tax(self, form16_result, args):
        """Calculate comprehensive tax using extracted Form16 data."""
        try:
            from form16_extractor.tax_calculators.comprehensive_calculator import (
                ComprehensiveTaxCalculator, ComprehensiveTaxCalculationInput
            )
            from form16_extractor.tax_calculators.interfaces.calculator_interface import (
                TaxRegimeType, AgeCategory
            )
            from decimal import Decimal
            
            # Extract financial data from Form16Document
            if not hasattr(form16_result, 'salary') or not hasattr(form16_result, 'chapter_via_deductions'):
                if args.verbose:
                    print("Warning: Insufficient Form16 data for tax calculation")
                return None
            
            # Get salary and deduction data
            salary_data = form16_result.salary
            gross_salary = Decimal(str(salary_data.gross_salary or 0))
            basic_salary = Decimal(str(salary_data.basic_salary or 0))
            perquisites = Decimal(str(getattr(salary_data, 'perquisites_value', 0) or 0))
            
            # Extract deductions
            deductions = form16_result.chapter_via_deductions
            section_80c = Decimal(str(deductions.section_80c_total or 0))
            section_80ccd_1b = Decimal(str(deductions.section_80ccd_1b or 0))
            
            # Calculate total TDS from quarterly data
            total_tds = Decimal('0')
            if hasattr(form16_result, 'quarterly_tds') and form16_result.quarterly_tds:
                for quarter_data in form16_result.quarterly_tds:
                    if hasattr(quarter_data, 'tax_deducted') and quarter_data.tax_deducted:
                        total_tds += Decimal(str(quarter_data.tax_deducted))
            
            # Store extracted data for display
            extraction_data = {
                'employee_name': getattr(form16_result.employee, 'name', 'N/A'),
                'employee_pan': getattr(form16_result.employee, 'pan', 'N/A'),
                'employer_name': getattr(form16_result.employer, 'name', 'N/A'),
                'gross_salary': float(gross_salary),
                'section_17_1': float(basic_salary),
                'perquisites': float(perquisites),
                'section_80c': float(section_80c),
                'section_80ccd_1b': float(section_80ccd_1b),
                'total_tds': float(total_tds),
            }
            
            # Estimate HRA from basic salary 
            estimated_basic = basic_salary if basic_salary > 0 else gross_salary * Decimal('0.5')  # Use actual basic or assume 50%
            estimated_hra = estimated_basic * Decimal('0.4')  # Assume 40% HRA of basic
            
            # Determine assessment year from extraction
            assessment_year = "2024-25"  # Default, can be enhanced to extract from form
            
            # Age category mapping
            age_map = {
                "below_60": AgeCategory.BELOW_60,
                "senior_60_to_80": AgeCategory.SENIOR_60_TO_80, 
                "super_senior_above_80": AgeCategory.SUPER_SENIOR_ABOVE_80
            }
            
            tax_results = {'extraction_data': extraction_data}
            calculator = ComprehensiveTaxCalculator()
            
            # Calculate for requested regime(s)
            regimes_to_calculate = []
            if args.tax_regime == "both":
                regimes_to_calculate = [("new", TaxRegimeType.NEW), ("old", TaxRegimeType.OLD)]
            elif args.tax_regime == "new":
                regimes_to_calculate = [("new", TaxRegimeType.NEW)]
            else:
                regimes_to_calculate = [("old", TaxRegimeType.OLD)]
            
            for regime_name, regime_type in regimes_to_calculate:
                # Create comprehensive input
                comprehensive_input = ComprehensiveTaxCalculationInput(
                    assessment_year=assessment_year,
                    regime_type=regime_type,
                    age_category=age_map[args.age_category],
                    gross_salary=gross_salary,
                    section_80c=section_80c,
                    section_80ccd_1b=section_80ccd_1b,
                    tds_deducted=total_tds,
                    basic_salary=estimated_basic,
                    hra_received=estimated_hra,
                    rent_paid=estimated_hra * Decimal('1.2'),  # Assume rent is 20% more than HRA
                    city_type=args.city_type,
                    work_state='KA',  # Default to Karnataka
                    professional_tax_paid=Decimal('2500'),  # Default professional tax
                    lta_received=Decimal('50000'),  # Standard LTA
                    medical_reimbursement=Decimal('15000'),  # Standard medical
                    perquisites_total=perquisites,
                )
                
                # Calculate tax
                result = calculator.calculate_tax(comprehensive_input)
                
                # Calculate final position
                balance = total_tds - result.total_tax_liability
                
                tax_results[regime_name] = {
                    'taxable_income': float(result.taxable_income),
                    'tax_liability': float(result.total_tax_liability),
                    'tds_paid': float(total_tds),
                    'balance': float(balance),
                    'status': 'refund_due' if balance > 0 else 'additional_payable',
                    'effective_tax_rate': float((result.total_tax_liability / gross_salary) * 100),
                }
            
            return tax_results
            
        except Exception as e:
            if args.verbose:
                print(f"Tax calculation error: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def _calculate_form16_based_tax(self, form16_result, args):
        """Calculate tax liability using ComprehensiveTaxCalculator with Form16 data."""
        try:
            from form16_extractor.tax_calculators.comprehensive_calculator import (
                ComprehensiveTaxCalculator, ComprehensiveTaxCalculationInput
            )
            from form16_extractor.tax_calculators.interfaces.calculator_interface import (
                TaxRegimeType, AgeCategory
            )
            from decimal import Decimal
            
            # Extract data from Form16Document (our actual structure)
            salary = form16_result.salary if hasattr(form16_result, 'salary') and form16_result.salary else None
            deductions = form16_result.chapter_via_deductions if hasattr(form16_result, 'chapter_via_deductions') and form16_result.chapter_via_deductions else None
            employer = form16_result.employer if hasattr(form16_result, 'employer') and form16_result.employer else None
            employee = form16_result.employee if hasattr(form16_result, 'employee') and form16_result.employee else None
            
            # Check if we have the new JSON structure instead
            has_form16_structure = hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_b')
            
            if not salary and not has_form16_structure:
                return None
            
            # Create tax inputs for both regimes
            calculator = ComprehensiveTaxCalculator()
            
            # Determine age category from CLI args
            age_category = AgeCategory.BELOW_60
            if hasattr(args, 'age_category'):
                age_map = {
                    'below_60': AgeCategory.BELOW_60,
                    'senior_60_to_80': AgeCategory.SENIOR_60_TO_80, 
                    'super_senior_above_80': AgeCategory.SUPER_SENIOR_ABOVE_80
                }
                age_category = age_map.get(args.age_category, AgeCategory.BELOW_60)
            
            # Extract basic data - include perquisites in total salary income
            section_17_1_salary = Decimal(str(salary.gross_salary or 0)) if salary else Decimal('0')
            
            # Check for perquisites (Section 17(2)) - try multiple sources
            section_17_2_perquisites = Decimal('0')
            if salary and hasattr(salary, 'perquisites_value') and salary.perquisites_value:
                section_17_2_perquisites = Decimal(str(salary.perquisites_value))
            elif hasattr(form16_result, 'detailed_perquisites') and form16_result.detailed_perquisites:
                # Sum up all detailed perquisites
                total_perq = sum(Decimal(str(v)) for v in form16_result.detailed_perquisites.values() if v)
                section_17_2_perquisites = total_perq
            
            # Total salary income (Section 17(1) + 17(2) + 17(3))
            gross_salary = section_17_1_salary + section_17_2_perquisites
            
            # Extract basic salary 
            basic_salary = Decimal('0')
            if salary and hasattr(salary, 'basic_salary'):
                basic_salary = Decimal(str(salary.basic_salary or 0))
            
            # If basic salary missing, estimate as 40% of gross
            if not basic_salary and gross_salary:
                basic_salary = gross_salary * Decimal('0.4')
            
            # Extract deductions
            section_80c = Decimal(str(deductions.section_80c_total or 0)) if deductions else Decimal('0')
            section_80ccd_1b = Decimal(str(deductions.section_80ccd_1b or 0)) if deductions else Decimal('0')
            section_80d = Decimal(str(deductions.section_80d_total or 0)) if deductions else Decimal('0')
            
            # Calculate for both regimes if requested
            results = {}
            regimes_to_calculate = []
            
            if hasattr(args, 'tax_regime') and args.tax_regime:
                if args.tax_regime == 'old':
                    regimes_to_calculate = [TaxRegimeType.OLD]
                elif args.tax_regime == 'new':
                    regimes_to_calculate = [TaxRegimeType.NEW]
                else:  # 'both'
                    regimes_to_calculate = [TaxRegimeType.OLD, TaxRegimeType.NEW]
            else:
                regimes_to_calculate = [TaxRegimeType.OLD, TaxRegimeType.NEW]
            
            for regime in regimes_to_calculate:
                # Create input for each regime
                tax_input = ComprehensiveTaxCalculationInput(
                    # Basic fields
                    gross_salary=gross_salary,
                    basic_salary=basic_salary,
                    section_80c=section_80c if regime == TaxRegimeType.OLD else Decimal('0'),
                    section_80ccd_1b=section_80ccd_1b,
                    section_80d=section_80d if regime == TaxRegimeType.OLD else Decimal('0'),
                    age_category=age_category,
                    regime_type=regime,
                    assessment_year="2024-25",
                    
                    # HRA fields (basic estimates)
                    hra_received=Decimal(str(salary.hra_received or 0)) if salary else Decimal('0'),
                    city_type='metro',  # Default assumption
                    
                    # Other defaults
                    salary_arrears={},
                    perquisites_total=Decimal(str(salary.perquisites_value or 0)) if salary else Decimal('0')
                )
                
                # Calculate tax for this regime
                result = calculator.calculate_tax(tax_input)
                results[regime] = result
            
            # Build CLI-friendly result
            return self._build_cli_tax_result(results, form16_result, args)
            
        except Exception as e:
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                print(f"Tax calculation error: {e}")
                traceback.print_exc()
            return None
    
    def _build_cli_tax_result(self, results, form16_result, args):
        """Build CLI-friendly tax result with regime comparison."""
        from form16_extractor.tax_calculators.interfaces.calculator_interface import TaxRegimeType
        from decimal import Decimal
        
        if not results:
            return None
        
        # Extract TDS from Form16 - check multiple possible locations
        total_tds = Decimal('0')
        
        # First try: Direct access to quarterly_tds_summary
        if hasattr(form16_result, 'quarterly_tds_summary') and form16_result.quarterly_tds_summary:
            # Check if there's a direct total_tds field
            if hasattr(form16_result.quarterly_tds_summary, 'total_tds') and hasattr(form16_result.quarterly_tds_summary.total_tds, 'deducted'):
                total_tds = Decimal(str(form16_result.quarterly_tds_summary.total_tds.deducted or 0))
            else:
                # Sum TDS from individual quarters
                for quarter_data in [form16_result.quarterly_tds_summary.quarter_1,
                                    form16_result.quarterly_tds_summary.quarter_2, 
                                    form16_result.quarterly_tds_summary.quarter_3,
                                    form16_result.quarterly_tds_summary.quarter_4]:
                    if quarter_data and hasattr(quarter_data, 'amount_deducted') and quarter_data.amount_deducted:
                        total_tds += Decimal(str(quarter_data.amount_deducted))
        
        # Third try: Check if it's under part_a (fallback for different structures)
        elif hasattr(form16_result, 'part_a') and hasattr(form16_result.part_a, 'quarterly_tds_summary'):
            part_a_tds = form16_result.part_a.quarterly_tds_summary
            if hasattr(part_a_tds, 'total_tds') and hasattr(part_a_tds.total_tds, 'deducted'):
                total_tds = Decimal(str(part_a_tds.total_tds.deducted or 0))
        
        # Fourth try: Look for quarterly_tds field (alternative structure)
        elif hasattr(form16_result, 'quarterly_tds') and form16_result.quarterly_tds:
            for quarter_data in form16_result.quarterly_tds:
                if hasattr(quarter_data, 'tax_deducted') and quarter_data.tax_deducted:
                    total_tds += Decimal(str(quarter_data.tax_deducted))
        
        # Extract salary and perquisites for display
        section_17_1_salary = float(form16_result.salary.gross_salary) if form16_result.salary else 0.0
        section_17_2_perquisites = 0.0
        
        # Check for perquisites (Section 17(2)) - try multiple sources
        if form16_result.salary and hasattr(form16_result.salary, 'perquisites_value') and form16_result.salary.perquisites_value:
            section_17_2_perquisites = float(form16_result.salary.perquisites_value)
        elif hasattr(form16_result, 'detailed_perquisites') and form16_result.detailed_perquisites:
            # Sum up all detailed perquisites
            total_perq = sum(float(v) for v in form16_result.detailed_perquisites.values() if v)
            section_17_2_perquisites = total_perq
        
        # Debug: log what we found for verbose mode
        if hasattr(args, 'verbose') and args.verbose:
            logging.debug(f"Section 17(1): {section_17_1_salary}")
            logging.debug(f"Section 17(2): {section_17_2_perquisites}")
        
        total_salary_income = section_17_1_salary + section_17_2_perquisites
        
        # Build result structure for CLI display
        cli_result = {
            'employee_info': {
                'name': self._extract_employee_name(form16_result),
                'pan': self._extract_employee_pan(form16_result),
                'employer': self._extract_employer_name(form16_result)
            },
            'financial_data': {
                'section_17_1_salary': section_17_1_salary,
                'section_17_2_perquisites': section_17_2_perquisites,
                'gross_salary': total_salary_income,  # Total salary income (17(1) + 17(2))
                'section_80c': self._extract_section_80c_display(form16_result),
                'section_80ccd_1b': self._extract_section_80ccd_1b_display(form16_result),
                'total_tds': float(total_tds)
            },
            'regime_comparison': {}
        }
        
        # Add regime-specific results
        for regime_type, calc_result in results.items():
            regime_key = 'old_regime' if regime_type == TaxRegimeType.OLD else 'new_regime'
            
            # Calculate refund/tax due
            tax_liability = calc_result.total_tax_liability
            refund_due = float(total_tds - tax_liability) if total_tds >= tax_liability else 0.0
            tax_due = float(tax_liability - total_tds) if tax_liability > total_tds else 0.0
            
            cli_result['regime_comparison'][regime_key] = {
                'taxable_income': float(calc_result.taxable_income),
                'tax_liability': float(calc_result.total_tax_liability),
                'tds_paid': float(total_tds),
                'refund_due': refund_due,
                'tax_due': tax_due,
                'effective_rate': float(calc_result.total_tax_liability / calc_result.total_income * 100) if calc_result.total_income > 0 else 0.0,
                'deductions_used': {
                    '80C': float(calc_result.section_80c) if hasattr(calc_result, 'section_80c') else 0.0,
                    '80CCD(1B)': float(calc_result.section_80ccd_1b) if hasattr(calc_result, 'section_80ccd_1b') else 0.0,
                    '80D': float(calc_result.section_80d) if hasattr(calc_result, 'section_80d') else 0.0
                }
            }
        
        # Determine recommended regime
        if len(results) == 2:
            old_tax = results[TaxRegimeType.OLD].total_tax_liability
            new_tax = results[TaxRegimeType.NEW].total_tax_liability
            
            if old_tax <= new_tax:
                cli_result['recommended_regime'] = 'old'
                cli_result['tax_savings'] = float(new_tax - old_tax)
            else:
                cli_result['recommended_regime'] = 'new'
                cli_result['tax_savings'] = float(old_tax - new_tax)
        else:
            # Single regime calculation
            regime = list(results.keys())[0]
            cli_result['recommended_regime'] = 'old' if regime == TaxRegimeType.OLD else 'new'
            cli_result['tax_savings'] = 0.0
        
        return cli_result
    
    def _display_tax_summary(self, tax_results, regime_choice):
        """Display compact tax summary using modular templates."""
        from form16_extractor.display import SummaryDisplayRenderer
        
        renderer = SummaryDisplayRenderer()
        summary_output = renderer.render_complete_summary(tax_results)
        print(summary_output)
    
    def _display_detailed_tax_breakdown(self, tax_results, regime_choice):
        """Display detailed tax breakdown using modular templates."""
        from form16_extractor.display import DetailedDisplayRenderer
        
        renderer = DetailedDisplayRenderer()
        detailed_output = renderer.render_complete_detailed(tax_results)
        print(detailed_output)
        
    def _display_tax_results(self, tax_results, regime_choice):
        """Display comprehensive tax calculation results using modular templates."""
        from form16_extractor.display import DefaultDisplayRenderer
        
        renderer = DefaultDisplayRenderer()
        default_output = renderer.render_complete_default(tax_results, regime_choice)
        print(default_output)
    
    def consolidate_form16s(self, args) -> int:
        """Consolidate multiple Form16s with financial year validation."""
        try:
            form16_files = args.files
            output_file = args.output if args.output else Path("consolidated_form16.json")
            
            if len(form16_files) < 2:
                print(f"Error: At least 2 Form16 files required for consolidation")
                return 1
            
            print(f"Consolidating {len(form16_files)} Form16 files...")
            
            # Validate all files exist
            for file_path in form16_files:
                if not file_path.exists():
                    print(f"Error: File not found: {file_path}")
                    return 1
                if not file_path.suffix.lower() == '.pdf':
                    print(f"Error: Only PDF files supported: {file_path}")
                    return 1
            
            # Extract data from all Form16s
            extracted_forms = []
            financial_years = set()
            
            print(f"\n Extracting data from Form16s...")
            for i, form16_file in enumerate(form16_files, 1):
                print(f"[{i}/{len(form16_files)}] Processing: {form16_file.name}")
                
                # Extract tables and Form16 data
                extraction_result = self.pdf_processor.extract_tables(form16_file)
                form16_result = self.extractor.extract_all(extraction_result.tables)
                
                # Build comprehensive JSON
                form16_json = Form16JSONBuilder.build_comprehensive_json(
                    form16_doc=form16_result,
                    pdf_file_name=form16_file.name,
                    processing_time=0,  # Not tracking individual processing time for consolidation
                    extraction_metadata=getattr(form16_result, 'extraction_metadata', {})
                )
                
                # Extract financial year information
                fy_info = self._extract_financial_year_info(form16_result, form16_file)
                financial_years.add(fy_info['financial_year'])
                
                extracted_forms.append({
                    'file_name': form16_file.name,
                    'financial_year': fy_info['financial_year'],
                    'assessment_year': fy_info['assessment_year'],
                    'form16_data': form16_json,
                    'employer_name': getattr(form16_result.employer, 'name', 'Unknown') if hasattr(form16_result, 'employer') else 'Unknown',
                    'employee_name': getattr(form16_result.employee, 'name', 'Unknown') if hasattr(form16_result, 'employee') else 'Unknown'
                })
                
                print(f"  ├── Employer: {extracted_forms[-1]['employer_name']}")
                print(f"  ├── Financial Year: {fy_info['financial_year']}")
                print(f"  └── Assessment Year: {fy_info['assessment_year']}")
            
            # Financial Year Validation
            print(f"\n Financial Year Validation:")
            print(f"├── Total Form16s: {len(extracted_forms)}")
            print(f"├── Unique Financial Years found: {len(financial_years)}")
            
            if len(financial_years) > 1:
                print(f" VALIDATION FAILED:")
                print(f"├── Multiple financial years detected: {sorted(financial_years)}")
                print(f"├── Cannot consolidate Form16s from different financial years")
                print(f"└── Please provide Form16s from the same financial year only")
                return 1
            
            common_fy = list(financial_years)[0]
            print(f"└──  All Form16s are from FY {common_fy}")
            
            # Check for duplicate employers
            employers = [form['employer_name'] for form in extracted_forms]
            duplicate_employers = set([emp for emp in employers if employers.count(emp) > 1])
            
            if duplicate_employers:
                print(f"\nWARNING: Duplicate employers detected:")
                for emp in duplicate_employers:
                    print(f"├── {emp}")
                print(f"└── Please verify these are for the same financial year")
            
            # Consolidate the data
            print(f"\nBuilding consolidated Form16...")
            
            consolidated_result = self._build_consolidated_form16(extracted_forms, common_fy)
            
            # Calculate consolidated tax if requested
            if args.calculate_tax:
                print(f"\n Calculating consolidated tax liability...")
                
                # Use the consolidated salary and deduction data for tax calculation
                consolidated_tax = self._calculate_consolidated_tax(consolidated_result, args)
                if consolidated_tax:
                    consolidated_result['consolidated_tax_calculations'] = consolidated_tax
                    
                    print(f"\n" + "="*80)
                    print(f"CONSOLIDATED TAX CALCULATION RESULTS") 
                    print(f"="*80)
                    self._display_consolidated_tax_results(consolidated_tax, args.tax_regime)
                else:
                    print(f"Warning: Consolidated tax calculation failed")
            
            # Save consolidated result
            with open(output_file, 'w') as f:
                json.dump(consolidated_result, f, indent=2, default=str)
            
            print(f"\n Consolidation completed successfully!")
            print(f"├── Input: {len(form16_files)} Form16 files")
            print(f"├── Financial Year: {common_fy}")
            print(f"├── Total Employers: {len(set(employers))}")
            print(f"└── Output: {output_file}")
            
            return 0
            
        except Exception as e:
            print(f"Error during consolidation: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _extract_financial_year_info(self, form16_result, file_path):
        """Extract financial year information from Form16."""
        
        # Try to extract from the form16_result structure
        # Financial year extraction with fallback to filename analysis
        # might not be perfect in all cases
        
        # Default values (assuming current assessment year 2024-25)
        default_fy = "2023-24"
        default_ay = "2024-25"
        
        # Try to get financial year from various sources
        fy_info = {
            'financial_year': default_fy,
            'assessment_year': default_ay,
            'source': 'default'
        }
        
        # Check if we can extract from the filename
        filename = file_path.stem.lower()
        
        # Common patterns in Form16 filenames
        if '2023' in filename and '2024' in filename:
            fy_info.update({
                'financial_year': '2023-24',
                'assessment_year': '2024-25',
                'source': 'filename'
            })
        elif '2022' in filename and '2023' in filename:
            fy_info.update({
                'financial_year': '2022-23', 
                'assessment_year': '2023-24',
                'source': 'filename'
            })
        elif '2024' in filename and '2025' in filename:
            fy_info.update({
                'financial_year': '2024-25',
                'assessment_year': '2025-26', 
                'source': 'filename'
            })
        
        return fy_info
    
    def _build_consolidated_form16(self, extracted_forms, common_fy):
        """Build consolidated Form16 data from multiple forms."""
        
        from decimal import Decimal
        
        # Initialize consolidated structure
        consolidated = {
            'consolidation_info': {
                'financial_year': common_fy,
                'total_employers': len(extracted_forms),
                'consolidation_timestamp': datetime.now().isoformat(),
                'employers': []
            },
            'consolidated_data': {
                'total_gross_salary': Decimal('0'),
                'total_tds': Decimal('0'),
                'total_perquisites': Decimal('0'),
                'combined_deductions': {},
                'employers_summary': []
            },
            'individual_form16s': extracted_forms
        }
        
        # Consolidate salary and tax data
        for form in extracted_forms:
            form16_data = form['form16_data']
            
            # Extract salary information
            if 'form16' in form16_data and 'part_b' in form16_data['form16']:
                part_b = form16_data['form16']['part_b']
                
                # Gross salary
                if 'gross_salary' in part_b and part_b['gross_salary'] and 'total' in part_b['gross_salary']:
                    gross_salary = Decimal(str(part_b['gross_salary']['total'] or 0))
                    consolidated['consolidated_data']['total_gross_salary'] += gross_salary
                
                # Perquisites
                if 'gross_salary' in part_b and part_b['gross_salary'] and 'section_17_2_perquisites' in part_b['gross_salary']:
                    perquisites = Decimal(str(part_b['gross_salary']['section_17_2_perquisites'] or 0))
                    consolidated['consolidated_data']['total_perquisites'] += perquisites
            
            # Extract TDS information
            if 'form16' in form16_data and 'part_a' in form16_data['form16']:
                part_a = form16_data['form16']['part_a']
                if 'quarterly_tds_summary' in part_a and 'total_tds' in part_a['quarterly_tds_summary']:
                    tds_data = part_a['quarterly_tds_summary']['total_tds']
                    if 'deducted' in tds_data:
                        tds = Decimal(str(tds_data['deducted'] or 0))
                        consolidated['consolidated_data']['total_tds'] += tds
            
            # Add employer summary
            employer_summary = {
                'employer_name': form['employer_name'],
                'file_name': form['file_name'],
                'financial_year': form['financial_year']
            }
            consolidated['consolidated_data']['employers_summary'].append(employer_summary)
            consolidated['consolidation_info']['employers'].append(form['employer_name'])
        
        return consolidated
    
    def _calculate_consolidated_tax(self, consolidated_result, args):
        """Calculate tax on consolidated income from multiple employers."""
        
        try:
            from decimal import Decimal
            
            consolidated_data = consolidated_result['consolidated_data']
            
            # For consolidated tax calculation, we'll use a simplified approach
            # based on the total income and TDS
            
            total_gross = consolidated_data['total_gross_salary']
            total_tds = consolidated_data['total_tds'] 
            total_perquisites = consolidated_data['total_perquisites']
            
            # Assume standard deductions and exemptions for consolidated calculation
            # This is a simplified approach - in reality, you'd need more detailed
            # information about each employer's calculations
            
            estimated_taxable_income = total_gross - Decimal('50000')  # Standard deduction
            estimated_taxable_income -= Decimal('200000')  # Assume standard Chapter VI-A deductions
            
            # Calculate tax liability for consolidated income
            if estimated_taxable_income > 0:
                # Use new regime calculation as default
                tax_liability = self._calculate_simple_tax(estimated_taxable_income)
            else:
                tax_liability = Decimal('0')
            
            balance = total_tds - tax_liability
            
            consolidated_tax = {
                'consolidated_summary': {
                    'total_employers': consolidated_result['consolidation_info']['total_employers'],
                    'total_gross_salary': total_gross,
                    'total_tds_deducted': total_tds,
                    'estimated_taxable_income': estimated_taxable_income,
                    'estimated_tax_liability': tax_liability,
                    'balance': balance,
                    'status': 'refund_due' if balance > 0 else 'additional_tax_payable',
                    'note': 'Simplified calculation based on consolidated data'
                }
            }
            
            return consolidated_tax
            
        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            return None
    
    def _calculate_simple_tax(self, taxable_income):
        """Calculate tax liability for consolidated income using current tax slabs."""
        from decimal import Decimal
        
        # New regime AY 2024-25 slabs
        tax = Decimal('0')
        
        if taxable_income <= 300000:
            return tax
        elif taxable_income <= 600000:
            tax += (taxable_income - 300000) * Decimal('0.05')
        elif taxable_income <= 900000:
            tax += 300000 * Decimal('0.05')
            tax += (taxable_income - 600000) * Decimal('0.10')
        elif taxable_income <= 1200000:
            tax += 300000 * Decimal('0.05')
            tax += 300000 * Decimal('0.10')
            tax += (taxable_income - 900000) * Decimal('0.15')
        elif taxable_income <= 1500000:
            tax += 300000 * Decimal('0.05')
            tax += 300000 * Decimal('0.10')
            tax += 300000 * Decimal('0.15')
            tax += (taxable_income - 1200000) * Decimal('0.20')
        else:
            tax += 300000 * Decimal('0.05')
            tax += 300000 * Decimal('0.10')
            tax += 300000 * Decimal('0.15')
            tax += 300000 * Decimal('0.20')
            tax += (taxable_income - 1500000) * Decimal('0.30')
        
        # Add surcharge for high income
        if taxable_income > 5000000:
            surcharge = tax * Decimal('0.10')  # 10% for 50L-1Cr
            tax += surcharge
        
        # Add cess
        cess = tax * Decimal('0.04')
        total_tax = tax + cess
        
        return total_tax.quantize(Decimal('1'))
    
    def _display_consolidated_tax_results(self, tax_results, regime_choice):
        """Display consolidated tax calculation results."""
        
        summary = tax_results['consolidated_summary']
        
        print(f" Consolidated Form16 Summary:")
        print(f"├── Total Employers: {summary['total_employers']}")
        print(f"├── Combined Gross Salary: Rs {summary['total_gross_salary']:,}")
        print(f"├── Combined TDS Deducted: Rs {summary['total_tds_deducted']:,}")
        print(f"└── Estimated Taxable Income: Rs {summary['estimated_taxable_income']:,}")
        
        print(f"\nConsolidated Tax Calculation:")
        print(f"├── Estimated Tax Liability: Rs {summary['estimated_tax_liability']:,}")
        print(f"├── Total TDS Paid: Rs {summary['total_tds_deducted']:,}")
        
        balance_indicator = "[REFUND]" if summary['status'] == 'refund_due' else "[PAYABLE]"
        balance_text = "Estimated Refund Due" if summary['status'] == 'refund_due' else "Additional Tax Payable"
        print(f"└── {balance_indicator} {balance_text}: Rs {abs(summary['balance']):,}")
        
        print(f"\nNote: {summary['note']}")
        print(f" For accurate calculation, consult a tax professional with detailed Form16s")
    
    def main(self):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Configure logging
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
            # Enable debug messages in verbose mode
            logging.getLogger('form16_extractor').setLevel(logging.DEBUG)
        else:
            # Suppress all debug/info messages in normal mode
            logging.basicConfig(level=logging.ERROR)
            logging.getLogger().setLevel(logging.ERROR)
            logging.getLogger('form16_extractor').setLevel(logging.ERROR)
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Route to appropriate handler
        if args.command == "extract":
            return self.extract_single_file(args)
        elif args.command == "batch":
            return self.batch_process(args)
        elif args.command == "consolidate":
            return self.consolidate_form16s(args)
        elif args.command == "validate":
            return self.validate_results(args)
        elif args.command == "test":
            return self.run_tests(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    def _extract_section_80c_display(self, form16_result):
        """Extract Section 80C deduction amount for display."""
        if hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_b') and hasattr(form16_result.form16.part_b, 'chapter_vi_a_deductions'):
            chapter_deductions = form16_result.form16.part_b.chapter_vi_a_deductions
            if hasattr(chapter_deductions, 'section_80C') and hasattr(chapter_deductions.section_80C, 'deductible_amount'):
                return float(chapter_deductions.section_80C.deductible_amount or 0)
        elif hasattr(form16_result, 'chapter_via_deductions') and form16_result.chapter_via_deductions:
            return float(form16_result.chapter_via_deductions.section_80c_total or 0)
        return 0.0
    
    def _extract_section_80ccd_1b_display(self, form16_result):
        """Extract Section 80CCD(1B) deduction amount for display."""
        if hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_b') and hasattr(form16_result.form16.part_b, 'chapter_vi_a_deductions'):
            chapter_deductions = form16_result.form16.part_b.chapter_vi_a_deductions
            if hasattr(chapter_deductions, 'section_80CCD_1B') and hasattr(chapter_deductions.section_80CCD_1B, 'deductible_amount'):
                return float(chapter_deductions.section_80CCD_1B.deductible_amount or 0)
        elif hasattr(form16_result, 'chapter_via_deductions') and form16_result.chapter_via_deductions:
            return float(form16_result.chapter_via_deductions.section_80ccd_1b or 0)
        return 0.0
    
    def _extract_employee_name(self, form16_result):
        """Extract employee name from Form16 data."""
        if hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_a') and hasattr(form16_result.form16.part_a, 'employee'):
            return form16_result.form16.part_a.employee.name or 'N/A'
        elif hasattr(form16_result, 'employee') and form16_result.employee:
            return form16_result.employee.name or 'N/A'
        return 'N/A'
    
    def _extract_employee_pan(self, form16_result):
        """Extract employee PAN from Form16 data."""
        if hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_a') and hasattr(form16_result.form16.part_a, 'employee'):
            return form16_result.form16.part_a.employee.pan or 'N/A'
        elif hasattr(form16_result, 'employee') and form16_result.employee:
            return form16_result.employee.pan or 'N/A'
        return 'N/A'
    
    def _extract_employer_name(self, form16_result):
        """Extract employer name from Form16 data."""
        if hasattr(form16_result, 'form16') and hasattr(form16_result.form16, 'part_a') and hasattr(form16_result.form16.part_a, 'employer'):
            return form16_result.form16.part_a.employer.name or 'N/A'
        elif hasattr(form16_result, 'employer') and form16_result.employer:
            return form16_result.employer.name or 'N/A'
        return 'N/A'
    
    
    def _display_colored_regime_components(self, tax_results, regime_choice):
        """Display regime components using modular colored templates."""
        from form16_extractor.display import ColoredDisplayRenderer
        
        renderer = ColoredDisplayRenderer()
        colored_output = renderer.render_complete_display(tax_results)
        print(colored_output)
    
    # Removed old placeholder methods - now using working Form16TaxIntegrator!


if __name__ == "__main__":
    cli = Form16CLI()
    exit_code = cli.main()
    sys.exit(exit_code)