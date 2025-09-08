#!/usr/bin/env python3
"""
Routing Coordinator
===================

Coordinates PART A and PART B table routing with multi-category scoring.
Integrates the PART A router (6-13 variable tables) with PART B router 
(1 consistent table) for comprehensive Form16 extraction routing.

Key Integration Points:
- PART A quarterly totals (₹5,261,194) for cross-validation
- PART B detailed breakdown (₹1,245,000 gross salary) 
- Multi-category scoring from Task 1.1 implementation
- Cross-validation framework between PART A ↔ PART B

TDD Implementation: RED → GREEN → REFACTOR
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

from form16_extractor.extractors.classification.part_a_router import PartARouter
from form16_extractor.extractors.classification.part_b_router import PartBRouter
from form16_extractor.extractors.classification.multi_category_classifier import MultiCategoryClassifier
from form16_extractor.pdf.table_classifier import TableType


@dataclass
class RoutingDecision:
    """Comprehensive routing decision combining PART A and PART B analysis"""
    table_index: int
    part_type: str  # 'PART_A' or 'PART_B'
    extractor_routes: Dict[str, Dict[str, float]]  # extractor -> {confidence, reasoning}
    cross_validation_data: Optional[Dict[str, Any]] = None
    routing_reasoning: str = ""


@dataclass
class CrossValidationData:
    """Cross-validation data between PART A quarterly and PART B detailed"""
    part_a_quarterly_total: Optional[float] = None
    part_b_gross_salary: Optional[float] = None
    variance_amount: Optional[float] = None
    variance_percentage: Optional[float] = None
    validation_status: str = "pending"  # pending, validated, discrepancy


class RoutingCoordinator:
    """
    Coordinates table routing between PART A and PART B routers.
    
    Integrates:
    - PART A Router: Quarterly totals and variable table handling
    - PART B Router: Detailed breakdown and consistent table handling  
    - Multi-Category Classifier: Domain-specific scoring from Task 1.1
    - Cross-Validation: PART A ↔ PART B salary total validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize routers
        self.part_a_router = PartARouter()
        self.part_b_router = PartBRouter()
        self.multi_category_classifier = MultiCategoryClassifier()
        
        # Cross-validation thresholds
        self.acceptable_variance_percentage = 5.0  # 5% variance acceptable
        self.high_confidence_threshold = 0.8
        self.minimum_routing_threshold = 0.4
        
        self.logger.info("Routing Coordinator initialized - integrating PART A & PART B routers")

    def coordinate_table_routing(self, tables: List[Dict[str, Any]]) -> List[RoutingDecision]:
        """
        Coordinate routing for all tables using both PART A and PART B routers.
        
        Args:
            tables: List of table information with classifications
            
        Returns:
            List of comprehensive routing decisions
        """
        routing_decisions = []
        part_a_tables = []
        part_b_tables = []
        
        # Separate tables by PART A/B classification
        for i, table_info in enumerate(tables):
            if self.part_a_router.should_handle_table(table_info):
                part_a_tables.append((i, table_info))
            elif self.part_b_router.should_handle_table(table_info):
                part_b_tables.append((i, table_info))
        
        self.logger.info(f"Routing coordination: {len(part_a_tables)} PART A tables, {len(part_b_tables)} PART B tables")
        
        # Route PART A tables
        for table_index, table_info in part_a_tables:
            routes = self.part_a_router.get_extraction_routes(table_info)
            
            # Enhance with multi-category scoring
            enhanced_routes = self._enhance_with_multi_category_scoring(table_info, routes)
            
            decision = RoutingDecision(
                table_index=table_index,
                part_type='PART_A',
                extractor_routes=enhanced_routes,
                routing_reasoning=f"PART A routing with {len(enhanced_routes)} extractors"
            )
            routing_decisions.append(decision)
        
        # Route PART B tables
        for table_index, table_info in part_b_tables:
            routes = self.part_b_router.get_extraction_routes(table_info)
            
            # Enhance with multi-category scoring
            enhanced_routes = self._enhance_with_multi_category_scoring(table_info, routes)
            
            decision = RoutingDecision(
                table_index=table_index,
                part_type='PART_B',
                extractor_routes=enhanced_routes,
                routing_reasoning=f"PART B routing with {len(enhanced_routes)} extractors"
            )
            routing_decisions.append(decision)
        
        # Add cross-validation data
        cross_validation = self._setup_cross_validation(part_a_tables, part_b_tables)
        if cross_validation:
            for decision in routing_decisions:
                decision.cross_validation_data = cross_validation
        
        return routing_decisions

    def get_extractor_routing_summary(self, routing_decisions: List[RoutingDecision]) -> Dict[str, List[int]]:
        """
        Generate summary of which tables route to which extractors.
        
        Args:
            routing_decisions: List of routing decisions
            
        Returns:
            Dict mapping extractor names to table indices
        """
        extractor_summary = {}
        
        for decision in routing_decisions:
            for extractor_name in decision.extractor_routes.keys():
                if extractor_name not in extractor_summary:
                    extractor_summary[extractor_name] = []
                extractor_summary[extractor_name].append(decision.table_index)
        
        # Log routing summary
        for extractor, table_indices in extractor_summary.items():
            self.logger.info(f"Extractor '{extractor}': routing {len(table_indices)} tables {table_indices}")
        
        return extractor_summary

    def validate_cross_part_consistency(self, routing_decisions: List[RoutingDecision]) -> CrossValidationData:
        """
        Validate consistency between PART A quarterly totals and PART B detailed breakdown.
        
        Args:
            routing_decisions: All routing decisions with cross-validation data
            
        Returns:
            Cross-validation results
        """
        part_a_quarterly_total = None
        part_b_gross_salary = None
        
        # Extract PART A quarterly totals
        for decision in routing_decisions:
            if decision.part_type == 'PART_A' and decision.cross_validation_data:
                cv_data = decision.cross_validation_data
                if 'quarterly_total' in cv_data:
                    part_a_quarterly_total = cv_data['quarterly_total']
                    break
        
        # Extract PART B gross salary
        for decision in routing_decisions:
            if decision.part_type == 'PART_B' and decision.cross_validation_data:
                cv_data = decision.cross_validation_data
                if 'gross_salary' in cv_data:
                    part_b_gross_salary = cv_data['gross_salary']
                    break
        
        # Calculate variance if both values available
        cross_validation = CrossValidationData(
            part_a_quarterly_total=part_a_quarterly_total,
            part_b_gross_salary=part_b_gross_salary
        )
        
        if part_a_quarterly_total and part_b_gross_salary:
            variance_amount = abs(part_a_quarterly_total - part_b_gross_salary)
            variance_percentage = (variance_amount / part_a_quarterly_total) * 100
            
            cross_validation.variance_amount = variance_amount
            cross_validation.variance_percentage = variance_percentage
            
            if variance_percentage <= self.acceptable_variance_percentage:
                cross_validation.validation_status = "validated"
                self.logger.info(f"Cross-validation PASSED: {variance_percentage:.1f}% variance (≤{self.acceptable_variance_percentage}%)")
            else:
                cross_validation.validation_status = "discrepancy"
                self.logger.warning(f"Cross-validation DISCREPANCY: {variance_percentage:.1f}% variance (>{self.acceptable_variance_percentage}%)")
        
        return cross_validation

    def _enhance_with_multi_category_scoring(self, table_info: Dict[str, Any], base_routes: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Enhance routing decisions with multi-category classifier scores"""
        table = table_info['table']
        
        # Get multi-category scores
        try:
            domain_scores = self.multi_category_classifier.score_table(table)
            
            # Enhance base routes with multi-category insights
            enhanced_routes = {}
            
            for extractor_name, route_info in base_routes.items():
                base_confidence = route_info['confidence']
                
                # Get corresponding domain score
                domain_score = 0.0
                if extractor_name == 'salary':
                    domain_score = domain_scores.salary_score
                elif extractor_name == 'tax':
                    domain_score = domain_scores.tax_score
                elif extractor_name == 'deductions':
                    domain_score = domain_scores.deduction_score
                elif extractor_name == 'identity':
                    domain_score = domain_scores.metadata_score  # Identity is part of metadata
                elif extractor_name == 'metadata':
                    domain_score = domain_scores.metadata_score
                
                # Combine base routing confidence with multi-category score
                combined_confidence = (base_confidence + domain_score) / 2.0
                combined_confidence = min(combined_confidence, 1.0)
                
                # Only include if above minimum threshold
                if combined_confidence >= self.minimum_routing_threshold:
                    enhanced_routes[extractor_name] = {
                        'confidence': combined_confidence,
                        'reasoning': f"{route_info['reasoning']} + Multi-category score: {domain_score:.2f}"
                    }
            
            return enhanced_routes
            
        except Exception as e:
            self.logger.warning(f"Multi-category scoring failed: {e}, using base routes")
            return base_routes

    def _setup_cross_validation(self, part_a_tables: List[Tuple[int, Dict]], part_b_tables: List[Tuple[int, Dict]]) -> Optional[Dict[str, Any]]:
        """Setup cross-validation data between PART A and PART B"""
        cross_validation_data = {}
        
        # Extract quarterly totals from PART A
        for table_index, table_info in part_a_tables:
            if self.part_a_router.is_quarterly_salary_table(table_info):
                quarterly_totals = self.part_a_router.extract_quarterly_totals(table_info)
                if quarterly_totals:
                    total_salary = sum(q.salary_paid for q in quarterly_totals)
                    cross_validation_data['quarterly_total'] = total_salary
                    break
        
        # Extract gross salary from PART B
        for table_index, table_info in part_b_tables:
            if self.part_b_router.is_salary_details_table(table_info):
                salary_details = self.part_b_router.extract_salary_details(table_info)
                if 'gross_salary' in salary_details:
                    cross_validation_data['gross_salary'] = salary_details['gross_salary']
                    break
        
        return cross_validation_data if cross_validation_data else None