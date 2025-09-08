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
        for subparser in [extract_parser, batch_parser, validate_parser, test_parser]:
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
            
            # Save result with proper formatting
            if args.format == "json":
                with open(output_file, 'w') as f:
                    # Always use pretty formatting to match specification
                    json.dump(result, f, indent=2, default=str)
            
            print(f"Extraction completed successfully!")
            print(f"Input: {input_file}")
            print(f"Output: {output_file}")
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
    
    def main(self):
        """Main entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Configure logging
        if args.verbose:
            import logging
            logging.basicConfig(level=logging.DEBUG)
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Route to appropriate handler
        if args.command == "extract":
            return self.extract_single_file(args)
        elif args.command == "batch":
            return self.batch_process(args)
        elif args.command == "validate":
            return self.validate_results(args)
        elif args.command == "test":
            return self.run_tests(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1


if __name__ == "__main__":
    cli = Form16CLI()
    exit_code = cli.main()
    sys.exit(exit_code)