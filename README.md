# Form16Extractor

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/badge/ci-github--actions-lightgrey)](#)
[![Coverage](https://img.shields.io/badge/coverage-XX%25-yellow)](#)

**A privacy-first, open-source tool to parse Indian Form 16 PDFs into structured JSON.**
*I built this to make my own tax filing easier — sharing it in case it helps others.*

![demo-gif](assets/demo.gif) <!-- replace with your GIF or screenshot -->

---

## TL;DR

Form16Extractor extracts Part A & Part B from Form 16 PDFs and outputs structured JSON with employee/employer details, salary components, deductions (80C/80D/etc.), TDS breakdown, and computed tax for old/new regimes.

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

### Install Form16 Extractor

```bash
git clone https://github.com/your-username/form16_extractor.git
cd form16_extractor
pip install -r requirements.txt

# Extract a Form16 
python cli.py extract --file path/to/Form16.pdf --output result.json

# Extract with tax calculation
python cli.py extract --file path/to/Form16.pdf --calculate-tax --summary
```

**Note:** If you encounter issues with camelot installation, see the [official camelot-py installation guide](https://camelot-py.readthedocs.io/en/master/user/install-deps.html).

---

## Quick CLI example

```bash
# Extract to JSON
python cli.py extract --file form16_sample.pdf --output result.json

# Extract with tax calculation
python cli.py extract --file form16_sample.pdf --calculate-tax

# Get detailed tax breakdown with regime comparison
python cli.py extract --file form16_sample.pdf --calculate-tax --summary --tax-regime both

# Calculate for specific regime only
python cli.py extract --file form16_sample.pdf --calculate-tax --tax-regime new

# Consolidate multiple Form16s from different employers
python cli.py consolidate --files company1.pdf company2.pdf --calculate-tax 
```

---

## Python usage example

```python
from form16_extractor.extractors.enhanced_form16_extractor import EnhancedForm16Extractor
from form16_extractor.pdf.reader import RobustPDFProcessor

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

---

## Example output (comprehensive)

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
5. **Zero Value Handling:** Recognizes and preserves explicit zero values vs missing data
6. **Confidence Scoring:** Each extracted field includes confidence metrics for quality assessment
7. **Structured Output:** Generates comprehensive JSON following official Form 16 Part A/Part B structure

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