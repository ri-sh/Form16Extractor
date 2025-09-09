# Indian Income Tax Calculation Guide

## Overview

This guide explains the comprehensive income tax calculation logic implemented in the Form16 Extractor for Financial Years 2024-25 and 2025-26 (Assessment Years 2025-26 and 2026-27).

## Tax Regime Structure

India currently has two tax regimes:

### 1. Old Tax Regime (Traditional)
- **Higher tax rates** but allows extensive **deductions and exemptions**
- Suitable for taxpayers with significant investments and expenses
- **NOT the default** from AY 2024-25 onwards

### 2. New Tax Regime (Default from AY 2024-25)
- **Lower tax rates** but **limited deductions**
- Simplified tax structure
- **Default regime** - taxpayers must opt out to choose old regime

## Tax Slabs and Rates

### FY 2024-25 (AY 2025-26)

#### New Tax Regime (Default)
| Income Range | Tax Rate | Cumulative Tax |
|--------------|----------|---------------|
| ₹0 - ₹3,00,000 | 0% | ₹0 |
| ₹3,00,001 - ₹6,00,000 | 5% | ₹15,000 |
| ₹6,00,001 - ₹9,00,000 | 10% | ₹45,000 |
| ₹9,00,001 - ₹12,00,000 | 15% | ₹90,000 |
| ₹12,00,001 - ₹15,00,000 | 20% | ₹1,50,000 |
| Above ₹15,00,000 | 30% | - |

#### Old Tax Regime
| Income Range | Tax Rate | Cumulative Tax |
|--------------|----------|---------------|
| ₹0 - ₹2,50,000 | 0% | ₹0 |
| ₹2,50,001 - ₹5,00,000 | 5% | ₹12,500 |
| ₹5,00,001 - ₹10,00,000 | 20% | ₹1,12,500 |
| Above ₹10,00,000 | 30% | - |

### FY 2025-26 (AY 2026-27) - Enhanced New Regime

| Income Range | Tax Rate | Key Changes |
|--------------|----------|-------------|
| ₹0 - ₹4,00,000 | 0% | **Increased from ₹3L** |
| ₹4,00,001 - ₹8,00,000 | 5% | **Wider slab** |
| ₹8,00,001 - ₹12,00,000 | 10% | Same |
| ₹12,00,001 - ₹16,00,000 | 15% | **Extended range** |
| ₹16,00,001 - ₹20,00,000 | 20% | Same |
| ₹20,00,001 - ₹24,00,000 | 25% | **New slab** |
| Above ₹24,00,000 | 30% | Same |

## Key Tax Components

### 1. Standard Deduction
- **FY 2024-25**: ₹50,000
- **FY 2025-26**: ₹75,000 (**increased**)
- Available in both regimes
- Deducted from salary income

### 2. Rebate under Section 87A

#### FY 2024-25 (New Regime)
- Income limit: ₹7,00,000
- Maximum rebate: ₹25,000
- **Effective zero tax** up to ₹7L income

#### FY 2025-26 (New Regime)
- Income limit: ₹12,00,000 (**significantly increased**)
- Maximum rebate: ₹60,000 (**more than doubled**)
- **Effective zero tax** up to ₹12L income

#### Old Regime (Both Years)
- Income limit: ₹5,00,000
- Maximum rebate: ₹12,500
- Effective zero tax up to ₹5L income

### 3. Surcharge Rates

#### New Regime
| Income Range | Surcharge Rate |
|--------------|----------------|
| ₹50L - ₹1Cr | 10% |
| ₹1Cr - ₹2Cr | 15% |
| ₹2Cr - ₹5Cr | 25% |
| Above ₹5Cr | **25%** (not 37%) |

#### Old Regime
| Income Range | Surcharge Rate |
|--------------|----------------|
| ₹50L - ₹1Cr | 10% |
| ₹1Cr - ₹2Cr | 15% |
| ₹2Cr - ₹5Cr | 25% |
| Above ₹5Cr | 37% |

### 4. Health & Education Cess
- **4%** on (Income Tax + Surcharge)
- Applied uniformly in both regimes

## Deductions Available

### Old Regime (Extensive Deductions)
- **Section 80C**: ₹1,50,000 (LIC, PPF, ELSS, etc.)
- **Section 80D**: Medical insurance premiums
- **Section 80CCD(1B)**: Additional NPS contribution (₹50,000)
- **Section 24(b)**: Home loan interest (₹2,00,000)
- **HRA Exemption**: Actual calculation based on rent paid
- **LTA**: Leave Travel Allowance exemption
- And many more...

### New Regime (Limited Deductions)
- **Standard Deduction**: ₹50K/₹75K
- **Employer NPS Contribution**: Section 80CCD(2)
- **Gratuity & Leave Encashment**: Section 10 exemptions
- **Professional Tax**: Section 16 deduction
- **Interest on deposits**: Section 80TTA/TTB (limited)

## Advanced Calculations

### 1. Multi-Company Form16 Consolidation
When an employee works for multiple companies in the same financial year:
- **Aggregate all salary components**
- **Sum up all TDS deducted**
- **Validate financial year consistency**
- **Detect and handle duplicate deductions**
- **Calculate final tax liability**

### 2. Section 89 Relief (Salary Arrears)
When employees receive salary arrears:
```
Relief Calculation:
1. Calculate tax for current year without arrears
2. Calculate tax for current year with arrears
3. Calculate additional tax for each arrear year
4. Relief = Current year additional tax - Sum of arrear year additional taxes
```

### 3. Perquisite Valuation
Complex calculations for various perquisites:
- **Accommodation**: 10-15% of basic salary
- **Motor Car**: ₹1,800-₹2,700 per month based on engine capacity
- **Interest-free Loans**: Interest benefit calculation
- **ESOP/Stock Options**: (FMV - Exercise Price) × Shares

### 4. Professional Tax by State
State-wise professional tax calculations:
- **Maharashtra**: Up to ₹3,000 annually
- **Karnataka**: Up to ₹3,000 annually
- **Tamil Nadu**: Up to ₹3,000 annually
- **Gujarat**: Up to ₹3,000 annually
- And others...

### 5. Gratuity Exemption Calculation
Based on employment type:

#### Government Employees
- **Fully exempt** from tax

#### Private Sector (Covered under Gratuity Act)
```
Formula: (15/26) × Last drawn salary × Years of service
Exemption: Minimum of (Formula, Actual received, ₹20,00,000)
```

#### Private Sector (Not Covered)
```
Formula: (15/30) × Last drawn salary × Years of service
Exemption: Minimum of (Formula, Actual received, ₹20,00,000)
```

## Tax Calculation Flow

### Step 1: Income Computation
1. **Gross Salary** = Basic + DA + Allowances + Perquisites
2. **Less**: Standard Deduction
3. **Less**: Professional Tax (Section 16)
4. **Less**: Other Section 16 deductions
5. **Income from Salary** = Net amount

### Step 2: Total Income
1. **Income from Salary** (from step 1)
2. **Plus**: Income from House Property
3. **Plus**: Income from Other Sources
4. **Plus**: Capital Gains
5. **Gross Total Income** = Sum of all incomes

### Step 3: Deductions (Old Regime Only)
1. **Less**: Chapter VI-A deductions (80C, 80D, etc.)
2. **Total Taxable Income** = GTI - Deductions

### Step 4: Tax Computation
1. **Apply tax slabs** to taxable income
2. **Less**: Rebate under Section 87A
3. **Plus**: Surcharge (if applicable)
4. **Plus**: Health & Education Cess (4%)
5. **Total Tax Liability**

### Step 5: Tax Payments
1. **Less**: TDS from all sources
2. **Less**: Advance Tax paid
3. **Less**: Self Assessment Tax
4. **Balance**: Tax payable/(refundable)

## Year-Specific Changes

### AY 2024-25 (FY 2023-24) - Introduction Phase
- New regime introduced as option
- Old regime remained default
- Standard deduction: ₹50,000

### AY 2025-26 (FY 2024-25) - Transition Phase
- **New regime becomes default**
- Rebate increased to ₹25,000 (income limit ₹7L)
- Standard deduction remains ₹50,000

### AY 2026-27 (FY 2025-26) - Enhancement Phase
- **Standard deduction increased to ₹75,000**
- **Rebate dramatically increased to ₹60,000 (income limit ₹12L)**
- Tax slabs revised for broader relief

## Integration Architecture

### Modular Design
```
Tax Calculator
├── Year-Specific Rule Providers
├── Regime Engines (Old/New)
├── Component Calculators
│   ├── Section 89 Relief
│   ├── Professional Tax
│   ├── Perquisite Calculator
│   ├── Gratuity Calculator
│   └── HRA/LTA Calculators
└── Multi-Company Consolidator
```

### Configuration-Driven
- **JSON-based tax rules** for each assessment year
- **Separate configurations** for old and new regimes
- **Easy updates** for annual tax changes

### Validation & Accuracy
- **Cross-verification** with IT department calculators
- **Edge case handling** for boundary conditions
- **Year-specific rule isolation**
- **Comprehensive error handling**

## Usage Examples

### Simple Tax Calculation
```python
from form16_extractor.tax_calculators import ComprehensiveTaxCalculator

calculator = ComprehensiveTaxCalculator()
result = calculator.calculate_tax(tax_input, assessment_year="2024-25")
```

### Multi-Company Consolidation
```python
from form16_extractor.consolidators import MultiCompanyConsolidator

consolidator = MultiCompanyConsolidator()
consolidated = consolidator.consolidate_form16s(form16_list)
```

### Section 89 Relief
```python
from form16_extractor.tax_calculators.components import Section89ReliefCalculator

relief_calc = Section89ReliefCalculator(rule_provider)
relief = relief_calc.calculate_section_89_relief(base_input, arrear_details, "2024-25")
```

## Compliance & Updates

This implementation follows:
- **Income Tax Act, 1961** provisions
- **Finance Act** amendments for each year
- **CBDT circulars** and notifications
- **Latest tax computation guidelines**

The system is designed to be **easily updatable** for annual tax changes through configuration updates rather than code changes.

## Support for Future Years

The architecture supports:
- **Easy addition of new assessment years**
- **Rule-specific customizations** per year
- **Backward compatibility** for historical calculations
- **Forward migration** of tax rules

---

*This guide covers the comprehensive income tax calculation logic implemented in the Form16 Extractor. For technical implementation details, refer to the source code documentation.*