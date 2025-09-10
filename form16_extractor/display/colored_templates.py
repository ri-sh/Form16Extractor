"""
Colored Display Templates for Form16 Tax Calculation Results

This module contains all the visual templates and formatting functions
for the colored display mode to improve code organization and maintainability.
"""

from typing import Dict, Any


class ColoredDisplayTemplates:
    """Templates and formatting functions for colored tax calculation display."""
    
    # ANSI Color Codes
    CYAN = '\033[96m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_RED = '\033[91m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # Background colors
    BG_GREEN = '\033[102m\033[30m'    # Light green bg with black text
    BG_RED = '\033[101m\033[30m'      # Light red bg with black text
    BG_BLUE = '\033[104m\033[97m'     # Blue bg with white text
    BG_YELLOW = '\033[103m\033[30m'   # Yellow bg with black text

    @classmethod
    def render_header(cls) -> str:
        """Render the main header section."""
        return f"""
{cls.CYAN}{cls.BOLD}{'='*65}{cls.RESET}
{cls.CYAN}{cls.BOLD}         TAX REGIME COMPARISON - VISUAL ANALYSIS{cls.RESET}
{cls.CYAN}{cls.BOLD}{'='*65}{cls.RESET}"""

    @classmethod
    def render_employee_details(cls, employee_info: Dict[str, str]) -> str:
        """Render employee information section."""
        return f"""
    {cls.BLUE}{cls.BOLD}EMPLOYEE DETAILS:{cls.RESET}
    {cls.WHITE}Name:{cls.RESET} {employee_info.get('name', 'N/A')}
    {cls.WHITE}PAN:{cls.RESET} {employee_info.get('pan', 'N/A')}
    {cls.WHITE}Employer:{cls.RESET} {employee_info.get('employer', 'N/A')}
    {cls.WHITE}Assessment Year:{cls.RESET} {employee_info.get('assessment_year', 'N/A')}"""

    @classmethod
    def render_income_breakdown(cls, section_17_1: float, section_17_2: float, total_salary: float) -> str:
        """Render income breakdown box."""
        return f"""
    {cls.MAGENTA}{cls.BOLD}INCOME BREAKDOWN:{cls.RESET}
    ┌───────────────────────────────────────────────────┐
    │ {cls.WHITE}Section 17(1) Basic Salary:{cls.RESET}        {cls.YELLOW}₹{section_17_1:>12,.0f}{cls.RESET}  │
    │ {cls.WHITE}Section 17(2) Perquisites/ESOPs:{cls.RESET}   {cls.YELLOW}₹{section_17_2:>12,.0f}{cls.RESET}  │
    │ ───────────────────────────────────────────────── │
    │ {cls.BOLD}{cls.WHITE}Total Taxable Salary:{cls.RESET}              {cls.CYAN}{cls.BOLD}₹{total_salary:>12,.0f}{cls.RESET}  │
    └───────────────────────────────────────────────────┘"""

    @classmethod
    def render_regime_comparison_header(cls) -> str:
        """Render regime comparison section header."""
        return f"\n    {cls.BOLD}{cls.UNDERLINE}REGIME COMPARISON ANALYSIS:{cls.RESET}"

    @classmethod
    def render_old_regime_box(
        cls, 
        is_winner: bool,
        total_salary: float,
        section_80c: float,
        section_80ccd_1b: float,
        taxable_income: float,
        tax_liability: float,
        tds_paid: float,
        refund_due: float,
        tax_due: float
    ) -> str:
        """Render OLD tax regime calculation box."""
        bg_color = cls.BG_GREEN if is_winner else cls.BG_RED
        border_color = cls.LIGHT_GREEN if is_winner else cls.LIGHT_RED
        status = " WINNER" if is_winner else " COSTLIER"
        
        balance_line = (
            f"    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Refund Due:{cls.RESET}                      {cls.LIGHT_GREEN}{cls.BOLD}₹{refund_due:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}"
            if refund_due > 0 else
            f"    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Additional Tax Due:{cls.RESET}              {cls.LIGHT_RED}{cls.BOLD}₹{tax_due:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}"
        )
        
        return f"""
    {border_color}┌─────────────────────────────────────────────────┐{cls.RESET}
    {border_color}│{bg_color}  OLD TAX REGIME (2024-25) - {status:<12} {cls.RESET}{border_color}       │{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Gross Salary:{cls.RESET}                    {cls.CYAN}₹{total_salary:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Less: Section 80C Deductions:{cls.RESET}    {cls.YELLOW}₹{section_80c:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Less: Section 80CCD(1B):{cls.RESET}         {cls.YELLOW}₹{section_80ccd_1b:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Less: Standard Deduction:{cls.RESET}        {cls.YELLOW}₹{50000:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│ ────────────────────────────────────────────────│ 
    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Taxable Income:{cls.RESET}                  {cls.MAGENTA}{cls.BOLD}₹{taxable_income:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Tax Liability:{cls.RESET}                   {cls.LIGHT_RED}{cls.BOLD}₹{tax_liability:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}TDS Already Paid:{cls.RESET}                {cls.LIGHT_GREEN}₹{tds_paid:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
{balance_line}
    {border_color}└─────────────────────────────────────────────────┘{cls.RESET}"""

    @classmethod
    def render_new_regime_box(
        cls,
        is_winner: bool,
        total_salary: float,
        section_80ccd_1b: float,
        taxable_income: float,
        tax_liability: float,
        tds_paid: float,
        refund_due: float,
        tax_due: float
    ) -> str:
        """Render NEW tax regime calculation box."""
        bg_color = cls.BG_GREEN if is_winner else cls.BG_RED
        border_color = cls.LIGHT_GREEN if is_winner else cls.LIGHT_RED
        status = " WINNER" if is_winner else " COSTLIER"
        
        balance_line = (
            f"    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Refund Due:{cls.RESET}                      {cls.LIGHT_GREEN}{cls.BOLD}₹{refund_due:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}"
            if refund_due > 0 else
            f"    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Additional Tax Due:{cls.RESET}              {cls.LIGHT_RED}{cls.BOLD}₹{tax_due:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}"
        )
        
        return f"""
    {border_color}┌─────────────────────────────────────────────────┐{cls.RESET}
    {border_color}│{bg_color}  NEW TAX REGIME (2024-25) - {status:<8} {cls.RESET}{border_color}           │{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Gross Salary:{cls.RESET}                    {cls.CYAN}₹{total_salary:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Less: Section 80CCD(1B):{cls.RESET}         {cls.YELLOW}₹{section_80ccd_1b:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}Less: Standard Deduction:{cls.RESET}        {cls.YELLOW}₹{50000:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.DIM}(No other deductions allowed){cls.RESET}                 {border_color} │{cls.RESET}
    {border_color}│─────────────────────────────────────────────────│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Taxable Income:{cls.RESET}                  {cls.MAGENTA}{cls.BOLD}₹{taxable_income:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.BOLD}{cls.WHITE}Tax Liability:{cls.RESET}                   {cls.LIGHT_RED}{cls.BOLD}₹{tax_liability:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
    {border_color}│{cls.RESET}  {cls.WHITE}TDS Already Paid:{cls.RESET}                {cls.LIGHT_GREEN}₹{tds_paid:>12,.0f}{cls.RESET} {border_color}│{cls.RESET}
{balance_line}
    {border_color}└─────────────────────────────────────────────────┘{cls.RESET}"""

    @classmethod
    def render_recommendation(cls, better_regime: str, savings: float) -> str:
        """Render final recommendation section."""
        regime_text = "OLD REGIME" if better_regime == 'old' else "NEW REGIME"
        
        return f"""
{cls.YELLOW}{cls.BOLD}{'='*65}{cls.RESET}
{cls.BG_GREEN}  RECOMMENDATION: Choose {regime_text} - Save Rs {savings:,.0f} annually! {cls.RESET}
{cls.YELLOW}{cls.BOLD}{'='*65}{cls.RESET}"""

    @classmethod
    def render_summary_metrics(
        cls, 
        old_effective_rate: float, 
        new_effective_rate: float, 
        savings: float
    ) -> str:
        """Render summary metrics section."""
        return f"""
    {cls.BLUE}{cls.BOLD}SUMMARY METRICS:{cls.RESET}
    • {cls.WHITE}Old Regime Effective Rate:{cls.RESET} {old_effective_rate:.2f}%
    • {cls.WHITE}New Regime Effective Rate:{cls.RESET} {new_effective_rate:.2f}%
    • {cls.WHITE}Annual Tax Savings:{cls.RESET} {cls.LIGHT_GREEN}Rs {savings:,.0f}{cls.RESET}
    • {cls.WHITE}Monthly Tax Savings:{cls.RESET} {cls.LIGHT_GREEN}Rs {savings/12:,.0f}{cls.RESET}
"""

    @classmethod
    def render_single_regime_message(cls, assessment_year: str) -> str:
        """Render message for single regime (historical years)."""
        return f"""
{cls.YELLOW}{cls.BOLD}{'='*65}{cls.RESET}
{cls.BG_BLUE}  TAX REGIME: Only OLD REGIME applicable for {assessment_year}        {cls.RESET}
{cls.YELLOW}{cls.BOLD}{'='*65}{cls.RESET}

    {cls.WHITE}Note:{cls.RESET} New tax regime was not available in {assessment_year}.
    Only old tax regime rules apply for this assessment year."""

    @classmethod
    def render_single_regime_summary(cls, effective_rate: float) -> str:
        """Render summary for single regime calculation."""
        return f"""
    {cls.BLUE}{cls.BOLD}TAX SUMMARY:{cls.RESET}
    • {cls.WHITE}Effective Tax Rate:{cls.RESET} {effective_rate:.2f}%
    • {cls.WHITE}Tax Regime:{cls.RESET} Old Regime (Only option for this year)
"""


class ColoredDisplayRenderer:
    """Main renderer class for colored tax calculation display."""
    
    def __init__(self):
        self.templates = ColoredDisplayTemplates()
    
    def render_complete_display(self, tax_results: Dict[str, Any]) -> str:
        """Render the complete colored display for tax regime comparison."""
        # Extract data
        old_regime = tax_results.get('regime_comparison', {}).get('old_regime', {})
        new_regime = tax_results.get('regime_comparison', {}).get('new_regime', {})
        employee_info = tax_results.get('employee_info', {})
        financial_data = tax_results.get('financial_data', {})
        
        # Check if new regime is actually calculated (has valid data)
        new_regime_available = (new_regime and 
                               'tax_liability' in new_regime and 
                               new_regime.get('tax_liability') not in [float('inf'), None])
        
        # Calculate key values
        old_tax = old_regime.get('tax_liability', float('inf'))
        new_tax = new_regime.get('tax_liability', float('inf')) if new_regime_available else float('inf')
        
        # Only compare if both regimes are available
        if new_regime_available:
            better_regime = 'old' if old_tax < new_tax else 'new'
            savings = abs(old_tax - new_tax)
        else:
            better_regime = 'old'  # Only old regime available
            savings = 0
        
        # Extract financial data
        section_17_1 = financial_data.get('section_17_1_salary', 0)
        section_17_2 = financial_data.get('section_17_2_perquisites', 0)
        section_80c = financial_data.get('section_80c', 0)
        section_80ccd_1b = financial_data.get('section_80ccd_1b', 0)
        total_tds = financial_data.get('total_tds', 0)
        total_salary = section_17_1 + section_17_2
        
        # Calculate taxable incomes
        old_taxable = max(0, total_salary - section_80c - section_80ccd_1b - 50000)
        new_taxable = max(0, total_salary - section_80ccd_1b - 50000)
        
        # Calculate refunds/dues
        old_refund_due = max(0, total_tds - old_tax)
        old_tax_due = max(0, old_tax - total_tds)
        new_refund_due = max(0, total_tds - new_tax)
        new_tax_due = max(0, new_tax - total_tds)
        
        # Calculate effective rates
        old_effective = (old_tax / total_salary * 100) if total_salary > 0 else 0
        new_effective = (new_tax / total_salary * 100) if total_salary > 0 else 0
        
        # Render all sections
        output = []
        output.append(self.templates.render_header())
        output.append(self.templates.render_employee_details(employee_info))
        output.append(self.templates.render_income_breakdown(section_17_1, section_17_2, total_salary))
        output.append(self.templates.render_regime_comparison_header())
        
        # Old regime box
        output.append(self.templates.render_old_regime_box(
            is_winner=(better_regime == 'old'),
            total_salary=total_salary,
            section_80c=section_80c,
            section_80ccd_1b=section_80ccd_1b,
            taxable_income=old_taxable,
            tax_liability=old_tax,
            tds_paid=total_tds,
            refund_due=old_refund_due,
            tax_due=old_tax_due
        ))
        
        # Only show new regime box if new regime is available
        if new_regime_available:
            # New regime box
            output.append(self.templates.render_new_regime_box(
                is_winner=(better_regime == 'new'),
                total_salary=total_salary,
                section_80ccd_1b=section_80ccd_1b,
                taxable_income=new_taxable,
                tax_liability=new_tax,
                tds_paid=total_tds,
                refund_due=new_refund_due,
                tax_due=new_tax_due
            ))
            
            output.append(self.templates.render_recommendation(better_regime, savings))
            output.append(self.templates.render_summary_metrics(old_effective, new_effective, savings))
        else:
            # Show single regime message for historical years
            output.append(self.templates.render_single_regime_message(employee_info.get('assessment_year', 'N/A')))
            output.append(self.templates.render_single_regime_summary(old_effective))
        
        return '\n'.join(output)