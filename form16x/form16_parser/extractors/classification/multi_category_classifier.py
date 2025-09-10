#!/usr/bin/env python3
"""
Multi-Category Table Classifier - REFACTORED Implementation
===========================================================

Addresses CRITICAL issue: 87.9% salary data lost due to rigid classification.
Implements multi-domain scoring to route tables to multiple extractors.

REFACTORED PHASE: Improved code structure while maintaining functionality.
Security: Uses only synthetic test data, no real PII or financial data.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ExtractorType(Enum):
    """Supported extractor types for multi-routing"""
    SALARY = "salary"
    PERQUISITE = "perquisite"  
    TAX = "tax"
    METADATA = "metadata"
    DEDUCTION = "deduction"


@dataclass
class DomainScore:
    """Multi-domain scores for table classification"""
    salary_score: float = 0.0
    perquisite_score: float = 0.0
    tax_score: float = 0.0
    metadata_score: float = 0.0
    deduction_score: float = 0.0


class MultiCategoryClassifier:
    """
    Multi-category table classifier to fix ₹10.82M salary under-extraction.
    
    Routes tables to multiple extractors based on domain relevance scores.
    Addresses root cause: rigid single classification ignores 87.9% salary data.
    """
    
    def __init__(self):
        """Initialize classifier with domain-specific patterns"""
        self.salary_keywords = [
            'salary', 'allowance', 'basic', 'hra', 'gross', 'perquisites',
            'allowances', 'income', 'earning', 'pay', 'remuneration', 'total'
        ]
        
        self.perquisite_keywords = [
            'value of perquisite', 'amount recovered', 'amount chargeable',
            'nature of perquisites', 'perquisite', 'benefit', 'facility'
        ]
        
        self.tax_keywords = [
            'tds', 'tax deducted', 'tax liability', 'quarterly', 'deducted at source',
            'income tax', 'advance tax', 'self assessment tax'
        ]
        
        self.metadata_keywords = [
            'certificate', 'pan', 'tan', 'assessment year', 'form no',
            'deductor', 'employee', 'employer', 'period', 'financial year'
        ]
        
        self.deduction_keywords = [
            'section 80', 'deduction', 'chapter vi', 'investment', 'insurance',
            'provident fund', 'life insurance', 'medical insurance'
        ]
        
        # Amount pattern for detecting monetary values
        self.amount_pattern = re.compile(r'₹[\d,]+\.?\d*|[\d,]+\.?\d*')
    
    def score_table(self, table: pd.DataFrame) -> DomainScore:
        """
        Score table across all domains - CORE METHOD to fix under-extraction.
        
        Args:
            table: Input table to classify
            
        Returns:
            DomainScore with scores for all domains [0.0, 1.0]
        """
        # Convert table to string for text analysis
        table_text = table.to_string().lower()
        
        # Calculate domain-specific scores
        salary_score = self._calculate_salary_score(table, self.salary_keywords)
        perquisite_score = self._calculate_perquisite_score(table, self.perquisite_keywords)
        tax_score = self._calculate_text_score(table_text, self.tax_keywords)
        metadata_score = self._calculate_text_score(table_text, self.metadata_keywords)
        deduction_score = self._calculate_text_score(table_text, self.deduction_keywords)
        
        return DomainScore(
            salary_score=min(salary_score, 1.0),
            perquisite_score=min(perquisite_score, 1.0),
            tax_score=min(tax_score, 1.0),
            metadata_score=min(metadata_score, 1.0),
            deduction_score=min(deduction_score, 1.0)
        )
    
    def get_extractor_routes(self, scores: DomainScore, threshold: float = 0.4) -> List[str]:
        """
        Get list of extractors to route table to based on scores.
        
        CRITICAL FIX: Enables multi-extractor routing to capture ₹10.82M lost salary data.
        
        Args:
            scores: Domain scores from score_table()
            threshold: Minimum score to route to extractor
            
        Returns:
            List of extractor names to process this table
        """
        routes = []
        
        # Map scores to extractor types
        score_mapping = [
            (scores.salary_score, ExtractorType.SALARY.value),
            (scores.perquisite_score, ExtractorType.PERQUISITE.value),
            (scores.tax_score, ExtractorType.TAX.value),
            (scores.metadata_score, ExtractorType.METADATA.value),
            (scores.deduction_score, ExtractorType.DEDUCTION.value)
        ]
        
        # Add routes for scores above threshold
        for score, extractor_type in score_mapping:
            if score > threshold:
                routes.append(extractor_type)
                
        return routes
    
    def _calculate_salary_score(self, table: pd.DataFrame, keywords: List[str]) -> float:
        """Calculate salary domain score based on keywords and amounts"""
        table_text = table.to_string().lower()
        
        # Keyword score (0-0.7)
        keyword_score = self._calculate_text_score(table_text, keywords)
        
        # Amount score (0-0.3) - reduced weight for pure metadata tables 
        amount_score = self._calculate_amount_score(table)
        
        # Reduce salary score if this looks like pure metadata
        metadata_indicators = ['form no', 'certificate', 'pan', 'tan', 'assessment year']
        metadata_matches = sum(1 for indicator in metadata_indicators if indicator in table_text)
        
        base_score = keyword_score * 0.7 + amount_score * 0.3
        
        # Penalize if too metadata-heavy and no strong salary indicators
        if metadata_matches >= 3 and keyword_score < 0.2:
            base_score *= 0.6
            
        return base_score
    
    def _calculate_perquisite_score(self, table: pd.DataFrame, keywords: List[str]) -> float:
        """Calculate perquisite domain score with table structure analysis"""
        table_text = table.to_string().lower()
        
        # Keyword score
        keyword_score = self._calculate_text_score(table_text, keywords)
        
        # Structure score - perquisite tables are typically 4-5 columns wide
        structure_score = 0.0
        if len(table.columns) >= 4:
            structure_score = 0.3
            
        # Check for specific perquisite column patterns
        column_text = ' '.join(str(col).lower() for col in table.columns)
        if 'value' in column_text and 'amount' in column_text:
            structure_score += 0.2
            
        return min(keyword_score + structure_score, 1.0)
    
    def _calculate_text_score(self, text: str, keywords: List[str]) -> float:
        """Calculate score based on keyword matches in text"""
        if not text or not keywords:
            return 0.0
            
        matches = sum(1 for keyword in keywords if keyword in text)
        # Higher multiplier for better scoring
        return min(matches / len(keywords) * 1.8, 1.0)
    
    def _calculate_amount_score(self, table: pd.DataFrame) -> float:
        """Calculate score based on monetary amounts found in table"""
        table_text = table.to_string()
        amounts = self.amount_pattern.findall(table_text)
        
        if not amounts:
            return 0.0
            
        # Score based on number of amounts and their magnitude
        large_amounts = [amt for amt in amounts if self._parse_amount(amt) > 10000]
        
        amount_count_score = min(len(amounts) * 0.1, 0.5)
        large_amount_score = min(len(large_amounts) * 0.2, 0.5)
        
        return amount_count_score + large_amount_score
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float value"""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹,]', '', amount_str)
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0