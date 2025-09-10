#!/usr/bin/env python3
"""
Salary Coordinator - Main Component
==================================

Main coordinator for salary breakdown extraction.
Orchestrates table structure analysis and contextual amount extraction.

Key Features:
- Multi-table processing with cross-validation
- Structure-aware extraction strategies
- Comprehensive component discovery
- Fallback and validation mechanisms
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd

from .table_structure_analyzer import TableStructureAnalyzer
from .amount_extractor import AmountExtractor
from .perquisite_extractor import PerquisiteExtractor
from form16x.form16_parser.models.form16_models import SalaryBreakdown


class SalaryCoordinator:
    """
    Main coordinator for salary breakdown extraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized components
        self.table_analyzer = TableStructureAnalyzer()
        self.amount_extractor = AmountExtractor()
        self.perquisite_extractor = PerquisiteExtractor()
        
        # Define target salary components
        self.target_components = [
            'basic_salary', 'hra_received', 'transport_allowance',
            'medical_allowance', 'special_allowance', 'total_allowances',
            'gross_salary', 'perquisites_value', 'net_taxable_salary'
        ]
    
    def extract_all_components(self, tables_data: List[pd.DataFrame]) -> Dict[str, float]:
        """
        Enhanced multi-table salary extraction
        
        Args:
            tables_data: List of DataFrame objects from salary tables
            
        Returns:
            Dictionary with salary components and their amounts
        """
        
        self.logger.info(f"Starting multi-table salary extraction with {len(tables_data)} tables")
        
        # Initialize results
        results = {component: 0.0 for component in self.target_components}
        
        # First pass: Look for semantic extraction results (highest priority)
        semantic_found = False
        for i, table_df in enumerate(tables_data):
            self.logger.debug(f"Checking table {i+1}/{len(tables_data)} for semantic extraction "
                             f"(shape: {table_df.shape})")
            
            # Try semantic extraction first 
            semantic_results = self.table_analyzer._extract_section_17_1_semantic(table_df)
            if semantic_results and semantic_results.get('gross_salary', 0) > 0:
                self.logger.info(f"Found semantic Section 17(1) results in table {i+1}: {semantic_results}")
                
                # Use semantic results with highest priority
                for component, amount in semantic_results.items():
                    if component in self.target_components:
                        results[component] = amount
                        self.logger.info(f"SEMANTIC: Set {component}: ₹{amount:,.2f}")
                
                semantic_found = True
                break  # Don't process other tables for Section 17 data
        
        # Second pass: Process remaining tables for other components (if no semantic results found)
        if not semantic_found:
            self.logger.info("No semantic results found, falling back to structure-based extraction")
            
            for i, table_df in enumerate(tables_data):
                self.logger.debug(f"Processing table {i+1}/{len(tables_data)} "
                                 f"(shape: {table_df.shape})")
                
                # Extract from this table using structure analysis
                table_results = self.table_analyzer.extract_salary_components_by_structure(table_df)
                
                # Merge results, keeping highest amounts
                for component, amount in table_results.items():
                    if component in self.target_components and amount > 0:
                        if results[component] == 0 or amount > results[component]:
                            results[component] = amount
                            self.logger.debug(f"Updated {component}: ₹{amount:,.2f}")
        
        # Apply cross-table validation (but preserve semantic results)
        results = self._apply_cross_table_validation(results, tables_data, semantic_found)
        
        # Always run specialized perquisite extraction for detailed breakdown
        self.logger.info("Running specialized perquisite extraction for detailed breakdown")
        perquisite_results = self.perquisite_extractor.extract_perquisites(tables_data)
        
        # Store detailed perquisite results (but don't include in results dict to avoid comparison issues)
        self.detailed_perquisites = perquisite_results
        
        # Only update total perquisites if not found in semantic extraction or if higher
        if perquisite_results.get('total_perquisites', 0) > 0:
            if results.get('perquisites_value', 0) == 0 or not semantic_found:
                results['perquisites_value'] = perquisite_results['total_perquisites']
                self.logger.info(f"Updated perquisites from specialized extraction: ₹{results['perquisites_value']:,.2f}")
            else:
                self.logger.info(f"Keeping semantic perquisites: ₹{results['perquisites_value']:,.2f}, "
                               f"specialized found: ₹{perquisite_results['total_perquisites']:,.2f}")
        
        # Calculate derived components
        results = self._calculate_derived_totals(results)
        
        # Log extraction summary
        extracted_count = sum(1 for amount in results.values() if amount > 0)
        self.logger.info(f"Extracted {extracted_count}/{len(self.target_components)} "
                        f"salary components")
        
        return results
    
    def create_salary_breakdown(self, components: Dict[str, float]) -> SalaryBreakdown:
        """
        Create SalaryBreakdown model from extracted components
        
        Args:
            components: Dictionary of salary components
            
        Returns:
            SalaryBreakdown model instance
        """
        return SalaryBreakdown(
            basic_salary=components.get('basic_salary', 0),
            hra_received=components.get('hra_received', 0),
            transport_allowance=components.get('transport_allowance', 0),
            medical_allowance=components.get('medical_allowance', 0),
            special_allowance=components.get('special_allowance', 0),
            total_allowances=components.get('total_allowances', 0),
            gross_salary=components.get('gross_salary', 0),
            perquisites_value=components.get('perquisites_value', 0),
            net_taxable_salary=components.get('net_taxable_salary', 0)
        )
    
    def extract_from_table(self, table: pd.DataFrame) -> Optional[SalaryBreakdown]:
        """
        Extract salary breakdown from a single table
        
        Args:
            table: DataFrame containing salary data
            
        Returns:
            SalaryBreakdown model or None if extraction failed
        """
        try:
            # Extract components using table analyzer
            components = self.table_analyzer.extract_salary_components_by_structure(table)
            
            if not components or not any(amount > 0 for amount in components.values()):
                return None
            
            # Fill in missing components with defaults
            for component in self.target_components:
                if component not in components:
                    components[component] = 0.0
            
            # Calculate derived components
            components = self._calculate_derived_totals(components)
            
            return self.create_salary_breakdown(components)
            
        except Exception as e:
            self.logger.error(f"Error extracting salary from table: {e}")
            return None
    
    def _apply_cross_table_validation(self, results: Dict[str, float], 
                                    tables_data: List[pd.DataFrame], semantic_found: bool = False) -> Dict[str, float]:
        """Apply validation and consistency checks across tables"""
        
        # Validation 1: Gross salary should be sum of basic + allowances
        basic = results.get('basic_salary', 0)
        allowances = results.get('total_allowances', 0)
        gross = results.get('gross_salary', 0)
        
        if basic > 0 and allowances > 0 and gross == 0:
            # Calculate gross from components
            results['gross_salary'] = basic + allowances
            self.logger.info(f"Calculated gross salary: ₹{results['gross_salary']:,.2f}")
        
        # Validation 2: Total allowances should be sum of individual allowances
        individual_allowances = (
            results.get('hra_received', 0) +
            results.get('transport_allowance', 0) +
            results.get('medical_allowance', 0) +
            results.get('special_allowance', 0)
        )
        
        if individual_allowances > 0 and allowances == 0:
            results['total_allowances'] = individual_allowances
            self.logger.info(f"Calculated total allowances: ₹{results['total_allowances']:,.2f}")
        
        # Validation 3: Look for missing components in other tables (but preserve semantic results)
        if not semantic_found:
            missing_components = [comp for comp, amount in results.items() if amount == 0]
            
            if missing_components:
                self.logger.debug(f"Searching for missing components: {missing_components}")
                
                for table_df in tables_data:
                    for component in missing_components[:]:  # Copy list to modify during iteration
                        # Use more aggressive search for missing components
                        amount = self._aggressive_component_search(table_df, component)
                        if amount:
                            results[component] = amount
                            missing_components.remove(component)
                            self.logger.info(f"Found missing {component}: ₹{amount:,.2f}")
        else:
            self.logger.info("Skipping missing component search (preserving semantic extraction results)")
        
        return results
    
    def _calculate_derived_totals(self, results: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived totals and relationships"""
        
        # Calculate total allowances if not present
        if results.get('total_allowances', 0) == 0:
            individual_total = (
                results.get('hra_received', 0) +
                results.get('transport_allowance', 0) +
                results.get('medical_allowance', 0) +
                results.get('special_allowance', 0)
            )
            if individual_total > 0:
                results['total_allowances'] = individual_total
        
        # Calculate gross salary if not present
        if results.get('gross_salary', 0) == 0:
            basic = results.get('basic_salary', 0)
            allowances = results.get('total_allowances', 0)
            if basic > 0 or allowances > 0:
                results['gross_salary'] = basic + allowances
        
        # Calculate net taxable salary if not present
        if results.get('net_taxable_salary', 0) == 0:
            gross = results.get('gross_salary', 0)
            perquisites = results.get('perquisites_value', 0)
            if gross > 0 or perquisites > 0:
                results['net_taxable_salary'] = gross + perquisites
        
        return results
    
    def _aggressive_component_search(self, table: pd.DataFrame, component: str) -> Optional[float]:
        """More aggressive search for a specific component"""
        
        # Get all possible labels for this component
        if component not in self.table_analyzer.salary_labels:
            return None
        
        labels = self.table_analyzer.salary_labels[component]
        
        # Search entire table for any mention
        for row_idx in range(table.shape[0]):
            for col_idx in range(table.shape[1]):
                cell_value = table.iloc[row_idx, col_idx]
                
                if pd.isna(cell_value):
                    continue
                
                cell_str = str(cell_value).lower().strip()
                
                # Check if this cell matches any label
                for label in labels:
                    if label in cell_str:
                        # Look for amounts in surrounding cells
                        amount = self._search_surrounding_cells(table, row_idx, col_idx, component)
                        if amount:
                            return amount
        
        return None
    
    def _search_surrounding_cells(self, table: pd.DataFrame, row: int, col: int, 
                                component: str) -> Optional[float]:
        """Search cells around a label for amounts"""
        
        # Define search pattern: right, down, up, left, diagonal
        search_offsets = [
            (0, 1), (0, 2), (0, 3),  # Right
            (1, 0), (2, 0),          # Down  
            (-1, 0),                 # Up
            (0, -1),                 # Left
            (1, 1), (1, -1)          # Diagonal
        ]
        
        amounts = []
        
        for row_offset, col_offset in search_offsets:
            new_row = row + row_offset
            new_col = col + col_offset
            
            # Check bounds
            if (0 <= new_row < table.shape[0] and 0 <= new_col < table.shape[1]):
                cell_value = table.iloc[new_row, new_col]
                amount = self.amount_extractor.extract_amount(str(cell_value), component)
                if amount:
                    amounts.append(amount)
        
        # Return the highest amount found
        return max(amounts) if amounts else None