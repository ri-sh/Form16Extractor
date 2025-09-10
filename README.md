# Form16x - Form16 Parser

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/badge/ci-github--actions-lightgrey)](#)
[![Coverage](https://img.shields.io/badge/coverage-XX%25-yellow)](#)

**A privacy-first, open-source tool to parse Indian Form 16 PDFs into structured JSON.**
*I built this to make my own tax filing easier — sharing it in case it helps others.*

![demo-gif](assets/demo.gif) <!-- replace with your GIF or screenshot -->

---

## TL;DR

Form16x extracts Part A & Part B from Form 16 PDFs and outputs structured JSON with employee/employer details, salary components, deductions (80C/80D/etc.), TDS breakdown, and computed tax for old/new regimes.

* Runs fully **offline** (no uploads).
* Works with common layout variants and imperfect PDFs.
* Useful for automation, bulk processing, or prepping data for ITR filing.

---

## Features

* **Multi-employer support**: consolidate multiple Form 16s into one combined JSON (helpful if you switched jobs in a year)
* Extracts employee & employer metadata (name, PAN, TAN, address)
* Salary breakup: basic, DA, HRA, allowances, exemptions
* Deduction extraction (80C, 80D, 80CCD, etc.)
* Quarterly TDS & challan references
* Tax computation: old vs new regime summary
* CLI + Python API
* Local processing only — no network calls by default
* Confidence scores & extraction metrics

---

## Installation

### Prerequisites

**Python 3.8 or higher** is required. Check your Python version:
```bash
python --version  # or python3 --version
```

### System Dependencies

This project uses **camelot-py** for robust PDF table extraction, which requires some system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt install ghostscript python3-tk
```

**macOS:**
```bash
brew install ghostscript tcl-tk
# Fix library linking (if needed):
mkdir -p ~/lib
ln -s "$(brew --prefix gs)/lib/libgs.dylib" ~/lib
```

**Windows:**
- Install [Ghostscript](https://www.ghostscript.com/download/gsdnld.html)
- Install [ActiveTcl Community Edition](https://www.activestate.com/products/tcl/)

### Install Form16x

**Option 1: Install from PyPI (Recommended - Once published)**
```bash
pip install form16x

# Now use the form16x command
form16x extract json path/to/Form16.pdf --calculate-tax
```

**Option 2: Install from Source (Current method)**
```bash
git clone https://github.com/ri-sh/form16x.git
cd form16x

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip to latest version (required for modern pyproject.toml support)
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install as package for form16x command (requires pip >= 21.3)
pip install -e .

# Now use the form16x command
form16x extract json path/to/Form16.pdf --calculate-tax
```

**Important:** If you get "setup.py not found" error, your pip version is too old. Upgrade pip:
```bash
python -m pip install --upgrade pip  # Requires pip >= 21.3 for pyproject.toml support
```

**Note:** If you encounter issues with camelot installation, see the [official camelot-py installation guide](https://camelot-py.readthedocs.io/en/master/user/install-deps.html).

---

## Quick CLI example

```bash
# Extract to JSON
form16x extract json form16_sample.pdf --output result.json

# Consolidate multiple Form16s from different employers
form16x consolidate --files company1.pdf company2.pdf --calculate-tax 

# Extract with tax calculation
form16x extract json form16_sample.pdf --calculate-tax

# Get detailed tax breakdown with regime comparison
form16x extract json form16_sample.pdf --calculate-tax --summary 

# Calculate for specific regime only
form16x extract json form16_sample.pdf --calculate-tax --tax-regime new

# Visual colored display with regime comparison (best for analysis)
form16x extract json form16_sample.pdf --calculate-tax --display-mode colored

# Plain table display for simple text output
form16x extract json form16_sample.pdf --calculate-tax --display-mode table

# Add bank interest income for accurate 80TTA/80TTB calculations
form16x extract json form16_sample.pdf --calculate-tax --bank-interest 25000

# Include other income sources (rental, freelance, etc.)
form16x extract json form16_sample.pdf --calculate-tax --other-income 50000

# Tax calculation for senior citizens (60-80 years)
form16x extract json form16_sample.pdf --calculate-tax --age-category senior_60_to_80

# NEW: Detailed salary breakdown analysis
form16x breakdown form16_sample.pdf --show-percentages

# NEW: Tax optimization recommendations
form16x optimize form16_sample.pdf --target-savings 50000

# Extract to CSV format
form16x extract csv form16_sample.pdf --output data.csv

# Get help and supported assessment years
form16x --help
form16x info
```

---

## New Commands (v2.2.0)

### Salary Breakdown Analysis

Get detailed salary component analysis with tree structure visualization:

```bash
# Basic salary breakdown
form16x breakdown path/to/Form16.pdf

# With percentage analysis
form16x breakdown path/to/Form16.pdf --show-percentages

# Demo mode for testing
form16x breakdown --demo
```

**Features:**
- Tree structure visualization of salary components
- Classification of Basic, HRA, Special Allowance, Transport, etc.
- Taxable vs non-taxable component separation
- Optional percentage analysis showing component distribution
- Rich terminal formatting with professional display

### Tax Optimization Engine

Get actionable tax-saving recommendations:

```bash
# Basic tax optimization analysis
form16x optimize path/to/Form16.pdf

# Target-based optimization (specify savings goal)
form16x optimize path/to/Form16.pdf --target-savings 50000

# Demo mode for testing
form16x optimize --demo
```

**Features:**
- Comprehensive analysis of tax-saving sections (80C, 80D, 80CCD(1B), 80TTA, etc.)
- ROI-based investment recommendations
- Regime-specific advice (Old vs New tax regime)
- Step-by-step implementation guidance
- Current vs optimized tax comparison
- Difficulty-based prioritization (Easy, Moderate, Difficult)
- Real savings calculations with exact amounts

**Sample Output:**
```
Your Current Tax Profile:
• Currently using: NEW regime
• Taxable income: ₹8,62,724
• Current tax liability: ₹78,723

Top Tax-Saving Recommendations:

1. Public Provident Fund Investment
   Section: 80C | Potential Savings: ₹20,000 | ROI: 20.00%
   Investment: ₹1,00,000
   Steps: Open PPF account → Set up monthly SIP → Invest before March 31st

2. Health Insurance Premium  
   Section: 80D | Potential Savings: ₹5,000 | ROI: 20.00%
   Investment: ₹25,000
   Steps: Compare plans → Choose family coverage → Pay premium before March 31st
```

---

## Python usage example

### Quick Start - Direct imports from form16x

```python
from form16x import TaxCalculationAPI, TaxRegime, EnhancedForm16Extractor
from decimal import Decimal

# Initialize API for tax calculations
api = TaxCalculationAPI()

# Calculate tax from Form16 PDF
result = api.calculate_tax_from_form16(
    form16_file="form16_sample.pdf",
    regime=TaxRegime.BOTH,
    bank_interest=Decimal("25000")
)

print(result['recommendation'])  # e.g., "NEW regime saves ₹25,000 annually"
```

### Detailed extraction example

```python
from form16x.form16_parser.extractors.enhanced_form16_extractor import EnhancedForm16Extractor
from form16x.form16_parser.pdf.reader import RobustPDFProcessor

# Initialize extractor and PDF processor
extractor = EnhancedForm16Extractor()
pdf_processor = RobustPDFProcessor()

# Extract tables from PDF
extraction_result = pdf_processor.extract_tables("form16_sample.pdf")
tables = extraction_result.tables

# Extract Form16 data
form16_result = extractor.extract_all(tables)

# Access extracted data
print(form16_result.employee.name)
print(form16_result.salary.gross_salary)
print(form16_result.employer.name)
```

### Tax Calculation API

```python
from form16x.form16_parser.api import TaxCalculationAPI, TaxRegime
from decimal import Decimal

# Initialize API
api = TaxCalculationAPI()

# Calculate tax from Form16 PDF
result = api.calculate_tax_from_form16(
    form16_file="form16_sample.pdf",
    regime=TaxRegime.BOTH,
    bank_interest=Decimal("25000")
)

# Calculate tax from manual input
result = api.calculate_tax_from_input(
    assessment_year="2024-25",
    gross_salary=Decimal("1200000"),
    regime=TaxRegime.BOTH,
    section_80c=Decimal("150000"),
    tds_paid=Decimal("180000")
)

print(result['recommendation'])  # e.g., "NEW regime saves ₹25,000 annually"
```

### Complete Tax Calculation Example for 2024-25

Here's a comprehensive example showing how to calculate tax for the 2024-25 assessment year with all major income sources and deductions:

```python
from form16x.form16_parser.api.tax_calculation_api import TaxCalculationAPI, TaxRegime, AgeCategoryEnum
from decimal import Decimal

# Initialize the tax calculation API
api = TaxCalculationAPI()

# Example: Software engineer with ₹15 lakhs gross salary
result = api.calculate_tax_from_input(
    assessment_year="2024-25",
    gross_salary=Decimal("1500000"),          # ₹15 lakhs gross salary
    basic_salary=Decimal("600000"),           # ₹6 lakhs basic salary
    hra_received=Decimal("180000"),           # ₹1.8 lakhs HRA received
    bank_interest=Decimal("45000"),           # ₹45,000 bank interest (triggers 80TTA)
    other_income=Decimal("75000"),            # ₹75,000 freelance/other income
    house_property_income=Decimal("120000"),  # ₹1.2 lakhs rental income
    section_80c=Decimal("150000"),            # ₹1.5 lakhs in PPF/ELSS/LIC (max limit)
    section_80ccd_1b=Decimal("50000"),        # ₹50,000 NPS contribution (additional)
    tds_paid=Decimal("185000"),               # ₹1.85 lakhs TDS already deducted
    city_type="metro",                        # Living in metro city (for HRA exemption)
    regime=TaxRegime.BOTH,                    # Calculate both old and new regime
    age_category=AgeCategoryEnum.BELOW_60,    # Below 60 years
    verbose=True
)

# Display results
if result['status'] == 'success':
    print(f"Assessment Year: {result['assessment_year']}")
    print(f"Regimes calculated: {', '.join(result['regimes_calculated'])}")
    print(f"\nRecommendation: {result['recommendation']}")
    
    # Show detailed breakdown for both regimes
    for regime_name, regime_data in result['results'].items():
        print(f"\n{'='*50}")
        print(f"{regime_name.upper()} REGIME CALCULATION")
        print(f"{'='*50}")
        print(f"Taxable Income: ₹{regime_data['taxable_income']:,.0f}")
        print(f"Tax Liability: ₹{regime_data['tax_liability']:,.0f}")
        print(f"TDS Paid: ₹{regime_data['tds_paid']:,.0f}")
        print(f"Balance: ₹{abs(regime_data['balance']):,.0f} ({'REFUND' if regime_data['balance'] > 0 else 'ADDITIONAL PAYABLE'})")
        print(f"Effective Tax Rate: {regime_data['effective_tax_rate']:.2f}%")
        
        # Show detailed tax calculation breakdown
        detailed = regime_data['detailed_calculation']
        print(f"\nTax Calculation Details:")
        print(f"  Tax Before Rebate: ₹{detailed['tax_before_rebate']:,.0f}")
        print(f"  Surcharge: ₹{detailed['surcharge']:,.0f}")
        print(f"  Health & Education Cess: ₹{detailed['cess']:,.0f}")
        print(f"  Rebate u/s 87A: ₹{detailed['rebate_87a']:,.0f}")
        
        # Show deductions breakdown for old regime
        if regime_name == 'old':
            deductions = detailed['deductions_used']
            print(f"\nDeductions Used:")
            print(f"  Section 80C: ₹{deductions['section_80c']:,.0f}")
            print(f"  Section 80CCD(1B): ₹{deductions['section_80ccd_1b']:,.0f}")
            print(f"  Total Deductions: ₹{deductions['total_deductions']:,.0f}")
    
    print(f"\n{'='*70}")
    print("INPUT SUMMARY")
    print(f"{'='*70}")
    input_data = result['input_data']
    print(f"Gross Salary: ₹{input_data['gross_salary']:,.0f}")
    print(f"Bank Interest: ₹{input_data['bank_interest']:,.0f}")
    print(f"Other Income: ₹{input_data['other_income']:,.0f}")
    print(f"House Property: ₹{input_data['house_property']:,.0f}")
    print(f"Section 80C: ₹{input_data['section_80c']:,.0f}")
    print(f"Section 80CCD(1B): ₹{input_data['section_80ccd_1b']:,.0f}")
    print(f"TDS Paid: ₹{input_data['tds_paid']:,.0f}")
    
else:
    print(f"Error: {result['error_message']}")

# Example output:
"""
Assessment Year: 2024-25
Regimes calculated: old, new

Recommendation: OLD regime recommended - saves ₹28,500 annually

==================================================
OLD REGIME CALCULATION
==================================================
Taxable Income: ₹1,540,000
Tax Liability: ₹156,000
TDS Paid: ₹185,000
Balance: ₹29,000 (REFUND)
Effective Tax Rate: 10.40%

Tax Calculation Details:
  Tax Before Rebate: ₹148,000
  Surcharge: ₹0
  Health & Education Cess: ₹5,920
  Rebate u/s 87A: ₹0

Deductions Used:
  Section 80C: ₹150,000
  Section 80CCD(1B): ₹50,000
  Total Deductions: ₹200,000

==================================================
NEW REGIME CALCULATION
==================================================
Taxable Income: ₹1,690,000
Tax Liability: ₹184,500
TDS Paid: ₹185,000
Balance: ₹500 (REFUND)  
Effective Tax Rate: 12.30%

Tax Calculation Details:
  Tax Before Rebate: ₹175,000
  Surcharge: ₹0
  Health & Education Cess: ₹7,000
  Rebate u/s 87A: ₹0

======================================================================
INPUT SUMMARY
======================================================================
Gross Salary: ₹1,500,000
Bank Interest: ₹45,000
Other Income: ₹75,000
House Property: ₹120,000
Section 80C: ₹150,000
Section 80CCD(1B): ₹50,000
TDS Paid: ₹185,000
"""
```

This example demonstrates:
- **Complete income calculation** with salary, bank interest, other income, and house property
- **All major deductions** including 80C and 80CCD(1B)
- **Both tax regimes** comparison for 2024-25
- **Detailed breakdown** with effective tax rates and recommendations
- **Real-world scenario** for a software engineer with diversified income sources

---

## Example output JSON (comprehensive)

```json
{
  "status": "success",
  "metadata": {
    "file_name": "form16_sample.pdf",
    "processing_time_seconds": 7.86,
    "extraction_timestamp": "2024-09-09 14:30:54",
    "extractor_version": "1.0.0"
  },
  "form16": {
    "part_a": {
      "header": {
        "form_number": "FORM NO. 16",
        "certificate_number": "CERT789123"
      },
      "employer": {
        "name": "TECH SOLUTIONS INDIA PRIVATE LIMITED",
        "address": "IT Park, Tower A, 3rd Floor, Business District, MUMBAI - 400001, Maharashtra",
        "tan": "ABCD12345E",
        "pan": "ABCDE1234F",
        "contact_number": "+91-22-12345678",
        "email": "hr@techsolutions.com"
      },
      "employee": {
        "name": "JOHN SMITH",
        "pan": "ADHPR1234P",
        "address": "123 Main Street, Andheri East, MUMBAI - 400069, Maharashtra",
        "employee_reference_number": "EMP001234"
      },
      "employment_period": {
        "from": "2023-04-01",
        "to": "2024-03-31"
      },
      "assessment_year": "2024-25",
      "quarterly_tds_summary": {
        "quarter_1": {
          "period": "Q1",
          "receipt_numbers": ["Q1234567"],
          "amount_paid_credited": 687500.0,
          "amount_deducted": 68750.0,
          "amount_deposited": 68750.0,
          "deposited_date": "2023-07-15",
          "status": "Deposited"
        },
        "quarter_2": {
          "period": "Q2",
          "receipt_numbers": ["Q2345678"],
          "amount_paid_credited": 687500.0,
          "amount_deducted": 68750.0,
          "amount_deposited": 68750.0,
          "deposited_date": "2023-10-15",
          "status": "Deposited"
        },
        "quarter_3": { "period": "Q3", "amount_deducted": 68750.0, "...": "..." },
        "quarter_4": { "period": "Q4", "amount_deducted": 68750.0, "...": "..." },
        "total_tds": {
          "amount_paid_credited": 2750000.0,
          "deducted": 275000.0,
          "deposited": 275000.0
        }
      }
    },
    "part_b": {
      "gross_salary": {
        "section_17_1_salary": 2400000.0,
        "section_17_2_perquisites": 150000.0,
        "section_17_3_profits_in_lieu": 0.0,
        "total": 2550000.0
      },
      "allowances_exempt_under_section_10": {
        "house_rent_allowance": 288000.0,
        "leave_travel_allowance": 50000.0,
        "other_exemptions": [
          {"description": "Conveyance Allowance", "amount": 19200.0},
          {"description": "Medical Reimbursement", "amount": 15000.0}
        ],
        "total_exemption": 397200.0
      },
      "deductions_under_section_16": {
        "standard_deduction": 50000.0,
        "professional_tax": 2500.0,
        "total": 52500.0
      },
      "chapter_vi_a_deductions": {
        "section_80C": {
          "components": {
            "ppf_contribution": 150000.0,
            "life_insurance_premium": 25000.0,
            "tuition_fees": 50000.0,
            "nsc": 0.0,
            "elss_investment": 0.0,
            "others": 100000.0
          },
          "total": 150000.0
        },
        "section_80CCD_1B": 50000.0,
        "section_80D": {
          "self_family": 25000.0,
          "parents": 30000.0,
          "total": 55000.0
        },
        "section_80G": 15000.0,
        "total_chapter_via_deductions": 270000.0
      },
      "tax_computation": {
        "income_chargeable_under_head_salary": 2100300.0,
        "tax_on_total_income": 315045.0,
        "health_and_education_cess": 12601.8,
        "total_tax_liability": 327646.8,
        "tax_payable": 327647.0,
        "less_tds": 275000.0,
        "tax_due_refund": -52647.0
      }
    }
  },
  "extraction_metrics": {
    "confidence_scores": {
      "employee": {"name": 0.95, "pan": 0.95, "address": 0.85},
      "employer": {"name": 0.92, "tan": 0.95, "address": 0.88},
      "salary": {"gross_salary": 0.94, "allowances": 0.87},
      "deductions": {"section_80c": 0.89, "section_80d": 0.86},
      "tax": {"tax_computation": 0.92, "tds_summary": 0.88}
    },
    "extraction_summary": {
      "total_fields": 250,
      "extracted_fields": 134,
      "extraction_rate": 53.6,
      "quality_score": 78.5
    }
  }
}
```

---

## How it works (high-level)

1. **PDF Processing:** Extracts tables and text from Form 16 PDFs using robust PDF processing with multiple fallback methods (camelot-py, pdfplumber)
2. **Multi-Category Classification:** Uses an enhanced classification system to identify table types (Part A employer/employee data, Part B salary details, tax deductions, quarterly TDS, etc.)
3. **Domain-Specific Extraction:** Routes tables to specialized extractors:
   - **Identity Extractor:** Employee and employer information (name, PAN, TAN, address)
   - **Salary Extractor:** Gross salary breakdown, allowances, perquisites, Section 17 components
   - **Deductions Extractor:** Chapter VI-A deductions (80C, 80D, 80CCD, etc.)
   - **Tax Computation Extractor:** Tax calculations, TDS summary, refund/payable amounts
4. **Enhanced Routing:** High-scoring tables are processed by multiple extractors to maximize field coverage
5. **Confidence Scoring:** Each extracted field includes confidence metrics for quality assessment
6. **Structured Output:** Generates comprehensive JSON following official Form 16 Part A/Part B structure

---

## Accuracy & metrics

On an internal test set, the extractor achieves \~85–90% coverage on common fields for digitally-created Form 16s. Coverage drops for heavily-scanned or handwritten copies — these are better handled if OCR is enabled and a manual review step is used.

If you report an issue, please include an anonymized sample (or run with `--debug` and paste the JSON output) so we can improve templates/heuristics.

---

## Privacy & Security

* **Local Processing Only:** All operations run locally - no external API calls or data uploads
* **No Data Retention:** No logging of sensitive financial data or Form16 contents  
* **Memory Cleanup:** Secure cleanup of Form16 data from memory after processing
* **Input Validation:** Safe PDF parsing with protection against malformed documents
* **Third-party Dependencies:** Uses well-vetted libraries like pydantic, pandas, camelot-py
* **Offline First:** Works completely offline once installed

---

## Contributing

Thanks — contributions welcome!

* Please open issues for bugs or dataset edge-cases.
* When filing a bug: include (1) anonymized sample PDF (if possible), (2) expected field value, (3) actual output JSON.
* See `CONTRIBUTING.md` for development setup, tests, and PR guidelines.

### Issue / PR templates

* Bug report: steps to reproduce + sample file (anonymized)
* Feature request: use-case + proposed UX

---

## Releases & changelog

We recommend tagging stable releases e.g. `v1.0.0`. Use the `CHANGELOG.md` to summarise accuracy claims and key changes.

**Release template**

* v1.0.0 — 2025-09-09

  * Initial public release
  * CLI + Python API
  * Extracts Part A & B, computes tax for old/new regimes
  * \~85% field coverage on digital PDFs

---

## License

## MIT License — see [LICENSE](LICENSE).