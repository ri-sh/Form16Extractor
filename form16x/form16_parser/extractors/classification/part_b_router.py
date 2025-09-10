#!/usr/bin/env python3
"""
PART B Table Router
===================

Routes PART B tables (detailed breakdowns) to appropriate extractors.
Handles the 1 consistent table structure in PART B containing detailed 
salary breakdown critical for primary extraction.

Key Insights from Multi-Form16 Analysis:
- PART B contains 1 consistent detailed salary table per form  
- Primary source for salary component extraction (basic, perquisites, gross)
- Must integrate with PART A quarterly totals for cross-validation
- More structured and predictable than PART A (6-13 variable tables)

TDD Implementation: RED → GREEN → REFACTOR
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

from form16x.form16_parser.pdf.table_classifier import TableType


@dataclass
class PartBRoute:
    """Routing decision for a PART B table"""
    table_index: int
    extractors: List[str]  # List of extractor names to route to
    confidence_scores: Dict[str, float]  # Confidence for each extractor
    salary_details: Optional[Dict[str, float]] = None  # Extracted detailed breakdown
    reasoning: str = ""


@dataclass
class SalaryDetails:
    """Detailed salary breakdown extracted from PART B"""
    basic_salary: float
    perquisites: float
    profits_in_lieu: float
    gross_salary: float
    allowances: Optional[float] = None


class PartBRouter:
    """
    Router for PART B tables containing detailed salary breakdowns.
    
    Handles:
    - Primary salary details table (section 17 breakdown)
    - Employer-employee identity information
    - Tax computation tables  
    - Section 80 deductions tables
    - Single consistent table structure per form
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # PART B specific patterns
        self.salary_section_patterns = [
            r'section\s+17\(1\)',           # Basic salary under section 17(1)
            r'perquisites?\s+u[/\\]s\s+17\(2\)',  # Perquisites under section 17(2)
            r'profits?\s+in\s+lieu.*17\(3\)',     # Profits in lieu under section 17(3)
            r'gross\s+salary',              # Gross salary total
        ]
        
        self.tax_computation_patterns = [
            r'gross\s+total\s+income',
            r'deductions?\s+under\s+chapter\s+vi[-a]?',
            r'total\s+income',
            r'tax\s+on\s+total\s+income'
        ]
        
        self.deduction_section_patterns = [
            r'section\s+80[a-z]',           # 80C, 80D, etc.
            r'life\s+insurance',            # Common 80C items
            r'medical\s+insurance',         # Common 80D items
            r'charitable\s+donation'        # Common 80G items
        ]
        
        self.identity_patterns = [
            r'employee.*name',
            r'employer.*name',
            r'pan\b',
            r'tan\b',
            r'address'
        ]
        
        # Confidence thresholds (higher than PART A due to structured nature)
        self.high_confidence_threshold = 0.9
        self.medium_confidence_threshold = 0.7
        self.minimum_routing_threshold = 0.5
        
        self.logger.info("PART B Router initialized for detailed table routing")

    def should_handle_table(self, table_info: Dict[str, Any]) -> bool:
        """
        Determine if this table should be handled by PART B router.
        
        Args:
            table_info: Table information with classification
            
        Returns:
            True if this is a PART B table, False otherwise
        """
        classification = table_info.get('classification')
        if not classification:
            return False
            
        table_type = classification.table_type
        
        # Handle PART B specific table types
        part_b_types = {
            TableType.PART_B_SALARY_DETAILS,     # Primary salary breakdown
            TableType.PART_B_EMPLOYER_EMPLOYEE,  # Identity information
            TableType.PART_B_TAX_COMPUTATION,    # Tax calculation  
            TableType.PART_B_TAX_DEDUCTIONS,     # Section 80 deductions
            TableType.FORM_12BA_PERQUISITES      # Perquisites details
        }
        
        is_part_b_type = table_type in part_b_types
        
        # Additional content-based check for misclassified tables
        if not is_part_b_type:
            table = table_info['table']
            is_part_b_content = self._has_part_b_content(table)
            return is_part_b_content
            
        return is_part_b_type

    def is_salary_details_table(self, table_info: Dict[str, Any]) -> bool:
        """Check if table contains PART B salary details (section 17 breakdown)"""
        table = table_info['table']
        
        # Check for section 17 patterns in column names and values
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for section 17 salary patterns
        section_17_matches = sum(
            1 for pattern in self.salary_section_patterns
            if re.search(pattern, all_text, re.IGNORECASE)
        )
        
        # Should have at least 2 section 17 patterns (basic + perquisites minimum)
        return section_17_matches >= 2

    def is_identity_table(self, table_info: Dict[str, Any]) -> bool:
        """Check if table contains employer-employee identity information"""
        table = table_info['table']
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for identity patterns
        identity_matches = sum(
            1 for pattern in self.identity_patterns
            if re.search(pattern, all_text, re.IGNORECASE)
        )
        
        # Should have at least 2 identity patterns (employee + employer minimum)  
        return identity_matches >= 2

    def get_extraction_routes(self, table_info: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Determine which extractors should process this PART B table.
        
        Args:
            table_info: Table information
            
        Returns:
            Dict mapping extractor names to confidence scores
        """
        routes = {}
        
        if not self.should_handle_table(table_info):
            return routes
            
        table = table_info['table']
        classification = table_info.get('classification')
        table_type = classification.table_type if classification else None
        
        # Route based on table type with high confidence (PART B is structured)
        if table_type == TableType.PART_B_SALARY_DETAILS:
            routes['salary'] = {
                'confidence': 0.95,
                'reasoning': 'PART B detailed salary breakdown (section 17)'
            }
        elif table_type == TableType.PART_B_EMPLOYER_EMPLOYEE:
            routes['identity'] = {
                'confidence': 0.9,
                'reasoning': 'PART B employer-employee identity information'
            }
        elif table_type == TableType.PART_B_TAX_COMPUTATION:
            routes['tax'] = {
                'confidence': 0.9,
                'reasoning': 'PART B tax computation table'
            }
        elif table_type == TableType.PART_B_TAX_DEDUCTIONS:
            routes['deductions'] = {
                'confidence': 0.9,
                'reasoning': 'PART B section 80 deductions'
            }
        elif table_type == TableType.FORM_12BA_PERQUISITES:
            routes['salary'] = {
                'confidence': 0.85,
                'reasoning': 'PART B perquisites details (Form 12BA)'
            }
        else:
            # Fallback to content analysis for misclassified tables
            salary_score = self._calculate_salary_relevance(table)
            tax_score = self._calculate_tax_relevance(table)
            deductions_score = self._calculate_deductions_relevance(table)
            identity_score = self._calculate_identity_relevance(table)
            
            # Route to extractors based on confidence thresholds
            if salary_score >= self.minimum_routing_threshold:
                routes['salary'] = {
                    'confidence': salary_score,
                    'reasoning': 'PART B salary content analysis'
                }
                
            if tax_score >= self.minimum_routing_threshold:
                routes['tax'] = {
                    'confidence': tax_score,
                    'reasoning': 'PART B tax content analysis'
                }
                
            if deductions_score >= self.minimum_routing_threshold:
                routes['deductions'] = {
                    'confidence': deductions_score,
                    'reasoning': 'PART B deductions content analysis'
                }
                
            if identity_score >= self.minimum_routing_threshold:
                routes['identity'] = {
                    'confidence': identity_score,
                    'reasoning': 'PART B identity content analysis'
                }
        
        return routes

    def extract_salary_details(self, table_info: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract detailed salary breakdown from PART B salary table.
        
        Args:
            table_info: Table containing section 17 salary breakdown
            
        Returns:
            Dict with detailed salary components
        """
        if not self.is_salary_details_table(table_info):
            return {}
            
        table = table_info['table']
        salary_details = {}
        
        # Search for section 17 components in table
        for idx, row in table.iterrows():
            row_text = ' '.join([str(val).lower() for val in row if pd.notna(val)])
            
            # Extract amounts from this row
            amounts = []
            for val in row:
                if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                    amounts.append(float(val))
            
            if not amounts:
                continue
                
            amount = amounts[0]  # Usually first amount column
            
            # Match against salary component patterns
            if re.search(r'section\s+17\(1\)', row_text, re.IGNORECASE):
                salary_details['basic_salary'] = amount
            elif re.search(r'perquisites?\s+u[/\\]s\s+17\(2\)', row_text, re.IGNORECASE):
                salary_details['perquisites'] = amount
            elif re.search(r'profits?\s+in\s+lieu.*17\(3\)', row_text, re.IGNORECASE):
                salary_details['profits_in_lieu'] = amount
            elif re.search(r'gross\s+salary', row_text, re.IGNORECASE):
                salary_details['gross_salary'] = amount
        
        return salary_details

    def get_routing_confidence(self, table_info: Dict[str, Any], extractor_name: str) -> float:
        """Get routing confidence for specific extractor"""
        routes = self.get_extraction_routes(table_info)
        
        if extractor_name in routes:
            return routes[extractor_name]['confidence']
        return 0.0

    def route_part_b_tables(self, table_infos: List[Dict[str, Any]]) -> Dict[str, List[PartBRoute]]:
        """
        Route PART B tables to extractors.
        
        Handles single consistent table structure (vs PART A's 6-13 variables).
        
        Args:
            table_infos: List of PART B table information
            
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
                
            # Extract salary details if available
            salary_details = {}
            if self.is_salary_details_table(table_info):
                details = self.extract_salary_details(table_info)
                if details:
                    salary_details = details
                    
            # Create route for each extractor
            for extractor_name, route_info in extraction_routes.items():
                route = PartBRoute(
                    table_index=i,
                    extractors=[extractor_name],
                    confidence_scores={extractor_name: route_info['confidence']},
                    salary_details=salary_details if salary_details else None,
                    reasoning=route_info['reasoning']
                )
                
                if extractor_name not in routes_by_extractor:
                    routes_by_extractor[extractor_name] = []
                routes_by_extractor[extractor_name].append(route)
        
        self.logger.info(
            f"PART B routing completed: {len(table_infos)} tables processed, "
            f"{len(routes_by_extractor)} extractors routed"
        )
        
        return routes_by_extractor

    def _has_part_b_content(self, table: pd.DataFrame) -> bool:
        """Check if table has PART B specific content patterns"""
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Look for PART B indicators
        part_b_indicators = [
            r'part\s*b',
            r'section\s+17',
            r'gross\s+salary',
            r'tax\s+computation',
            r'section\s+80'
        ]
        
        return any(
            re.search(pattern, all_text, re.IGNORECASE)
            for pattern in part_b_indicators
        )

    def _calculate_salary_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for salary extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Salary keywords (higher weights for PART B specific terms)
        salary_keywords = [
            ('section 17', 0.4),    # Primary PART B indicator
            ('gross salary', 0.3),
            ('perquisites', 0.2),
            ('basic salary', 0.2),
            ('allowance', 0.1)
        ]
        
        for keyword, weight in salary_keywords:
            if keyword in all_text:
                score += weight
                
        # Presence of salary-range amounts
        for val in table.values.flatten():
            if pd.notna(val) and isinstance(val, (int, float)):
                if 100000 <= val <= 10000000:  # Typical annual salary range
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
            ('tax computation', 0.5),
            ('total income', 0.3),
            ('tax on', 0.2),
            ('gross total income', 0.3),
            ('chapter vi', 0.2)
        ]
        
        for keyword, weight in tax_keywords:
            if keyword in all_text:
                score += weight
                
        return min(score, 1.0)

    def _calculate_deductions_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for deductions extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Deductions keywords
        deduction_keywords = [
            ('section 80', 0.4),
            ('deductions', 0.3),
            ('life insurance', 0.2),
            ('medical insurance', 0.2),
            ('charitable', 0.1)
        ]
        
        for keyword, weight in deduction_keywords:
            if keyword in all_text:
                score += weight
                
        return min(score, 1.0)

    def _calculate_identity_relevance(self, table: pd.DataFrame) -> float:
        """Calculate relevance score for identity extraction"""
        score = 0.0
        
        all_text = ' '.join([
            str(col).lower() for col in table.columns
        ] + [
            str(val).lower() for val in table.values.flatten() if pd.notna(val)
        ])
        
        # Identity keywords
        identity_keywords = [
            ('employee', 0.3),
            ('employer', 0.3),
            ('pan', 0.2),
            ('tan', 0.2),
            ('address', 0.1),
            ('name', 0.1)
        ]
        
        for keyword, weight in identity_keywords:
            if keyword in all_text:
                score += weight
                
        return min(score, 1.0)