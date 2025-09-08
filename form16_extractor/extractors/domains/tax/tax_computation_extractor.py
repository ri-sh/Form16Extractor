#!/usr/bin/env python3

"""
Simple Tax Extractor Component
==============================

Modular component extracted from simple_extractor.py tax logic.
This is NOT the comprehensive tax_computation.py extractor - this is specifically
the basic tax extraction logic from simple_extractor.py for modularization.
"""

import pandas as pd
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from form16_extractor.extractors.base.abstract_field_extractor import AbstractFieldExtractor
from form16_extractor.models.form16_models import TaxComputation
from form16_extractor.pdf.table_classifier import TableType


class SimpleTaxExtractorComponent(AbstractFieldExtractor):
    """Component for extracting tax data using simple_extractor.py logic"""
    
    def extract(self, tables_by_type: Dict, **kwargs) -> Tuple[Optional[TaxComputation], Dict[str, Any]]:
        """Extract tax data from classified tables using simple_extractor logic"""
        
        # Get tax computation tables (same as simple_extractor.py)
        tax_tables = (tables_by_type.get(TableType.PART_B_TAX_COMPUTATION, []) +
                     tables_by_type.get(TableType.PART_B_TAX_DEDUCTIONS, []) +
                     tables_by_type.get(TableType.PART_A_SUMMARY, []))
        
        return self._extract_tax_data(tax_tables)
    
    def _extract_tax_data(self, tax_tables: List[Dict[str, Any]]) -> Tuple[Optional[TaxComputation], Dict[str, Any]]:
        """Extract tax computation data from Part A Summary tables with enhanced precision (from simple_extractor.py)"""
        
        metadata = {'strategy': 'enhanced_semantic_search', 'tables_used': len(tax_tables), 'confidence': 0.7}
        
        extracted_values = {
            'gross_total_income': Decimal('0'),
            'tax_on_total_income': Decimal('0'),
            'health_education_cess': Decimal('0'), 
            'total_tax_liability': Decimal('0')
        }
        
        # Enhanced keyword patterns for more precise matching (exact from simple_extractor.py)
        tax_patterns = {
            'gross_total_income': [
                'gross total income', 'total income (as per itr)', 'total income',
                'gross income', 'taxable income'
            ],
            'tax_on_total_income': [
                'tax on total income', 'income tax', 'tax on income',
                'income tax payable', 'tax calculated on total income'
            ],
            'health_education_cess': [
                'health and education cess', 'education cess', 'cess @4%',
                'cess on income tax', 'health & education cess'
            ],
            'total_tax_liability': [
                'total tax liability', 'tax payable', 'total tax payable',
                'total tax and cess', 'aggregate tax liability'
            ]
        }
        
        extraction_quality_score = 0
        field_confidence_scores = {}
        
        # Search for tax computation values in summary tables (exact logic from simple_extractor.py)
        for table_info in tax_tables:
            table = table_info['table']
            
            # Enhanced extraction with position validation
            for field_name, patterns in tax_patterns.items():
                best_match_confidence = 0
                best_amount = None
                
                for i in range(len(table)):
                    for j in range(len(table.columns)):
                        cell_value = table.iloc[i, j]
                        if pd.isna(cell_value):
                            continue
                            
                        cell_text = str(cell_value).lower().strip()
                        
                        # Calculate match confidence for this cell
                        match_confidence = self._calculate_text_match_confidence(cell_text, patterns)
                        
                        if match_confidence > 0.6:  # High confidence text match
                            # Look for amount with enhanced nearby search
                            amount = self._find_enhanced_nearby_amount(table, i, j)
                            if amount and amount > 0:
                                # Validate amount is reasonable for tax computation
                                if self._validate_tax_amount(field_name, amount):
                                    if match_confidence > best_match_confidence:
                                        best_match_confidence = match_confidence
                                        best_amount = amount
                
                if best_amount:
                    extracted_values[field_name] = best_amount
                    field_confidence_scores[field_name] = best_match_confidence
                    extraction_quality_score += best_match_confidence
        
        # Create tax computation object (exact from simple_extractor.py)
        tax_computation = TaxComputation(
            gross_total_income=extracted_values['gross_total_income'],
            tax_on_total_income=extracted_values['tax_on_total_income'],
            health_education_cess=extracted_values['health_education_cess'],
            total_tax_liability=extracted_values['total_tax_liability']
        )
        
        # Enhanced confidence calculation with cross-validation (from simple_extractor.py)
        found_values = sum(1 for v in extracted_values.values() if v > 0)
        avg_field_confidence = (extraction_quality_score / len(tax_patterns)) if tax_patterns else 0
        
        # Cross-validation: check if values are logically consistent
        validation_bonus = self._validate_tax_computation_consistency(extracted_values)
        
        if found_values >= 3 and avg_field_confidence > 0.8:
            metadata['confidence'] = min(0.95, 0.85 + avg_field_confidence/5 + validation_bonus)
        elif found_values >= 2 and avg_field_confidence > 0.7:
            metadata['confidence'] = min(0.90, 0.75 + avg_field_confidence/4 + validation_bonus)
        else:
            metadata['confidence'] = min(0.80, 0.60 + avg_field_confidence/3 + validation_bonus)
        
        metadata['field_confidence_scores'] = field_confidence_scores
        metadata['validation_bonus'] = validation_bonus
        
        return tax_computation, metadata
    
    def _calculate_text_match_confidence(self, text: str, patterns: List[str]) -> float:
        """Calculate confidence score for text matching against patterns (exact from simple_extractor.py)"""
        
        if not patterns:
            return 0.0
        
        best_match = 0.0
        
        for pattern in patterns:
            # Exact match gets highest score
            if pattern.lower() == text.lower():
                return 1.0
            
            # Contains pattern gets high score
            if pattern.lower() in text.lower():
                score = 0.9
                # Bonus for shorter text (more precise match)
                if len(text) <= len(pattern) * 1.5:
                    score += 0.05
                best_match = max(best_match, score)
            
            # Pattern contains text (partial match)
            elif text.lower() in pattern.lower() and len(text) > 5:
                score = 0.7
                best_match = max(best_match, score)
            
            # Word overlap scoring
            else:
                text_words = set(text.lower().split())
                pattern_words = set(pattern.lower().split())
                
                if len(pattern_words) > 0:
                    overlap = len(text_words & pattern_words) / len(pattern_words)
                    if overlap >= 0.6:  # At least 60% word overlap
                        score = 0.6 + (overlap * 0.3)
                        best_match = max(best_match, score)
        
        return best_match
    
    def _find_enhanced_nearby_amount(self, table: pd.DataFrame, row: int, col: int) -> Optional[Decimal]:
        """Enhanced nearby amount search with better position scoring (exact from simple_extractor.py)"""
        
        candidates = []
        
        # Same row search (priority 1 - most common in Form16)
        for c in range(len(table.columns)):
            if c != col:
                cell_value = table.iloc[row, c]
                amount = self._parse_amount(cell_value)
                if amount and amount > 0:
                    # Calculate position score (right side columns get higher priority)
                    position_score = 1.0 + (c / len(table.columns)) * 0.2
                    candidates.append((Decimal(str(amount)), position_score, f"same_row_col_{c}"))
        
        # Adjacent rows search (priority 2)
        for r_offset in [-1, 1]:
            new_row = row + r_offset
            if 0 <= new_row < len(table):
                for c in range(len(table.columns)):
                    cell_value = table.iloc[new_row, c]
                    amount = self._parse_amount(cell_value)
                    if amount and amount > 0:
                        position_score = 0.8 + (c / len(table.columns)) * 0.1
                        candidates.append((Decimal(str(amount)), position_score, f"adjacent_row_{new_row}_col_{c}"))
        
        # Return highest scoring candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def _validate_tax_amount(self, field_name: str, amount: float) -> bool:
        """Validate that tax amount is reasonable for the field type (from simple_extractor.py)"""
        
        if amount <= 0:
            return False
        
        # Reasonable ranges for tax computation fields (in INR) - from simple_extractor.py
        field_ranges = {
            'gross_total_income': (50000, 50000000),      # 50K to 5CR 
            'tax_on_total_income': (0, 15000000),         # 0 to 1.5CR
            'health_education_cess': (0, 600000),         # 0 to 6L
            'total_tax_liability': (0, 15000000)          # 0 to 1.5CR
        }
        
        min_val, max_val = field_ranges.get(field_name, (0, 100000000))
        return min_val <= amount <= max_val
    
    def _validate_tax_computation_consistency(self, extracted_values: Dict[str, Decimal]) -> float:
        """Validate logical consistency between tax computation values (from simple_extractor.py)"""
        
        validation_bonus = 0.0
        
        gross_income = extracted_values.get('gross_total_income', Decimal('0'))
        tax_on_income = extracted_values.get('tax_on_total_income', Decimal('0'))
        cess = extracted_values.get('health_education_cess', Decimal('0'))
        total_liability = extracted_values.get('total_tax_liability', Decimal('0'))
        
        # Check if we have the key values
        if gross_income > 0 and tax_on_income > 0:
            # Tax should be reasonable percentage of income (5-35%)
            tax_rate = (tax_on_income / gross_income) * 100
            if 5 <= tax_rate <= 35:
                validation_bonus += 0.05
            
            # Cess should be ~4% of income tax
            if cess > 0:
                expected_cess = tax_on_income * Decimal('0.04')
                cess_diff = abs(cess - expected_cess) / expected_cess
                if cess_diff <= 0.1:  # Within 10%
                    validation_bonus += 0.05
        
        # Total liability should be sum of components
        if total_liability > 0 and tax_on_income > 0:
            expected_total = tax_on_income + (cess or Decimal('0'))
            if abs(total_liability - expected_total) <= expected_total * Decimal('0.1'):  # Within 10%
                validation_bonus += 0.05
        
        return validation_bonus
    
    # Required abstract methods from AbstractFieldExtractor
    
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Select tables relevant for tax computation extraction"""
        relevant_tables = []
        
        # Priority order for tax computation tables
        table_priorities = [
            TableType.PART_B_TAX_COMPUTATION,
            TableType.PART_B_TAX_DEDUCTIONS, 
            TableType.PART_A_SUMMARY
        ]
        
        for table_type in table_priorities:
            if table_type in tables_by_type:
                relevant_tables.extend(tables_by_type[table_type])
        
        return relevant_tables
    
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract raw tax computation data from tables"""
        tax_computation, metadata = self._extract_tax_data(tables)
        
        # Convert tax computation object back to dict for consistency with abstract interface
        return {
            'gross_total_income': tax_computation.gross_total_income,
            'tax_on_total_income': tax_computation.tax_on_total_income,
            'health_education_cess': tax_computation.health_education_cess,
            'total_tax_liability': tax_computation.total_tax_liability,
            'metadata': metadata
        }
    
    def create_model(self, data: Dict[str, Any]) -> TaxComputation:
        """Create TaxComputation model from extracted data"""
        return TaxComputation(
            gross_total_income=data.get('gross_total_income', Decimal('0')),
            tax_on_total_income=data.get('tax_on_total_income', Decimal('0')),
            health_education_cess=data.get('health_education_cess', Decimal('0')),
            total_tax_liability=data.get('total_tax_liability', Decimal('0'))
        )
    
    def get_strategy_name(self) -> str:
        """Return strategy name for metadata"""
        return "simple_tax_extraction"