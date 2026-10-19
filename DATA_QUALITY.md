# Data quality and provenance

## Why the current app validates provenance

The repository's original CSV files were created as a small dashboard prototype. A plausible NCT-shaped ID does not prove that the associated title, sponsor, phase, dates, or location match the public registry. The updated dashboard therefore requires each row to carry source metadata produced by the ingestion job, and it checks that the source URL matches the row's NCT ID.

These checks improve traceability; they are not an independent audit of every field against the live registry. Open individual registry URLs for high-stakes use and record the snapshot retrieval date.

## Refresh procedure

Run from the repository root:

    python -m src.ingestion.clinical_trials_api
    python -m src.cleaning.clean_trials
    streamlit run app.py

The ingestion step:
- queries the public ClinicalTrials.gov API v2 for studies whose listed location country is India;
- follows API pagination and retries transient failures;
- converts nested study fields into one row per study;
- records the API source marker, matching study URL, fetch timestamp, and number of Indian sites;
- refuses to replace the raw CSV with an empty or structurally invalid response.

The cleaning step:
- requires NCT IDs and source provenance;
- removes duplicate study IDs;
- standardizes status and phase labels;
- records date precision and only computes duration from full day-level dates;
- derives the has_indian_location flag without claiming the study is India-only;
- atomically writes the cleaned CSV.

## Interpretation cautions

1. A study can have sites in India and other countries. has_indian_location means at least one Indian site is listed, not that the study is India-only.
2. The dashboard's city/state fields represent the first Indian site returned by the registry. They are not a complete site-level dataset; india_site_count is a per-study count.
3. Therapeutic areas are keyword-derived from conditions. They are useful for exploration, not a validated clinical taxonomy.
4. Registry dates may be reported only as a year or month. Those dates are not rounded into falsely precise durations.
5. Enrollment is copied from the registry's enrollment field. It should not be described as realized enrollment unless separately confirmed.
6. Recruitment status and other registry details can change; include the fetch date when sharing a metric.
