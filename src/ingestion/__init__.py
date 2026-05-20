"""
Ingestion package for Clinical Trials Analytics Dashboard.

This package handles data ingestion from various sources including:
- ClinicalTrials.gov API v2
- CSV/Excel file uploads
- Database connections

Modules:
- clinical_trials_api: API ingestion from ClinicalTrials.gov
- validators: Data validation utilities
- processors: Data processing and cleaning
"""

from .clinical_trials_api import (
    ClinicalTrialsAPIClient,
    extract_trial_record,
    save_trials_to_csv,
    main
)

__all__ = [
    "ClinicalTrialsAPIClient",
    "extract_trial_record",
    "save_trials_to_csv",
    "main"
]

__version__ = "1.0.0"
