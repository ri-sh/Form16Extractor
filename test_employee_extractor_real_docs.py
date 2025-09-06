#!/usr/bin/env python3
"""
Test Employee Extractor Against REAL Form16 Documents
====================================================

This script uses Camelot to extract tables from all 5 real Form16 documents
and tests our EmployeeExtractor implementation to ensure robust field extraction.

Following TDD approach: Test against real data to validate implementation.
"""

import logging
import time
from pathlib import Path
import pandas as pd
from form16_extractor.pdf.reader import RobustPDFProcessor
from form16_extractor.extractors.employee import EmployeeExtractor
from form16_extractor.models.form16_models import EmployeeInfo

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_tables_with_camelot(pdf_file: Path):
    """Use Camelot to extract and analyze table structures"""
    logger.info(f"\n📊 ANALYZING TABLE STRUCTURES: {pdf_file.name}")
    logger.info("=" * 50)
    
    pdf_processor = RobustPDFProcessor()
    extraction_result = pdf_processor.extract_tables(pdf_file)
    
    logger.info(f"🔧 Strategy used: {extraction_result.strategy_used.value}")
    logger.info(f"📋 Tables extracted: {len(extraction_result.tables)}")
    logger.info(f"🎯 Confidence: {extraction_result.confidence_score:.2f}")
    
    # Analyze first few tables for employee data patterns
    employee_data_found = []
    
    for i, table in enumerate(extraction_result.tables[:5]):  # First 5 tables
        if table.empty:
            continue
            
        logger.info(f"\n📄 Table {i} ({table.shape[0]}x{table.shape[1]}):")
        
        # Convert to text for analysis
        table_text = ""
        for row_idx in range(min(5, len(table))):  # First 5 rows
            row_data = []
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip()
                if cell_value and cell_value.lower() not in ['nan', 'none']:
                    row_data.append(cell_value)
            if row_data:
                table_text += " | ".join(row_data) + "\n"
        
        if table_text:
            logger.info(f"   Sample content:\n{table_text}")
            
            # Look for employee data patterns
            text_lower = table_text.lower()
            patterns_found = []
            
            if 'employee name' in text_lower or 'rishabh roy' in text_lower:
                patterns_found.append("Employee Name")
            if 'employee pan' in text_lower or 'byhpr6078p' in text_lower:
                patterns_found.append("Employee PAN")
            if 'employee id' in text_lower or '870937' in text_lower:
                patterns_found.append("Employee ID")
            if 'designation' in text_lower or 'software engineering' in text_lower:
                patterns_found.append("Employee Designation")
            if 'address' in text_lower and 'employee' in text_lower:
                patterns_found.append("Employee Address")
                
            if patterns_found:
                logger.info(f"   🎯 Employee patterns found: {', '.join(patterns_found)}")
                employee_data_found.append({
                    'table_index': i,
                    'patterns': patterns_found,
                    'table': table
                })
    
    return extraction_result.tables, employee_data_found

def test_employee_extraction_on_real_docs():
    """Test employee extractor against all real Form16 documents"""
    
    # Initialize extractors
    employee_extractor = EmployeeExtractor()
    
    # Test files from fixtures
    fixture_dir = Path("tests/fixtures/sample_form16s")
    if not fixture_dir.exists():
        logger.warning(f"Fixture directory not found: {fixture_dir}")
        return False
        
    test_files = list(fixture_dir.glob("*.pdf"))
    if not test_files:
        logger.warning(f"No PDF files found in {fixture_dir}")
        return False
    
    logger.info("🧪 TESTING EMPLOYEE EXTRACTOR AGAINST REAL FORM16 DOCUMENTS")
    logger.info("=" * 70)
    
    results = []
    
    for pdf_file in test_files:
        logger.info(f"\nPROCESSING: {pdf_file.name}")
        logger.info("-" * 50)
        
        start_time = time.time()
        
        try:
            # Step 1: Analyze table structures with Camelot
            tables, employee_data_tables = analyze_tables_with_camelot(pdf_file)
            
            # Step 2: Extract employee information
            logger.info(f"\nEXTRACTING EMPLOYEE INFORMATION...")
            employee_result = employee_extractor.extract_with_confidence(tables)
            
            employee_info = employee_result['employee_info']
            confidence_scores = employee_result['confidence_scores']
            
            processing_time = time.time() - start_time
            
            # Log results
            logger.info(f"\n✅ EXTRACTION RESULTS:")
            logger.info(f"   👤 Name: {employee_info.name or 'Not found'}")
            logger.info(f"   🆔 PAN: {employee_info.pan or 'Not found'}")
            logger.info(f"   🏷️  Employee ID: {employee_info.employee_id or 'Not found'}")
            logger.info(f"   💼 Designation: {employee_info.designation or 'Not found'}")
            logger.info(f"   🏠 Address: {employee_info.address[:50] + '...' if employee_info.address else 'Not found'}")
            
            logger.info(f"\n📊 CONFIDENCE SCORES:")
            for field, score in confidence_scores.items():
                if score > 0:
                    logger.info(f"   {field}: {score:.2f}")
            
            # Calculate extraction success rate for available fields
            # Employee ID is often not provided in Form16s, so we calculate based on available fields
            available_fields = ['name', 'pan', 'designation', 'address']  # Core fields that should be present
            extracted_core_fields = sum(1 for field in [employee_info.name, employee_info.pan, 
                                                       employee_info.designation, employee_info.address] if field)
            
            # If Employee ID is present, count it as bonus
            total_fields = len(available_fields)
            extracted_fields = extracted_core_fields
            if employee_info.employee_id:
                total_fields += 1
                extracted_fields += 1
            
            extraction_rate = (extracted_fields / total_fields) * 100
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
            
            logger.info(f"\n📈 PERFORMANCE METRICS:")
            logger.info(f"   ⚡ Processing time: {processing_time:.2f}s")
            logger.info(f"   📊 Extraction rate: {extraction_rate:.1f}% ({extracted_fields}/{total_fields})")
            logger.info(f"   🎯 Average confidence: {avg_confidence:.2f}")
            logger.info(f"   📋 Employee tables found: {len(employee_data_tables)}")
            
            results.append({
                'file': pdf_file.name,
                'success': True,
                'extraction_rate': extraction_rate,
                'avg_confidence': avg_confidence,
                'processing_time': processing_time,
                'extracted_fields': extracted_fields,
                'employee_tables_found': len(employee_data_tables),
                'employee_info': employee_info
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_file.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'file': pdf_file.name,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            })
    
    # Summary
    logger.info(f"\n" + "=" * 70)
    logger.info("📊 EMPLOYEE EXTRACTION SUMMARY")
    logger.info("=" * 70)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    logger.info(f"✅ Successful extractions: {len(successful)}/{len(results)}")
    logger.info(f"❌ Failed extractions: {len(failed)}")
    
    if successful:
        avg_extraction_rate = sum(r['extraction_rate'] for r in successful) / len(successful)
        avg_confidence = sum(r['avg_confidence'] for r in successful) / len(successful)
        avg_processing_time = sum(r['processing_time'] for r in successful) / len(successful)
        total_employee_tables = sum(r['employee_tables_found'] for r in successful)
        
        logger.info(f"\n📊 AVERAGE METRICS:")
        logger.info(f"   📈 Extraction rate: {avg_extraction_rate:.1f}%")
        logger.info(f"   🎯 Confidence: {avg_confidence:.2f}")
        logger.info(f"   ⚡ Processing time: {avg_processing_time:.2f}s")
        logger.info(f"   📋 Employee tables found: {total_employee_tables}")
        
        logger.info(f"\n📋 DETAILED RESULTS:")
        for r in successful:
            logger.info(f"   {r['file']}: {r['extraction_rate']:.1f}% extraction, "
                       f"{r['avg_confidence']:.2f} confidence, {r['processing_time']:.1f}s")
    
    if failed:
        logger.info(f"\n❌ FAILED FILES:")
        for r in failed:
            logger.info(f"   {r['file']}: {r['error']}")
    
    # Success criteria
    success_rate = len(successful) / len(results) if results else 0
    avg_extraction_rate = sum(r['extraction_rate'] for r in successful) / len(successful) if successful else 0
    
    logger.info(f"\n🎯 FINAL ASSESSMENT:")
    logger.info(f"   Success rate: {success_rate:.1%}")
    logger.info(f"   Average extraction rate: {avg_extraction_rate:.1f}%")
    
    # Test criteria: 80% success rate, 92% average extraction rate for available fields
    if success_rate >= 0.8 and avg_extraction_rate >= 92:
        logger.info("🎉 EMPLOYEE EXTRACTOR TEST PASSED!")
        logger.info("   Ready to implement employer and salary extractors.")
        return True
    else:
        logger.warning("⚠️  Employee extractor needs improvement")
        if success_rate < 0.8:
            logger.warning(f"   - Success rate too low: {success_rate:.1%} (need 80%)")
        if avg_extraction_rate < 70:
            logger.warning(f"   - Extraction rate too low: {avg_extraction_rate:.1f}% (need 70%)")
        return False

if __name__ == "__main__":
    logger.info("EMPLOYEE EXTRACTOR REAL DOCUMENT TESTING")
    logger.info("=" * 70)
    
    test_passed = test_employee_extraction_on_real_docs()
    
    logger.info("\n" + "=" * 70)
    logger.info("🏆 TEST RESULTS")
    logger.info("=" * 70)
    logger.info(f"Employee Extractor Test: {'✅ PASS' if test_passed else '❌ FAIL'}")
    
    if test_passed:
        logger.info("🎉 Employee extraction working robustly!")
        logger.info("📋 Next: Implement employer information extractor")
        exit(0)
    else:
        logger.error("❌ Employee extractor needs fixes")
        exit(1)