# Implementation Status — Clinical Trials Dashboard

This file supersedes earlier prototype notes that described the project as production-ready or characterized its checked-in sample rows as verified registry data. The current source of truth for setup and data interpretation is README.md and DATA_QUALITY.md.

## Implemented in the current code

- ClinicalTrials.gov API v2 client with pagination, bounded retries, structured field extraction, and atomic raw-file writes.
- Explicit source metadata on each ingested study: source name, matching registry URL, and retrieval timestamp.
- Cleaner validation for NCT IDs and provenance; duplicate-ID removal; phase/status normalization; location semantics; and date-precision-aware duration calculation.
- CSV loader with schema, unique-ID, provenance, and location checks. The current app refuses to render charts when the dataset lacks provenance.
- Corrected dashboard summaries: active sponsors means distinct sponsors with at least one active trial; most active therapeutic area is based on active trials; static duration claims have been removed.
- Regression tests for API extraction, normalization, cleaning, summary calculations, filtering, and CSV deduplication.
- GitHub Actions workflow configured to run the test suite on pushes to fix branches and pull requests to main.

## Not yet claimed as verified

- The new code has not been executed against the live ClinicalTrials.gov API in this environment.
- The checked-in legacy CSV has not been regenerated in this branch; therefore the dashboard validation gate is expected to reject it until the refresh pipeline is run.
- Automated test results should be checked in the GitHub Actions workflow. Do not describe the tests as passing until the run confirms it.
- Field-level agreement with the live registry has not been independently audited. The source marker and URL establish traceability, not clinical accuracy.

## Refresh and run

From the repository root:

    pip install -r requirements.txt
    python -m src.ingestion.clinical_trials_api
    python -m src.cleaning.clean_trials
    streamlit run app.py

Run tests with:

    pip install -r requirements-dev.txt
    python -m pytest -q

## Known analytical limitations

The current table is one row per study and keeps only the first listed Indian site for city/state display. The number of Indian sites is retained as a study-level count. Therapeutic areas use condition-keyword rules, incomplete date precision suppresses duration calculation, and enrollment counts may be missing or represent registry-planned enrollment rather than realized enrollment.
