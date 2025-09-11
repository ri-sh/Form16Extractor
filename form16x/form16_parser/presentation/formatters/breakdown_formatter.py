"""
Breakdown Formatter - Handles salary breakdown display formatting.

This formatter is responsible for displaying salary component breakdowns
in various visual formats including tree structure and tabular format.
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class BreakdownFormatter:
    """Formatter for salary breakdown display."""
    
    def __init__(self):
        """Initialize the breakdown formatter."""
        self.console = Console()
    
    def display_salary_breakdown(
        self,
        breakdown_data: Dict[str, Any],
        format_type: str = 'tree',
        show_percentages: bool = False
    ) -> None:
        """
        Display comprehensive salary breakdown.
        
        Args:
            breakdown_data: Salary breakdown data dictionary
            format_type: Display format ('tree', 'table', 'json')
            show_percentages: Whether to show percentage calculations
        """
        if not breakdown_data:
            self.console.print("[red]No breakdown data available[/red]")
            return
        
        self._display_breakdown_header()
        
        if format_type == 'tree':
            self._display_tree_breakdown(breakdown_data, show_percentages)
        elif format_type == 'table':
            self._display_table_breakdown(breakdown_data, show_percentages)
        elif format_type == 'json':
            self._display_json_breakdown(breakdown_data)
        else:
            self.console.print(f"[red]Unknown format type: {format_type}[/red]")
            return
        
        self._display_breakdown_summary(breakdown_data)
    
    def display_demo_breakdown(
        self,
        employee_name: str = "Ashish Mittal",
        employer_name: str = "Taxedo Technologies",
        format_type: str = 'tree',
        show_percentages: bool = False
    ) -> None:
        """
        Display demo salary breakdown for demonstration purposes.
        
        Args:
            employee_name: Demo employee name
            employer_name: Demo employer name
            format_type: Display format
            show_percentages: Whether to show percentages
        """
        demo_data = {
            'employee_name': employee_name,
            'employer_name': employer_name,
            'assessment_year': '2024-25',
            'gross_salary': 1200000,
            'components': {
                'basic_salary': 600000,
                'hra': 240000,
                'other_allowances': 360000
            },
            'deductions': {
                'tds': 78724,
                'professional_tax': 2500
            },
            'net_salary': 1121276
        }
        
        self.display_salary_breakdown(demo_data, format_type, show_percentages)
    
    def _display_breakdown_header(self) -> None:
        """Display formatted header for salary breakdown."""
        header_text = Text()
        header_text.append("Salary Breakdown Analysis", style="bold cyan")
        
        subtitle = Text()
        subtitle.append("Detailed component-wise breakdown of your salary structure", style="dim")
        
        self.console.print()
        self.console.print(header_text, justify="center")
        self.console.print(subtitle, justify="center")
        self.console.print("─" * 60, style="dim", justify="center")
        self.console.print()
    
    def _display_tree_breakdown(
        self, 
        breakdown_data: Dict[str, Any], 
        show_percentages: bool
    ) -> None:
        """Display breakdown in tree format."""
        gross_salary = breakdown_data.get('gross_salary', 0)
        components = breakdown_data.get('components', {})
        deductions = breakdown_data.get('deductions', {})
        net_salary = breakdown_data.get('net_salary', 0)
        
        # Create main tree
        tree = Tree(f"[bold cyan]Total Gross Salary: ₹{gross_salary:,.0f}[/bold cyan]")
        
        # Add salary components branch
        components_branch = tree.add("[bold green]Basic Salary Components[/bold green]")
        
        for component, amount in components.items():
            percentage = (amount / gross_salary * 100) if gross_salary > 0 else 0
            component_name = component.replace('_', ' ').title()
            
            if show_percentages:
                components_branch.add(f"{component_name}: ₹{amount:,.0f} ({percentage:.1f}%)")
            else:
                components_branch.add(f"{component_name}: ₹{amount:,.0f}")
        
        # Add deductions branch if available
        if deductions:
            deductions_branch = tree.add("[bold red]Tax Deducted at Source[/bold red]")
            
            total_deductions = sum(deductions.values())
            deduction_percentage = (total_deductions / gross_salary * 100) if gross_salary > 0 else 0
            
            if show_percentages:
                deductions_branch.add(f"Total TDS: ₹{total_deductions:,.0f} ({deduction_percentage:.1f}%)")
            else:
                deductions_branch.add(f"Total TDS: ₹{total_deductions:,.0f}")
            
            net_percentage = (net_salary / gross_salary * 100) if gross_salary > 0 else 0
            
            if show_percentages:
                deductions_branch.add(f"Net Take-Home Salary: ₹{net_salary:,.0f} ({net_percentage:.1f}%)")
            else:
                deductions_branch.add(f"Net Take-Home Salary: ₹{net_salary:,.0f}")
        
        self.console.print(tree)
    
    def _display_table_breakdown(
        self, 
        breakdown_data: Dict[str, Any], 
        show_percentages: bool
    ) -> None:
        """Display breakdown in table format."""
        gross_salary = breakdown_data.get('gross_salary', 0)
        components = breakdown_data.get('components', {})
        deductions = breakdown_data.get('deductions', {})
        
        # Create salary components table
        table = Table(title="Salary Component Breakdown")
        
        if show_percentages:
            table.add_column("Component", style="white", justify="left")
            table.add_column("Amount", style="yellow", justify="right")
            table.add_column("Percentage", style="cyan", justify="right")
        else:
            table.add_column("Component", style="white", justify="left")
            table.add_column("Amount", style="yellow", justify="right")
        
        # Add component rows
        for component, amount in components.items():
            component_name = component.replace('_', ' ').title()
            percentage = (amount / gross_salary * 100) if gross_salary > 0 else 0
            
            if show_percentages:
                table.add_row(component_name, f"₹{amount:,.0f}", f"{percentage:.1f}%")
            else:
                table.add_row(component_name, f"₹{amount:,.0f}")
        
        # Add separator and totals
        if show_percentages:
            table.add_row("─" * 20, "─" * 15, "─" * 10)
            table.add_row("[bold]Gross Total[/bold]", f"[bold]₹{gross_salary:,.0f}[/bold]", "[bold]100.0%[/bold]")
        else:
            table.add_row("─" * 20, "─" * 15)
            table.add_row("[bold]Gross Total[/bold]", f"[bold]₹{gross_salary:,.0f}[/bold]")
        
        self.console.print(table)
        
        # Display deductions table if available
        if deductions:
            self.console.print()
            deductions_table = Table(title="Deductions Breakdown")
            
            if show_percentages:
                deductions_table.add_column("Deduction", style="white", justify="left")
                deductions_table.add_column("Amount", style="red", justify="right")
                deductions_table.add_column("Percentage", style="cyan", justify="right")
            else:
                deductions_table.add_column("Deduction", style="white", justify="left")
                deductions_table.add_column("Amount", style="red", justify="right")
            
            for deduction, amount in deductions.items():
                deduction_name = deduction.replace('_', ' ').title()
                percentage = (amount / gross_salary * 100) if gross_salary > 0 else 0
                
                if show_percentages:
                    deductions_table.add_row(deduction_name, f"₹{amount:,.0f}", f"{percentage:.1f}%")
                else:
                    deductions_table.add_row(deduction_name, f"₹{amount:,.0f}")
            
            self.console.print(deductions_table)
    
    def _display_json_breakdown(self, breakdown_data: Dict[str, Any]) -> None:
        """Display breakdown in JSON format."""
        import json
        
        formatted_json = json.dumps(breakdown_data, indent=2, ensure_ascii=False)
        
        panel = Panel(
            formatted_json,
            title="[bold cyan]Salary Breakdown (JSON Format)[/bold cyan]",
            border_style="cyan"
        )
        
        self.console.print(panel)
    
    def _display_breakdown_summary(self, breakdown_data: Dict[str, Any]) -> None:
        """Display summary information for the breakdown."""
        employee_name = breakdown_data.get('employee_name', 'N/A')
        employer_name = breakdown_data.get('employer_name', 'N/A')
        assessment_year = breakdown_data.get('assessment_year', 'N/A')
        
        summary_text = f"Summary for {employee_name}\n"
        summary_text += f"Employer: {employer_name}\n"
        summary_text += f"Assessment Year: {assessment_year}"
        
        self.console.print()
        self.console.print(summary_text, style="dim")
    
    def display_simple_breakdown(
        self, 
        gross_salary: float, 
        components: Dict[str, float],
        employee_name: str = "N/A",
        employer_name: str = "N/A"
    ) -> None:
        """
        Display a simple salary breakdown without complex formatting.
        
        Args:
            gross_salary: Total gross salary
            components: Dictionary of salary components
            employee_name: Employee name
            employer_name: Employer name
        """
        self.console.print(f"\n[bold cyan]Salary Breakdown for {employee_name}[/bold cyan]")
        self.console.print(f"Employer: {employer_name}")
        self.console.print("─" * 40)
        
        for component, amount in components.items():
            component_name = component.replace('_', ' ').title()
            percentage = (amount / gross_salary * 100) if gross_salary > 0 else 0
            self.console.print(f"{component_name:.<25} ₹{amount:>10,.0f} ({percentage:>5.1f}%)")
        
        self.console.print("─" * 40)
        self.console.print(f"{'Gross Total':.<25} ₹{gross_salary:>10,.0f} (100.0%)")
    
    def display_error_message(self, error: str) -> None:
        """
        Display error message for breakdown operations.
        
        Args:
            error: Error message to display
        """
        error_panel = Panel(
            f"[red]Error: {error}[/red]",
            title="[bold red]Breakdown Error[/bold red]",
            border_style="red"
        )
        
        self.console.print(error_panel)