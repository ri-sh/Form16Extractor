#!/usr/bin/env python3
"""
Table Classification System
===========================

Classifies Form16 tables by type and content to improve extraction accuracy.
Uses structure-based patterns to identify table types without relying on data.
"""

import logging
import re
from enum import Enum
from typing import List, Dict, Optional, Tuple
import pandas as pd
from dataclasses import dataclass


class TableType(Enum):
    """Form16 table types based on structure analysis"""
    PART_A_SUMMARY = "part_a_summary"           # TDS summary table
    PART_B_EMPLOYER_EMPLOYEE = "part_b_employer_employee"  # Side-by-side info
    PART_B_SALARY_DETAILS = "part_b_salary_details"       # Salary breakdown
    PART_B_TAX_DEDUCTIONS = "part_b_tax_deductions"       # 80C, 80D etc.
    PART_B_TAX_COMPUTATION = "part_b_tax_computation"     # Tax calculation
    FORM_12BA_PERQUISITES = "form_12ba_perquisites"       # Perquisites details
    QUARTERLY_TDS = "quarterly_tds"              # Quarterly breakdown
    VERIFICATION_SECTION = "verification_section" # Signature/verification
    HEADER_METADATA = "header_metadata"          # Form headers
    UNKNOWN = "unknown"                          # Unclassified


@dataclass
class TableClassification:
    """Result of table classification"""
    table_type: TableType
    confidence: float
    features_matched: List[str]
    row_count: int
    col_count: int
    has_amounts: bool
    metadata: Dict[str, any]


class Form16TableClassifier:
    """Classify Form16 tables by structure and content patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Classification patterns based on real Form16 analysis
        self.classification_patterns = {
            TableType.PART_A_SUMMARY: {
                'required_headers': [
                    'amount of salary paid',
                    'amount of tax deducted',
                    'total amount paid'
                ],
                'alternative_headers': [
                    'salary paid',
                    'tax deducted',
                    'tds amount'
                ],
                'structure_hints': [
                    'part a',
                    'certificate under section 203',
                    'tax deducted at source'
                ],
                'min_numeric_cols': 2,
                'expected_rows': (3, 15)
            },
            
            TableType.PART_B_EMPLOYER_EMPLOYEE: {
                'required_headers': [
                    'name and address of the employer',
                    'name and address of the employee'
                ],
                'alternative_headers': [
                    'employer name',
                    'employee name',
                    'deductor name'
                ],
                'structure_hints': [
                    'part b',
                    'tan of',
                    'pan of'
                ],
                'min_numeric_cols': 0,
                'expected_rows': (2, 10)
            },
            
            TableType.PART_B_SALARY_DETAILS: {
                'required_headers': [
                    'salary as per provisions',
                    'basic salary',
                    'gross salary'
                ],
                'alternative_headers': [
                    'allowances',
                    'hra received',
                    'perquisites',
                    'section 17'
                ],
                'structure_hints': [
                    'section 17(1)',
                    'section 17(2)',
                    'section 17(3)',
                    'salary breakdown'
                ],
                'min_numeric_cols': 1,
                'expected_rows': (5, 25)
            },
            
            TableType.PART_B_TAX_DEDUCTIONS: {
                'required_headers': [
                    'deduction under chapter vi-a',
                    'section 80c',
                    'section 80d'
                ],
                'alternative_headers': [
                    'chapter vi',
                    '80c amount',
                    'deductions claimed'
                ],
                'structure_hints': [
                    'chapter vi-a',
                    'section 80',
                    'deduction under'
                ],
                'min_numeric_cols': 1,
                'expected_rows': (3, 20)
            },
            
            TableType.PART_B_TAX_COMPUTATION: {
                'required_headers': [
                    'tax on total income',
                    'total tax liability',
                    'tax payable'
                ],
                'alternative_headers': [
                    'income tax',
                    'surcharge',
                    'education cess',
                    'rebate'
                ],
                'structure_hints': [
                    'tax computation',
                    'tax payable',
                    'rebate under section'
                ],
                'min_numeric_cols': 1,
                'expected_rows': (5, 15)
            },
            
            TableType.QUARTERLY_TDS: {
                'required_headers': [
                    'quarter',
                    'amount of tax deducted',
                    'amount of tax deposited'
                ],
                'alternative_headers': [
                    'q1', 'q2', 'q3', 'q4',
                    'receipt number',
                    'challan'
                ],
                'structure_hints': [
                    'quarterly details',
                    'deposit date',
                    'bsr code'
                ],
                'min_numeric_cols': 1,
                'expected_rows': (4, 8)
            },
            
            TableType.FORM_12BA_PERQUISITES: {
                'required_headers': [
                    'perquisites',
                    'accommodation',
                    'motor car'
                ],
                'alternative_headers': [
                    'form 12ba',
                    'stock option',
                    'club expenses'
                ],
                'structure_hints': [
                    'form 12ba',
                    'perquisite value',
                    'benefit provided'
                ],
                'min_numeric_cols': 1,
                'expected_rows': (3, 15)
            },
            
            TableType.VERIFICATION_SECTION: {
                'required_headers': [
                    'signature',
                    'designation',
                    'date'
                ],
                'alternative_headers': [
                    'hereby certify',
                    'place',
                    'full name'
                ],
                'structure_hints': [
                    'verification',
                    'i hereby certify',
                    'working in the capacity'
                ],
                'min_numeric_cols': 0,
                'expected_rows': (1, 8)
            },
            
            TableType.HEADER_METADATA: {
                'required_headers': [
                    'form no. 16',
                    'certificate number',
                    'assessment year'
                ],
                'alternative_headers': [
                    'financial year',
                    'period from',
                    'period to'
                ],
                'structure_hints': [
                    'form no.',
                    'certificate under',
                    'assessment year'
                ],
                'min_numeric_cols': 0,
                'expected_rows': (1, 10)
            }
        }
    
    def classify_table(self, table: pd.DataFrame, table_index: int = 0) -> TableClassification:
        """
        Classify a single table by its structure and content
        
        Args:
            table: DataFrame to classify
            table_index: Index of table in document (for context)
            
        Returns:
            TableClassification with type and confidence
        """
        if table.empty:
            return TableClassification(
                table_type=TableType.UNKNOWN,
                confidence=0.0,
                features_matched=[],
                row_count=0,
                col_count=0,
                has_amounts=False,
                metadata={'reason': 'empty_table'}
            )
        
        self.logger.debug(f"Classifying table {table_index} ({table.shape[0]}x{table.shape[1]})")
        
        # Extract table features
        table_text = self._extract_table_text(table)
        numeric_cols = self._count_numeric_columns(table)
        has_amounts = self._detect_amounts(table)
        
        # Score each table type
        scores = {}
        features_matched = {}
        
        for table_type, patterns in self.classification_patterns.items():
            score, matched_features = self._score_table_type(
                table, table_text, patterns, numeric_cols, has_amounts
            )
            scores[table_type] = score
            features_matched[table_type] = matched_features
        
        # Find best match
        best_type = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_type]
        best_features = features_matched[best_type]
        
        # Apply confidence threshold
        if best_score < 0.3:
            best_type = TableType.UNKNOWN
            best_score = 0.0
            best_features = []
        
        self.logger.debug(f"Table {table_index} classified as {best_type.value} (confidence: {best_score:.2f})")
        
        return TableClassification(
            table_type=best_type,
            confidence=best_score,
            features_matched=best_features,
            row_count=table.shape[0],
            col_count=table.shape[1],
            has_amounts=has_amounts,
            metadata={
                'table_index': table_index,
                'numeric_columns': numeric_cols,
                'all_scores': {t.value: s for t, s in scores.items()}
            }
        )
    
    def classify_tables(self, tables: List[pd.DataFrame]) -> List[TableClassification]:
        """
        Classify multiple tables from a Form16 document
        
        Args:
            tables: List of DataFrames to classify
            
        Returns:
            List of TableClassification results
        """
        classifications = []
        
        for i, table in enumerate(tables):
            classification = self.classify_table(table, i)
            classifications.append(classification)
        
        # Post-process classifications for context
        self._apply_contextual_rules(classifications)
        
        self.logger.info(f"Classified {len(classifications)} tables: "
                        f"{self._get_classification_summary(classifications)}")
        
        return classifications
    
    def _score_table_type(self, table: pd.DataFrame, table_text: str, 
                         patterns: Dict, numeric_cols: int, has_amounts: bool) -> Tuple[float, List[str]]:
        """Score how well a table matches a specific type"""
        
        score = 0.0
        matched_features = []
        
        # Check required headers (high weight)
        required_matches = 0
        for header in patterns['required_headers']:
            if self._contains_header(table_text, header):
                required_matches += 1
                matched_features.append(f"required_header:{header}")
        
        if patterns['required_headers']:
            required_score = required_matches / len(patterns['required_headers'])
            score += required_score * 0.4
        
        # Check alternative headers (medium weight)
        alternative_matches = 0
        for header in patterns['alternative_headers']:
            if self._contains_header(table_text, header):
                alternative_matches += 1
                matched_features.append(f"alternative_header:{header}")
        
        if patterns['alternative_headers']:
            alternative_score = min(1.0, alternative_matches / len(patterns['alternative_headers']))
            score += alternative_score * 0.25
        
        # Check structure hints (medium weight)
        hint_matches = 0
        for hint in patterns['structure_hints']:
            if hint.lower() in table_text.lower():
                hint_matches += 1
                matched_features.append(f"structure_hint:{hint}")
        
        if patterns['structure_hints']:
            hint_score = min(1.0, hint_matches / len(patterns['structure_hints']))
            score += hint_score * 0.2
        
        # Check numeric column requirement
        if numeric_cols >= patterns['min_numeric_cols']:
            score += 0.1
            matched_features.append(f"numeric_cols:{numeric_cols}")
        
        # Check row count expectation
        row_count = table.shape[0]
        min_rows, max_rows = patterns['expected_rows']
        if min_rows <= row_count <= max_rows:
            score += 0.05
            matched_features.append(f"row_count_match:{row_count}")
        
        return score, matched_features
    
    def _extract_table_text(self, table: pd.DataFrame) -> str:
        """Extract searchable text from table"""
        text_parts = []
        
        # Include column names
        if hasattr(table, 'columns'):
            text_parts.extend([str(col) for col in table.columns if pd.notna(col)])
        
        # Include cell contents
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = table.iloc[row_idx, col_idx]
                if pd.notna(cell_value):
                    text_parts.append(str(cell_value))
        
        return ' '.join(text_parts)
    
    def _contains_header(self, text: str, header: str) -> bool:
        """Check if text contains header pattern (case-insensitive, flexible matching)"""
        text_lower = text.lower()
        header_lower = header.lower()
        
        # Direct match
        if header_lower in text_lower:
            return True
        
        # Flexible matching for common variations
        header_words = header_lower.split()
        if len(header_words) > 1:
            # Check if all words are present (order doesn't matter)
            return all(word in text_lower for word in header_words)
        
        return False
    
    def _count_numeric_columns(self, table: pd.DataFrame) -> int:
        """Count columns that contain primarily numeric data"""
        numeric_count = 0
        
        for col_idx in range(len(table.columns)):
            numeric_cells = 0
            total_cells = 0
            
            for row_idx in range(len(table)):
                cell_value = table.iloc[row_idx, col_idx]
                if pd.notna(cell_value) and str(cell_value).strip():
                    total_cells += 1
                    if self._is_numeric_value(str(cell_value)):
                        numeric_cells += 1
            
            if total_cells > 0 and numeric_cells / total_cells > 0.5:
                numeric_count += 1
        
        return numeric_count
    
    def _detect_amounts(self, table: pd.DataFrame) -> bool:
        """Detect if table contains monetary amounts"""
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx])
                if self._looks_like_amount(cell_value):
                    return True
        return False
    
    def _is_numeric_value(self, value: str) -> bool:
        """Check if string represents a numeric value"""
        value_clean = re.sub(r'[,\s₹Rs\.INR]', '', value.strip())
        try:
            float(value_clean)
            return True
        except ValueError:
            return False
    
    def _looks_like_amount(self, value: str) -> bool:
        """Check if value looks like a monetary amount"""
        if not value or pd.isna(value):
            return False
        
        value_str = str(value).strip()
        
        # Common amount patterns
        amount_indicators = ['₹', 'rs.', 'rs ', 'inr', ',', '.00']
        if any(indicator in value_str.lower() for indicator in amount_indicators):
            return True
        
        # Large numeric values (likely amounts)
        if self._is_numeric_value(value_str):
            try:
                num_val = float(re.sub(r'[,\s₹Rs\.INR]', '', value_str))
                return num_val > 100  # Amounts typically > 100
            except ValueError:
                pass
        
        return False
    
    def _apply_contextual_rules(self, classifications: List[TableClassification]):
        """Apply contextual rules to improve classification accuracy"""
        
        # Rule 1: Part A tables usually come first
        for i in range(min(3, len(classifications))):
            if classifications[i].table_type == TableType.UNKNOWN:
                # Check if it could be Part A based on position
                if classifications[i].has_amounts and classifications[i].row_count <= 10:
                    # Re-evaluate as potential Part A
                    classifications[i].table_type = TableType.PART_A_SUMMARY
                    classifications[i].confidence = 0.4
                    classifications[i].features_matched.append("contextual:early_position")
        
        # Rule 2: Employer/Employee info usually comes after Part A
        part_a_indices = [i for i, c in enumerate(classifications) 
                         if c.table_type == TableType.PART_A_SUMMARY]
        
        if part_a_indices:
            next_index = part_a_indices[0] + 1
            if (next_index < len(classifications) and 
                classifications[next_index].table_type == TableType.UNKNOWN and
                not classifications[next_index].has_amounts):
                
                classifications[next_index].table_type = TableType.PART_B_EMPLOYER_EMPLOYEE
                classifications[next_index].confidence = 0.45
                classifications[next_index].features_matched.append("contextual:after_part_a")
    
    def _get_classification_summary(self, classifications: List[TableClassification]) -> str:
        """Get summary string of classifications"""
        type_counts = {}
        for classification in classifications:
            table_type = classification.table_type
            type_counts[table_type] = type_counts.get(table_type, 0) + 1
        
        return ", ".join([f"{t.value}:{c}" for t, c in type_counts.items()])


def get_table_classifier() -> Form16TableClassifier:
    """Get singleton table classifier instance"""
    return Form16TableClassifier()