"""
Rich UI Components for Form16x CLI

Provides beautiful, animated, and user-friendly CLI components using the Rich library.
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import time

from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.align import Align
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich import print as rprint


class RichUIComponents:
    """Rich UI components for beautiful CLI display"""
    
    def __init__(self):
        self.console = Console()
    
    def show_animated_header(self, title: str, subtitle: str = ""):
        """Show animated header with title and subtitle"""
        # Create animated border
        for i in range(3):
            if i < 2:
                border_char = "━" if i == 0 else "═"
                self.console.print(f"[bold blue]{border_char * 80}[/bold blue]")
                time.sleep(0.1)
        
        # Main title with animation
        title_text = Text(title, style="bold magenta", justify="center")
        title_panel = Panel(title_text, box=DOUBLE, border_style="bright_blue")
        self.console.print(title_panel)
        
        if subtitle:
            subtitle_text = Text(subtitle, style="italic cyan", justify="center")
            self.console.print(Align.center(subtitle_text))
            self.console.print()
        
        time.sleep(0.3)
    
    def create_salary_tree(self, salary_data: Dict[str, Any], show_percentages: bool = False) -> Tree:
        """Create a rich tree structure for salary breakdown"""
        gross_salary = float(salary_data.get('gross_salary', 0))
        
        # Root tree
        tree = Tree(
            f"[bold green]Total Gross Salary: ₹{gross_salary:,.0f}[/bold green]",
            style="bold green"
        )
        
        # Basic salary components
        basic_branch = tree.add("[bold blue]Basic Salary Components[/bold blue]")
        
        section_17_1 = float(salary_data.get('section_17_1_salary', 0))
        if section_17_1 > 0:
            percentage = (section_17_1 / gross_salary * 100) if gross_salary > 0 else 0
            basic_text = f"Basic Salary: ₹{section_17_1:,.0f}"
            if show_percentages:
                basic_text += f" ({percentage:.1f}%)"
            basic_branch.add(f"[green]{basic_text}[/green]")
        
        # HRA if available
        hra_amount = float(salary_data.get('hra_received', 0))
        if hra_amount > 0:
            percentage = (hra_amount / gross_salary * 100) if gross_salary > 0 else 0
            hra_text = f"House Rent Allowance: ₹{hra_amount:,.0f}"
            if show_percentages:
                hra_text += f" ({percentage:.1f}%)"
            basic_branch.add(f"[yellow]{hra_text}[/yellow]")
        
        # Other allowances
        other_allowances = gross_salary - section_17_1 - hra_amount
        if other_allowances > 0:
            percentage = (other_allowances / gross_salary * 100) if gross_salary > 0 else 0
            other_text = f"Other Allowances: ₹{other_allowances:,.0f}"
            if show_percentages:
                other_text += f" ({percentage:.1f}%)"
            basic_branch.add(f"[cyan]{other_text}[/cyan]")
        
        # Perquisites
        perquisites = float(salary_data.get('section_17_2_perquisites', 0))
        if perquisites > 0:
            perq_branch = tree.add("[bold magenta]Perquisites and Benefits[/bold magenta]")
            percentage = (perquisites / gross_salary * 100) if gross_salary > 0 else 0
            perq_text = f"Total Perquisites: ₹{perquisites:,.0f}"
            if show_percentages:
                perq_text += f" ({percentage:.1f}%)"
            perq_branch.add(f"[magenta]{perq_text}[/magenta]")
        
        # Profits in lieu of salary
        profits = float(salary_data.get('section_17_3_profits_in_lieu', 0))
        if profits > 0:
            profit_branch = tree.add("[bold red]Profits in Lieu of Salary[/bold red]")
            percentage = (profits / gross_salary * 100) if gross_salary > 0 else 0
            profit_text = f"Total Profits: ₹{profits:,.0f}"
            if show_percentages:
                profit_text += f" ({percentage:.1f}%)"
            profit_branch.add(f"[red]{profit_text}[/red]")
        
        # TDS Information
        tds_amount = float(salary_data.get('total_tds', 0))
        if tds_amount > 0:
            tds_branch = tree.add("[bold yellow]Tax Deducted at Source[/bold yellow]")
            percentage = (tds_amount / gross_salary * 100) if gross_salary > 0 else 0
            tds_text = f"Total TDS: ₹{tds_amount:,.0f}"
            if show_percentages:
                tds_text += f" ({percentage:.1f}%)"
            tds_branch.add(f"[yellow]{tds_text}[/yellow]")
            
            # Net salary after TDS
            net_salary = gross_salary - tds_amount
            net_percentage = (net_salary / gross_salary * 100) if gross_salary > 0 else 0
            net_text = f"Net Take-Home Salary: ₹{net_salary:,.0f}"
            if show_percentages:
                net_text += f" ({net_percentage:.1f}%)"
            tds_branch.add(f"[bright_green]{net_text}[/bright_green]")
        
        return tree
    
    def create_tax_optimization_panel(self, current_tax_data: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> Panel:
        """Create a panel showing tax optimization suggestions"""
        
        # Current tax situation
        old_tax = current_tax_data.get('old_regime', {}).get('tax_liability', 0)
        new_tax = current_tax_data.get('new_regime', {}).get('tax_liability', 0)
        current_deductions = current_tax_data.get('old_regime', {}).get('deductions_used', {})
        
        content = []
        
        # Current situation
        content.append("[bold blue]CURRENT TAX SITUATION[/bold blue]\n")
        content.append(f"Old Regime Tax: [red]₹{old_tax:,.0f}[/red]")
        content.append(f"New Regime Tax: [green]₹{new_tax:,.0f}[/green]")
        content.append(f"Current 80C Used: [yellow]₹{current_deductions.get('80C', 0):,.0f}[/yellow]")
        content.append("")
        
        # Optimization suggestions
        content.append("[bold green]OPTIMIZATION OPPORTUNITIES[/bold green]\n")
        
        total_potential_savings = 0
        for i, suggestion in enumerate(suggestions, 1):
            investment_type = suggestion.get('type', 'Unknown')
            amount = suggestion.get('amount', 0)
            tax_savings = suggestion.get('tax_savings', 0)
            ease = suggestion.get('ease', 'Medium')
            
            total_potential_savings += tax_savings
            
            ease_indicator = {"Easy": "[green]Easy[/green]", "Medium": "[yellow]Medium[/yellow]", "Hard": "[red]Hard[/red]"}.get(ease, "[yellow]Medium[/yellow]")
            
            content.append(f"[bold]{i}. {investment_type}[/bold]")
            content.append(f"   Investment Amount: ₹{amount:,.0f}")
            content.append(f"   Tax Savings: [green]₹{tax_savings:,.0f}[/green]")
            content.append(f"   Implementation Difficulty: {ease_indicator}")
            content.append("")
        
        # Summary
        content.append(f"[bold magenta]TOTAL POTENTIAL SAVINGS: ₹{total_potential_savings:,.0f}[/bold magenta]")
        
        panel_content = "\n".join(content)
        
        return Panel(
            panel_content,
            title="[bold cyan]Tax Optimization Analysis[/bold cyan]",
            box=ROUNDED,
            border_style="cyan"
        )
    
    def create_interactive_progress(self, task_name: str, steps: List[str]) -> Progress:
        """Create an interactive progress bar for multi-step operations"""
        progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            console=self.console
        )
        return progress
    
    def show_comparison_table(self, old_regime: Dict, new_regime: Dict) -> Table:
        """Create a beautiful comparison table for tax regimes"""
        table = Table(show_header=True, header_style="bold magenta", box=HEAVY)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Old Regime", justify="right", style="red")
        table.add_column("New Regime", justify="right", style="green")
        table.add_column("Difference", justify="right", style="yellow")
        
        # Add rows
        components = [
            ("Taxable Income", "taxable_income"),
            ("Tax Liability", "tax_liability"),
            ("TDS Paid", "tds_paid"),
            ("Balance", "balance"),
            ("Effective Rate", "effective_tax_rate")
        ]
        
        for name, key in components:
            old_val = old_regime.get(key, 0)
            new_val = new_regime.get(key, 0)
            
            if key == "effective_tax_rate":
                old_str = f"{old_val:.2f}%"
                new_str = f"{new_val:.2f}%"
                diff_str = f"{new_val - old_val:+.2f}%"
            else:
                old_str = f"₹{old_val:,.0f}"
                new_str = f"₹{new_val:,.0f}"
                diff_val = new_val - old_val
                diff_str = f"₹{diff_val:+,.0f}"
                if diff_val < 0:
                    diff_str = f"[green]{diff_str}[/green]"
                elif diff_val > 0:
                    diff_str = f"[red]{diff_str}[/red]"
            
            table.add_row(name, old_str, new_str, diff_str)
        
        return table
    
    def show_loading_animation(self, message: str, duration: float = 2.0):
        """Show a loading animation with message"""
        with self.console.status(f"[bold green]{message}...") as status:
            time.sleep(duration)
    
    def get_user_input(self, prompt: str, choices: Optional[List[str]] = None) -> str:
        """Get user input with validation"""
        if choices:
            return Prompt.ask(prompt, choices=choices, console=self.console)
        else:
            return Prompt.ask(prompt, console=self.console)
    
    def confirm_action(self, message: str) -> bool:
        """Get confirmation from user"""
        return Confirm.ask(message, console=self.console)
    
    def display_success_message(self, message: str):
        """Display a success message with animation"""
        success_panel = Panel(
            f"[bold green]SUCCESS: {message}[/bold green]",
            box=ROUNDED,
            border_style="green"
        )
        self.console.print(success_panel)
        time.sleep(0.5)
    
    def display_error_message(self, message: str):
        """Display an error message"""
        error_panel = Panel(
            f"[bold red]ERROR: {message}[/bold red]",
            box=ROUNDED,
            border_style="red"
        )
        self.console.print(error_panel)