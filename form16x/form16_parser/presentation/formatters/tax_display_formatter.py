"""
Tax Display Formatter - Handles all tax calculation result display.

This formatter is responsible for displaying tax calculation results in various formats
including colored console output, tabular format, and detailed breakdowns.
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class TaxDisplayFormatter:
    """Formatter for tax calculation results display."""
    
    def __init__(self):
        """Initialize the tax display formatter."""
        self.console = Console()
    
    def display_tax_results(
        self, 
        tax_results: Dict[str, Any], 
        regime_choice: str,
        display_mode: str = 'colored'
    ) -> None:
        """
        Display comprehensive tax calculation results.
        
        Args:
            tax_results: Tax calculation results dictionary
            regime_choice: Tax regime choice ('old', 'new', 'both')
            display_mode: Display mode ('colored', 'table')
        """
        if not tax_results:
            self.console.print("[red]No tax calculation results to display[/red]")
            return
        
        if regime_choice == 'both':
            self._display_regime_comparison(tax_results, display_mode)
        else:
            self._display_single_regime(tax_results, regime_choice, display_mode)
    
    def display_detailed_breakdown(
        self, 
        tax_results: Dict[str, Any], 
        regime_choice: str
    ) -> None:
        """
        Display detailed tax calculation breakdown.
        
        Args:
            tax_results: Tax calculation results dictionary
            regime_choice: Tax regime choice
        """
        if not tax_results or 'results' not in tax_results:
            return
        
        self.console.print("\n[bold cyan]DETAILED TAX BREAKDOWN[/bold cyan]")
        self.console.print("=" * 60)
        
        results = tax_results['results']
        extraction_data = tax_results.get('extraction_data', {})
        
        # Display employee information
        self._display_employee_info(extraction_data)
        
        # Display income breakdown
        self._display_income_breakdown(extraction_data)
        
        # Display tax calculation for each regime
        for regime, result in results.items():
            if regime_choice == 'both' or regime == regime_choice:
                self._display_regime_breakdown(regime, result)
    
    def display_summary(self, tax_results: Dict[str, Any], regime_choice: str) -> None:
        """
        Display tax calculation summary.
        
        Args:
            tax_results: Tax calculation results dictionary
            regime_choice: Tax regime choice
        """
        if not tax_results or 'results' not in tax_results:
            return
        
        results = tax_results['results']
        
        self.console.print("\n[bold yellow]TAX CALCULATION SUMMARY[/bold yellow]")
        self.console.print("-" * 40)
        
        for regime, result in results.items():
            if regime_choice == 'both' or regime == regime_choice:
                self._display_regime_summary(regime, result)
    
    def _display_regime_comparison(
        self, 
        tax_results: Dict[str, Any], 
        display_mode: str
    ) -> None:
        """Display comparison between tax regimes."""
        results = tax_results.get('results', {})
        comparison = tax_results.get('comparison', {})
        extraction_data = tax_results.get('extraction_data', {})
        
        if display_mode == 'colored':
            self._display_colored_regime_comparison(results, comparison, extraction_data)
        else:
            self._display_tabular_regime_comparison(results, comparison, extraction_data)
    
    def _display_colored_regime_comparison(
        self, 
        results: Dict[str, Any], 
        comparison: Dict[str, Any],
        extraction_data: Dict[str, Any]
    ) -> None:
        """Display colored regime comparison."""
        self.console.print("\n" + "=" * 65)
        self.console.print("[bold cyan]         TAX REGIME COMPARISON - VISUAL ANALYSIS[/bold cyan]")
        self.console.print("=" * 65)
        
        # Employee details
        self.console.print("\n[bold blue]EMPLOYEE DETAILS:[/bold blue]")
        self.console.print(f"[white]Name:[/white] {extraction_data.get('employee_name', 'N/A')}")
        self.console.print(f"[white]PAN:[/white] {extraction_data.get('employee_pan', 'N/A')}")
        self.console.print(f"[white]Employer:[/white] {extraction_data.get('employer_name', 'N/A')}")
        
        # Income breakdown
        gross_salary = extraction_data.get('gross_salary', 0)
        section_17_1 = extraction_data.get('section_17_1', 0)
        perquisites = extraction_data.get('perquisites', 0)
        
        self.console.print(f"\n[bold magenta]INCOME BREAKDOWN:[/bold magenta]")
        income_table = Table(show_header=False, box=None, padding=(0, 1))
        income_table.add_row(f"[white]Section 17(1) Basic Salary:[/white]", f"[yellow]₹ {section_17_1:>12,.0f}[/yellow]")
        income_table.add_row(f"[white]Section 17(2) Perquisites/ESOPs:[/white]", f"[yellow]₹ {perquisites:>12,.0f}[/yellow]")
        income_table.add_row("─" * 35, "─" * 15)
        income_table.add_row(f"[bold white]Total Taxable Salary:[/bold white]", f"[bold cyan]₹ {gross_salary:>12,.0f}[/bold cyan]")
        
        panel = Panel(income_table, border_style="white")
        self.console.print(panel)
        
        # Regime comparison
        self.console.print(f"\n[bold][underline]REGIME COMPARISON ANALYSIS:[/underline][/bold]")
        
        old_result = results.get('old', {})
        new_result = results.get('new', {})
        
        recommended_regime = comparison.get('recommended_regime', 'old')
        savings = comparison.get('savings_amount', 0)
        
        # Display regimes with winner/loser styling
        if recommended_regime == 'old':
            self._display_regime_panel(old_result, "OLD", True, extraction_data)
            self._display_regime_panel(new_result, "NEW", False, extraction_data)
        else:
            self._display_regime_panel(old_result, "OLD", False, extraction_data)
            self._display_regime_panel(new_result, "NEW", True, extraction_data)
        
        # Recommendation
        self.console.print("\n" + "=" * 65)
        recommendation_text = f"  RECOMMENDATION: Choose {recommended_regime.upper()} REGIME - Save Rs {savings:,.0f} annually! "
        self.console.print(f"[black on green]{recommendation_text}[/black on green]")
        self.console.print("=" * 65)
    
    def _display_regime_panel(
        self, 
        result: Dict[str, Any], 
        regime_name: str, 
        is_winner: bool,
        extraction_data: Dict[str, Any]
    ) -> None:
        """Display individual regime panel with styling."""
        if not result:
            return
        
        style = "green" if is_winner else "red"
        status = "WINNER" if is_winner else "COSTLIER"
        header_style = f"[{style}]"
        
        title = f"{regime_name} TAX REGIME (2024-25) - {status}"
        
        gross_salary = extraction_data.get('gross_salary', 0)
        section_80c = extraction_data.get('section_80c', 0)
        section_80ccd_1b = extraction_data.get('section_80ccd_1b', 0)
        
        # Create table for regime details
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row(f"[white]Gross Salary:[/white]", f"[cyan]₹ {gross_salary:>12,.0f}[/cyan]")
        
        if regime_name == "OLD":
            table.add_row(f"[white]Less: Section 80C Deductions:[/white]", f"[yellow]₹ {section_80c:>12,.0f}[/yellow]")
        
        table.add_row(f"[white]Less: Section 80CCD(1B):[/white]", f"[yellow]₹ {section_80ccd_1b:>12,.0f}[/yellow]")
        table.add_row(f"[white]Less: Standard Deduction:[/white]", f"[yellow]₹      50,000[/yellow]")
        
        if regime_name == "NEW":
            table.add_row(f"[dim](No other deductions allowed)[/dim]", "")
        
        table.add_row("─" * 35, "─" * 15)
        
        taxable_income = result.get('taxable_income', 0)
        tax_liability = result.get('tax_liability', 0)
        tds_paid = extraction_data.get('total_tds', 0)
        balance = result.get('balance', 0)
        
        table.add_row(f"[bold white]Taxable Income:[/bold white]", f"[bold magenta]₹ {taxable_income:>12,.0f}[/bold magenta]")
        table.add_row(f"[bold white]Tax Liability:[/bold white]", f"[bold red]₹ {tax_liability:>12,.0f}[/bold red]")
        table.add_row(f"[white]TDS Already Paid:[/white]", f"[green]₹ {tds_paid:>12,.0f}[/green]")
        
        if balance >= 0:
            table.add_row(f"[bold white]Refund Due:[/bold white]", f"[bold green]₹ {balance:>12,.0f}[/bold green]")
        else:
            table.add_row(f"[bold white]Additional Tax Due:[/bold white]", f"[bold red]₹ {abs(balance):>12,.0f}[/bold red]")
        
        panel_title = f"[{style} on {'white' if is_winner else 'black'}]  {title}   [/{style} on {'white' if is_winner else 'black'}]"
        panel = Panel(table, title=panel_title, border_style=style)
        self.console.print(panel)
    
    def _display_tabular_regime_comparison(
        self, 
        results: Dict[str, Any], 
        comparison: Dict[str, Any],
        extraction_data: Dict[str, Any]
    ) -> None:
        """Display tabular regime comparison."""
        table = Table(title="Tax Regime Comparison")
        
        table.add_column("Component", style="white", justify="left")
        table.add_column("OLD Regime", style="yellow", justify="right")
        table.add_column("NEW Regime", style="cyan", justify="right")
        
        old_result = results.get('old', {})
        new_result = results.get('new', {})
        
        gross_salary = extraction_data.get('gross_salary', 0)
        
        table.add_row("Gross Salary", f"₹{gross_salary:,.0f}", f"₹{gross_salary:,.0f}")
        table.add_row("Taxable Income", 
                     f"₹{old_result.get('taxable_income', 0):,.0f}",
                     f"₹{new_result.get('taxable_income', 0):,.0f}")
        table.add_row("Tax Liability",
                     f"₹{old_result.get('tax_liability', 0):,.0f}",
                     f"₹{new_result.get('tax_liability', 0):,.0f}")
        
        self.console.print(table)
        
        # Display recommendation
        recommended_regime = comparison.get('recommended_regime', 'old')
        savings = comparison.get('savings_amount', 0)
        self.console.print(f"\n[bold green]Recommendation:[/bold green] Choose {recommended_regime.upper()} regime")
        self.console.print(f"[bold green]Annual Savings:[/bold green] ₹{savings:,.0f}")
    
    def _display_single_regime(
        self, 
        tax_results: Dict[str, Any], 
        regime_choice: str,
        display_mode: str
    ) -> None:
        """Display single regime results."""
        results = tax_results.get('results', {})
        result = results.get(regime_choice, {})
        
        if not result:
            self.console.print(f"[red]No results available for {regime_choice} regime[/red]")
            return
        
        self.console.print(f"\n[bold cyan]{regime_choice.upper()} TAX REGIME CALCULATION[/bold cyan]")
        self.console.print("=" * 50)
        
        taxable_income = result.get('taxable_income', 0)
        tax_liability = result.get('tax_liability', 0)
        effective_rate = result.get('effective_tax_rate', 0)
        
        self.console.print(f"Taxable Income: ₹{taxable_income:,.0f}")
        self.console.print(f"Tax Liability: ₹{tax_liability:,.0f}")
        self.console.print(f"Effective Tax Rate: {effective_rate:.2f}%")
    
    def _display_employee_info(self, extraction_data: Dict[str, Any]) -> None:
        """Display employee information."""
        self.console.print(f"Employee: {extraction_data.get('employee_name', 'N/A')}")
        self.console.print(f"PAN: {extraction_data.get('employee_pan', 'N/A')}")
        self.console.print(f"Employer: {extraction_data.get('employer_name', 'N/A')}")
    
    def _display_income_breakdown(self, extraction_data: Dict[str, Any]) -> None:
        """Display income breakdown."""
        self.console.print("\nIncome Breakdown:")
        self.console.print(f"  Basic Salary: ₹{extraction_data.get('section_17_1', 0):,.0f}")
        self.console.print(f"  Perquisites: ₹{extraction_data.get('perquisites', 0):,.0f}")
        self.console.print(f"  Gross Salary: ₹{extraction_data.get('gross_salary', 0):,.0f}")
    
    def _display_regime_breakdown(self, regime: str, result: Dict[str, Any]) -> None:
        """Display detailed breakdown for a specific regime."""
        self.console.print(f"\n{regime.upper()} Regime:")
        self.console.print(f"  Taxable Income: ₹{result.get('taxable_income', 0):,.0f}")
        self.console.print(f"  Tax Liability: ₹{result.get('tax_liability', 0):,.0f}")
        self.console.print(f"  Effective Rate: {result.get('effective_tax_rate', 0):.2f}%")
    
    def _display_regime_summary(self, regime: str, result: Dict[str, Any]) -> None:
        """Display summary for a specific regime."""
        taxable_income = result.get('taxable_income', 0)
        tax_liability = result.get('tax_liability', 0)
        
        self.console.print(f"{regime.upper()}: ₹{tax_liability:,.0f} on ₹{taxable_income:,.0f}")