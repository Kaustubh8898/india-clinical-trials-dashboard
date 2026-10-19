# India Clinical Trials Intelligence Dashboard

A Streamlit + Plotly analytics dashboard for exploring public clinical-trial registry records with listed Indian study locations. The project includes a ClinicalTrials.gov API v2 ingestion pipeline, data-cleaning steps, sponsor and therapeutic-area summaries, geographic exploration, filters, and CSV export.

> **Data integrity note:** The CSV included in the original prototype is a legacy sample and does not contain the explicit provenance markers required by the current app. The dashboard intentionally refuses to present that file as verified registry data. Refresh it using the pipeline below before interpreting the charts or quoting any numbers.

## What the dashboard does

- Summarizes trials by recruitment status, phase, therapeutic area, sponsor, and location.
- Lets users filter by phase, status, sponsor, state, therapeutic area, and start year.
- Shows sponsor portfolio and enrollment summaries.
- Exports filtered trial records as CSV.
- Uses a dated registry snapshot. It is **not** a real-time feed.
- Keeps one row per study; location columns describe the first listed Indian site, while the india_site_count field records the number of Indian sites found. Use a site-level table for analyses that require every site separately.

The dashboard contains registry metadata, not patient-level data, treatment-effect estimates, or evidence that a therapy is effective. Therapeutic-area categories are heuristic keyword labels based on registry condition text and should be treated as exploratory.

## Data pipeline

    ClinicalTrials.gov API v2
             |
             v
    data/raw/india_trials_raw.csv
             |
             v
    src/cleaning/clean_trials.py
             |
             v
    data/processed/india_trials_clean.csv
             |
             v
    src/data_loader.py (schema + provenance checks)
             |
             v
    Streamlit dashboard

### 1. Install

Python 3.10+ is recommended.

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

### 2. Refresh the registry snapshot

The API request is public and does not require an API key.

    python -m src.ingestion.clinical_trials_api
    python -m src.cleaning.clean_trials

Run these commands in order. The ingestion job will preserve the last raw CSV if a request fails or returns no records. The cleaner requires NCT-shaped IDs, a ClinicalTrials.gov API v2 source marker, and a source URL matching each record's NCT ID. It writes the processed CSV atomically.

### 3. Start the dashboard

    streamlit run app.py

The app validates provenance before drawing charts. If validation fails, follow the error text and rerun the pipeline rather than bypassing the check.

### 4. Run tests

Install development dependencies and execute the tests:

    pip install -r requirements-dev.txt
    python -m pytest -q

## Data fields and interpretation

| Field | Meaning |
|---|---|
| nct_id | ClinicalTrials.gov study identifier |
| source_url | Registry record URL derived from the same NCT ID |
| data_source | Source marker written by the ingestion code |
| fetched_date | Time this pipeline retrieved the study record |
| phase | Registry phase enum normalized for display |
| recruitment_status | Registry recruitment status normalized for display |
| conditions | Registry condition labels joined into one string |
| city, state, country | First listed Indian study site |
| india_site_count | Number of Indian locations found for the study |
| has_indian_location | Whether source location fields indicate at least one Indian site |
| trial_duration_days | Derived only when both start and completion dates are reported at day precision and the range is non-negative |
| therapeutic_area | Exploratory keyword-based grouping of condition labels |

The source marker is a traceability check, not an independent guarantee that the registry's content is clinically correct. For research or business decisions, open the source_url and verify individual records and the date of retrieval.

## Project structure

    .
    ├── app.py
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── src/
    │   ├── config.py
    │   ├── data_loader.py
    │   ├── ingestion/clinical_trials_api.py
    │   ├── cleaning/clean_trials.py
    │   └── visualizations.py
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── tests/
    └── DATA_QUALITY.md

## Current limitations

- Each row is a study, not an individual trial site. Geographic counts therefore reflect the first listed Indian location and may undercount site activity.
- Therapeutic-area classification uses a keyword map and can misclassify conditions with ambiguous wording or assign uncommon conditions to Other.
- Duration is unavailable unless both source dates specify a day. Year-only and month-only registry dates must not be interpreted as exact days.
- Enrollment counts may be missing and represent registry enrollment fields, not necessarily final realized enrollment.
- The dashboard does not calculate clinical efficacy, patient demographics, cohort outcomes, or causal treatment comparisons.

## License

No open-source license is currently specified. Contact the repository owner before reusing this project beyond permitted GitHub viewing and forking terms.
