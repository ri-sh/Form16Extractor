#!/usr/bin/env python3

"""
Abstract Field Extractor
=========================

Template method pattern for standardized field extraction across all components.
Defines the 4-step extraction flow while allowing component-specific implementations.

Staff Software Engineer approach:
- Template Method pattern for consistent extraction flow
- Hook methods for component-specific customization
- Shared utilities via mixins
- Preserve exact simple_extractor.py algorithm logic
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal

from form16x.form16_parser.pdf.table_classifier import TableType


class AbstractFieldExtractor(ABC):
    """
    Template method base class for Form16 field extraction.
    
    Defines standardized 4-step extraction flow:
    1. get_relevant_tables() - Select tables for this component
    2. extract_raw_data() - Core extraction logic (component-specific)
    3. validate_data() - Domain-specific validation (optional hook)
    4. create_model() - Convert to Pydantic model (component-specific)
    
    Benefits:
    - Consistent extraction flow across all components
    - Shared confidence scoring and metadata generation
    - Easy testing and maintenance
    - Preserves exact simple_extractor.py algorithm structure
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> Tuple[Optional[Any], Dict[str, Any]]:
        """
        Template method - defines the standardized extraction flow.
        
        This method should NOT be overridden by subclasses.
        Instead, implement the abstract methods below.
        
        Args:
            tables_by_type: Classified tables grouped by type
            
        Returns:
            Tuple of (extracted_model, extraction_metadata)
        """
        
        # Step 1: Get relevant tables for this component
        relevant_tables = self.get_relevant_tables(tables_by_type)
        
        if not relevant_tables:
            return None, {
                'strategy': self.get_strategy_name(),
                'tables_used': 0,
                'confidence': 0.0,
                'status': 'no_relevant_tables'
            }
        
        self.logger.debug(f"Processing {len(relevant_tables)} relevant tables")
        
        try:
            # Step 2: Extract raw data (component-specific logic)
            raw_data = self.extract_raw_data(relevant_tables)
            
            if not raw_data:
                return None, {
                    'strategy': self.get_strategy_name(),
                    'tables_used': len(relevant_tables),
                    'confidence': 0.0,
                    'status': 'no_data_extracted'
                }
            
            # Step 3: Validate extracted data (optional hook)
            validated_data = self.validate_data(raw_data)
            
            # Step 4: Create final model (component-specific)
            final_model = self.create_model(validated_data)
            
            # Generate metadata
            confidence_score = self.calculate_confidence(validated_data, relevant_tables)
            metadata = {
                'strategy': self.get_strategy_name(),
                'tables_used': len(relevant_tables),
                'confidence': confidence_score,
                'status': 'success',
                'fields_extracted': len(validated_data) if isinstance(validated_data, dict) else 1
            }
            
            self.logger.debug(f"Extraction successful: {metadata}")
            return final_model, metadata
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return None, {
                'strategy': self.get_strategy_name(),
                'tables_used': len(relevant_tables),
                'confidence': 0.0,
                'status': 'extraction_error',
                'error': str(e)
            }
    
    # ===============================
    # ABSTRACT METHODS - MUST IMPLEMENT
    # ===============================
    
    @abstractmethod
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Select tables relevant for this component's extraction.
        
        This method determines which table types this component processes.
        Should return the same table selection logic as simple_extractor.py
        
        Args:
            tables_by_type: All classified tables
            
        Returns:
            List of relevant table_info dicts for this component
        """
        pass
    
    @abstractmethod
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Core extraction logic - extract raw field values from tables.
        
        This should contain the EXACT logic from simple_extractor.py methods.
        No algorithm changes - just copy the working extraction logic.
        
        Args:
            tables: List of relevant table_info dicts
            
        Returns:
            Dict of extracted field values (e.g., {'basic_salary': 50000, 'gross_salary': 80000})
        """
        pass
    
    @abstractmethod
    def create_model(self, data: Dict[str, Any]) -> Any:
        """
        Create final Pydantic model from extracted data.
        
        Convert raw extracted values to the appropriate Pydantic model
        (e.g., SalaryBreakdown, TaxComputation, etc.)
        
        Args:
            data: Validated extracted data
            
        Returns:
            Pydantic model instance
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Return strategy name for metadata.
        
        Should match the strategy names used in simple_extractor.py
        (e.g., 'enhanced_semantic_search', 'position_template', etc.)
        """
        pass
    
    # ===============================
    # HOOK METHODS - CAN OVERRIDE
    # ===============================
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook method for domain-specific validation.
        
        Override this method to add component-specific validation logic.
        Default implementation does no validation.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Validated/corrected data
        """
        return data
    
    def calculate_confidence(self, data: Dict[str, Any], tables: List[Dict[str, Any]]) -> float:
        """
        Hook method for confidence calculation.
        
        Override this method to implement component-specific confidence scoring.
        Default implementation provides basic confidence based on data completeness.
        
        Args:
            data: Validated extracted data
            tables: Tables used for extraction
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not data:
            return 0.0
        
        # Basic confidence: more fields extracted = higher confidence
        base_confidence = 0.6
        
        # Bonus for having multiple fields
        if isinstance(data, dict):
            field_count = len([v for v in data.values() if v is not None])
            if field_count > 1:
                base_confidence += min(0.3, field_count * 0.1)
        
        # Bonus for using multiple tables
        if len(tables) > 1:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    # ===============================
    # UTILITY METHODS (will be moved to mixins)
    # ===============================
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal safely"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_amount(self, value: Any) -> Optional[float]:
        """Basic amount parsing - will be replaced by mixin"""
        if value is None:
            return None
            
        import re
        text = str(value).strip()
        if not text or text.lower() in ['nan', 'none', '']:
            return None
        
        # Remove currency symbols and formatting
        clean_text = re.sub(r'[₹,\s]', '', text)
        clean_text = re.sub(r'/-$', '', clean_text)
        
        try:
            return float(clean_text)
        except (ValueError, TypeError):
            return None