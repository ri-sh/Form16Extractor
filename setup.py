#!/usr/bin/env python3
"""
Setup script for Taxedo - Form16 Extraction and Tax Calculation Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
with open(requirements_path, encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="form16-parser",
    version="2.1.0",
    description="A robust Python library for extracting structured data from Indian Form16 tax documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rishabh Roy",
    author_email="dev@example.com",
    url="https://github.com/ri-sh/form16x",
    license="MIT",
    
    # Package information
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    
    # Console script entry point
    entry_points={
        "console_scripts": [
            "form16x=form16x.form16_parser.cli:main",
        ],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Utilities",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "form16", "tax-calculation", "indian-tax", "pdf-extraction", 
        "tax-return", "income-tax", "automation", "finance"
    ],
    
    # Package data
    package_data={
        "form16x": [
            "*.md",
            "*.txt", 
            "*.json",
            "templates/*",
        ],
    },
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/ri-sh/form16x/issues",
        "Source": "https://github.com/ri-sh/form16x",
        "Documentation": "https://github.com/ri-sh/form16x/blob/master/README.md",
    },
)