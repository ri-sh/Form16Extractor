"""
Display Templates for all Form16 Tax Calculation Display Modes

This module contains templates and formatting functions for all display modes:
- Summary (table) mode - compact tabular display
- Detailed mode - comprehensive breakdown with all components
- Default mode - standard text-based results
- Colored mode - imported from colored_templates.py
"""

from typing import Dict, Any, Optional
from .colored_templates import ColoredDisplayRenderer


class DisplayTemplates:
    """Base templates and utilities for all display modes."""
    
    # ANSI Color Codes (used across different display modes)
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency amount with proper comma separation."""
        return f"₹{amount:,.0f}"

    @staticmethod
    def determine_better_regime(old_tax: float, new_tax: float) -> tuple[str, float]:
        """Determine which regime is better and calculate savings."""
        if old_tax < new_tax:
            return 'old', new_tax - old_tax
        elif new_tax < old_tax:
            return 'new', old_tax - new_tax
        else:
            return 'equal', 0.0


class SummaryDisplayRenderer:
    """Renderer for summary/table display mode - compact and professional."""
    
    def __init__(self):
        self.colors = DisplayTemplates()

    def render_header(self, employee_info: Dict[str, str]) -> str:
        """Render summary header section."""
        return f"""
FORM16 SUMMARY
{'-' * 50}
Employee    : {employee_info.get('name', 'N/A')}
PAN         : {employee_info.get('pan', 'N/A')}
Employer    : {employee_info.get('employer', 'N/A')}"""

    def render_income_summary(self, financial_data: Dict[str, float]) -> str:
        """Render income summary section."""
        section_17_1 = financial_data.get('section_17_1_salary', 0)
        section_17_2 = financial_data.get('section_17_2_perquisites', 0)
        total_taxable = financial_data.get('gross_salary', 0)
        total_tds = financial_data.get('total_tds', 0)
        
        output = [f"Gross Salary : Rs {section_17_1:,.0f}"]
        
        if section_17_2 > 0:
            output.append(f"Perquisites  : Rs {section_17_2:,.0f}")
            output.append(f"Total Taxable Salary (Gross + Perquisites): Rs {total_taxable:,.0f}")
        else:
            output.append(f"Total Taxable Salary: Rs {total_taxable:,.0f}")
        
        output.append(f"Total TDS   : Rs {total_tds:,.0f}")
        
        return '\n'.join(output)

    def render_regime_comparison_table(self, regime_comparison: Dict[str, Dict]) -> str:
        """Render regime comparison in tabular format."""
        if len(regime_comparison) != 2:
            return self._render_single_regime(regime_comparison)
        
        old_data = regime_comparison.get('old_regime', {})
        new_data = regime_comparison.get('new_regime', {})
        
        # Determine better regime for coloring
        old_tax = old_data.get('tax_liability', 0)
        new_tax = new_data.get('tax_liability', 0)
        better_regime, savings = DisplayTemplates.determine_better_regime(old_tax, new_tax)
        
        old_color = self.colors.GREEN if better_regime == 'old' else self.colors.RED
        new_color = self.colors.GREEN if better_regime == 'new' else self.colors.RED
        reset = self.colors.RESET
        
        # Build comparison table
        output = [
            "\nTAX REGIME COMPARISON",
            "=" * 50,
            f"{'PARTICULARS':<25} {old_color}{'OLD REGIME':<15}{reset} {new_color}{'NEW REGIME':<15}{reset}",
            "-" * 55
        ]
        
        # Add table rows
        rows = [
            ('Taxable Income', 'taxable_income'),
            ('Tax Liability', 'tax_liability'), 
            ('TDS Paid', 'tds_paid'),
        ]
        
        for label, key in rows:
            old_val = old_data.get(key, 0)
            new_val = new_data.get(key, 0)
            output.append(f"{label:<25} {old_color}{old_val:>12,.0f}{reset}   {new_color}{new_val:>12,.0f}{reset}")
        
        # Net balance row
        old_balance = old_data.get('refund_due', 0) if old_data.get('refund_due', 0) > 0 else -old_data.get('tax_due', 0)
        new_balance = new_data.get('refund_due', 0) if new_data.get('refund_due', 0) > 0 else -new_data.get('tax_due', 0)
        output.append(f"{'Net Refund/Tax Due':<25} {old_color}{old_balance:>12,.0f}{reset}   {new_color}{new_balance:>12,.0f}{reset}")
        
        # Effective rate row
        old_rate = old_data.get('effective_rate', 0)
        new_rate = new_data.get('effective_rate', 0)
        output.append(f"{'Effective Tax Rate':<25} {old_color}{old_rate:>11.2f}%{reset}   {new_color}{new_rate:>11.2f}%{reset}")
        
        output.append("-" * 55)
        
        # Add recommendation
        if better_regime == 'equal':
            output.append(f"{self.colors.BOLD}Both regimes result in same tax liability{reset}")
        else:
            regime_name = "Old Regime" if better_regime == 'old' else "New Regime"
            output.append(f"{self.colors.BOLD}{self.colors.GREEN}RECOMMENDATION: {regime_name} saves Rs {savings:,.0f}{reset}")
        
        return '\n'.join(output)

    def _render_single_regime(self, regime_comparison: Dict[str, Dict]) -> str:
        """Render single regime display."""
        output = ["\nTAX CALCULATION RESULT", "=" * 30]
        
        for regime_key, regime_data in regime_comparison.items():
            regime_name = "OLD REGIME" if regime_key == 'old_regime' else "NEW REGIME"
            output.extend([
                f"\n{regime_name}",
                "-" * 30,
                f"Taxable Income     : Rs {regime_data['taxable_income']:,.0f}",
                f"Tax Liability      : Rs {regime_data['tax_liability']:,.0f}",
                f"TDS Paid          : Rs {regime_data['tds_paid']:,.0f}"
            ])
            
            if regime_data['refund_due'] > 0:
                output.append(f"Refund Due        : Rs {regime_data['refund_due']:,.0f}")
            else:
                output.append(f"Additional Tax Due: Rs {regime_data['tax_due']:,.0f}")
            
            output.append(f"Effective Tax Rate: {regime_data['effective_rate']:.2f}%")
        
        return '\n'.join(output)

    def render_complete_summary(self, tax_results: Dict[str, Any]) -> str:
        """Render complete summary display."""
        employee_info = tax_results.get('employee_info', {})
        financial_data = tax_results.get('financial_data', {})
        regime_comparison = tax_results.get('regime_comparison', {})
        
        output = []
        output.append(self.render_header(employee_info))
        output.append(self.render_income_summary(financial_data))
        output.append(self.render_regime_comparison_table(regime_comparison))
        
        return '\n'.join(output)


class DetailedDisplayRenderer:
    """Renderer for detailed display mode - comprehensive breakdown."""
    
    def __init__(self):
        self.colors = DisplayTemplates()

    def render_detailed_header(self, employee_info: Dict[str, str]) -> str:
        """Render detailed analysis header."""
        return f"""
DETAILED TAX ANALYSIS
{'=' * 60}
Employee        : {employee_info.get('name', 'N/A')}
PAN             : {employee_info.get('pan', 'N/A')}
Employer        : {employee_info.get('employer', 'N/A')}
Assessment Year : 2024-25"""

    def render_income_breakdown(self, financial_data: Dict[str, float]) -> str:
        """Render detailed income breakdown."""
        section_17_1 = financial_data.get('section_17_1_salary', 0)
        section_17_2 = financial_data.get('section_17_2_perquisites', 0)
        total_taxable = financial_data.get('gross_salary', 0)
        section_80c = financial_data.get('section_80c', 0)
        section_80ccd_1b = financial_data.get('section_80ccd_1b', 0)
        total_tds = financial_data.get('total_tds', 0)
        
        output = [
            "\nINCOME BREAKDOWN",
            "-" * 40,
            f"Gross Salary           : Rs {section_17_1:,.0f}"
        ]
        
        if section_17_2 > 0:
            output.extend([
                f"Perquisites (17(2))    : Rs {section_17_2:,.0f}",
                f"Total Taxable Salary (Gross + Perquisites): Rs {total_taxable:,.0f}"
            ])
        else:
            output.append(f"Total Taxable Salary   : Rs {total_taxable:,.0f}")
        
        output.extend([
            f"Section 80C Deductions : Rs {section_80c:,.0f}",
            f"Section 80CCD(1B)      : Rs {section_80ccd_1b:,.0f}",
            f"Total TDS Deducted     : Rs {total_tds:,.0f}"
        ])
        
        return '\n'.join(output)

    def render_detailed_regime_breakdown(self, regime_comparison: Dict[str, Dict]) -> str:
        """Render detailed regime-by-regime breakdown."""
        if len(regime_comparison) == 2:
            old_tax = regime_comparison['old_regime']['tax_liability']
            new_tax = regime_comparison['new_regime']['tax_liability']
            better_regime, _ = DisplayTemplates.determine_better_regime(old_tax, new_tax)
        else:
            better_regime = 'equal'
        
        output = [
            "\nDETAILED REGIME COMPARISON",
            "=" * 60
        ]
        
        for regime_key, regime_data in regime_comparison.items():
            is_old_regime = regime_key == 'old_regime'
            regime_name = "OLD TAX REGIME" if is_old_regime else "NEW TAX REGIME"
            
            # Color coding for better regime
            color = ""
            reset = self.colors.RESET
            if len(regime_comparison) == 2:
                if (is_old_regime and better_regime == 'old') or (not is_old_regime and better_regime == 'new'):
                    color = self.colors.GREEN
                elif better_regime != 'equal':
                    color = self.colors.RED
            
            output.extend([
                f"\n{color}{self.colors.BOLD}{regime_name}{reset}",
                f"{color}{'-' * 30}{reset}",
                f"{color}Taxable Income    : Rs {regime_data['taxable_income']:,.0f}{reset}",
                f"{color}Tax Liability     : Rs {regime_data['tax_liability']:,.0f}{reset}",
                f"{color}TDS Already Paid  : Rs {regime_data['tds_paid']:,.0f}{reset}"
            ])
            
            # Show deductions used
            deductions = regime_data.get('deductions_used', {})
            if any(v > 0 for v in deductions.values()):
                output.append(f"{color}Deductions Utilized:{reset}")
                for section, amount in deductions.items():
                    if amount > 0:
                        output.append(f"{color}  Section {section:<8} : Rs {amount:,.0f}{reset}")
            
            # Refund or tax due
            if regime_data.get('refund_due', 0) > 0:
                output.append(f"{color}Refund Due        : Rs {regime_data['refund_due']:,.0f}{reset}")
            else:
                output.append(f"{color}Additional Tax Due: Rs {regime_data.get('tax_due', 0):,.0f}{reset}")
            
            output.append(f"{color}Effective Tax Rate: {regime_data.get('effective_rate', 0):.2f}%{reset}")
        
        # Add comparison summary
        if len(regime_comparison) == 2:
            old_tax = regime_comparison['old_regime']['tax_liability']
            new_tax = regime_comparison['new_regime']['tax_liability']
            better_regime, savings = DisplayTemplates.determine_better_regime(old_tax, new_tax)
            
            output.extend([
                f"\n{self.colors.BOLD}COMPARISON SUMMARY{reset}",
                f"{self.colors.BOLD}{'-' * 30}{reset}"
            ])
            
            if better_regime == 'old':
                output.append(f"{self.colors.BOLD}{self.colors.GREEN}Old Regime is better by Rs {savings:,.0f}{reset}")
            elif better_regime == 'new':
                output.append(f"{self.colors.BOLD}{self.colors.GREEN}New Regime is better by Rs {savings:,.0f}{reset}")
            else:
                output.append(f"{self.colors.BOLD}Both regimes have equal tax liability{reset}")
        
        return '\n'.join(output)

    def render_complete_detailed(self, tax_results: Dict[str, Any]) -> str:
        """Render complete detailed display."""
        employee_info = tax_results.get('employee_info', {})
        financial_data = tax_results.get('financial_data', {})
        regime_comparison = tax_results.get('regime_comparison', {})
        
        output = []
        output.append(self.render_detailed_header(employee_info))
        output.append(self.render_income_breakdown(financial_data))
        output.append(self.render_detailed_regime_breakdown(regime_comparison))
        
        return '\n'.join(output)


class DefaultDisplayRenderer:
    """Renderer for default display mode - standard text-based results."""
    
    def render_extraction_summary(self, extraction_data: Dict[str, Any]) -> str:
        """Render extracted Form16 data summary."""
        output = [
            "✓ Form16 Data Extracted:",
            "",
            f"- Employee: {extraction_data.get('employee_name', 'N/A')} (PAN: {extraction_data.get('employee_pan', 'N/A')})",
            f"- Employer: {extraction_data.get('employer_name', 'N/A')}"
        ]
        
        gross_salary = extraction_data.get('gross_salary', 0)
        perquisites = extraction_data.get('perquisites', 0)
        section_17_1 = extraction_data.get('section_17_1', 0)
        
        gross_display = f"₹{gross_salary:,.0f}"
        if perquisites > 0:
            gross_display += f" (₹{section_17_1:,.0f} + ₹{perquisites:,.0f} perquisites)"
        
        output.append(f"- Gross Salary: {gross_display}")
        
        if extraction_data.get('section_80c', 0) > 0:
            output.append(f"- Section 80C (PPF): ₹{extraction_data['section_80c']:,.0f}")
        if extraction_data.get('section_80ccd_1b', 0) > 0:
            output.append(f"- Section 80CCD(1B): ₹{extraction_data['section_80ccd_1b']:,.0f}")
        
        output.append(f"- Total TDS Deducted: ₹{extraction_data.get('total_tds', 0):,.0f} (across 4 quarters)")
        
        return '\n'.join(output)

    def render_regime_results(self, tax_results: Dict[str, Any], regime_choice: str) -> str:
        """Render regime calculation results."""
        output = [
            "",
            "COMPREHENSIVE TAX CALCULATION RESULTS:",
            ""
        ]
        
        if regime_choice == "both" and 'old' in tax_results and 'new' in tax_results:
            # Show both regimes
            for regime_name in ['new', 'old']:
                if regime_name in tax_results:
                    data = tax_results[regime_name]
                    regime_display = f"{regime_name.title()} Regime"
                    
                    output.extend([
                        f"{regime_display}:",
                        f"- Taxable Income: ₹{data.get('taxable_income', 0):,.0f} (after exemptions & deductions)",
                        f"- Tax Liability: ₹{data.get('tax_liability', 0):,.0f} (including cess)",
                        f"- TDS Paid: ₹{data.get('tds_paid', 0):,.0f}"
                    ])
                    
                    if data.get('status') == 'refund_due':
                        output.append(f"- [REFUND] Refund Due: Rs {abs(data.get('balance', 0)):,.0f}")
                    else:
                        output.append(f"- [PAYABLE] Additional Tax Payable: Rs {abs(data.get('balance', 0)):,.0f}")
                    
                    output.extend([
                        f"- Effective Tax Rate: {data.get('effective_tax_rate', 0):.2f}%",
                        ""
                    ])
            
            # Show recommendation
            old_tax = tax_results['old'].get('tax_liability', 0)
            new_tax = tax_results['new'].get('tax_liability', 0)
            better_regime, savings = DisplayTemplates.determine_better_regime(old_tax, new_tax)
            
            if better_regime == 'old':
                output.append(f"✓ Recommendation: Old Regime saves ₹{savings:,.0f} in taxes")
            elif better_regime == 'new':
                output.append(f"✓ Recommendation: New Regime saves ₹{savings:,.0f} in taxes")
            else:
                output.append("✓ Both regimes result in the same tax liability")
        
        else:
            # Show single regime
            regime_name = 'new' if 'new' in tax_results else 'old'
            if regime_name in tax_results:
                data = tax_results[regime_name]
                regime_display = f"{regime_name.title()} Regime"
                
                output.extend([
                    f"{regime_display}:",
                    f"- Taxable Income: ₹{data.get('taxable_income', 0):,.0f} (after exemptions & deductions)",
                    f"- Tax Liability: ₹{data.get('tax_liability', 0):,.0f} (including cess)",
                    f"- TDS Paid: ₹{data.get('tds_paid', 0):,.0f}"
                ])
                
                if data.get('status') == 'refund_due':
                    output.append(f"- [REFUND] Refund Due: Rs {abs(data.get('balance', 0)):,.0f}")
                else:
                    output.append(f"- [PAYABLE] Additional Tax Payable: Rs {abs(data.get('balance', 0)):,.0f}")
                
                output.append(f"- Effective Tax Rate: {data.get('effective_tax_rate', 0):.2f}%")
        
        return '\n'.join(output)

    def render_complete_default(self, tax_results: Dict[str, Any], regime_choice: str = "both") -> str:
        """Render complete default display."""
        extraction_data = tax_results.get('extraction_data', {})
        
        output = []
        output.append(self.render_extraction_summary(extraction_data))
        output.append(self.render_regime_results(tax_results, regime_choice))
        
        return '\n'.join(output)


class DisplayRenderer:
    """Main display renderer that coordinates all display modes."""
    
    def __init__(self):
        self.summary_renderer = SummaryDisplayRenderer()
        self.detailed_renderer = DetailedDisplayRenderer()
        self.default_renderer = DefaultDisplayRenderer()
        self.colored_renderer = ColoredDisplayRenderer()

    def render(self, tax_results: Dict[str, Any], display_mode: str = 'table', regime_choice: str = 'both') -> str:
        """
        Render tax results in the specified display mode.
        
        Args:
            tax_results: Tax calculation results
            display_mode: 'table', 'detailed', 'default', or 'colored'
            regime_choice: 'old', 'new', or 'both'
            
        Returns:
            Formatted display string
        """
        if display_mode == 'table':
            return self.summary_renderer.render_complete_summary(tax_results)
        elif display_mode == 'detailed':
            return self.detailed_renderer.render_complete_detailed(tax_results)
        elif display_mode == 'colored':
            return self.colored_renderer.render_complete_display(tax_results)
        elif display_mode == 'default':
            return self.default_renderer.render_complete_default(tax_results, regime_choice)
        else:
            # Fallback to table mode
            return self.summary_renderer.render_complete_summary(tax_results)

    def print_display(self, tax_results: Dict[str, Any], display_mode: str = 'table', regime_choice: str = 'both'):
        """Print the rendered display to console."""
        output = self.render(tax_results, display_mode, regime_choice)
        print(output)