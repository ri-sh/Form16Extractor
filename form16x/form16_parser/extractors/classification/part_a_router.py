#!/usr/bin/env python3
"""
PART A Table Router
===================

Routes PART A tables (quarterly totals, summaries) to appropriate extractors.
Handles the 6-13 variable table structure in PART A containing quarterly 
salary totals (₹5,261,194) critical for cross-validation with PART B.

Key Insights from Multi-Form16 Analysis:
- PART A contains quarterly salary totals for validation
- 6-13 variable tables per form (vs 1 consistent PART B table)
- 87.9% of PART A tables contain salary data but classified as "mixed"
- Critical for mathematical cross-validation: PART A quarterly vs PART B detailed

TDD Implementation: RED → GREEN → REFACTOR
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

from form16x.form16_parser.pdf.table_classifier import TableType


@dataclass
class PartARoute:
    """Routing decision for a PART A table"""
    table_index: int
    extractors: List[str]  # List of extractor names to route to
    confidence_scores: Dict[str, float]  # Confidence for each extractor
    quarterly_totals: Optional[Dict[str, float]] = None  # Extracted quarterly data
    reasoning: str = ""


@dataclass
class QuarterlyTotal:
    """Quarterly salary total extracted from PART A"""
    quarter: str
    salary_paid: float
    tax_deducted: float
    net_salary: Optional[float] = None


class PartARouter:
    """
    Router for PART A tables containing quarterly totals and summaries.
    
    Handles:
    - Quarterly salary tables (₹5,261,194 total validation)
    - Summary tables with annual totals
    - Mixed content tables with salary components
    - Variable table count (6-13 tables per form)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # PART A specific patterns
        self.quarterly_patterns = [
            r'q[1-4]\s+\d{4}[-/]\d{2,4}',  # Q1 2023-24, Q1 2023/24
            r'quarter\s*[1-4]',             # Quarter 1, Quarter 2
            r'apr[-/]jun|jul[-/]sep|oct[-/]dec|jan[-/]mar',  # Monthly ranges
        ]
        
        self.salary_total_patterns = [
            r'salary\s+paid',
            r'gross\s+salary',
            r'total\s+salary',
            r'annual\s+salary'
        ]
        
        self.summary_patterns = [
            r'gross\s+total\s+income',
            r'total\s+income',
            r'taxable\s+income',
            r'deductions?\s+under\s+chapter\s+vi[-a]?'
        ]
        
        # Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.medium_confidence_threshold = 0.5
        self.minimum_routing_threshold = 0.4
        
        self.logger.info("PART A Router initialized for quarterly table routing")

    def should_handle_table(self, table_info: Dict[str, Any]) -> bool:
        """
        Determine if this table should be handled by PART A router.
        
        Args:
            table_info: Table information with classification
            
        Returns:
            True if this is a PART A table, False otherwise
        """
        classification = table_info.get('classification')
        if not classification:
            return False
            
        table_type = classification.table_type
        
        # Handle PART A specific table types
        part_a_types = {
            TableType.PART_A_SUMMARY,
            TableType.HEADER_METADATA,  # Sometimes contains PART A info
            TableType.QUARTERLY_TDS     # Often contains PART A quarterly data
        }
        
        is_part_a_type = table_type in part_a_types
        
        # Additional content-based check for misclassified tables
        if not is_part_a_type:
            table = table_info['table']
            is_part_a_content = self._has_part_a_content(table)
            return is_part_a_content
            
        return is_part_a_type

    def is_quarterly_salary_table(self, table_info: Dict[str, Any]) -> bool:
        """Check if table contains quarterly salary data"""
        table = table_info['table']
        
        # Check for quarterly patterns in column names and values
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for quarterly patterns
        has_quarterly = any(
            re.search(pattern, all_text, re.IGNORECASE) 
            for pattern in self.quarterly_patterns
        )
        
        # Look for salary amount patterns
        has_salary = any(
            re.search(pattern, all_text, re.IGNORECASE)
            for pattern in self.salary_total_patterns
        )
        
        return has_quarterly and has_salary

    def is_summary_table(self, table_info: Dict[str, Any]) -> bool:
        """Check if table contains PART A summary data"""
        table = table_info['table']
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for summary patterns
        return any(
            re.search(pattern, all_text, re.IGNORECASE)
            for pattern in self.summary_patterns
        )

    def get_extraction_routes(self, table_info: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Determine which extractors should process this PART A table.
        
        Args:
            table_info: Table information
            
        Returns:
            Dict mapping extractor names to confidence scores
        """
        routes = {}
        
        if not self.should_handle_table(table_info):
            return routes
            
        table = table_info['table']
        
        # Analyze content for routing
        salary_score = self._calculate_salary_relevance(table)
        tax_score = self._calculate_tax_relevance(table)
        metadata_score = self._calculate_metadata_relevance(table)
        
        # Route to extractors based on confidence thresholds
        if salary_score >= self.minimum_routing_threshold:
            routes['salary'] = {
                'confidence': salary_score,
                'reasoning': 'PART A quarterly/summary salary data'
            }
            
        if tax_score >= self.minimum_routing_threshold:
            routes['tax'] = {
                'confidence': tax_score,
                'reasoning': 'PART A tax deduction totals'
            }
            
        if metadata_score >= self.minimum_routing_threshold:
            routes['metadata'] = {
                'confidence': metadata_score,
                'reasoning': 'PART A summary metadata'
            }
        
        return routes

    def extract_quarterly_totals(self, table_info: Dict[str, Any]) -> List[QuarterlyTotal]:
        """
        Extract quarterly salary totals from PART A table.
        
        Args:
            table_info: Table containing quarterly data
            
        Returns:
            List of quarterly totals for cross-validation
        """
        if not self.is_quarterly_salary_table(table_info):
            return []
            
        table = table_info['table']
        quarterly_totals = []
        
        # Try to identify quarterly data structure
        for idx, row in table.iterrows():
            row_text = ' '.join([str(val).lower() for val in row if pd.notna(val)])
            
            # Look for quarterly indicators
            quarter_match = None
            for pattern in self.quarterly_patterns:
                match = re.search(pattern, row_text, re.IGNORECASE)
                if match:
                    quarter_match = match.group(0)
                    break
                    
            if quarter_match:
                # Extract amounts from this row
                amounts = []
                for val in row:
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 1000:
                        amounts.append(float(val))
                        
                if amounts:
                    # Assume first large amount is salary, second is tax
                    salary_paid = amounts[0]
                    tax_deducted = amounts[1] if len(amounts) > 1 else 0.0
                    
                    quarterly_total = QuarterlyTotal(
                        quarter=quarter_match,
                        salary_paid=salary_paid,
                        tax_deducted=tax_deducted,
                        net_salary=salary_paid - tax_deducted if tax_deducted > 0 else None
                    )
                    quarterly_totals.append(quarterly_total)
        
        return quarterly_totals

    def get_routing_confidence(self, table_info: Dict[str, Any], extractor_name: str) -> float:
        """Get routing confidence for specific extractor"""
        routes = self.get_extraction_routes(table_info)
        
        if extractor_name in routes:
            return routes[extractor_name]['confidence']
        return 0.0

    def route_part_a_tables(self, table_infos: List[Dict[str, Any]]) -> Dict[str, List[PartARoute]]:
        """
        Route multiple PART A tables to extractors.
        
        Handles variable table count (6-13 tables per form).
        
        Args:
            table_infos: List of PART A table information
            
        Returns:
            Dict mapping extractor names to list of routes
        """
        routes_by_extractor = {}
        
        for i, table_info in enumerate(table_infos):
            if not self.should_handle_table(table_info):
                continue
                
            # Get routing decisions for this table
            extraction_routes = self.get_extraction_routes(table_info)
            
            if not extraction_routes:
                continue
                
            # Extract quarterly totals if available
            quarterly_totals = {}
            if self.is_quarterly_salary_table(table_info):
                qtotals = self.extract_quarterly_totals(table_info)
                if qtotals:
                    quarterly_totals = {
                        'quarters': [q.quarter for q in qtotals],
                        'total_salary': sum(q.salary_paid for q in qtotals),
                        'total_tax': sum(q.tax_deducted for q in qtotals)
                    }
                    
            # Create route for each extractor
            for extractor_name, route_info in extraction_routes.items():
                route = PartARoute(
                    table_index=i,
                    extractors=[extractor_name],
                    confidence_scores={extractor_name: route_info['confidence']},
                    quarterly_totals=quarterly_totals if quarterly_totals else None,
                    reasoning=route_info['reasoning']
                )
                
                if extractor_name not in routes_by_extractor:
                    routes_by_extractor[extractor_name] = []
                routes_by_extractor[extractor_name].append(route)
        
        self.logger.info(
            f"PART A routing completed: {len(table_infos)} tables processed, "
            f"{len(routes_by_extractor)} extractors routed"
        )
        
        return routes_by_extractor

    def _has_part_a_content(self, table: pd.DataFrame) -> bool:
        """Check if table has PART A specific content patterns"""
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for PART A indicators
        part_a_indicators = [
            r'part\s*a',
            r'quarterly',
            r'gross\s+total\s+income',
            r'deductions?\s+under\s+chapter'
        ]
        
        return any(
            re.search(pattern, all_text, re.IGNORECASE)
            for pattern in part_a_indicators
        )

    def _calculate_salary_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for salary extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Salary keywords
        salary_keywords = [
            ('salary', 0.3),
            ('gross', 0.2),
            ('basic', 0.2),
            ('allowance', 0.2),
            ('quarterly', 0.1),
            ('annual', 0.1)
        ]
        
        for keyword, weight in salary_keywords:
            if keyword in all_text:
                score += weight
                
        # Presence of large amounts (likely salary figures)
        for val in table.values.flatten():
            if pd.notna(val) and isinstance(val, (int, float)):
                if 50000 <= val <= 10000000:  # Reasonable salary range
                    score += 0.1
                    
        return min(score, 1.0)

    def _calculate_tax_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for tax extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Tax keywords
        tax_keywords = [
            ('tax', 0.4),
            ('tds', 0.3),
            ('deducted', 0.2),
            ('chapter', 0.1)
        ]
        
        for keyword, weight in tax_keywords:
            if keyword in all_text:
                score += weight
                
        return min(score, 1.0)

    def _calculate_metadata_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for metadata extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Metadata keywords
        metadata_keywords = [
            ('total', 0.2),
            ('income', 0.2),
            ('assessment', 0.2),
            ('year', 0.1),
            ('summary', 0.1)
        ]
        
        for keyword, weight in metadata_keywords:
            if keyword in all_text:
                score += weight
                
        return min(score, 1.0)