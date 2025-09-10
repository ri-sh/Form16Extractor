# Contributing to Form16 Extractor

Thank you for considering contributing. 

The Form16 Extractor project aims to make working with Indian tax documents easier for developers, and community contributions are what make it better.

## Ways to Contribute

- **Bug Reports**: Found something broken? Let us know.
- **Feature Requests**: Have an idea for improvement? We would appreciate your feedback.
- **Code Contributions**: Fix bugs, add features, improve performance.
- **Documentation**: Help make our docs clearer and more comprehensive.
- **Testing**: Help test on different Form16 formats and edge cases.

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/ri-sh/Form16Extractor.git
   cd Form16Extractor
   ```

2. **Set up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify Setup**
   ```bash
   # Run tests to make sure everything works
   python -m pytest
   
   # Check code formatting
   black --check .
   flake8 .
   ```

## Running Tests

We use pytest for testing:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=form16_extractor

# Run specific test categories
python -m pytest tests/unit/models/          # Model tests
python -m pytest tests/unit/extractors/      # Extractor tests
python -m pytest -m "not slow"              # Skip slow tests

# Run tests for specific Form16 components
python -m pytest tests/unit/extractors/domains/identity/
python -m pytest tests/unit/extractors/domains/salary/
```

## Code Style Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking

These run automatically via pre-commit hooks, but you can run them manually:

```bash
black .
isort .
flake8 .
mypy form16_extractor/
```

## 🐛 Reporting Bugs

Good bug reports help us fix issues faster. Please include:

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what went wrong.

**To Reproduce**
Steps to reproduce the behavior:
1. Load Form16 file '...'
2. Run extraction with '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python version: [e.g. 3.9.7]
- form16-extractor version: [e.g. 1.0.0]

**Form16 Details (if applicable):**
- Assessment Year: [e.g. 2024-25]
- Employer type: [e.g. IT Company, Government, etc.]
- Any unusual formatting or layout?

**Additional context**
Add any other context about the problem here.
```

**Important**: Never include actual personal data (PAN, names, addresses) in bug reports. Use anonymized/sample data instead.

## Feature Requests Feature Requests

We love new ideas! When suggesting features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - what problem does this solve?
3. **Propose a solution** - how should it work?
4. **Consider the scope** - should this be core functionality or a plugin?

## 🔧 Contributing Code

### Before You Start

- **Check the issues** - is someone already working on this?
- **Open an issue** for big changes to discuss the approach
- **Start small** - consider beginning with documentation or test improvements

### Pull Request Process

1. **Create a branch** with a descriptive name:
   ```bash
   git checkout -b feature/add-section-80tta-support
   git checkout -b bugfix/handle-missing-pan
   git checkout -b docs/improve-api-examples
   ```

2. **Make your changes**:
   - Write tests for new functionality
   - Update documentation if needed
   - Follow existing code patterns and style
   - Add type hints to new functions

3. **Test thoroughly**:
   ```bash
   python -m pytest
   python -m pytest --cov=form16_extractor --cov-report=html
   ```

4. **Update documentation**:
   - Add docstrings to new functions/classes
   - Update README if needed
   - Add examples for new features

5. **Submit the PR**:
   - Use a clear title and description
   - Reference related issues
   - Include testing details

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have added tests for my changes
- [ ] All new and existing tests pass
- [ ] I have tested with real Form16 documents (anonymized)

## Documentation
- [ ] I have updated the documentation
- [ ] I have added docstrings to new functions
- [ ] I have updated the CHANGELOG.md

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] My changes generate no new warnings
- [ ] No personal/sensitive data in code or tests
```

## Development Guidelines Development Guidelines

### Code Organization

```
form16_extractor/
├── extractors/           # Core extraction logic
│   ├── domains/         # Domain-specific extractors
│   │   ├── identity/    # Employee/employer extraction
│   │   ├── salary/      # Salary component extraction
│   │   └── deductions/  # Tax deductions extraction
│   └── base/            # Base extractor interfaces
├── models/              # Pydantic data models
├── pdf/                 # PDF processing utilities
└── utils/               # Helper utilities
```

### Adding New Extractors

1. **Create in appropriate domain** (`extractors/domains/`)
2. **Implement the interface** (`IExtractor`)
3. **Add comprehensive tests** (`tests/unit/extractors/domains/`)
4. **Update models** if needed (`models/form16_models.py`)

### Testing Guidelines

- **Test real scenarios** but use anonymized data
- **Test edge cases** - missing fields, malformed data
- **Test confidence scoring** - verify extraction quality
- **Mock external dependencies** - PDF libraries, etc.
- **Use descriptive test names** - `test_extract_employee_name_from_key_value_format`

### Privacy & Security

- **No real PII** in tests, examples, or documentation
- **Sanitize error messages** - don't log personal data
- **Local processing only** - no network calls
- **Secure file handling** - proper cleanup of temporary files

## Types of Contributions Types of Contributions We Need

### High Priority
- **Support for new Form16 formats** - different employers use different layouts
- **Better error handling** - more helpful error messages
- **Performance improvements** - faster processing for large batches
- **OCR support** - handle scanned/image-based Form16s

### Medium Priority  
- **Additional validation** - detect inconsistencies in tax calculations
- **Export formats** - CSV, Excel output options
- **CLI tool** - command-line interface for batch processing
- **Visualization** - generate charts from extracted data

### Documentation & Testing
- **More examples** - real-world usage patterns
- **Performance benchmarks** - how fast is it?
- **Error scenario docs** - how to handle common issues
- **Integration guides** - using with popular frameworks

## Coding Standards Coding Standards

### Python Style
- Follow **PEP 8**
- Use **type hints** everywhere
- Maximum **100 character** line length
- Prefer **descriptive names** over comments

### Documentation
- **Docstrings** for all public functions/classes
- **Examples** in docstrings where helpful
- **Type information** in docstrings
- **Error conditions** documented

### Testing
- **Arrange-Act-Assert** pattern
- **Descriptive test names**
- **One assertion per test** (generally)
- **Test both happy path and edge cases**

## Recognition

Contributors get:
- **Credit** in CHANGELOG.md and README.md
- **GitHub contributor badge**
- **Thanks** in release notes for significant contributions

## Getting Help

Stuck? Need clarification? Here's how to get help:

- **GitHub Discussions** - for questions and brainstorming
- **GitHub Issues** - for bugs and feature requests  
- **Code Review** - we'll help make your PR better

## Thank You

Every contribution makes the Form16 Extractor better for the entire Indian developer community. Whether it's fixing a typo or adding major features, your help is appreciated! 

---

*Happy coding.*