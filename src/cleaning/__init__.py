"""
Data cleaning package for Clinical Trials Analytics Dashboard.

This package handles data quality, standardization, and transformation
for clinical trial datasets.

Modules:
- clean_trials: Main cleaning and standardization module
"""

from .clean_trials import (
    TrialDataCleaner,
    print_cleaning_report,
    main
)

__all__ = [
    "TrialDataCleaner",
    "print_cleaning_report",
    "main"
]

__version__ = "1.0.0"
