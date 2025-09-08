"""
PDF Processing Infrastructure - ROBUST for ANY Form 16
=====================================================

Handles PDF table extraction using multiple strategies for maximum robustness.
Uses Camelot as primary, with fallbacks for different Form 16 layouts.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from dataclasses import dataclass
from enum import Enum

# PDF processing libraries
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class ExtractionStrategy(Enum):
    """PDF table extraction strategies"""
    CAMELOT_LATTICE = "camelot_lattice"
    CAMELOT_STREAM = "camelot_stream"
    TABULA_LATTICE = "tabula_lattice"
    TABULA_STREAM = "tabula_stream"
    PDFPLUMBER = "pdfplumber"
    FALLBACK = "fallback"


@dataclass
class TableExtractionResult:
    """Result of table extraction from PDF"""
    tables: List[pd.DataFrame]
    strategy_used: ExtractionStrategy
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]
    warnings: List[str]
    page_numbers: List[int]


class IPDFProcessor(ABC):
    """Abstract interface for PDF processing"""
    
    @abstractmethod
    def extract_tables(self, pdf_path: Path) -> TableExtractionResult:
        """Extract tables from PDF file"""
        pass
    
    @abstractmethod
    def get_supported_strategies(self) -> List[ExtractionStrategy]:
        """Get list of supported extraction strategies"""
        pass


class RobustPDFProcessor(IPDFProcessor):
    """
    Robust PDF processor that tries multiple extraction strategies
    to handle ANY Form 16 document structure
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.extraction_strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> Dict[ExtractionStrategy, bool]:
        """Initialize available extraction strategies"""
        strategies = {
            ExtractionStrategy.CAMELOT_LATTICE: CAMELOT_AVAILABLE,
            ExtractionStrategy.CAMELOT_STREAM: CAMELOT_AVAILABLE,
            ExtractionStrategy.TABULA_LATTICE: TABULA_AVAILABLE,
            ExtractionStrategy.TABULA_STREAM: TABULA_AVAILABLE,
            ExtractionStrategy.PDFPLUMBER: PDFPLUMBER_AVAILABLE,
            ExtractionStrategy.FALLBACK: True  # Always available
        }
        
        available_count = sum(strategies.values())
        self.logger.info(f"Initialized PDF processor with {available_count} available strategies")
        
        return strategies
    
    def get_supported_strategies(self) -> List[ExtractionStrategy]:
        """Get list of supported extraction strategies"""
        return [strategy for strategy, available in self.extraction_strategies.items() if available]
    
    def extract_tables(self, pdf_path: Path) -> TableExtractionResult:
        """
        Extract tables using multiple strategies for maximum robustness
        """
        import time
        start_time = time.time()
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.logger.info(f"Extracting tables from: {pdf_path.name}")
        
        # Try strategies in order of preference
        preferred_order = [
            ExtractionStrategy.CAMELOT_LATTICE,
            ExtractionStrategy.CAMELOT_STREAM,
            ExtractionStrategy.TABULA_LATTICE,
            ExtractionStrategy.PDFPLUMBER,
            ExtractionStrategy.FALLBACK
        ]
        
        best_result = None
        all_warnings = []
        
        for strategy in preferred_order:
            if not self.extraction_strategies.get(strategy, False):
                continue
                
            try:
                self.logger.debug(f"Trying strategy: {strategy.value}")
                result = self._extract_with_strategy(pdf_path, strategy)
                
                if result and result.tables:
                    self.logger.info(f"Success with {strategy.value}: {len(result.tables)} tables extracted")
                    
                    # Calculate confidence score for this result
                    confidence = self._calculate_extraction_confidence(result.tables, strategy)
                    
                    if best_result is None or confidence > best_result.confidence_score:
                        result.confidence_score = confidence
                        result.strategy_used = strategy
                        best_result = result
                    
                    all_warnings.extend(result.warnings)
                    
                    # If we got high-confidence results, stop trying
                    if confidence > 0.8:
                        break
                        
            except Exception as e:
                warning = f"Strategy {strategy.value} failed: {str(e)}"
                self.logger.warning(warning)
                all_warnings.append(warning)
                continue
        
        processing_time = time.time() - start_time
        
        if best_result is None:
            # Create a fallback result with empty tables
            best_result = TableExtractionResult(
                tables=[],
                strategy_used=ExtractionStrategy.FALLBACK,
                confidence_score=0.0,
                processing_time=processing_time,
                metadata={"pdf_path": str(pdf_path), "total_strategies_tried": len(preferred_order)},
                warnings=all_warnings,
                page_numbers=[]
            )
            self.logger.error("All extraction strategies failed")
        else:
            best_result.processing_time = processing_time
            best_result.warnings = list(set(all_warnings))  # Remove duplicates
            self.logger.info(f"Best result: {best_result.strategy_used.value} "
                           f"(confidence: {best_result.confidence_score:.2f})")
        
        return best_result
    
    def _extract_with_strategy(self, pdf_path: Path, strategy: ExtractionStrategy) -> Optional[TableExtractionResult]:
        """Extract tables using a specific strategy"""
        
        if strategy == ExtractionStrategy.CAMELOT_LATTICE:
            return self._extract_with_camelot(pdf_path, flavor='lattice')
        
        elif strategy == ExtractionStrategy.CAMELOT_STREAM:
            return self._extract_with_camelot(pdf_path, flavor='stream')
        
        elif strategy == ExtractionStrategy.TABULA_LATTICE:
            return self._extract_with_tabula(pdf_path, lattice=True)
        
        elif strategy == ExtractionStrategy.TABULA_STREAM:
            return self._extract_with_tabula(pdf_path, lattice=False)
        
        elif strategy == ExtractionStrategy.PDFPLUMBER:
            return self._extract_with_pdfplumber(pdf_path)
        
        elif strategy == ExtractionStrategy.FALLBACK:
            return self._extract_with_fallback(pdf_path)
        
        return None
    
    def _extract_with_camelot(self, pdf_path: Path, flavor: str = 'lattice') -> TableExtractionResult:
        """Extract using Camelot (primary strategy)"""
        if not CAMELOT_AVAILABLE:
            raise ImportError("Camelot not available")
        
        # Camelot parameters optimized for Form 16
        camelot_kwargs = {
            'flavor': flavor,
            'pages': 'all',
            'suppress_stdout': True
        }
        
        if flavor == 'lattice':
            camelot_kwargs.update({
                'line_scale': 40,  # Adjust for better line detection
                'copy_text': ['h'],  # Handle headers properly
                'shift_text': ['l', 'r'],  # Handle text alignment
            })
        else:  # stream
            camelot_kwargs.update({
                'row_tol': 2,  # Row tolerance
                'column_tol': 0,  # Column tolerance
                'edge_tol': 50,  # Edge tolerance
            })
        
        tables = camelot.read_pdf(str(pdf_path), **camelot_kwargs)
        
        if not tables:
            return TableExtractionResult(
                tables=[], 
                strategy_used=ExtractionStrategy.CAMELOT_LATTICE if flavor == 'lattice' else ExtractionStrategy.CAMELOT_STREAM,
                confidence_score=0.0,
                processing_time=0.0,
                metadata={},
                warnings=["No tables found with Camelot"],
                page_numbers=[]
            )
        
        # Convert to DataFrames and clean
        dataframes = []
        page_numbers = []
        warnings = []
        
        for table in tables:
            try:
                df = table.df
                
                # Clean the dataframe
                df = self._clean_dataframe(df)
                
                if not df.empty and len(df.columns) > 1:
                    dataframes.append(df)
                    page_numbers.append(table.page)
                else:
                    warnings.append(f"Skipped empty/invalid table on page {table.page}")
                    
            except Exception as e:
                warnings.append(f"Error processing table: {str(e)}")
        
        return TableExtractionResult(
            tables=dataframes,
            strategy_used=ExtractionStrategy.CAMELOT_LATTICE if flavor == 'lattice' else ExtractionStrategy.CAMELOT_STREAM,
            confidence_score=0.0,  # Will be calculated later
            processing_time=0.0,
            metadata={
                'flavor': flavor,
                'total_tables_found': len(tables),
                'valid_tables': len(dataframes)
            },
            warnings=warnings,
            page_numbers=page_numbers
        )
    
    def _extract_with_tabula(self, pdf_path: Path, lattice: bool = True) -> TableExtractionResult:
        """Extract using Tabula (fallback strategy)"""
        if not TABULA_AVAILABLE:
            raise ImportError("Tabula not available")
        
        tabula_kwargs = {
            'pages': 'all',
            'multiple_tables': True,
            'lattice': lattice,
            'pandas_options': {'header': None}  # Don't assume header row
        }
        
        tables = tabula.read_pdf(str(pdf_path), **tabula_kwargs)
        
        if not tables:
            return TableExtractionResult(
                tables=[],
                strategy_used=ExtractionStrategy.TABULA_LATTICE if lattice else ExtractionStrategy.TABULA_STREAM,
                confidence_score=0.0,
                processing_time=0.0,
                metadata={},
                warnings=["No tables found with Tabula"],
                page_numbers=[]
            )
        
        # Clean and validate tables
        cleaned_tables = []
        warnings = []
        
        for i, table in enumerate(tables):
            try:
                if isinstance(table, pd.DataFrame):
                    cleaned_df = self._clean_dataframe(table)
                    if not cleaned_df.empty:
                        cleaned_tables.append(cleaned_df)
                else:
                    warnings.append(f"Table {i} is not a valid DataFrame")
                    
            except Exception as e:
                warnings.append(f"Error cleaning table {i}: {str(e)}")
        
        return TableExtractionResult(
            tables=cleaned_tables,
            strategy_used=ExtractionStrategy.TABULA_LATTICE if lattice else ExtractionStrategy.TABULA_STREAM,
            confidence_score=0.0,
            processing_time=0.0,
            metadata={'lattice_mode': lattice, 'total_tables': len(tables)},
            warnings=warnings,
            page_numbers=list(range(1, len(cleaned_tables) + 1))  # Approximate page numbers
        )
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> TableExtractionResult:
        """Extract using pdfplumber (text-based extraction)"""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available")
        
        import pdfplumber
        
        tables = []
        page_numbers = []
        warnings = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract tables from this page
                    page_tables = page.extract_tables()
                    
                    for table_data in page_tables:
                        if table_data and len(table_data) > 1:  # At least 2 rows
                            # Convert to DataFrame
                            df = pd.DataFrame(table_data)
                            cleaned_df = self._clean_dataframe(df)
                            
                            if not cleaned_df.empty:
                                tables.append(cleaned_df)
                                page_numbers.append(page_num)
                
                except Exception as e:
                    warnings.append(f"Error extracting from page {page_num}: {str(e)}")
        
        return TableExtractionResult(
            tables=tables,
            strategy_used=ExtractionStrategy.PDFPLUMBER,
            confidence_score=0.0,
            processing_time=0.0,
            metadata={'total_pages_processed': len(pdf.pages) if 'pdf' in locals() else 0},
            warnings=warnings,
            page_numbers=page_numbers
        )
    
    def _extract_with_fallback(self, pdf_path: Path) -> TableExtractionResult:
        """Fallback extraction method"""
        self.logger.info("Using fallback extraction strategy")
        
        # Create empty result that won't break the pipeline
        return TableExtractionResult(
            tables=[pd.DataFrame()],  # Empty DataFrame
            strategy_used=ExtractionStrategy.FALLBACK,
            confidence_score=0.1,  # Low but not zero
            processing_time=0.0,
            metadata={'fallback_used': True, 'pdf_path': str(pdf_path)},
            warnings=["Fallback strategy used - no tables extracted"],
            page_numbers=[]
        )
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize extracted DataFrame"""
        if df.empty:
            return df
        
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Remove completely empty rows and columns
        cleaned_df = cleaned_df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean string values
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == object:  # String column
                cleaned_df[col] = cleaned_df[col].astype(str)
                cleaned_df[col] = cleaned_df[col].str.strip()
                cleaned_df[col] = cleaned_df[col].replace(['nan', 'None', '', 'NaN'], None)
        
        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        return cleaned_df
    
    def _calculate_extraction_confidence(self, tables: List[pd.DataFrame], strategy: ExtractionStrategy) -> float:
        """Calculate confidence score for extracted tables"""
        if not tables:
            return 0.0
        
        # Base confidence by strategy
        strategy_confidence = {
            ExtractionStrategy.CAMELOT_LATTICE: 0.9,
            ExtractionStrategy.CAMELOT_STREAM: 0.8,
            ExtractionStrategy.TABULA_LATTICE: 0.7,
            ExtractionStrategy.TABULA_STREAM: 0.6,
            ExtractionStrategy.PDFPLUMBER: 0.5,
            ExtractionStrategy.FALLBACK: 0.1
        }.get(strategy, 0.5)
        
        # Adjust based on table quality
        quality_scores = []
        
        for table in tables:
            if table.empty:
                quality_scores.append(0.0)
                continue
            
            # Factors that indicate good table extraction:
            # 1. Reasonable number of rows and columns
            rows, cols = table.shape
            size_score = min(1.0, (rows * cols) / 100)  # Normalize
            
            # 2. Low percentage of null values
            null_percentage = table.isnull().sum().sum() / (rows * cols)
            null_score = max(0.0, 1.0 - null_percentage)
            
            # 3. Presence of numeric data (amounts)
            numeric_cols = table.select_dtypes(include=['number']).shape[1]
            numeric_score = min(1.0, numeric_cols / max(1, cols))
            
            table_quality = (size_score * 0.4 + null_score * 0.4 + numeric_score * 0.2)
            quality_scores.append(table_quality)
        
        # Average quality across all tables
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Combine strategy confidence with quality
        final_confidence = strategy_confidence * 0.6 + avg_quality * 0.4
        
        return min(1.0, max(0.0, final_confidence))


# Factory function for easy usage
def create_pdf_processor() -> IPDFProcessor:
    """Create a robust PDF processor instance"""
    return RobustPDFProcessor()