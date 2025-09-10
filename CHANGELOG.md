# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-09-09

### Added

#### Comprehensive Tax Calculation API (P0 - COMPLETED)
- **Complete Programmatic API**: Created comprehensive `TaxCalculationAPI` class for standalone tax calculations independent of CLI
- **Dual Calculation Methods**: Support for both Form16 PDF extraction (`calculate_tax_from_form16`) and manual input (`calculate_tax_from_input`)
- **Multi-Regime Analysis**: Automatic comparison between old and new tax regimes with recommendations
- **Regime Selection**: Automated recommendations showing exact annual savings between regimes
- **Bank Interest Integration**: Automatic Section 80TTA/80TTB deduction calculation for bank interest income
- **Clean Architecture**: Proper separation of concerns between CLI orchestration and business logic components

#### Multi-Year Tax Calculation Support (P1 - COMPLETED)  
- **Extended Year Coverage**: Full support for assessment years 2020-21 through 2025-26
- **Year-Specific Tax Rules**: Accurate tax slabs, deductions, and exemptions for each assessment year
- **Regime Availability Logic**: Automatic detection of old/new regime availability by year (new regime from 2020-21 onwards)
- **Historical Tax Analysis**: Calculate taxes for any supported assessment year with period-appropriate rules
- **Future Year Planning**: Support for upcoming assessment years with projected tax rules

#### Enhanced Form16 Integration for Other Income Sources (P2 - COMPLETED)
- **Automatic Income Extraction**: Direct extraction of bank interest, dividend, and other income from Form16 documents where available
- **Reduced Manual Input**: Minimized dependency on CLI parameters for income sources through intelligent Form16 parsing
- **Comprehensive Income Mapping**: Complete mapping of Form16 other income fields to tax calculation inputs
- **Income Source Validation**: Automatic validation and categorization of different income types from Form16

#### User-Friendly CLI Interface (NEW)
- **Taxedo Command**: Introduced standalone `taxedo` CLI tool for easy installation and usage
- **Simplified Command Format**: New user-friendly format: `taxedo extract json form16.pdf` instead of `--file` flags
- **Multiple Output Formats**: Direct format specification in command: `taxedo extract csv form16.pdf`
- **Backward Compatibility**: Legacy `--file` format still fully supported
- **Professional Installation**: Package installation with `pip install -e .` enables `taxedo` command globally

#### Visual Tax Display System (NEW)
- **Colorful Visual Analysis**: Rich colored display with winner/loser highlighting for tax regime comparison
- **Professional Table Format**: Clean tabular display mode perfect for reports and documentation
- **Smart Display Modes**: `--display-mode colored` (default) and `--display-mode table` options
- **Tax Regime Visualization**: Visual boxes showing Old vs New regime with clear recommendations
- **Summary Enhancements**: Detailed summary mode with monthly savings breakdown and effective tax rates
- **Action-Oriented Output**: Clear recommendations like "Choose NEW REGIME - Save Rs 80,080 annually!"
- **Currency Formatting**: Professional ₹ symbols and proper number formatting throughout

#### Advanced Tax Calculation Engine
- **Comprehensive Tax Components**: Full implementation of basic tax, surcharge, health and education cess calculations
- **Marginal Relief Calculations**: Accurate marginal relief for surcharge calculations at ₹50L and ₹1Cr thresholds  
- **Section-wise Deduction Processing**: Complete support for all major tax-saving sections (80C, 80D, 80CCD, 80E, 80G, etc.)
- **Exemption Calculations**: Comprehensive handling of Section 10 exemptions (HRA, LTA, gratuity, etc.)
- **TDS and Tax Balance**: Accurate calculation of refunds due or additional tax payable

#### Developer Experience Enhancements
- **Type-Safe API**: Complete type hints and Pydantic models for all API inputs and outputs
- **Comprehensive Error Handling**: Detailed error messages with specific error codes for different failure scenarios
- **Extensive Documentation**: Complete API documentation with practical examples and use cases
- **Test Coverage**: Full test suite covering all API methods and edge cases
- **Utility Methods**: Helper functions for checking supported years and regime availability

### Enhanced Features

#### CLI Integration
- **Seamless API Integration**: CLI now uses the new API internally while maintaining backward compatibility
- **Enhanced Error Reporting**: Better error messages and validation feedback through improved API error handling
- **Performance Improvements**: Faster tax calculations through optimized API architecture
- **User-Friendly Commands**: Simplified command syntax with positional arguments for better user experience
- **Visual Enhancement**: Rich colored output with professional formatting and clear recommendations
- **Flexible Output**: Support for both colored visual analysis and clean tabular reports

#### Data Architecture Improvements  
- **Clean Separation of Concerns**: Business logic properly separated from CLI presentation layer
- **Modular Design**: Highly modular API components enabling selective usage (extraction-only, calculation-only, etc.)
- **Interface-Based Architecture**: Clean interfaces enabling easy extension and testing
- **Memory Efficiency**: Optimized data structures and processing for better memory usage

### Technical Implementation

#### Architecture Enhancements
- **API Package Structure**: New `form16_extractor.api` package with clean public interface
- **Enhanced Data Mappers**: Improved `Form16ToTaxMapper` with comprehensive Form16 to tax input conversion
- **Robust PDF Processing**: Enhanced PDF extraction pipeline with better error handling and performance
- **Configuration Management**: Flexible configuration system for different calculation scenarios

#### Code Quality
- **Professional Documentation**: Comprehensive docstrings and examples for all public APIs
- **Error Resilience**: Graceful handling of malformed PDFs and incomplete data
- **Performance Optimization**: Efficient processing for both single calculations and batch operations
- **Memory Safety**: Proper resource management and cleanup throughout the API

### Migration Guide
- **Backward Compatibility**: All existing CLI commands remain fully compatible
- **New API Usage**: Simple import and usage pattern: `from form16_extractor.api import TaxCalculationAPI`
- **Enhanced Capabilities**: Existing users can now access programmatic API for custom integrations
- **Gradual Migration**: Can adopt new API features incrementally without breaking existing workflows

## [2.0.2] - 2025-09-09

### Added
#### Progress Animation System
- **Beautiful Terminal Animations**: Complete progress animation system using Rich library for PDF processing operations
- **Multi-Stage Progress Tracking**: Real-time progress indicators showing "Reading PDF", "Extracting tables", "Classifying tables", "Reading data from table", "Extracting JSON", "Computing tax"
- **Interactive Progress Bars**: Animated progress bars with percentage completion, time elapsed, and stage descriptions
- **Status Spinners**: Elegant status spinners for consolidation and validation operations
- **Graceful Fallback**: Simple text-based progress indicators when Rich library is unavailable or in verbose mode
- **PDF Processing Stages**: Six distinct processing stages with appropriate progress weighting and visual feedback

#### User Experience Improvements
- **Professional Progress Feedback**: Users now see exactly what stage of processing is happening in real-time
- **Non-Blocking Animation**: Progress animations don't interfere with verbose logging or error messages
- **Consolidation Progress**: Multi-file consolidation now shows per-file progress with animated status indicators
- **Processing Time Visibility**: Time elapsed is shown during processing for better user awareness

### Technical Implementation
- **Rich Library Integration**: Added Rich 14.1.0 dependency for advanced terminal output capabilities
- **Modular Progress Architecture**: Created dedicated `form16_extractor.progress` package with reusable components
- **Context Manager Pattern**: Progress tracking uses context managers for clean resource management
- **Fallback Support**: Automatic detection of Rich availability with graceful degradation to simple progress indicators
- **CLI Integration**: Seamless integration into existing CLI commands without breaking changes

## [2.0.1] - 2024-09-09

### Enhanced
#### Display & User Experience
- **Improved Colored Display Mode**: Complete overhaul of the colored terminal display for tax regime comparison
- **Perfect Box Alignment**: All tax calculation boxes now have consistent 4-space indentation and perfect vertical line alignment
- **Clean Visual Formatting**: Removed redundant headers, fixed box width consistency, and improved horizontal separators
- **Professional Layout**: All headers (EMPLOYEE DETAILS, INCOME BREAKDOWN, REGIME COMPARISON ANALYSIS, SUMMARY METRICS) now align consistently
- **Income Breakdown Box**: Corrected spacing and alignment for perquisites display
- **Box Drawing Characters**: Standardized all box drawing with proper Unicode characters and consistent styling
- **Template Modularization**: Extracted display templates into separate files for better code organization and maintainability

#### Bug Fixes
- **Vertical Line Alignment**: Fixed misaligned vertical borders in tax regime comparison boxes
- **Currency Symbol Formatting**: Standardized ₹ symbol positioning and right-alignment of monetary values
- **Header Spacing**: Corrected double-indentation issues in employee details and summary sections
- **Box Width Consistency**: Ensured all boxes have uniform width (49 characters) for professional appearance

### Technical Improvements
- **Template Architecture**: Refactored colored display into modular template system for easier maintenance
- **Code Organization**: Separated display logic into dedicated template files (`colored_templates.py`, `display_templates.py`)
- **Consistent Formatting**: Implemented systematic 4-space indentation throughout the colored display mode
- **Display Renderer Pattern**: Created structured renderer classes for different display modes

## [2.0.0] - 2024-09-09

### Added

#### Multi-Company Form16 Consolidation
- **Multi-Company Support**: Complete implementation for employees working at multiple companies within the same financial year
- **Financial Year Validation**: Automatic validation to ensure all Form16s belong to the same assessment year
- **Consolidated Tax Calculation**: Combined income and TDS computation across multiple employers
- **Employee Consistency Validation**: PAN and employee detail verification across all documents
- **Duplicate Detection**: Identification and warning system for potential duplicate entries

#### Comprehensive Tax Calculation System
- **Dual Regime Support**: Complete tax calculation for both old and new tax regimes (AY 2024-25)
- **Accurate Surcharge Calculations**: Proper surcharge computation (10% for >50L, 15% for >1Cr) with marginal relief
- **HRA Calculator**: Metro/non-metro HRA exemption calculations with three-way comparison method
- **LTA Calculator**: Leave Travel Allowance exemption with block year validation
- **Professional Tax**: State-wise professional tax deduction calculations
- **Section 89 Relief**: Salary arrears relief calculation
- **Gratuity Calculator**: Statutory gratuity exemption calculation (up to 20L limit)
- **Perquisite Valuation**: Comprehensive perquisite calculations for accommodation, motor car, ESOP
- **Regime Comparison**: Automatic recommendation engine for optimal tax regime selection

#### Enhanced CLI Interface
- **Tax Calculation Commands**: Integrated tax calculation directly in CLI extraction workflow
- **Consolidation Command**: Dedicated consolidation command for multiple Form16 processing
- **Regime Comparison**: Side-by-side tax regime comparison with recommendations
- **Summary Mode**: Detailed tax breakdown and computation display
- **Validation Commands**: Enhanced validation for consolidated results

#### Technical Infrastructure
- **Domain-Driven Architecture**: Modular consolidator and tax calculator components
- **Year-Specific Rule System**: Extensible tax rule provider architecture for multi-year support
- **Exception Handling**: Comprehensive custom exception system for consolidation and tax calculations
- **Interface-Based Design**: Clean interfaces for calculators, consolidators, and integrators
- **Enhanced Validation**: Form16 consistency validation and financial year matching

### Enhanced Features

#### Data Models
- **Consolidated Form16 Models**: New data models supporting multi-company scenarios
- **Tax Calculation Models**: Comprehensive models for tax computation results
- **Validation Models**: Enhanced validation with detailed error reporting

#### Integration Layer
- **Form16-Tax Integration**: Seamless integration between Form16 extraction and tax calculation
- **Data Mapping**: Intelligent mapping between Form16 fields and tax calculation inputs
- **Error Propagation**: Comprehensive error handling across integration layers

#### Testing
- **Comprehensive Test Suite**: New test suites for consolidation and tax calculation components
- **Unit Test Coverage**: Full coverage for all new tax calculation and consolidation features
- **Integration Tests**: End-to-end testing for multi-company scenarios

### Changed
- **CLI Interface**: Enhanced with new commands for consolidation and tax calculation
- **Architecture**: Expanded from extraction-only to full tax processing ecosystem
- **Data Models**: Extended to support multi-company and tax calculation scenarios
- **Documentation**: Completely updated with new capabilities and professional language

### Technical Details
- **New Components**: 25+ new modules including consolidators, tax calculators, and integrators
- **Code Quality**: Professional docstrings, comprehensive error handling, and clean architecture
- **Performance**: Optimized for multi-document processing and complex tax calculations
- **Extensibility**: Plugin architecture for future tax years and additional features

### Migration from 1.x
- **Backward Compatibility**: All existing Form16 extraction APIs remain unchanged
- **New APIs**: Additional APIs for consolidation and tax calculation
- **Enhanced Output**: Extended JSON structure with tax calculation results
- **CLI Changes**: New commands added, existing commands remain compatible

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Form16 Extractor
- **Core Features**:
  - Complete Form16 PDF parsing and data extraction
  - Support for both Part A (TDS summary) and Part B (detailed breakdown)
  - Employee information extraction (name, PAN, designation, address)
  - Employer information extraction (name, TAN, PAN, address)
  - Comprehensive salary breakdown extraction
  - Tax deductions extraction (Section 80C, 80D, 80E, etc.)
  - Quarterly TDS details extraction
  - Tax computation with refund/payable calculations

- **Data Models**:
  - Type-safe Pydantic models for all extracted data
  - Comprehensive validation with proper error handling
  - Support for all major Form16 fields and sections

- **Extraction Engine**:
  - Advanced pattern matching for robust field detection
  - Confidence scoring for extraction quality assessment
  - Multiple extraction strategies for different Form16 formats
  - Graceful handling of missing or corrupted data

- **Developer Experience**:
  - Clean, intuitive Python API
  - Comprehensive type hints throughout
  - Detailed error reporting and logging
  - Extensive unit test coverage (54 tests)

- **Output Formats**:
  - Structured JSON output with complete schema
  - Confidence scores and extraction metrics
  - Error reporting with field-level details

- **Privacy & Security**:
  - No data retention or transmission
  - Local processing only
  - No PII in logs or error messages
  - Memory-safe operations

### Technical Details
- **Python Support**: Python 3.8+
- **Dependencies**: pydantic, pandas, pdfplumber, python-dateutil
- **Architecture**: Domain-driven design with modular extractors
- **Testing**: Comprehensive unit test suite with 95%+ coverage
- **Documentation**: Full API documentation and examples

### Supported Form16 Features
- Employee identification (Name, PAN, Employee ID)
- Employer identification (Name, TAN, PAN, Address)
- Salary components (Basic, HRA, Special Allowance, etc.)
- Perquisites under Section 17(2)
- Exemptions under Section 10
- Standard deduction and professional tax
- Chapter VI-A deductions (80C, 80D, 80E, 80G, etc.)
- Quarterly TDS breakdown with challan details
- Tax computation with surcharge and cess
- Refund/tax payable calculations

### Known Limitations
- Requires Form16 PDFs to be text-extractable (not scanned images)
- Some custom Form16 formats may require manual verification
- Advanced perquisites calculation may need review for complex cases

---

## Upcoming Features (Roadmap)

### [2.2.0] - Planned

#### Critical Backlog Items
- **CSV/XLSX Export Functionality (P1)**:
  - Complete implementation of CSV export format for extracted Form16 data
  - Complete implementation of XLSX export format with customizable templates
  - Currently CLI accepts --format csv/xlsx but doesn't create files

- **Batch Processing Enhancements (P2)**:
  - Add tax calculation support to batch processing command
  - Enable bulk tax computation for multiple Form16 files
  - Currently limited to extraction only, missing --calculate-tax option

#### Legacy Features
- **Tax Optimization Engine (P1)**:
  - Intelligent tax-saving suggestions based on individual financial profile
  - Investment recommendation engine for tax efficiency
  - Deduction optimization across multiple financial instruments

- **Advanced Integration (P0)**:
  - REST API wrapper for enterprise integration
  - Database integration for historical tax data management

### [2.3.0] - Planned
- **Multi-Year Tax Planning(P1)**:
  - Historical tax analysis across multiple assessment years
  - Tax trend analysis and future planning recommendations
  - Capital gains integration for comprehensive tax calculation

- **Developer Tools(P1)**:
  - Form16 anonymization utilities for testing
  - Test data generators for development
  - Debugging and visualization tools
  - Performance profiling and optimization tools
  
- **Enhanced Format Support(P3)**:
  - Support for scanned Form16 documents (OCR)
  - Better handling of custom employer formats
  - Multi-language Form16 support

- **Pattern Recognition Enhancements (P3)**:
  - ML-based field detection for complex layouts
  - Automatic format learning and adaptation
  - Improved confidence scoring algorithms
---

## Support

For questions, bug reports, or feature requests, please visit our [GitHub Issues](https://github.com/ri-sh/Form16Extractor/issues) page.