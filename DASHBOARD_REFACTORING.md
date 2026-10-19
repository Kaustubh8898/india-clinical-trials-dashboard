# Dashboard Refactoring Notes

This document originally recorded the first UI/data-loader refactor. Some statements in that earlier version treated the prototype CSV as verified data. Those statements are superseded and should not be used as project evidence.

Use README.md for the current setup, and DATA_QUALITY.md for provenance and interpretation rules.

The current implementation separates the pipeline into:
1. Public ClinicalTrials.gov API v2 ingestion.
2. Raw-record validation and cleaning.
3. Provenance-checked data loading.
4. Interactive Streamlit / Plotly exploration.

The committed prototype CSV does not include the provenance metadata required by the current app. After a successful refresh, the dashboard can render a dated registry snapshot. The dashboard is not real-time, does not contain patient-level data, and does not establish treatment efficacy.

For the current implementation status and known limitations, see IMPLEMENTATION_SUMMARY.md.
