#!/usr/bin/env python3
"""
Test Form16 extraction with ACTUAL documents
============================================

This script tests our Form16 extraction pipeline against all real 
Form16 documents in ~/Downloads/form16/ to ensure robust extraction.

Following TDD approach: Test against real data after each phase.
"""

import logging
import time
from pathlib import Path
from form16_extractor.pdf.reader import RobustPDFProcessor
from form16_extractor.models.form16_models import Form16Document, ExtractionResult

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_extraction():
    """Test PDF table extraction with actual Form16 documents"""
    
    # Initialize PDF processor
    pdf_processor = RobustPDFProcessor()
    
    # Test files from our fixtures
    test_files = Path("tests/fixtures/sample_form16s").glob("*.pdf")
    
    logger.info("🚀 Testing PDF extraction with ACTUAL Form16 documents")
    logger.info("=" * 60)
    
    results = []
    
    for pdf_file in test_files:
        logger.info(f"\n📄 Processing: {pdf_file.name}")
        logger.info("-" * 40)
        
        start_time = time.time()
        
        try:
            # Extract tables
            extraction_result = pdf_processor.extract_tables(pdf_file)
            
            processing_time = time.time() - start_time
            
            # Log results
            logger.info(f"✅ Strategy: {extraction_result.strategy_used.value}")
            logger.info(f"📊 Tables extracted: {len(extraction_result.tables)}")
            logger.info(f"🎯 Confidence: {extraction_result.confidence_score:.2f}")
            logger.info(f"⏱️  Processing time: {processing_time:.2f}s")
            
            if extraction_result.warnings:
                logger.warning(f"⚠️  Warnings: {len(extraction_result.warnings)}")
                for warning in extraction_result.warnings[:3]:  # Show first 3
                    logger.warning(f"   - {warning}")
            
            # Check table quality
            total_rows = sum(len(table) for table in extraction_result.tables)
            total_cols = sum(len(table.columns) for table in extraction_result.tables if not table.empty)
            logger.info(f"📏 Total data: {total_rows} rows, ~{total_cols} columns")
            
            # Show sample of first table if available
            if extraction_result.tables and not extraction_result.tables[0].empty:
                sample_table = extraction_result.tables[0]
                logger.info(f"📋 First table sample ({sample_table.shape[0]}x{sample_table.shape[1]}):")
                logger.info(f"   Columns: {list(sample_table.columns[:5])}")  # First 5 columns
                if len(sample_table) > 0:
                    logger.info(f"   Sample row: {sample_table.iloc[0].tolist()[:3]}")  # First 3 values
            
            results.append({
                'file': pdf_file.name,
                'success': True,
                'tables_count': len(extraction_result.tables),
                'confidence': extraction_result.confidence_score,
                'processing_time': processing_time,
                'strategy': extraction_result.strategy_used.value,
                'warnings_count': len(extraction_result.warnings)
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_file.name}: {str(e)}")
            results.append({
                'file': pdf_file.name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            })
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 EXTRACTION SUMMARY")
    logger.info("=" * 60)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    logger.info(f"✅ Successful extractions: {len(successful)}/{len(results)}")
    logger.info(f"❌ Failed extractions: {len(failed)}")
    
    if successful:
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        avg_processing_time = sum(r['processing_time'] for r in successful) / len(successful)
        total_tables = sum(r['tables_count'] for r in successful)
        
        logger.info(f"🎯 Average confidence: {avg_confidence:.2f}")
        logger.info(f"⏱️  Average processing time: {avg_processing_time:.2f}s")
        logger.info(f"📊 Total tables extracted: {total_tables}")
        
        # Strategy breakdown
        strategies = {}
        for r in successful:
            strategy = r['strategy']
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        logger.info(f"🔧 Strategies used:")
        for strategy, count in strategies.items():
            logger.info(f"   - {strategy}: {count} files")
    
    if failed:
        logger.info(f"\n❌ Failed files:")
        for r in failed:
            logger.info(f"   - {r['file']}: {r['error']}")
    
    # Test success criteria
    success_rate = len(successful) / len(results) if results else 0
    logger.info(f"\n🎯 SUCCESS RATE: {success_rate:.1%}")
    
    if success_rate >= 0.8:  # 80% success rate
        logger.info("🎉 PHASE 1 COMPLETE: PDF extraction working robustly!")
        return True
    else:
        logger.warning("⚠️  PDF extraction needs improvement")
        return False

def test_model_creation():
    """Test creating Form16Document with extracted data"""
    logger.info("\n🏗️  Testing Form16 model creation...")
    
    # Create a sample Form16 document
    form16 = Form16Document()
    
    # Add some test data
    form16.employee.name = "RISHABH ROY"
    form16.employee.pan = "BYHPR6078P"
    form16.employer.name = "SALESFORCE.COM INDIA PRIVATE LIMITED"
    form16.employer.tan = "BLRS20885E"
    
    # Test JSON output
    json_output = form16.to_json_output()
    
    logger.info("✅ Form16 model created successfully")
    logger.info(f"📄 Employee: {json_output['form16_data']['employee_info'].get('name', 'Not found')}")
    logger.info(f"🏢 Employer: {json_output['form16_data']['employer_info'].get('name', 'Not found')}")
    
    return True

if __name__ == "__main__":
    logger.info("🧪 TESTING FORM16 EXTRACTION PIPELINE")
    logger.info("=" * 60)
    
    # Phase 1: Test PDF extraction
    pdf_test_passed = test_pdf_extraction()
    
    # Phase 2: Test model creation
    model_test_passed = test_model_creation()
    
    logger.info("\n" + "=" * 60)
    logger.info("🏆 OVERALL TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"📄 PDF Extraction: {'✅ PASS' if pdf_test_passed else '❌ FAIL'}")
    logger.info(f"🏗️  Model Creation: {'✅ PASS' if model_test_passed else '❌ FAIL'}")
    
    if pdf_test_passed and model_test_passed:
        logger.info("🎉 ALL TESTS PASSED - Ready for next phase!")
        exit(0)
    else:
        logger.error("❌ Some tests failed - needs attention")
        exit(1)