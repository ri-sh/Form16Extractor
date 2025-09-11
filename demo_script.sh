#!/bin/bash

# Form16X CLI Demo Script (Auto Demo Mode)
clear

# Function to create prominent headers
print_header() {
    echo ""
    echo "╭─────────────────────────────────────────────────────────────╮"
    echo "│                                                             │"
    echo "│$(printf "%63s" " " | sed "s/ /$(echo "$1" | cut -c1-63)/1")"
    echo "│                                                             │"
    echo "╰─────────────────────────────────────────────────────────────╯"
    echo ""
}

# Function to create section headers
print_section() {
    echo ""
    echo "┌───────────────────────────────────────────────────┐"
    echo "│ $1$(printf "%*s" $((50 - ${#1})) " ")│"
    echo "└───────────────────────────────────────────────────┘"
    echo ""
}

print_header "Form16X CLI Demo - Complete Workflow"

echo "This demo shows the complete tax processing workflow with form16x"
echo "Note: Using --demo flag to show sanitized dummy data for privacy"
echo ""
sleep 1

print_section "1. Tax Calculation"
echo "   Calculate taxes for both OLD and NEW regimes with automatic recommendations"
echo ""
echo -e "\033[1;36m$ form16x extract json ~/Downloads/form16/Form16.pdf --calculate-tax --demo\033[0m"
sleep 2
python3 -m form16x.form16_parser.cli extract json ~/Downloads/form16/Form16.pdf --calculate-tax --demo
echo ""
echo "Press any key to continue..."
read -n 1 -s
clear

print_section "2. JSON Data Extraction"
echo "   Extract structured data and save to JSON file for further processing"
echo ""
echo -e "\033[1;36m$ form16x extract json ~/Downloads/form16/Form16.pdf --output form16_extracted.json --demo\033[0m"
sleep 3
python3 -m form16x.form16_parser.cli extract json ~/Downloads/form16/Form16.pdf --output form16_extracted.json --demo
echo ""
echo "JSON file created: form16_extracted.json"
echo ""
echo "Viewing extracted data (sample):"
echo "cat form16_extracted.json | head -20"
if [ -f "form16_extracted.json" ]; then
    cat form16_extracted.json | head -20
    echo "... (truncated for demo)"
else
    echo '{'
    echo '  "status": "success",'
    echo '  "form16": {'
    echo '    "employee_name": "ASHISH MITTAL",'
    echo '    "gross_salary": 1200000'
    echo '  }'
    echo '... (demo data)'
fi
echo ""
echo "Press any key to continue..."
read -n 1 -s
clear

print_section "3. Tax Optimization Analysis"
echo "   Get personalized tax-saving recommendations and regime comparison"
echo ""
echo -e "\033[1;36m$ form16x optimize ~/Downloads/form16/Form16.pdf --demo\033[0m"
sleep 3
python3 -m form16x.form16_parser.cli optimize ~/Downloads/form16/Form16.pdf --demo
echo ""
echo "Press any key to continue..."
read -n 1 -s
clear

print_section "4. Multi-Company Consolidation"
echo "   Consolidation is useful for people who have multiple Form16s within the same year"
echo "   or have switched companies during the financial year. It combines all income and"
echo "   TDS from different employers for accurate tax calculation."
echo ""
echo -e "\033[1;36m$ form16x consolidate --files ~/Downloads/form16/Company1_Form16.pdf ~/Downloads/form16/Company2_Form16.pdf --calculate-tax --demo\033[0m"
sleep 3
python3 -m form16x.form16_parser.cli consolidate --files ~/Downloads/form16/Company1_Form16.pdf ~/Downloads/form16/Company2_Form16.pdf --calculate-tax --demo
echo ""
echo "Press any key to continue..."
read -n 1 -s
clear

print_section "5. Batch Processing"
echo "   Process multiple Form16 files in bulk for efficient large-scale tax processing"
echo "   Useful for tax consultants or organizations handling multiple employee Form16s"
echo ""
echo -e "\033[1;36m$ form16x batch --input-dir ~/Downloads/form16/ --output-dir ./batch_results/ --demo\033[0m"
sleep 3
python3 -m form16x.form16_parser.cli batch --input-dir ~/Downloads/form16/ --output-dir ./batch_results/ --demo
echo ""
echo "Press any key to continue..."
read -n 1 -s
clear

print_header "Demo Completed!"

echo "Form16x provides a complete tax processing solution:"
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│ • Tax calculation with regime comparison                │"
echo "│ • Structured data extraction to JSON                   │"
echo "│ • Tax optimization recommendations                      │"
echo "│ • Multi-employer consolidation support                 │"
echo "│ • Bulk batch processing for multiple files             │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

# Clean up demo files
rm -f form16_extracted.json 2>/dev/null