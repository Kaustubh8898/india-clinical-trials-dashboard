# Data Cleaning Guide

The cleaner prepares raw ClinicalTrials.gov API v2 rows for the dashboard. It is designed to be run after API ingestion, not against unprovenanced prototype rows.

## Run

    python -m src.ingestion.clinical_trials_api
    python -m src.cleaning.clean_trials

The cleaner expects the following core fields: nct_id, brief_title, sponsor, phase, conditions, recruitment_status, start_date, completion_date, enrollment_count, city, state, country, fetched_date, data_source, and source_url.

## What it does

1. Checks that each NCT ID has the expected format.
2. Requires the ClinicalTrials.gov API v2 source marker and a source URL that matches each ID.
3. Removes duplicate NCT IDs.
4. Standardizes sponsor spacing and trial phase/status labels.
5. Parses start/completion dates while preserving whether the source reported a year, month, or full day.
6. Calculates trial_duration_days only when both date fields specify a full day and the range is non-negative.
7. Normalizes city/state/country text.
8. Creates has_indian_location from country/state/site-count evidence. This means that at least one Indian site is listed; it does not mean that the entire study is restricted to India.
9. Reports missing values and writes the output CSV atomically.

## Main output columns

- nct_id: registry study ID.
- source_url and data_source: source traceability.
- fetched_date: pipeline retrieval time.
- city, state, country: first listed Indian site.
- india_site_count: count of Indian sites for a study.
- has_indian_location: derived location-presence flag.
- trial_duration_days: duration only where source date precision supports a day-level calculation.
- therapeutic_area: exploratory keyword-based classification of condition labels.

## Important limitations

A valid-looking ID is not proof that a row is true; that is why the current pipeline requires explicit source metadata. Even with metadata, source-marker validation is not an independent audit of registry values. Therapeutic area is a keyword heuristic, not a validated clinical taxonomy. Enrollment should not be described as realized enrollment unless confirmed separately.

See DATA_QUALITY.md for additional interpretation cautions.
