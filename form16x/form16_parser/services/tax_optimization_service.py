"""
Tax Optimization Service - Core business logic for tax optimization analysis.

This service orchestrates the entire tax optimization workflow:
1. Tax calculation and regime comparison
2. Optimization opportunity analysis
3. Suggestion prioritization and formatting
"""

from typing import Dict, Any, Optional
from pathlib import Path
from decimal import Decimal

from ..analyzers.tax_optimization_engine import TaxOptimizationEngine
from ..api.tax_calculation_api import TaxCalculationAPI
from ..utils.json_builder import Form16JSONBuilder


class TaxOptimizationService:
    """Service for handling tax optimization analysis workflow."""
    
    def __init__(self):
        """Initialize the optimization service with required dependencies."""
        self.optimizer = TaxOptimizationEngine()
        self.tax_calculator = TaxCalculationAPI()
        self.json_builder = Form16JSONBuilder()
    
    def analyze_tax_optimization(
        self, 
        form16_result: Any,
        file_path: Path,
        target_savings: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze tax optimization opportunities for a given Form16.
        
        Args:
            form16_result: Extracted Form16 data
            file_path: Path to the original PDF file
            target_savings: Optional target savings amount
            
        Returns:
            Dict containing optimization analysis and recommendations
        """
        # Step 1: Calculate tax for both regimes
        tax_results = self._calculate_tax_for_regimes(form16_result)
        
        # Step 2: Build Form16 JSON for analysis
        form16_json = self.json_builder.build_comprehensive_json(
            form16_result, 
            file_path.name, 
            0.0, 
            {}
        )
        
        # Step 3: Analyze optimization opportunities
        optimization_analysis = self.optimizer.analyze_optimization_opportunities(
            tax_results, form16_json, target_savings
        )
        
        # Convert optimization_analysis to dict if it's an object
        if hasattr(optimization_analysis, 'suggestions'):
            optimization_dict = {
                'suggestions': optimization_analysis.suggestions,
                'total_potential_savings': getattr(optimization_analysis, 'total_potential_savings', 0)
            }
        else:
            optimization_dict = optimization_analysis
        
        # Step 4: Build comprehensive result
        return {
            'tax_calculations': tax_results,
            'optimization_analysis': optimization_dict,
            'form16_data': form16_json,
            'file_info': {
                'name': file_path.name,
                'path': str(file_path)
            }
        }
    
    def create_demo_analysis(self, complexity_level: str = "medium") -> Dict[str, Any]:
        """
        Create demo tax optimization analysis for demonstration purposes.
        
        Args:
            complexity_level: Level of complexity for demo data
            
        Returns:
            Dict containing demo optimization analysis
        """
        # Create demo optimization analysis
        optimization_analysis = self.optimizer.create_dummy_optimization_analysis(complexity_level)
        
        # Create demo tax results based on ₹25L salary (realistic calculation)
        demo_taxable_income = 2125000  # ₹25L gross - standard deduction - exemptions  
        demo_tax_results = {
            'results': {
                'old': {
                    'tax_liability': 468000,  # OLD regime tax on ₹21.25L
                    'taxable_income': demo_taxable_income,
                    'tds_paid': 450000,
                    'balance': -18000,
                    'effective_tax_rate': 22.0
                },
                'new': {
                    'tax_liability': 331250,  # NEW regime tax on ₹21.25L  
                    'taxable_income': demo_taxable_income,
                    'tds_paid': 350000,
                    'balance': 18750,
                    'effective_tax_rate': 15.6
                }
            },
            'comparison': {
                'savings_with_new': 136750,  # NEW saves ₹1.37L vs OLD
                'recommended_regime': 'new'
            },
            'recommendation': 'NEW regime saves ₹1,36,750 annually'
        }
        
        # Convert optimization_analysis to dict if it's an object
        if hasattr(optimization_analysis, 'suggestions'):
            optimization_dict = {
                'suggestions': optimization_analysis.suggestions,
                'total_potential_savings': getattr(optimization_analysis, 'total_potential_savings', 0)
            }
        else:
            optimization_dict = optimization_analysis
        
        return {
            'tax_calculations': demo_tax_results,
            'optimization_analysis': optimization_dict,
            'demo_mode': True,
            'current_tax_liability': 331250,  # NEW regime tax
            'recommended_regime': 'new',
            'tax_savings': 136750,  # Savings vs OLD regime
            'current_taxable_income': demo_taxable_income
        }
    
    def _calculate_tax_for_regimes(self, form16_result: Any) -> Dict[str, Any]:
        """
        Calculate tax for both old and new regimes.
        
        Args:
            form16_result: Extracted Form16 data
            
        Returns:
            Dict containing tax calculations for both regimes
        """
        # This would integrate with existing tax calculation logic
        # For now, return a structured result format
        return {
            'results': {
                'old': {},
                'new': {}
            },
            'comparison': {},
            'recommendation': ''
        }