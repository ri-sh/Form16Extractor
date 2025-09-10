#!/usr/bin/env python3

"""
Salary Extractor Component
==========================

Component for extracting salary breakdown data from Form16 tables
using coordinator-based semantic extraction.
"""

import pandas as pd
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from form16x.form16_parser.extractors.base.abstract_field_extractor import AbstractFieldExtractor
from form16x.form16_parser.models.form16_models import SalaryBreakdown
from form16x.form16_parser.pdf.table_classifier import TableType


class EnhancedSalaryExtractorComponent(AbstractFieldExtractor):
    """
    Component for extracting salary breakdown data from Form16 tables.
    
    Uses specialized coordinator architecture:
    - SalaryCoordinator: Main orchestrator
    - TableStructureAnalyzer: Structure-aware extraction  
    - AmountExtractor: Specialized amount parsing
    """
    
    def __init__(self):
        super().__init__()
        # Initialize the coordinator which manages all specialized components
        from .salary_coordinator import SalaryCoordinator
        self.coordinator = SalaryCoordinator()
        
        # Modern extraction uses coordinator-based semantic analysis
        
        # Semantic patterns for field extraction
        self.detailed_salary_patterns = {
            # Basic components (expanded patterns)
            'basic_salary': [
                'basic salary', 'basic pay', 'basic wages', 'salary basic', 'basic',
                'basic sal', 'salary basic', 'basic amount', 'base salary', 'base pay'
            ],
            'dearness_allowance': [
                'dearness allowance', 'da', 'dearness pay', 'dearness', 'dear allowance',
                'dearness all', 'da allowance'
            ],
            
            # Allowances (significantly expanded)
            'hra_received': [
                'house rent allowance', 'hra', 'rent allowance', 'housing allowance',
                'house rent', 'rent', 'housing', 'residential allowance', 'accommodation allowance'
            ],
            'transport_allowance': [
                'transport allowance', 'conveyance allowance', 'transport', 'travel allowance',
                'conveyance', 'travelling allowance', 'ta', 'conv allowance', 'vehicle allowance'
            ],
            'medical_allowance': [
                'medical allowance', 'medical reimbursement', 'health allowance', 'medical',
                'medical reimb', 'health', 'medical expenses', 'medical facility', 'medicine allowance',
                'healthcare allowance', 'medical benefit'
            ],
            'special_allowance': [
                'special allowance', 'special pay', 'special', 'misc allowance', 'miscellaneous allowance',
                'spl allowance', 'spl all', 'special sal', 'additional allowance', 'other special'
            ],
            'overtime_allowance': [
                'overtime allowance', 'ot allowance', 'overtime', 'extra time', 'ot',
                'overtime pay', 'extra hours', 'additional hours', 'shift allowance'
            ],
            'commission_bonus': [
                'commission', 'bonus', 'incentive', 'performance bonus', 'annual bonus',
                'performance pay', 'incentive pay', 'achievement bonus', 'commission pay',
                'variable pay', 'performance allowance', 'profit bonus'
            ],
            'leave_travel_allowance': [
                'leave travel allowance', 'lta', 'travel concession', 'leave travel',
                'travel allowance', 'ltc', 'holiday allowance', 'vacation allowance'
            ],
            'food_allowance': [
                'food allowance', 'meal allowance', 'canteen allowance', 'food',
                'meal', 'lunch allowance', 'food facility', 'canteen', 'dining allowance',
                'food reimbursement', 'subsistence allowance'
            ],
            'phone_allowance': [
                'phone allowance', 'mobile allowance', 'communication allowance', 'telephone allowance',
                'mobile', 'phone', 'telecom allowance', 'cell phone allowance', 'communication'
            ],
            'other_allowances': [
                'other allowances', 'miscellaneous allowances', 'misc', 'sundry', 'others',
                'additional allowances', 'various allowances', 'remaining allowances',
                'other benefits', 'misc benefits', 'sundry allowances'
            ],
            
            # Perquisites (expanded with more variations)
            'perquisites_value': [
                'perquisites', 'perquisite value', 'benefits', 'fringe benefits', 'perqs',
                'perq', 'employee benefits', 'company benefits', 'additional benefits',
                'value of perquisites', 'perquisite', 'non-cash benefits'
            ],
            'stock_options': [
                'stock options', 'esop', 'equity compensation', 'share options', 'employee stock',
                'stock option plan', 'equity', 'shares', 'stock benefit', 'equity benefit',
                'share benefit', 'stock grant'
            ],
            'accommodation_perquisite': [
                'accommodation', 'housing benefit', 'rent free', 'free accommodation',
                'company accommodation', 'furnished accommodation', 'residential facility',
                'housing facility', 'lodging', 'residence benefit'
            ],
            'car_perquisite': [
                'motor car', 'vehicle perquisite', 'car benefit', 'company car',
                'vehicle benefit', 'car facility', 'motor vehicle', 'automobile',
                'company vehicle', 'car allowance perquisite'
            ],
            'other_perquisites': [
                'other perquisites', 'misc perquisites', 'additional benefits', 'other benefits',
                'miscellaneous perquisites', 'sundry perquisites', 'various perquisites',
                'remaining perquisites', 'additional perqs'
            ],
            
            # Totals and sections (enhanced)
            'total_allowances': [
                'total allowances', 'gross allowances', 'allowances total', 'total all',
                'sum of allowances', 'allowances sum', 'aggregate allowances', 'all allowances'
            ],
            'gross_salary': [
                'gross salary', 'total salary', 'gross total', 'total gross', 'gross pay',
                'total pay', 'gross amount', 'total amount', 'gross compensation'
            ],
            'salary_section_17_1': [
                'section 17(1)', 'salary section 17(1)', '17(1)', 'sec 17(1)',
                'section 17 (1)', 'salary under section 17(1)', 'income section 17(1)'
            ],
            'total_income_section_17': [
                'income under section 17', 'section 17 total', 'total section 17',
                'section 17 income', 'income sec 17', 'total income section 17',
                'aggregate income section 17'
            ],
            'profit_in_lieu': [
                'profit in lieu', 'profit lieu', 'section 17(3)', 'sec 17(3)',
                'profit in lieu of salary', 'section 17 (3)', '17(3)'
            ],
            
            # Exemptions (significantly expanded)
            'hra_exemption': [
                'hra exemption', 'house rent exemption', 'exempt hra', 'hra exempt',
                'exemption hra', 'hra less exemption', 'house rent exempt', 'rent exemption'
            ],
            'transport_exemption': [
                'transport exemption', 'conveyance exemption', 'exempt transport',
                'transport exempt', 'ta exemption', 'conveyance exempt', 'travel exemption'
            ],
            'other_exemptions': [
                'other exemptions', 'misc exemptions', 'additional exemptions', 'various exemptions',
                'remaining exemptions', 'sundry exemptions', 'other exempt', 'misc exempt'
            ],
            
            # Net amounts (enhanced)
            'net_taxable_salary': [
                'net taxable salary', 'taxable salary', 'net salary', 'taxable income',
                'net taxable income', 'salary taxable', 'taxable amount', 'net pay'
            ]
        }
        
        # Semantic patterns for variable structure tables
        self.semantic_patterns = {
            TableType.PART_A_SUMMARY: {
                'total_salary_paid': [
                    'total salary paid', 'gross salary', 'total remuneration',
                    'total earnings', 'salary paid'
                ]
            }
        }
    
    def get_relevant_tables(self, tables_by_type: Dict[TableType, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Get salary tables for extraction.
        
        Args:
            tables_by_type: Classified tables
            
        Returns:
            List of salary table_info dicts prioritized by extraction potential
        """
        # Priority order based on gap analysis results
        relevant_tables = []
        
        # 1st Priority: Part B salary details (structured salary data)
        part_b_tables = tables_by_type.get(TableType.PART_B_SALARY_DETAILS, [])
        relevant_tables.extend(part_b_tables)
        
        # 2nd Priority: Part A summary (computed totals and exemptions)
        part_a_tables = tables_by_type.get(TableType.PART_A_SUMMARY, [])
        relevant_tables.extend(part_a_tables)
        
        # 3rd Priority: Header metadata (sometimes contains salary info)
        header_tables = tables_by_type.get(TableType.HEADER_METADATA, [])
        relevant_tables.extend(header_tables)
        
        # 4th Priority: Verification section (perquisites details)
        verification_tables = tables_by_type.get(TableType.VERIFICATION_SECTION, [])
        relevant_tables.extend(verification_tables)
        
        if self.logger:
            self.logger.debug(f"Identified {len(relevant_tables)} salary-relevant tables: "
                            f"PartB={len(part_b_tables)}, PartA={len(part_a_tables)}, "
                            f"Header={len(header_tables)}, Verification={len(verification_tables)}")
        
        return relevant_tables
    
    def extract_raw_data(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract salary data from multiple tables using specialized coordinator.
        
        Args:
            tables: List of salary table_info dicts
            
        Returns:
            Dict of extracted salary values with detailed breakdown
        """
        
        # Extract table DataFrames
        table_dfs = []
        for table_info in tables:
            table = table_info['table']
            if not table.empty:
                table_dfs.append(table)
        
        if not table_dfs:
            return {}
        
        # Use coordinator for extraction
        components = self.coordinator.extract_all_components(table_dfs)
        
        # Convert to expected format
        return components
    
    def extract_from_table(self, table: pd.DataFrame) -> Optional[SalaryBreakdown]:
        """Extract salary data from single table using coordinator."""
        if table is None or table.empty:
            return None
            
        # Use the specialized coordinator for extraction
        return self.coordinator.extract_from_table(table)
    
    def extract(self, tables_by_type: Dict) -> Tuple[Optional[SalaryBreakdown], Dict]:
        """Main extraction method for compatibility."""
        
        # Extract DataFrames from table metadata
        table_dfs = []
        
        # Handle legacy format - extract tables from any available type
        for table_type, table_list in tables_by_type.items():
            if isinstance(table_list, list):
                for table_item in table_list:
                    # Handle both DataFrame and dict formats
                    if hasattr(table_item, 'shape'):  # It's a DataFrame
                        table_dfs.append(table_item)
                    elif isinstance(table_item, dict) and 'table' in table_item:
                        # It's a metadata dict containing 'table' key
                        table_df = table_item['table']
                        if hasattr(table_df, 'shape'):
                            table_dfs.append(table_df)
        
        if not table_dfs:
            return None, {}
        
        # Extract components using coordinator
        components = self.coordinator.extract_all_components(table_dfs)
        
        # Create SalaryBreakdown
        salary_breakdown = self.coordinator.create_salary_breakdown(components)
        
        # Create metadata
        metadata = {
            'extraction_method': 'coordinator_based',
            'tables_processed': len(table_dfs),
            'components_found': sum(1 for v in components.values() if v > 0)
        }
        
        # Include detailed perquisites if available
        if hasattr(self.coordinator, 'detailed_perquisites'):
            metadata['detailed_perquisites'] = self.coordinator.detailed_perquisites
        
        return salary_breakdown, metadata
    
    # Legacy position-based extraction method removed - using coordinator-based approach
    
    def _extract_salary_semantic(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract salary components using semantic pattern matching
        
        Args:
            table: DataFrame to extract from
            
        Returns:
            Dict of extracted salary values
        """
        extracted = {}
        
        for field_name, patterns in self.detailed_salary_patterns.items():
            amount = self._find_amount_by_patterns(table, patterns)
            if amount and amount > 0:
                extracted[field_name] = amount
        
        return extracted
    
    def _extract_perquisites(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract perquisites (Section 17(2)) from salary table
        
        Args:
            table: DataFrame to extract from
            
        Returns:
            Dict of perquisites values
        """
        perquisites = {}
        
        # Look for perquisites patterns specifically
        perquisites_fields = [
            'perquisites_value', 'stock_options', 'accommodation_perquisite', 
            'car_perquisite', 'other_perquisites'
        ]
        
        for field_name in perquisites_fields:
            patterns = self.detailed_salary_patterns.get(field_name, [])
            amount = self._find_amount_by_patterns(table, patterns)
            if amount and amount > 0:
                perquisites[field_name] = amount
        
        return perquisites
    
    def _find_amount_by_patterns(self, table: pd.DataFrame, patterns: List[str]) -> Optional[float]:
        """
        Pattern matching with fuzzy matching support
        
        Args:
            table: DataFrame to search
            patterns: List of text patterns to match
            
        Returns:
            Extracted amount or None
        """
        import re
        
        for row_idx in range(len(table)):
            for col_idx in range(len(table.columns)):
                cell_value = str(table.iloc[row_idx, col_idx]).strip().lower()
                
                if not cell_value or cell_value in ['nan', 'none', '']:
                    continue
                
                # Check if cell matches any pattern
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    
                    # Exact substring match (original behavior)
                    if pattern_lower in cell_value:
                        amount = self._extract_adjacent_amount(table, row_idx, col_idx)
                        if amount and amount > 0:
                            return amount
                    
                    # Enhanced fuzzy matching for common abbreviations
                    elif self._fuzzy_pattern_match(cell_value, pattern_lower):
                        amount = self._extract_adjacent_amount(table, row_idx, col_idx)
                        if amount and amount > 0:
                            return amount
        
        return None
    
    def _fuzzy_pattern_match(self, cell_value: str, pattern: str) -> bool:
        """
        Enhanced fuzzy matching for salary field patterns
        
        Args:
            cell_value: Cell content to match against
            pattern: Pattern to match
            
        Returns:
            True if fuzzy match found
        """
        import re
        
        # Common abbreviation mappings based on gap analysis
        abbreviation_mappings = {
            'house rent allowance': ['hra', 'h.r.a', 'house rent', 'rent allowance'],
            'dearness allowance': ['da', 'd.a', 'dearness', 'dear allowance'],
            'leave travel allowance': ['lta', 'l.t.a', 'leave travel', 'ltc'],
            'transport allowance': ['ta', 't.a', 'conveyance', 'travel'],
            'medical allowance': ['medical', 'health allowance', 'medical reimb'],
            'special allowance': ['special', 'spl', 'spl allowance', 'additional'],
            'perquisites': ['perqs', 'perq', 'benefits', 'fringe'],
            'basic salary': ['basic', 'basic sal', 'base salary', 'base pay'],
            'gross salary': ['gross', 'total salary', 'gross sal', 'total pay'],
            'exemption': ['exempt', 'exemption', 'less exemption']
        }
        
        # Check if pattern has known abbreviations
        for full_term, abbreviations in abbreviation_mappings.items():
            if pattern in full_term or full_term in pattern:
                for abbrev in abbreviations:
                    if abbrev in cell_value:
                        return True
        
        # Word-boundary fuzzy matching (handle partial word matches)
        pattern_words = pattern.split()
        if len(pattern_words) > 1:
            # Multi-word patterns: check if most significant words are present
            significant_words = [w for w in pattern_words if len(w) > 3]  # Skip small words
            matches = sum(1 for word in significant_words if word in cell_value)
            if len(significant_words) > 0 and matches / len(significant_words) >= 0.7:  # 70% of words match
                return True
        
        # Handle common formatting variations
        normalized_cell = re.sub(r'[^\w\s]', ' ', cell_value)  # Remove punctuation
        normalized_pattern = re.sub(r'[^\w\s]', ' ', pattern)
        
        if normalized_pattern in normalized_cell:
            return True
        
        return False
    
    def _extract_adjacent_amount(self, table: pd.DataFrame, row_idx: int, col_idx: int) -> Optional[float]:
        """
        Extract amount from adjacent cells (right, below, diagonal)
        
        Args:
            table: DataFrame
            row_idx: Row index of pattern match
            col_idx: Column index of pattern match
            
        Returns:
            Extracted amount or None
        """
        from decimal import Decimal, InvalidOperation
        import re
        
        # Check adjacent cells: right, below, diagonal
        adjacent_cells = []
        
        # Right cell
        if col_idx + 1 < len(table.columns):
            adjacent_cells.append(table.iloc[row_idx, col_idx + 1])
        
        # Below cell
        if row_idx + 1 < len(table):
            adjacent_cells.append(table.iloc[row_idx + 1, col_idx])
        
        # Diagonal (below-right)
        if row_idx + 1 < len(table) and col_idx + 1 < len(table.columns):
            adjacent_cells.append(table.iloc[row_idx + 1, col_idx + 1])
        
        # Same cell (pattern and amount together)
        adjacent_cells.append(table.iloc[row_idx, col_idx])
        
        for cell_value in adjacent_cells:
            cell_str = str(cell_value).strip()
            if cell_str and cell_str.lower() not in ['nan', 'none', '']:
                # Extract numeric amount
                amount_match = re.search(r'[\d,]+\.?\d*', cell_str)
                if amount_match:
                    try:
                        amount_str = amount_match.group().replace(',', '')
                        amount = float(Decimal(amount_str))
                        if amount > 0:
                            return amount
                    except (InvalidOperation, ValueError):
                        continue
        
        return None
    
    def create_model(self, data: Dict[str, Any]) -> SalaryBreakdown:
        """
        Create SalaryBreakdown from extracted data with totals calculation and validation
        
        Args:
            data: Extracted salary values
            
        Returns:
            SalaryBreakdown model with calculated totals and cross-validation
        """
        # Apply totals calculation and cross-validation
        validated_data = self._calculate_totals_and_validate(data)
        
        return self._create_salary_breakdown(validated_data)
    
    def _calculate_totals_and_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate missing totals and perform cross-validation (Task 8.4)
        
        Args:
            data: Extracted salary data
            
        Returns:
            Data with calculated totals and validation applied
        """
        from decimal import Decimal
        
        validated_data = data.copy()
        
        # Calculate total allowances if not present
        if not validated_data.get('total_allowances'):
            allowance_fields = [
                'hra_received', 'transport_allowance', 'medical_allowance', 
                'special_allowance', 'overtime_allowance', 'commission_bonus',
                'leave_travel_allowance', 'food_allowance', 'phone_allowance', 
                'other_allowances', 'dearness_allowance'
            ]
            
            total_allowances = Decimal('0')
            allowances_found = 0
            
            for field in allowance_fields:
                if validated_data.get(field):
                    total_allowances += Decimal(str(validated_data[field]))
                    allowances_found += 1
            
            if allowances_found > 0:
                validated_data['total_allowances'] = float(total_allowances)
                if self.logger:
                    self.logger.debug(f"Calculated total allowances: {total_allowances} from {allowances_found} components")
        
        # Calculate gross salary if not present
        if not validated_data.get('gross_salary'):
            basic = validated_data.get('basic_salary', 0)
            allowances = validated_data.get('total_allowances', 0)
            perquisites = validated_data.get('perquisites_value', 0)
            
            if basic or allowances or perquisites:
                gross_salary = Decimal(str(basic)) + Decimal(str(allowances)) + Decimal(str(perquisites))
                validated_data['gross_salary'] = float(gross_salary)
                if self.logger:
                    self.logger.debug(f"Calculated gross salary: {gross_salary} (Basic: {basic}, Allowances: {allowances}, Perquisites: {perquisites})")
        
        # Cross-validation: Check for discrepancies
        discrepancies = self._validate_salary_consistency(validated_data)
        if discrepancies and self.logger:
            for discrepancy in discrepancies:
                self.logger.warning(f"Salary validation discrepancy: {discrepancy}")
        
        return validated_data
    
    def _validate_salary_consistency(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate consistency between salary components and totals
        
        Args:
            data: Salary data to validate
            
        Returns:
            List of validation discrepancy messages
        """
        from decimal import Decimal
        discrepancies = []
        
        # Validation 1: Total allowances vs sum of individual allowances
        total_allowances = data.get('total_allowances')
        if total_allowances:
            allowance_fields = [
                'hra_received', 'transport_allowance', 'medical_allowance', 
                'special_allowance', 'overtime_allowance', 'commission_bonus',
                'leave_travel_allowance', 'food_allowance', 'phone_allowance', 
                'other_allowances', 'dearness_allowance'
            ]
            
            calculated_total = sum(Decimal(str(data.get(field, 0))) for field in allowance_fields)
            extracted_total = Decimal(str(total_allowances))
            
            # Allow 1% variance for rounding
            variance = abs(calculated_total - extracted_total)
            tolerance = extracted_total * Decimal('0.01')  # 1% tolerance
            
            if variance > tolerance:
                discrepancies.append(
                    f"Total allowances mismatch: extracted {extracted_total}, calculated {calculated_total}, variance {variance}"
                )
        
        # Validation 2: Gross salary vs components
        gross_salary = data.get('gross_salary')
        if gross_salary:
            basic = Decimal(str(data.get('basic_salary', 0)))
            allowances = Decimal(str(data.get('total_allowances', 0)))
            perquisites = Decimal(str(data.get('perquisites_value', 0)))
            
            calculated_gross = basic + allowances + perquisites
            extracted_gross = Decimal(str(gross_salary))
            
            variance = abs(calculated_gross - extracted_gross)
            tolerance = extracted_gross * Decimal('0.02')  # 2% tolerance for gross salary
            
            if variance > tolerance:
                discrepancies.append(
                    f"Gross salary mismatch: extracted {extracted_gross}, calculated {calculated_gross}, variance {variance}"
                )
        
        # Validation 3: Section 17(1) vs allowances
        section_17_1 = data.get('salary_section_17_1')
        if section_17_1:
            basic = Decimal(str(data.get('basic_salary', 0)))
            allowances = Decimal(str(data.get('total_allowances', 0)))
            
            calculated_17_1 = basic + allowances
            extracted_17_1 = Decimal(str(section_17_1))
            
            variance = abs(calculated_17_1 - extracted_17_1)
            tolerance = extracted_17_1 * Decimal('0.01')
            
            if variance > tolerance:
                discrepancies.append(
                    f"Section 17(1) mismatch: extracted {extracted_17_1}, calculated {calculated_17_1}, variance {variance}"
                )
        
        return discrepancies
    
    # Specialized extraction methods
    
    def _extract_summary_table_data(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract data specific to Part A summary tables
        
        Args:
            table: DataFrame representing Part A summary table
            
        Returns:
            Dict of extracted summary values
        """
        extracted = {}
        
        # Specific patterns for Part A summary tables
        summary_patterns = {
            'total_allowances': ['total allowances', 'gross allowances', 'allowances total'],
            'hra_exemption': ['hra exemption', 'house rent exemption', 'exempt hra'],
            'transport_exemption': ['transport exemption', 'conveyance exemption'],
            'other_exemptions': ['other exemptions', 'misc exemptions', 'additional exemptions'],
            'net_taxable_salary': ['total taxable income', 'net taxable salary', 'taxable income'],
            'gross_salary': ['total salary', 'gross salary', 'total amount of salary']
        }
        
        for field_name, patterns in summary_patterns.items():
            amount = self._find_amount_by_patterns(table, patterns)
            if amount and amount > 0:
                extracted[field_name] = amount
        
        return extracted
    
    def _extract_verification_perquisites(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract perquisites data from verification section tables
        
        Args:
            table: DataFrame representing verification section
            
        Returns:
            Dict of perquisites values
        """
        extracted = {}
        
        # Verification section specific patterns
        verification_patterns = {
            'accommodation_perquisite': ['accommodation', 'residential facility', 'housing benefit'],
            'car_perquisite': ['motor car', 'vehicle', 'automobile', 'car benefit'],
            'stock_options': ['stock options', 'equity', 'esop', 'share benefit'],
            'other_perquisites': ['other perquisites', 'misc benefits', 'additional perquisites'],
            'perquisites_value': ['total perquisites', 'perquisite value', 'benefits value']
        }
        
        for field_name, patterns in verification_patterns.items():
            amount = self._find_amount_by_patterns(table, patterns)
            if amount and amount > 0:
                extracted[field_name] = amount
        
        return extracted
    
    def _extract_header_salary_data(self, table: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract salary-related data from header/metadata tables
        
        Args:
            table: DataFrame representing header metadata
            
        Returns:
            Dict of salary values from header
        """
        extracted = {}
        
        # Header tables sometimes contain summary salary information
        header_patterns = {
            'gross_salary': ['total salary', 'gross amount', 'annual salary'],
            'total_allowances': ['total allowances', 'allowances paid'],
            'net_taxable_salary': ['taxable income', 'net taxable']
        }
        
        for field_name, patterns in header_patterns.items():
            amount = self._find_amount_by_patterns(table, patterns)
            if amount and amount > 0:
                extracted[field_name] = amount
        
        return extracted
    
    def get_strategy_name(self) -> str:
        """Return strategy name for metadata"""
        return "coordinator_semantic"
    
    def calculate_confidence(self, data: Dict[str, Any], tables: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence for salary extraction
        
        Args:
            data: Extracted data
            tables: Tables used
            
        Returns:
            Confidence score
        """
        if not data:
            return 0.0
        
        # High confidence for coordinator-based extraction
        base_confidence = 0.9
        
        # Check for key fields
        key_fields = ['gross_salary', 'basic_salary', 'hra']
        key_count = sum(1 for field in key_fields if data.get(field))
        
        if key_count >= 2:
            base_confidence = 0.95
        
        return base_confidence
    
    # ===============================
    # Helper methods
    # ===============================
    
    # Position template methods removed - using coordinator-based semantic extraction
    
    def _create_salary_breakdown(self, data: Dict[str, Any]) -> SalaryBreakdown:
        """Create comprehensive SalaryBreakdown from all extracted salary data"""
        
        # Parse amounts safely with fallback to None for optional fields
        def safe_parse_optional(key: str) -> Optional[Decimal]:
            value = data.get(key)
            if value is None:
                return None
            
            # If already a Decimal, return it
            if isinstance(value, Decimal):
                return value if value >= 0 else None  # Accept zero values
            
            # Parse the amount
            parsed = self._parse_amount(value)
            return parsed if parsed is not None and parsed >= 0 else None  # Accept zero values
        
        return SalaryBreakdown(
            # Basic salary components
            basic_salary=safe_parse_optional('basic_salary'),
            dearness_allowance=safe_parse_optional('dearness_allowance'),
            
            # Allowances (Section 17(1))
            hra_received=safe_parse_optional('hra_received') or safe_parse_optional('hra'),
            transport_allowance=safe_parse_optional('transport_allowance'),
            medical_allowance=safe_parse_optional('medical_allowance'),
            special_allowance=safe_parse_optional('special_allowance'),
            overtime_allowance=safe_parse_optional('overtime_allowance'),
            commission_bonus=safe_parse_optional('commission_bonus'),
            leave_travel_allowance=safe_parse_optional('leave_travel_allowance'),
            food_allowance=safe_parse_optional('food_allowance'),
            phone_allowance=safe_parse_optional('phone_allowance'),
            other_allowances=safe_parse_optional('other_allowances'),
            
            # Perquisites (Section 17(2))
            perquisites_value=safe_parse_optional('perquisites_value'),
            stock_options=safe_parse_optional('stock_options'),
            accommodation_perquisite=safe_parse_optional('accommodation_perquisite'),
            car_perquisite=safe_parse_optional('car_perquisite'),
            other_perquisites=safe_parse_optional('other_perquisites'),
            
            # Profits in lieu of salary (Section 17(3))
            profit_in_lieu=safe_parse_optional('profit_in_lieu'),
            
            # Calculated totals
            total_allowances=safe_parse_optional('total_allowances'),
            gross_salary=safe_parse_optional('gross_salary'),
            salary_section_17_1=safe_parse_optional('salary_section_17_1'),
            total_income_section_17=safe_parse_optional('total_income_section_17'),
            
            # Exemptions and deductions
            hra_exemption=safe_parse_optional('hra_exemption'),
            transport_exemption=safe_parse_optional('transport_exemption'),
            other_exemptions=safe_parse_optional('other_exemptions'),
            
            # Net amounts
            net_taxable_salary=safe_parse_optional('net_taxable_salary')
        )