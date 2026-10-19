# Quick Start — India Clinical Trials Intelligence Dashboard

## Important data note

The CSV in the original prototype is a legacy sample without the provenance fields now required by the app. The dashboard will stop and show a validation message rather than presenting those rows as verified ClinicalTrials.gov data. Refresh the dataset before using the dashboard or quoting metrics.

## Setup

Python 3.10+ is recommended.

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Refresh data

Run from the repository root, in this order:

    python -m src.ingestion.clinical_trials_api
    python -m src.cleaning.clean_trials

The first command retrieves studies with listed Indian locations from ClinicalTrials.gov API v2. The second command validates source provenance, standardizes fields, preserves date precision, and writes the cleaned CSV. A failed fetch does not replace the previous raw CSV with an empty result.

## Run the app

    streamlit run app.py

## Run regression tests

    pip install -r requirements-dev.txt
    python -m pytest -q

For the scope and limitations of the dataset, read README.md and DATA_QUALITY.md. This application is a dated registry snapshot, not a real-time feed and not a patient-outcomes or treatment-efficacy tool.
