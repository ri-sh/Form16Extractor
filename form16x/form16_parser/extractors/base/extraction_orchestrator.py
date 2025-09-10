#!/usr/bin/env python3
"""
Extraction Orchestrator - GREEN PHASE Implementation
====================================================

Multi-extractor routing system to fix ₹10.82M salary under-extraction.
Routes tables to multiple extractors based on domain relevance scores.

This is the minimum implementation to make tests pass (GREEN phase).
Security: Uses only synthetic test data, no real PII or financial information.
"""

import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd

from ..classification.multi_category_classifier import MultiCategoryClassifier, DomainScore


class ExtractionOrchestrator:
    """
    Orchestrates multi-extractor routing to fix salary under-extraction.
    
    CRITICAL FIX: Routes "mixed" tables to multiple extractors instead of ignoring them.
    Addresses root cause: 87.9% salary data lost due to single-extractor routing.
    """
    
    def __init__(self):
        """Initialize orchestrator with classifier and empty extractor registry"""
        self.classifier = MultiCategoryClassifier()
        self.extractors: Dict[str, Any] = {}
        
        # Performance and lineage tracking
        self.performance_metrics = {
            'tables_processed': 0,
            'total_extractions': 0,
            'processing_times': [],
            'routes_distribution': defaultdict(int)
        }
        self.extraction_lineage: List[Dict] = []
    
    def register_extractor(self, domain: str, extractor: Any) -> None:
        """
        Register an extractor for a specific domain.
        
        Args:
            domain: Domain name (salary, perquisite, metadata, etc.)
            extractor: Extractor instance with extract() method
        """
        self.extractors[domain] = extractor
    
    def process_table(self, table: pd.DataFrame, threshold: float = 0.4) -> Dict[str, Any]:
        """
        Process table through multiple extractors based on domain scores.
        
        CORE METHOD: This fixes the ₹10.82M under-extraction by routing
        tables to ALL relevant extractors instead of just one.
        
        Args:
            table: Input table to process
            threshold: Minimum score to route to extractor
            
        Returns:
            Dict with results from all relevant extractors
        """
        start_time = time.time()
        
        # Score table across all domains
        scores = self.classifier.score_table(table)
        
        # Get routes based on scores
        routes = self.classifier.get_extractor_routes(scores, threshold)
        
        # Process through all relevant extractors
        results = {}
        errors = []
        extractors_called = []
        
        for route in routes:
            if route in self.extractors:
                try:
                    # Call extractor
                    extractor_result = self.extractors[route].extract(table)
                    results[route] = extractor_result
                    extractors_called.append(route)
                    
                    # Update metrics
                    self.performance_metrics['routes_distribution'][route] += 1
                    
                except Exception as e:
                    errors.append(f"Error in {route} extractor: {str(e)}")
            else:
                errors.append(f"{route} extractor not registered")
        
        # Include errors in results if any
        if errors:
            results['errors'] = errors
        
        # Track lineage for debugging
        lineage_entry = {
            'timestamp': time.time(),
            'table_shape': table.shape,
            'domain_scores': {
                'salary': scores.salary_score,
                'perquisite': scores.perquisite_score,
                'tax': scores.tax_score,
                'metadata': scores.metadata_score,
                'deduction': scores.deduction_score
            },
            'routes_taken': routes,
            'extractors_called': extractors_called,
            'threshold_used': threshold
        }
        self.extraction_lineage.append(lineage_entry)
        
        # Update performance metrics
        processing_time = time.time() - start_time
        self.performance_metrics['tables_processed'] += 1
        self.performance_metrics['total_extractions'] += len(extractors_called)
        self.performance_metrics['processing_times'].append(processing_time)
        
        return results
    
    def process_batch(self, tables: List[pd.DataFrame], threshold: float = 0.4) -> List[Dict[str, Any]]:
        """
        Process multiple tables in batch.
        
        Args:
            tables: List of tables to process
            threshold: Minimum score threshold
            
        Returns:
            List of results, one per table
        """
        batch_results = []
        
        for table in tables:
            result = self.process_table(table, threshold)
            batch_results.append(result)
            
        return batch_results
    
    def get_extraction_lineage(self, table: pd.DataFrame) -> Optional[Dict]:
        """
        Get extraction lineage for debugging under-extraction.
        
        Args:
            table: Table to get lineage for
            
        Returns:
            Lineage information for the table
        """
        # For simplicity, return the latest lineage entry
        # In production, this would match by table hash/signature
        if self.extraction_lineage:
            return self.extraction_lineage[-1]
        return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring.
        
        Returns:
            Performance metrics dictionary
        """
        # Calculate averages
        avg_processing_time = 0
        if self.performance_metrics['processing_times']:
            avg_processing_time = sum(self.performance_metrics['processing_times']) / len(self.performance_metrics['processing_times'])
        
        return {
            'tables_processed': self.performance_metrics['tables_processed'],
            'total_extractions': self.performance_metrics['total_extractions'],
            'average_processing_time': avg_processing_time,
            'routes_distribution': dict(self.performance_metrics['routes_distribution'])
        }