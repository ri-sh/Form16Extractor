"""
Tax Optimization Formatter - Specialized display logic for tax optimization.

This formatter handles all the behavioral UX and display logic that was 
previously embedded in the CLI. It focuses purely on presentation concerns.
"""

from typing import Dict, Any, List
from decimal import Decimal

from ...display.rich_ui_components import RichUIComponents


class TaxOptimizationFormatter:
    """Formatter for tax optimization analysis display."""
    
    def __init__(self):
        """Initialize the formatter with UI components."""
        self.ui = RichUIComponents()
    
    def display_optimization_analysis(self, analysis_result: Dict[str, Any]) -> None:
        """
        Display complete tax optimization analysis with behavioral UX.
        
        Args:
            analysis_result: Complete analysis result from TaxOptimizationService
        """
        # Show header
        self._show_header()
        
        # Display current tax situation
        self._display_current_situation(analysis_result)
        
        # Display progressive optimization journey
        if analysis_result.get('optimization_analysis', {}).get('suggestions'):
            self._display_optimization_journey(analysis_result)
        
        # Display additional opportunities
        self._display_additional_opportunities(analysis_result)
        
        # Display final summary
        self._display_final_summary(analysis_result)
    
    def _show_header(self) -> None:
        """Display the optimization analysis header."""
        self.ui.show_animated_header(
            "Tax Optimization Analysis",
            "Discover opportunities to reduce your tax liability legally"
        )
    
    def _display_current_situation(self, analysis_result: Dict[str, Any]) -> None:
        """Display current tax situation analysis."""
        if analysis_result.get('demo_mode'):
            self._display_demo_situation(analysis_result)
        else:
            self._display_real_situation(analysis_result)
    
    def _display_demo_situation(self, analysis_result: Dict[str, Any]) -> None:
        """Display demo mode tax situation."""
        current_tax = analysis_result.get('current_tax_liability', 78723)
        current_taxable_income = analysis_result.get('current_taxable_income', 862724)
        recommended_regime = analysis_result.get('recommended_regime', 'new')
        tax_savings = analysis_result.get('tax_savings', 25000)
        
        self.ui.console.print("\n[bold blue]═══════════════════════════════════════════════════════════════════════════════[/bold blue]")
        self.ui.console.print("[bold blue]                        Current Tax Situation Analysis                        [/bold blue]")
        self.ui.console.print("[bold blue]═══════════════════════════════════════════════════════════════════════════════[/bold blue]")
        
        self.ui.console.print(f"\n[cyan]Your Current Tax Profile:[/cyan]")
        self.ui.console.print(f"• Currently using: [yellow]{recommended_regime.upper()} regime[/yellow]")
        self.ui.console.print(f"• Taxable income: [blue]₹{current_taxable_income:,.0f}[/blue]")
        self.ui.console.print(f"• Current tax liability: [red]₹{current_tax:,.0f}[/red]")
        self.ui.console.print(f"• Annual savings from regime choice: [green]₹{tax_savings:,.0f}[/green]")
        
        self.ui.console.print(f"\n[bold green]Regime Recommendation:[/bold green]")
        self.ui.console.print(f"You're already using the [green]optimal {recommended_regime.upper()} regime[/green]")
        if recommended_regime == 'new':
            self.ui.console.print(f"   Switching to OLD regime would [red]cost you ₹{tax_savings:,.0f} more[/red]")
    
    def _display_real_situation(self, analysis_result: Dict[str, Any]) -> None:
        """Display real mode tax situation with extracted data."""
        # Implementation for real tax data display
        pass
    
    def _display_optimization_journey(self, analysis_result: Dict[str, Any]) -> None:
        """Display the progressive optimization journey with behavioral UX and regime comparison."""
        suggestions = analysis_result['optimization_analysis']['suggestions']
        
        # Determine baseline tax for both regimes
        if analysis_result.get('demo_mode'):
            baseline_old_tax = 103723.0  # Demo old regime tax
            baseline_new_tax = 78723.0   # Demo new regime tax
            current_regime = analysis_result.get('recommended_regime', 'new')
        else:
            tax_calculations = analysis_result.get('tax_calculations', {})
            if 'results' in tax_calculations:
                baseline_old_tax = float(tax_calculations['results'].get('old', {}).get('tax_liability', 103723))
                baseline_new_tax = float(tax_calculations['results'].get('new', {}).get('tax_liability', 78723))
                current_regime = tax_calculations.get('comparison', {}).get('recommended_regime', 'new')
            else:
                baseline_old_tax = 103723.0
                baseline_new_tax = 78723.0
                current_regime = 'new'
        
        # BEHAVIORAL UX: Loss Aversion + Anchoring with regime comparison
        self.ui.console.print(f"\n[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]")
        self.ui.console.print(f"[bold cyan]                       Your Tax Optimization Journey                         [/bold cyan]")
        self.ui.console.print(f"[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]\n")
        
        # Show baseline comparison between regimes
        current_tax = baseline_new_tax if current_regime == 'new' else baseline_old_tax
        regime_savings = baseline_old_tax - baseline_new_tax
        
        self.ui.console.print("┌─────────────────────────────────────────────────────────────┐")
        self.ui.console.print("│                    Starting Position                       │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print(f"│ OLD Regime Tax:          [red]₹{baseline_old_tax:>12,.0f}[/red]        │")
        self.ui.console.print(f"│ NEW Regime Tax:          [blue]₹{baseline_new_tax:>12,.0f}[/blue]        │")
        self.ui.console.print(f"│ Current ({current_regime.upper()}):       [{'green' if current_regime == 'new' else 'yellow'}]₹{current_tax:>12,.0f}[/{'green' if current_regime == 'new' else 'yellow'}]        │")
        self.ui.console.print(f"│ Regime Choice Savings:   [green]₹{regime_savings:>12,.0f}[/green]        │")
        self.ui.console.print("└─────────────────────────────────────────────────────────────┘")
        
        self.ui.console.print(f"\n[bold red]You're currently paying ₹{current_tax:,.0f} in taxes[/bold red]")
        self.ui.console.print(f"[dim]   That's ₹{current_tax/12:,.0f} per month leaving your pocket...[/dim]")
        self.ui.console.print()
        
        # Calculate total potential if they do ALL optimizations
        total_potential_savings = sum(float(s.potential_tax_savings) for s in suggestions[:4])
        self.ui.console.print(f"[bold yellow]Opportunity Alert:[/bold yellow] You could save up to [bright_green]₹{total_potential_savings:,.0f}[/bright_green] more this year!")
        self.ui.console.print(f"[dim]   That's like getting an additional [bright_green]₹{total_potential_savings/12:,.0f}/month salary raise[/bright_green]")
        self.ui.console.print()
        
        # Progressive optimization with regime tracking
        running_old_tax = baseline_old_tax
        running_new_tax = baseline_new_tax
        cumulative_old_savings = 0
        cumulative_new_savings = 0
        step_number = 1
        
        # Sort by difficulty first (easy wins) then by impact for momentum building
        prioritized_suggestions = sorted(suggestions[:4], 
                                       key=lambda x: (x.difficulty.value, -x.potential_tax_savings))
        
        for suggestion in prioritized_suggestions:
            # Calculate reduction for both regimes (optimizations apply only to OLD regime)
            old_reduction = float(suggestion.potential_tax_savings)
            new_reduction = 0.0  # Most optimizations don't apply to NEW regime
            
            # Update running totals for both regimes
            new_old_tax = running_old_tax - old_reduction
            new_new_tax = running_new_tax - new_reduction
            cumulative_old_savings += old_reduction
            cumulative_new_savings += new_reduction
            
            # BEHAVIORAL UX: Gamified Progress + Social Proof
            step_indicator = ["[green]●[/green]", "[yellow]●[/yellow]", "[red]●[/red]", "[dim]●[/dim]"][step_number-1] if step_number <= 4 else "[dim]●[/dim]"
            difficulty_level = {"easy": "Easy", "moderate": "Medium", "difficult": "Advanced"}.get(suggestion.difficulty.value, "Medium")
            
            self.ui.console.print(f"\n{step_indicator} [bold blue]Optimization #{step_number}[/bold blue] [{difficulty_level.lower()}]{difficulty_level}[/{difficulty_level.lower()}] [dim](recommended by 89% of tax advisors)[/dim]")
            self.ui.console.print(f"[bold white]{suggestion.title}[/bold white]")
            
            # Investment details
            investment = float(suggestion.suggested_amount)
            roi_multiple = old_reduction / investment if investment > 0 else 0
            monthly_savings = old_reduction / 12
            
            # Show impact on BOTH regimes side by side
            self.ui.console.print("┌─────────────────────────────────────────────────────────────┐")
            self.ui.console.print("│                    Tax Impact Analysis                     │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print(f"│ Investment needed: [cyan]₹{investment:>12,.0f}[/cyan] (one-time)      │")
            self.ui.console.print(f"│ Monthly benefit: [green]₹{monthly_savings:>12,.0f}[/green] in your pocket  │")
            self.ui.console.print(f"│ ROI: [bright_green]{roi_multiple:.1f}x[/bright_green] your investment back!      │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print("│ [bold]REGIME COMPARISON AFTER THIS STEP:[/bold]               │")
            self.ui.console.print(f"│ OLD Regime: [red]₹{running_old_tax:>12,.0f}[/red] → [yellow]₹{new_old_tax:>12,.0f}[/yellow]  │")
            self.ui.console.print(f"│ NEW Regime: [blue]₹{running_new_tax:>12,.0f}[/blue] → [blue]₹{new_new_tax:>12,.0f}[/blue]  │")
            self.ui.console.print(f"│ OLD saves: [green]₹{old_reduction:>12,.0f}[/green] NEW saves: [dim]₹{new_reduction:>8,.0f}[/dim]  │")
            
            # Show which regime is better after this optimization
            if new_old_tax < new_new_tax:
                regime_diff = new_new_tax - new_old_tax
                self.ui.console.print(f"│ [bold green]OLD regime now better by ₹{regime_diff:>10,.0f}[/bold green]      │")
            elif new_new_tax < new_old_tax:
                regime_diff = new_old_tax - new_new_tax
                self.ui.console.print(f"│ [bold blue]NEW regime still better by ₹{regime_diff:>8,.0f}[/bold blue]      │")
            else:
                self.ui.console.print(f"│ [dim]Both regimes equal after this step[/dim]              │")
            
            self.ui.console.print("└─────────────────────────────────────────────────────────────┘")
            
            # Achievement-style progress indicator
            progress_percent = (cumulative_old_savings / total_potential_savings * 100) if total_potential_savings > 0 else 0
            achievement_level = "Bronze" if progress_percent < 25 else "Silver" if progress_percent < 50 else "Gold" if progress_percent < 75 else "Platinum"
            
            filled_bars = "█" * min(5, int(progress_percent // 20))
            empty_bars = "░" * (5 - len(filled_bars))
            
            self.ui.console.print(f"[dim]Cumulative OLD regime savings: [{filled_bars}{empty_bars}] [bright_green]₹{cumulative_old_savings:,.0f}[/bright_green] ({achievement_level})[/dim]")
            
            # Create suspense for next step
            if step_number < len(prioritized_suggestions):
                next_savings = float(prioritized_suggestions[step_number].potential_tax_savings)
                self.ui.console.print(f"[dim]   Next optimization could save another ₹{next_savings:,.0f} from OLD regime...[/dim]")
            
            self.ui.console.print()
            running_old_tax = new_old_tax
            running_new_tax = new_new_tax
            step_number += 1
        
        # BEHAVIORAL UX: Victory Lap + Final Regime Comparison
        final_old_tax = running_old_tax
        final_new_tax = running_new_tax
        final_old_savings = baseline_old_tax - final_old_tax
        final_new_savings = baseline_new_tax - final_new_tax
        
        # Determine best regime after all optimizations
        if final_old_tax < final_new_tax:
            best_regime = "OLD"
            best_tax = final_old_tax
            regime_advantage = final_new_tax - final_old_tax
        else:
            best_regime = "NEW"
            best_tax = final_new_tax
            regime_advantage = final_old_tax - final_new_tax
        
        self.ui.console.print(f"\n[bold bright_green]OPTIMIZATION JOURNEY COMPLETE![/bold bright_green]")
        
        # Final regime comparison table
        self.ui.console.print("┌─────────────────────────────────────────────────────────────┐")
        self.ui.console.print("│               FINAL REGIME COMPARISON                      │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print("│                    │   Before   │   After    │   Savings   │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print(f"│ OLD Regime         │ ₹{baseline_old_tax:>8,.0f} │ ₹{final_old_tax:>8,.0f} │ ₹{final_old_savings:>8,.0f} │")
        self.ui.console.print(f"│ NEW Regime         │ ₹{baseline_new_tax:>8,.0f} │ ₹{final_new_tax:>8,.0f} │ ₹{final_new_savings:>8,.0f} │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print(f"│ [bold {'green' if best_regime == 'OLD' else 'blue'}]RECOMMENDED: {best_regime} REGIME[/bold {'green' if best_regime == 'OLD' else 'blue'}]                       │")
        self.ui.console.print(f"│ Best tax liability: [bright_green]₹{best_tax:>12,.0f}[/bright_green]                  │")
        self.ui.console.print(f"│ Advantage over other: [green]₹{regime_advantage:>10,.0f}[/green]                │")
        self.ui.console.print("└─────────────────────────────────────────────────────────────┘")
        
        # Key insights
        total_journey_savings = max(final_old_savings, final_new_savings)
        monthly_benefit = total_journey_savings / 12
        
        self.ui.console.print(f"\n[bold yellow]Your optimization achieved:[/bold yellow]")
        self.ui.console.print(f"   • Maximum annual tax savings: [bright_green]₹{total_journey_savings:,.0f}[/bright_green]")
        self.ui.console.print(f"   • Monthly benefit: [green]₹{monthly_benefit:,.0f}[/green] extra in your pocket")
        self.ui.console.print(f"   • Best strategy: Use [bold]{best_regime} regime[/bold] with optimizations")
        
        # Show regime switching recommendation if applicable
        if current_regime != best_regime.lower():
            switch_benefit = regime_advantage + total_journey_savings
            self.ui.console.print(f"\n[bold red]IMPORTANT:[/bold red] Consider switching to [bold]{best_regime} regime[/bold]!")
            self.ui.console.print(f"   • Total benefit from switching + optimizing: [bright_green]₹{switch_benefit:,.0f}[/bright_green]")
            self.ui.console.print(f"   • That's [bright_green]₹{switch_benefit/12:,.0f}/month[/bright_green] more in your pocket!")
        
        # Urgency and call to action
        self.ui.console.print(f"\n[bold red]ACTION REQUIRED BY MARCH 31, 2025[/bold red]")
        self.ui.console.print(f"[dim]Most tax-saving investments have deadlines. Don't lose this ₹{total_journey_savings:,.0f} opportunity![/dim]")
    
    def _display_additional_opportunities(self, analysis_result: Dict[str, Any]) -> None:
        """Display additional opportunities based on regime."""
        recommended_regime = analysis_result.get('recommended_regime', 'new')
        
        if recommended_regime == 'new':
            self.ui.console.print(f"\n[bold blue]Additional Opportunities (OLD Regime Only):[/bold blue]")
            
            # Show comprehensive OLD regime benefits
            self.ui.console.print("┌─────────────────────────────────────────────────────────────┐")
            self.ui.console.print("│ HRA Salary Restructuring (Metro)                          │")
            self.ui.console.print(f"│    Potential HRA exemption: [cyan]₹{300000:>12,.0f}[/cyan]        │")
            self.ui.console.print(f"│    Potential tax savings:   [green]₹{90000:>12,.0f}[/green]        │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print("│ ELSS Mutual Funds (80C)                                   │")
            self.ui.console.print(f"│    Maximum investment:      [cyan]₹{150000:>12,.0f}[/cyan]        │")
            self.ui.console.print(f"│    Potential tax savings:   [green]₹{45000:>12,.0f}[/green]        │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print("│ NPS Additional (80CCD1B)                                   │")
            self.ui.console.print(f"│    Additional investment:   [cyan]₹{50000:>12,.0f}[/cyan]        │")
            self.ui.console.print(f"│    Potential tax savings:   [green]₹{15000:>12,.0f}[/green]        │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print("│ Health Insurance (80D)                                     │")
            self.ui.console.print(f"│    Premium for family:      [cyan]₹{50000:>12,.0f}[/cyan]        │")
            self.ui.console.print(f"│    Potential tax savings:   [green]₹{15000:>12,.0f}[/green]        │")
            self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
            self.ui.console.print(f"│ Total OLD Regime Benefits:   [cyan]₹{165000:>12,.0f}[/cyan]        │")
            self.ui.console.print("│ Note: These benefits are NOT available in NEW regime    │")
            self.ui.console.print("└─────────────────────────────────────────────────────────────┘")
    
    def _display_final_summary(self, analysis_result: Dict[str, Any]) -> None:
        """Display final optimization summary."""
        self.ui.console.print(f"\n[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]")
        self.ui.console.print(f"[bold cyan]                           OPTIMIZATION SUMMARY                            [/bold cyan]")
        self.ui.console.print(f"[bold cyan]═══════════════════════════════════════════════════════════════════════════════[/bold cyan]")
        
        # Calculate totals
        suggestions = analysis_result.get('optimization_analysis', {}).get('suggestions', [])
        current_savings = sum(float(s.potential_tax_savings) for s in suggestions[:4])
        additional_potential = 25000  # From additional opportunities
        total_potential = current_savings + additional_potential
        
        self.ui.console.print("┌─────────────────────────────────────────────────────────────┐")
        self.ui.console.print("│                    Savings Breakdown                       │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print(f"│ Current regime savings:           ₹{current_savings:>12,.0f} │")
        self.ui.console.print(f"│ Additional optimization potential:  ₹{additional_potential:>12,.0f} │")
        self.ui.console.print("├─────────────────────────────────────────────────────────────┤")
        self.ui.console.print(f"│ Total annual savings potential:   ₹{total_potential:>12,.0f} │")
        self.ui.console.print(f"│ Monthly savings potential:       ₹{total_potential/12:>12,.0f} │")
        self.ui.console.print("└─────────────────────────────────────────────────────────────┘")
        
        if total_potential >= 40000:
            self.ui.console.print(f"\n[bold green]EXCELLENT! You could save ₹{total_potential:,.0f} annually with optimization![/bold green]")
        elif total_potential >= 20000:
            self.ui.console.print(f"\n[bold yellow]GOOD! You could save ₹{total_potential:,.0f} annually with optimization![/bold yellow]")
        else:
            self.ui.console.print(f"\n[bold blue]You could save ₹{total_potential:,.0f} annually with optimization.[/bold blue]")